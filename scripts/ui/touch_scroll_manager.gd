extends Node

const SCROLL_GROUP: StringName = &"touch_scroll_containers"
const AXIS_NONE: int = 0
const AXIS_HORIZONTAL: int = 1
const AXIS_VERTICAL: int = 2

# Native ScrollContainer dragging is disabled because child Buttons can consume the
# gesture before it reaches the container. The manager handles physical touch
# events in _input(), before GUI dispatch.
const NATIVE_TOUCH_DEADZONE_PX: int = 100000
const GESTURE_START_SCREEN_PX: float = 12.0
const DIAGONAL_COMMIT_SCREEN_PX: float = 24.0
const AXIS_DOMINANCE_RATIO: float = 1.18
const MIN_FLING_SCREEN_SPEED: float = 220.0
const MAX_FLING_LOGICAL_SPEED: float = 3600.0
const INERTIA_FRICTION: float = 7.5
const INERTIA_STOP_LOGICAL_SPEED: float = 32.0
const EMULATED_MOUSE_SUPPRESSION_MSEC: int = 140
const CANCEL_EVENT_DEVICE_ID: int = 17001

var _touch_states: Dictionary = {}
var _inertia_states: Dictionary = {}
var _suppress_emulated_mouse_until_msec: int = 0


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	set_process(true)
	set_process_input(true)
	get_tree().node_added.connect(_on_node_added)
	call_deferred("_configure_existing_scroll_containers")


func _exit_tree() -> void:
	if get_tree() != null and get_tree().node_added.is_connected(_on_node_added):
		get_tree().node_added.disconnect(_on_node_added)
	_touch_states.clear()
	_inertia_states.clear()


func _input(event: InputEvent) -> void:
	if event.device == CANCEL_EVENT_DEVICE_ID:
		return
	if event is InputEventScreenTouch:
		var touch: InputEventScreenTouch = event as InputEventScreenTouch
		if touch.device != InputEvent.DEVICE_ID_EMULATION:
			_handle_screen_touch(touch)
		return
	if event is InputEventScreenDrag:
		var drag: InputEventScreenDrag = event as InputEventScreenDrag
		if drag.device != InputEvent.DEVICE_ID_EMULATION:
			_handle_screen_drag(drag)
		return
	if _should_suppress_emulated_mouse(event):
		get_viewport().set_input_as_handled()


func _process(delta: float) -> void:
	if _inertia_states.is_empty():
		return
	var finished_ids: Array[int] = []
	for key: Variant in _inertia_states.keys():
		var instance_id: int = int(key)
		var state: Dictionary = _inertia_states.get(instance_id, {})
		var scroll: ScrollContainer = state.get("scroll") as ScrollContainer
		if not is_instance_valid(scroll):
			finished_ids.append(instance_id)
			continue
		var axis: int = int(state.get("axis", AXIS_NONE))
		var velocity: float = float(state.get("velocity", 0.0))
		if axis == AXIS_NONE or absf(velocity) < INERTIA_STOP_LOGICAL_SPEED:
			finished_ids.append(instance_id)
			continue
		var before: float = _scroll_value(scroll, axis)
		_apply_finger_delta(scroll, axis, velocity * delta)
		var after: float = _scroll_value(scroll, axis)
		velocity *= exp(-INERTIA_FRICTION * delta)
		state["velocity"] = velocity
		_inertia_states[instance_id] = state
		if is_equal_approx(before, after):
			finished_ids.append(instance_id)
	for instance_id: int in finished_ids:
		_finish_inertia(instance_id, true)


func _configure_existing_scroll_containers() -> void:
	_configure_node_tree(get_tree().root)


func _configure_node_tree(node: Node) -> void:
	if node is ScrollContainer:
		_configure_scroll_container(node as ScrollContainer)
	for child: Node in node.get_children():
		_configure_node_tree(child)


func _on_node_added(node: Node) -> void:
	if node is ScrollContainer:
		call_deferred("_configure_scroll_container", node as ScrollContainer)


