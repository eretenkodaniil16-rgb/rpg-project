class_name InGamePauseController
extends Node

const PAUSE_MENU_SCENE: PackedScene = preload("res://scenes/ui/in_game_pause_menu.tscn")
const MAIN_MENU_SCENE: String = "res://scenes/menus/main_menu.tscn"

var _game_world: Node = null
var _pause_menu: InGamePauseMenu = null
var _owns_tree_pause: bool = false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_game_world = get_parent()
	_install_pause_menu()
	if not tree_exiting.is_connected(_release_pause_state):
		tree_exiting.connect(_release_pause_state)


func _input(event: InputEvent) -> void:
	if not event.is_action_pressed("ui_cancel"):
		return
	if event is InputEventKey and (event as InputEventKey).echo:
		return
	if is_instance_valid(_pause_menu) and _pause_menu.handle_cancel():
		get_viewport().set_input_as_handled()
		return
	if open_pause_menu():
		get_viewport().set_input_as_handled()


func toggle_pause_menu() -> bool:
	if is_pause_menu_open():
		close_pause_menu()
		return true
	return open_pause_menu()


func open_pause_menu() -> bool:
	if not _can_open_pause_menu():
		return false
	_release_mobile_input()
	_pause_menu.open()
	get_tree().paused = true
	_owns_tree_pause = true
	return true


func close_pause_menu() -> void:
	if is_instance_valid(_pause_menu):
		_pause_menu.close()
	_release_pause_state()


func is_pause_menu_open() -> bool:
	return is_instance_valid(_pause_menu) and _pause_menu.is_open()


func get_pause_menu_for_testing() -> InGamePauseMenu:
	return _pause_menu


func _install_pause_menu() -> void:
	var interface: CanvasLayer = _game_world.get_node_or_null("Interface") as CanvasLayer
	if interface == null:
		push_warning("Не удалось установить меню паузы: узел Interface отсутствует.")
		return
	_pause_menu = PAUSE_MENU_SCENE.instantiate() as InGamePauseMenu
	if _pause_menu == null:
		push_warning("Не удалось создать сцену внутриигрового меню паузы.")
		return
	_pause_menu.name = "PauseMenu"
	_pause_menu.resume_requested.connect(close_pause_menu)
	_pause_menu.return_to_menu_requested.connect(_on_return_to_menu_requested)
	interface.add_child(_pause_menu)


func _can_open_pause_menu() -> bool:
	if not is_instance_valid(_pause_menu) or _pause_menu.is_open():
		return false
	if get_tree().paused or GameState.input_locked:
		return false
	if is_instance_valid(_game_world) and _game_world.has_method("_any_overlay_visible"):
		return not bool(_game_world.call("_any_overlay_visible"))
	return true


func _release_mobile_input() -> void:
	if not is_instance_valid(_game_world):
		return
	var mobile_controls: Node = _game_world.get_node_or_null("Interface/MobileControls")
	if mobile_controls != null and mobile_controls.has_method("release_all_input"):
		mobile_controls.call("release_all_input")


func _on_return_to_menu_requested() -> void:
	close_pause_menu()
	if is_instance_valid(_game_world) and _game_world.has_method("return_to_menu"):
		_game_world.call("return_to_menu")
		return
	push_warning("Игровой runtime не предоставляет return_to_menu; используется fallback.")
	get_tree().change_scene_to_file(MAIN_MENU_SCENE)


func _release_pause_state() -> void:
	if not _owns_tree_pause:
		return
	var tree: SceneTree = get_tree()
	if tree != null:
		tree.paused = false
	_owns_tree_pause = false
