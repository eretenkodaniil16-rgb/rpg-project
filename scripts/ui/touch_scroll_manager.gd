extends Node

const SCROLL_GROUP: StringName = &"touch_scroll_containers"
const HORIZONTAL_DEADZONE_PX: int = 4
const VERTICAL_DEADZONE_PX: int = 6
const NESTED_VERTICAL_DEADZONE_PX: int = 10
const OMNIDIRECTIONAL_DEADZONE_PX: int = 8


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	get_tree().node_added.connect(_on_node_added)
	call_deferred("_configure_existing_scroll_containers")


func _exit_tree() -> void:
	if get_tree() != null and get_tree().node_added.is_connected(_on_node_added):
		get_tree().node_added.disconnect(_on_node_added)


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
		call_deferred("_configure_ancestor_scroll_containers", node)


func _configure_ancestor_scroll_containers(node: Node) -> void:
	var current: Node = node.get_parent()
	while current != null:
		if current is ScrollContainer:
			_configure_scroll_container(current as ScrollContainer)
		current = current.get_parent()


func _configure_scroll_container(scroll: ScrollContainer) -> void:
	if not is_instance_valid(scroll):
		return
	var horizontal_enabled: bool = scroll.horizontal_scroll_mode != ScrollContainer.SCROLL_MODE_DISABLED
	var vertical_enabled: bool = scroll.vertical_scroll_mode != ScrollContainer.SCROLL_MODE_DISABLED
	if horizontal_enabled:
		scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
	if vertical_enabled:
		scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER

	scroll.scroll_deadzone = _deadzone_for(scroll, horizontal_enabled, vertical_enabled)
	scroll.scroll_horizontal_by_default = horizontal_enabled and not vertical_enabled
	scroll.scroll_hint_mode = ScrollContainer.SCROLL_HINT_MODE_ALL
	scroll.tile_scroll_hint = false
	scroll.mouse_force_pass_scroll_events = true
	scroll.set_meta("touch_scroll_horizontal", horizontal_enabled)
	scroll.set_meta("touch_scroll_vertical", vertical_enabled)
	scroll.set_meta("touch_scroll_nested", _has_nested_scroll_container(scroll))
	if not scroll.is_in_group(SCROLL_GROUP):
		scroll.add_to_group(SCROLL_GROUP)


func _deadzone_for(scroll: ScrollContainer, horizontal_enabled: bool, vertical_enabled: bool) -> int:
	if horizontal_enabled and not vertical_enabled:
		return HORIZONTAL_DEADZONE_PX
	if vertical_enabled and not horizontal_enabled:
		return NESTED_VERTICAL_DEADZONE_PX if _has_nested_scroll_container(scroll) else VERTICAL_DEADZONE_PX
	return OMNIDIRECTIONAL_DEADZONE_PX


func _has_nested_scroll_container(scroll: ScrollContainer) -> bool:
	for child: Node in scroll.get_children():
		if _node_contains_scroll_container(child):
			return true
	return false


func _node_contains_scroll_container(node: Node) -> bool:
	if node is ScrollContainer:
		return true
	for child: Node in node.get_children():
		if _node_contains_scroll_container(child):
			return true
	return false
