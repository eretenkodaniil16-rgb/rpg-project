extends Node

const SCROLL_GROUP: StringName = &"touch_scroll_containers"
const PRESS_DRAG_DEADZONE_PX: int = 12


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


func _configure_scroll_container(scroll: ScrollContainer) -> void:
	if not is_instance_valid(scroll):
		return
	if scroll.horizontal_scroll_mode != ScrollContainer.SCROLL_MODE_DISABLED:
		scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
	if scroll.vertical_scroll_mode != ScrollContainer.SCROLL_MODE_DISABLED:
		scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
	scroll.scroll_deadzone = PRESS_DRAG_DEADZONE_PX
	if not scroll.is_in_group(SCROLL_GROUP):
		scroll.add_to_group(SCROLL_GROUP)
