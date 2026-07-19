extends Node

const SCROLL_GROUP: StringName = &"touch_scroll_containers"
const NO_POINTER: int = -999
const MOUSE_POINTER: int = -2
const DRAG_THRESHOLD_PX: float = 12.0

var _active_scroll: ScrollContainer
var _pointer_id: int = NO_POINTER
var _press_position: Vector2 = Vector2.ZERO
var _last_position: Vector2 = Vector2.ZERO
var _dragging: bool = false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	get_tree().node_added.connect(_on_node_added)
	call_deferred("_configure_existing_scroll_containers")


func _input(event: InputEvent) -> void:
	if event is InputEventScreenTouch:
		var touch: InputEventScreenTouch = event as InputEventScreenTouch
		if touch.pressed:
			_begin_pointer(touch.position, touch.index)
		else:
			_end_pointer(touch.index)
	elif event is InputEventScreenDrag:
		var drag: InputEventScreenDrag = event as InputEventScreenDrag
		_drag_pointer(drag.position, drag.index)
	elif event is InputEventMouseButton:
		var button: InputEventMouseButton = event as InputEventMouseButton
		if button.button_index == MOUSE_BUTTON_LEFT:
			if button.pressed:
				_begin_pointer(button.position, MOUSE_POINTER)
			else:
				_end_pointer(MOUSE_POINTER)
	elif event is InputEventMouseMotion and _pointer_id == MOUSE_POINTER and Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
		var motion: InputEventMouseMotion = event as InputEventMouseMotion
		_drag_pointer(motion.position, MOUSE_POINTER)


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
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
	scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
	scroll.scroll_deadzone = 0
	if not scroll.is_in_group(SCROLL_GROUP):
		scroll.add_to_group(SCROLL_GROUP)


func _begin_pointer(position: Vector2, pointer_id: int) -> void:
	if _pointer_id != NO_POINTER:
		return
	var candidate: ScrollContainer = _pick_scroll_container(position)
	if candidate == null:
		return
	_active_scroll = candidate
	_pointer_id = pointer_id
	_press_position = position
	_last_position = position
	_dragging = false


func _drag_pointer(position: Vector2, pointer_id: int) -> void:
	if pointer_id != _pointer_id or not is_instance_valid(_active_scroll):
		return
	var finger_delta: Vector2 = position - (_last_position if _dragging else _press_position)
	if not _dragging:
		var total_scroll_delta: Vector2 = _filter_scroll_delta(_active_scroll, -finger_delta)
		if total_scroll_delta.length() < DRAG_THRESHOLD_PX:
			return
		_dragging = true
	var scroll_delta: Vector2 = _filter_scroll_delta(_active_scroll, -finger_delta)
	_apply_scroll_delta(_active_scroll, scroll_delta)
	_last_position = position
	get_viewport().set_input_as_handled()


func _end_pointer(pointer_id: int) -> void:
	if pointer_id != _pointer_id:
		return
	if _dragging:
		get_viewport().set_input_as_handled()
	_active_scroll = null
	_pointer_id = NO_POINTER
	_press_position = Vector2.ZERO
	_last_position = Vector2.ZERO
	_dragging = false


func _pick_scroll_container(position: Vector2) -> ScrollContainer:
	var selected: ScrollContainer
	var selected_depth: int = -1
	var selected_area: float = INF
	for value: Node in get_tree().get_nodes_in_group(SCROLL_GROUP):
		var scroll: ScrollContainer = value as ScrollContainer
		if not is_instance_valid(scroll) or not scroll.is_visible_in_tree():
			continue
		if not scroll.get_global_rect().has_point(position) or not _can_scroll(scroll):
			continue
		var depth: int = _node_depth(scroll)
		var area: float = scroll.size.x * scroll.size.y
		if depth > selected_depth or (depth == selected_depth and area < selected_area):
			selected = scroll
			selected_depth = depth
			selected_area = area
	return selected


func _node_depth(node: Node) -> int:
	var depth: int = 0
	var current: Node = node
	while current != null:
		depth += 1
		current = current.get_parent()
	return depth


func _can_scroll(scroll: ScrollContainer) -> bool:
	return _horizontal_scroll_limit(scroll) > 0 or _vertical_scroll_limit(scroll) > 0


func _filter_scroll_delta(scroll: ScrollContainer, delta: Vector2) -> Vector2:
	return Vector2(delta.x if _horizontal_scroll_limit(scroll) > 0 else 0.0, delta.y if _vertical_scroll_limit(scroll) > 0 else 0.0)


func _apply_scroll_delta(scroll: ScrollContainer, delta: Vector2) -> void:
	var horizontal_limit: int = _horizontal_scroll_limit(scroll)
	var vertical_limit: int = _vertical_scroll_limit(scroll)
	if horizontal_limit > 0 and not is_zero_approx(delta.x):
		scroll.scroll_horizontal = clampi(scroll.scroll_horizontal + roundi(delta.x), 0, horizontal_limit)
	if vertical_limit > 0 and not is_zero_approx(delta.y):
		scroll.scroll_vertical = clampi(scroll.scroll_vertical + roundi(delta.y), 0, vertical_limit)


func _horizontal_scroll_limit(scroll: ScrollContainer) -> int:
	var bar: HScrollBar = scroll.get_h_scroll_bar()
	return maxi(roundi(bar.max_value - bar.page), 0) if bar != null else 0


func _vertical_scroll_limit(scroll: ScrollContainer) -> int:
	var bar: VScrollBar = scroll.get_v_scroll_bar()
	return maxi(roundi(bar.max_value - bar.page), 0) if bar != null else 0