func _configure_scroll_container(scroll: ScrollContainer) -> void:
	if not is_instance_valid(scroll):
		return
	var horizontal_enabled: bool = scroll.horizontal_scroll_mode != ScrollContainer.SCROLL_MODE_DISABLED
	var vertical_enabled: bool = scroll.vertical_scroll_mode != ScrollContainer.SCROLL_MODE_DISABLED
	if horizontal_enabled:
		scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
	if vertical_enabled:
		scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
	# Prevent the built-in touch handler from applying the same drag a second time.
	scroll.scroll_deadzone = NATIVE_TOUCH_DEADZONE_PX
	scroll.scroll_horizontal_by_default = horizontal_enabled and not vertical_enabled
	scroll.scroll_hint_mode = ScrollContainer.SCROLL_HINT_MODE_ALL
	scroll.tile_scroll_hint = false
	scroll.mouse_force_pass_scroll_events = true
	scroll.set_meta("touch_scroll_horizontal", horizontal_enabled)
	scroll.set_meta("touch_scroll_vertical", vertical_enabled)
	if not scroll.is_in_group(SCROLL_GROUP):
		scroll.add_to_group(SCROLL_GROUP)


func _handle_screen_touch(event: InputEventScreenTouch) -> void:
	if event.pressed:
		_begin_touch(event)
	else:
		_end_touch(event)


func _begin_touch(event: InputEventScreenTouch) -> void:
	var candidates: Array[ScrollContainer] = _scroll_candidates_at(event.position)
	# Touching a moving list must stop it immediately, even when the finger
	# remains still and the gesture later resolves as a normal tap.
	for candidate: ScrollContainer in candidates:
		_stop_inertia(candidate, true)
	_touch_states[event.index] = {
		"candidates": candidates,
		"screen_delta": Vector2.ZERO,
		"logical_delta": Vector2.ZERO,
		"logical_velocity": Vector2.ZERO,
		"screen_velocity": Vector2.ZERO,
		"axis": AXIS_NONE,
		"scroll": null,
		"claimed": false,
		"continued_inertia": false,
	}


func _handle_screen_drag(event: InputEventScreenDrag) -> void:
	if not _touch_states.has(event.index):
		return
	var state: Dictionary = _touch_states[event.index]
	var screen_delta: Vector2 = state.get("screen_delta", Vector2.ZERO)
	var logical_delta: Vector2 = state.get("logical_delta", Vector2.ZERO)
	screen_delta += event.screen_relative
	logical_delta += event.relative
	state["screen_delta"] = screen_delta
	state["logical_delta"] = logical_delta
	var previous_logical_velocity: Vector2 = state.get("logical_velocity", Vector2.ZERO)
	var previous_screen_velocity: Vector2 = state.get("screen_velocity", Vector2.ZERO)
	state["logical_velocity"] = previous_logical_velocity.lerp(event.velocity, 0.42)
	state["screen_velocity"] = previous_screen_velocity.lerp(event.screen_velocity, 0.42)

	if not bool(state.get("claimed", false)):
		var axis: int = _axis_for_screen_delta(screen_delta)
		if axis == AXIS_NONE:
			_touch_states[event.index] = state
			return
		var scroll: ScrollContainer = _pick_scroll_for_axis(
			state.get("candidates", []),
			axis,
			_component(screen_delta, axis)
		)
		if scroll == null:
			_touch_states[event.index] = state
			return
		var continued_inertia: bool = _stop_inertia(scroll, false)
		state["axis"] = axis
		state["scroll"] = scroll
		state["claimed"] = true
		state["continued_inertia"] = continued_inertia
		if not continued_inertia:
			scroll.emit_signal("scroll_started")
		_cancel_gui_press(event.index, event.position)
		_apply_finger_delta(scroll, axis, _component(logical_delta, axis))
		state["logical_delta"] = Vector2.ZERO
	else:
		var active_scroll: ScrollContainer = state.get("scroll") as ScrollContainer
		var active_axis: int = int(state.get("axis", AXIS_NONE))
		if is_instance_valid(active_scroll) and active_axis != AXIS_NONE:
			_apply_finger_delta(active_scroll, active_axis, _component(event.relative, active_axis))

	_touch_states[event.index] = state
	_suppress_emulated_mouse()
	get_viewport().set_input_as_handled()


