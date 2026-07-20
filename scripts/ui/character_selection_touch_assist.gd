extends Node

const TAP_MAX_DISTANCE_PX: float = 16.0
const TAP_MAX_PATH_PX: float = 24.0
const TAP_MAX_DURATION_MSEC: int = 650
const HIT_MARGIN_PX: float = 14.0

var _touch_states: Dictionary = {}


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	set_process_input(true)


func _exit_tree() -> void:
	_touch_states.clear()


func _input(event: InputEvent) -> void:
	if event is InputEventScreenTouch:
		var touch: InputEventScreenTouch = event as InputEventScreenTouch
		if touch.device == InputEvent.DEVICE_ID_EMULATION:
			return
		if touch.pressed:
			_begin_touch(touch)
		else:
			_finish_touch(touch)
	elif event is InputEventScreenDrag:
		var drag: InputEventScreenDrag = event as InputEventScreenDrag
		if drag.device != InputEvent.DEVICE_ID_EMULATION:
			_update_drag(drag)


func _begin_touch(event: InputEventScreenTouch) -> void:
	var button: BaseButton = _selector_button_at(event.position)
	if button == null:
		return
	_touch_states[event.index] = {
		"button": button,
		"press_position": event.position,
		"last_position": event.position,
		"maximum_distance": 0.0,
		"path_length": 0.0,
		"started_msec": Time.get_ticks_msec()
	}


func _update_drag(event: InputEventScreenDrag) -> void:
	if not _touch_states.has(event.index):
		return
	var state: Dictionary = _touch_states[event.index]
	var press_position: Vector2 = state.get("press_position", event.position)
	var last_position: Vector2 = state.get("last_position", event.position)
	state["maximum_distance"] = maxf(
		float(state.get("maximum_distance", 0.0)),
		event.position.distance_to(press_position)
	)
	state["path_length"] = float(state.get("path_length", 0.0)) + event.position.distance_to(last_position)
	state["last_position"] = event.position
	_touch_states[event.index] = state


func _finish_touch(event: InputEventScreenTouch) -> void:
	if not _touch_states.has(event.index):
		return
	var state: Dictionary = _touch_states[event.index]
	_touch_states.erase(event.index)
	var button: BaseButton = state.get("button") as BaseButton
	if not is_instance_valid(button) or button.disabled or not button.is_visible_in_tree():
		return
	if Time.get_ticks_msec() - int(state.get("started_msec", 0)) > TAP_MAX_DURATION_MSEC:
		return
	if float(state.get("maximum_distance", 0.0)) > TAP_MAX_DISTANCE_PX:
		return
	if float(state.get("path_length", 0.0)) > TAP_MAX_PATH_PX:
		return
	if not button.get_global_rect().grow(HIT_MARGIN_PX).has_point(event.position):
		return
	call_deferred("_activate_button", button)


func _activate_button(button: BaseButton) -> void:
	if not is_instance_valid(button) or button.disabled or not button.is_visible_in_tree():
		return
	button.emit_signal("pressed")


func _selector_button_at(position: Vector2) -> BaseButton:
	return _deepest_selector_button(get_tree().root, position, null, -1)


func _deepest_selector_button(node: Node, position: Vector2, best: BaseButton, best_depth: int) -> BaseButton:
	var result: BaseButton = best
	var result_depth: int = best_depth
	if node is BaseButton:
		var button: BaseButton = node as BaseButton
		if button.has_meta("selector_id") and button.is_visible_in_tree() and not button.disabled:
			var depth: int = _node_depth(button)
			if depth > result_depth and button.get_global_rect().grow(HIT_MARGIN_PX).has_point(position):
				result = button
				result_depth = depth
	for child: Node in node.get_children():
		var candidate: BaseButton = _deepest_selector_button(child, position, result, result_depth)
		if candidate != null:
			var candidate_depth: int = _node_depth(candidate)
			if candidate_depth > result_depth:
				result = candidate
				result_depth = candidate_depth
	return result


func _node_depth(node: Node) -> int:
	var depth: int = 0
	var current: Node = node
	while current != null:
		depth += 1
		current = current.get_parent()
	return depth