func _end_touch(event: InputEventScreenTouch) -> void:
	if not _touch_states.has(event.index):
		return
	var state: Dictionary = _touch_states[event.index]
	_touch_states.erase(event.index)
	if not bool(state.get("claimed", false)):
		return
	_suppress_emulated_mouse()
	get_viewport().set_input_as_handled()
	var scroll: ScrollContainer = state.get("scroll") as ScrollContainer
	var axis: int = int(state.get("axis", AXIS_NONE))
	if not is_instance_valid(scroll) or axis == AXIS_NONE:
		return
	var logical_velocity: Vector2 = state.get("logical_velocity", Vector2.ZERO)
	var screen_velocity: Vector2 = state.get("screen_velocity", Vector2.ZERO)
	var axis_screen_speed: float = absf(_component(screen_velocity, axis))
	var axis_logical_velocity: float = clampf(
		_component(logical_velocity, axis),
		-MAX_FLING_LOGICAL_SPEED,
		MAX_FLING_LOGICAL_SPEED
	)
	if axis_screen_speed >= MIN_FLING_SCREEN_SPEED and absf(axis_logical_velocity) >= INERTIA_STOP_LOGICAL_SPEED:
		_inertia_states[scroll.get_instance_id()] = {
			"scroll": scroll,
			"axis": axis,
			"velocity": axis_logical_velocity,
		}
	else:
		scroll.emit_signal("scroll_ended")


func _axis_for_screen_delta(delta: Vector2) -> int:
	var horizontal: float = absf(delta.x)
	var vertical: float = absf(delta.y)
	var largest: float = maxf(horizontal, vertical)
	if largest < GESTURE_START_SCREEN_PX:
		return AXIS_NONE
	if horizontal >= vertical * AXIS_DOMINANCE_RATIO:
		return AXIS_HORIZONTAL
	if vertical >= horizontal * AXIS_DOMINANCE_RATIO:
		return AXIS_VERTICAL
	if largest >= DIAGONAL_COMMIT_SCREEN_PX:
		return AXIS_HORIZONTAL if horizontal >= vertical else AXIS_VERTICAL
	return AXIS_NONE


func _scroll_candidates_at(position: Vector2) -> Array[ScrollContainer]:
	var result: Array[ScrollContainer] = []
	for node: Node in get_tree().get_nodes_in_group(SCROLL_GROUP):
		var scroll: ScrollContainer = node as ScrollContainer
		if not is_instance_valid(scroll) or not scroll.is_visible_in_tree():
			continue
		if scroll.size.x <= 0.0 or scroll.size.y <= 0.0:
			continue
		if not scroll.get_global_rect().has_point(position):
			continue
		if not _point_inside_clipping_ancestors(scroll, position):
			continue
		result.append(scroll)
	return result


func _point_inside_clipping_ancestors(control: Control, position: Vector2) -> bool:
	var current: Node = control
	while current != null:
		if current is Control:
			var current_control: Control = current as Control
			if current_control.clip_contents and not current_control.get_global_rect().has_point(position):
				return false
		current = current.get_parent()
	return true


func _pick_scroll_for_axis(candidates: Array, axis: int, finger_delta: float) -> ScrollContainer:
	var directional_best: ScrollContainer = null
	var directional_depth: int = -1
	var fallback_best: ScrollContainer = null
	var fallback_depth: int = -1
	for candidate: Variant in candidates:
		var scroll: ScrollContainer = candidate as ScrollContainer
		if not is_instance_valid(scroll):
			continue
		if not _axis_enabled(scroll, axis) or _scroll_limit(scroll, axis) <= 0.5:
			continue
		var depth: int = _node_depth(scroll)
		if depth > fallback_depth:
			fallback_best = scroll
			fallback_depth = depth
		if _can_scroll_in_direction(scroll, axis, finger_delta) and depth > directional_depth:
			directional_best = scroll
			directional_depth = depth
	return directional_best if directional_best != null else fallback_best


func _axis_enabled(scroll: ScrollContainer, axis: int) -> bool:
	if axis == AXIS_HORIZONTAL:
		return bool(scroll.get_meta("touch_scroll_horizontal", false))
	if axis == AXIS_VERTICAL:
		return bool(scroll.get_meta("touch_scroll_vertical", false))
	return false


func _can_scroll_in_direction(scroll: ScrollContainer, axis: int, finger_delta: float) -> bool:
	var value: float = _scroll_value(scroll, axis)
	var limit: float = _scroll_limit(scroll, axis)
	var scroll_delta: float = -finger_delta
	if scroll_delta > 0.0:
		return value < limit - 0.5
	if scroll_delta < 0.0:
		return value > 0.5
	return true


func _apply_finger_delta(scroll: ScrollContainer, axis: int, finger_delta: float) -> void:
	if not is_instance_valid(scroll) or is_zero_approx(finger_delta):
		return
	var limit: float = _scroll_limit(scroll, axis)
	if axis == AXIS_HORIZONTAL:
		var horizontal_bar: HScrollBar = scroll.get_h_scroll_bar()
		horizontal_bar.value = clampf(horizontal_bar.value - finger_delta, 0.0, limit)
	elif axis == AXIS_VERTICAL:
		var vertical_bar: VScrollBar = scroll.get_v_scroll_bar()
		vertical_bar.value = clampf(vertical_bar.value - finger_delta, 0.0, limit)


func _scroll_value(scroll: ScrollContainer, axis: int) -> float:
	if axis == AXIS_HORIZONTAL:
		return scroll.get_h_scroll_bar().value
	if axis == AXIS_VERTICAL:
		return scroll.get_v_scroll_bar().value
	return 0.0


func _scroll_limit(scroll: ScrollContainer, axis: int) -> float:
	if axis == AXIS_HORIZONTAL:
		var horizontal_bar: HScrollBar = scroll.get_h_scroll_bar()
		return maxf(horizontal_bar.max_value - horizontal_bar.page, 0.0)
	if axis == AXIS_VERTICAL:
		var vertical_bar: VScrollBar = scroll.get_v_scroll_bar()
		return maxf(vertical_bar.max_value - vertical_bar.page, 0.0)
	return 0.0


func _node_depth(node: Node) -> int:
	var depth: int = 0
	var current: Node = node
	while current.get_parent() != null:
		depth += 1
		current = current.get_parent()
	return depth


func _component(vector: Vector2, axis: int) -> float:
	return vector.x if axis == AXIS_HORIZONTAL else vector.y


func _stop_inertia(scroll: ScrollContainer, emit_ended: bool) -> bool:
	if not is_instance_valid(scroll):
		return false
	var instance_id: int = scroll.get_instance_id()
	if not _inertia_states.has(instance_id):
		return false
	_finish_inertia(instance_id, emit_ended)
	return true


func _finish_inertia(instance_id: int, emit_ended: bool) -> void:
	if not _inertia_states.has(instance_id):
		return
	var state: Dictionary = _inertia_states[instance_id]
	_inertia_states.erase(instance_id)
	var scroll: ScrollContainer = state.get("scroll") as ScrollContainer
	if emit_ended and is_instance_valid(scroll):
		scroll.emit_signal("scroll_ended")


func _cancel_gui_press(touch_index: int, position: Vector2) -> void:
	# Buttons receive an emulated mouse press before the gesture is classified.
	# A canceled release clears their pressed state without activating them.
	var mouse_cancel: InputEventMouseButton = InputEventMouseButton.new()
	mouse_cancel.device = CANCEL_EVENT_DEVICE_ID
	mouse_cancel.position = position
	mouse_cancel.global_position = position
	mouse_cancel.button_index = MOUSE_BUTTON_LEFT
	mouse_cancel.button_mask = 0
	mouse_cancel.pressed = false
	mouse_cancel.canceled = true
	Input.parse_input_event(mouse_cancel)

	var touch_cancel: InputEventScreenTouch = InputEventScreenTouch.new()
	touch_cancel.device = CANCEL_EVENT_DEVICE_ID
	touch_cancel.index = touch_index
	touch_cancel.position = position
	touch_cancel.pressed = false
	touch_cancel.canceled = true
	Input.parse_input_event(touch_cancel)


func _suppress_emulated_mouse() -> void:
	_suppress_emulated_mouse_until_msec = maxi(
		_suppress_emulated_mouse_until_msec,
		Time.get_ticks_msec() + EMULATED_MOUSE_SUPPRESSION_MSEC
	)


func _should_suppress_emulated_mouse(event: InputEvent) -> bool:
	if not (event is InputEventMouseButton or event is InputEventMouseMotion):
		return false
	if event.device != InputEvent.DEVICE_ID_EMULATION:
		return false
	if Time.get_ticks_msec() <= _suppress_emulated_mouse_until_msec:
		return true
	for state_value: Variant in _touch_states.values():
		if state_value is Dictionary:
			var touch_state: Dictionary = state_value
			if bool(touch_state.get("claimed", false)):
				return true
	return false
