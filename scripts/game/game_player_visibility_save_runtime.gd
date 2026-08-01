extends "res://scripts/game/game_guard_post_polish_runtime.gd"

const MAIN_MENU_SCENE: String = "res://scenes/menus/main_menu.tscn"
const GAME_SCENE: String = "res://scenes/game/game.tscn"
const CHARACTER_CREATOR_SCENE: String = "res://scenes/character_creation/character_creator.tscn"
const PAUSE_SAVE_MENU_SCRIPT: Script = preload("res://scripts/ui/game_pause_save_menu.gd")

var _pause_save_menu: GamePauseSaveMenu
var _defeat_transition_running: bool = false


func _ready() -> void:
	super._ready()
	_install_pause_save_menu()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel") and is_instance_valid(_pause_save_menu) and _pause_save_menu.is_menu_open():
		_pause_save_menu.close_menu()
		get_viewport().set_input_as_handled()
		return
	super._unhandled_input(event)


func return_to_menu() -> void:
	if not is_instance_valid(_pause_save_menu):
		return
	if GameState.input_locked and not _pause_save_menu.is_menu_open():
		return
	_pause_save_menu.toggle_menu()


func _any_overlay_visible() -> bool:
	return super._any_overlay_visible() or (is_instance_valid(_pause_save_menu) and _pause_save_menu.is_menu_open())


func _target_is_valid(target: Node) -> bool:
	return super._target_is_valid(target) and _target_is_visible_to_player(target)


func _select_nearest_target() -> void:
	var targets: Array[Node] = _visible_active_targets()
	if targets.is_empty():
		_set_selected_target(null)
		return
	var nearest: Node = targets[0]
	var nearest_distance: float = player.global_position.distance_squared_to((nearest as Node2D).global_position)
	for target: Node in targets:
		var candidate_distance: float = player.global_position.distance_squared_to((target as Node2D).global_position)
		if candidate_distance < nearest_distance:
			nearest = target
			nearest_distance = candidate_distance
	_set_selected_target(nearest)


func _cycle_target() -> void:
	if GameState.input_locked or _attack_in_progress or _any_overlay_visible():
		return
	if _turn_system.active and not _turn_system.is_player_turn(player):
		show_combat_message("Сейчас ход другого участника.", false)
		return
	var targets: Array[Node] = _visible_active_targets()
	if targets.is_empty():
		_set_selected_target(null)
		show_combat_message("В поле зрения нет доступных целей.", false)
		return
	var current_index: int = targets.find(_selected_target)
	if current_index < 0:
		_set_selected_target(targets[0])
		show_combat_message("Цель выбрана. Расстояние показано на поле.", true)
	elif current_index + 1 < targets.size():
		_set_selected_target(targets[current_index + 1])
		show_combat_message("Выбрана следующая видимая цель.", true)
	else:
		_set_selected_target(null)
		show_combat_message("Цель снята.", true)


func handle_player_defeat(_source: Node = null) -> void:
	if _defeat_transition_running:
		return
	_defeat_transition_running = true
	GameState.input_locked = true
	if GameState.has_manual_save():
		show_combat_message("Персонаж погиб. Загружается последнее ручное сохранение.", false)
		await get_tree().create_timer(1.0).timeout
		if GameState.load_last_manual_save():
			GameState.input_locked = false
			get_tree().change_scene_to_file(GAME_SCENE)
			return
		show_combat_message("Последнее сохранение повреждено. Начинается новая игра.", false)
	else:
		show_combat_message("Персонаж погиб. Ручных сохранений нет — игра начнётся сначала.", false)
		await get_tree().create_timer(1.0).timeout
	GameState.discard_autosave()
	GameState.new_game()
	GameState.input_locked = false
	get_tree().change_scene_to_file(CHARACTER_CREATOR_SCENE)


func _install_pause_save_menu() -> void:
	if is_instance_valid(_pause_save_menu):
		return
	_pause_save_menu = PAUSE_SAVE_MENU_SCRIPT.new() as GamePauseSaveMenu
	_pause_save_menu.name = "GamePauseSaveMenu"
	_pause_save_menu.main_menu_requested.connect(_leave_to_main_menu)
	$Interface.add_child(_pause_save_menu)


func _leave_to_main_menu() -> void:
	GameState.input_locked = false
	GameState.save_game()
	get_tree().change_scene_to_file(MAIN_MENU_SCENE)


func _visible_active_targets() -> Array[Node]:
	var result: Array[Node] = []
	for target: Node in super._available_targets():
		if _target_is_visible_to_player(target):
			result.append(target)
	return result


func _target_is_visible_to_player(target: Node) -> bool:
	if not is_instance_valid(target) or not (target is Node2D):
		return false
	var visibility: Node = get_tree().get_first_node_in_group("player_visibility")
	if visibility == null or not visibility.has_method("is_world_position_visible"):
		return true
	return bool(visibility.call("is_world_position_visible", (target as Node2D).global_position))
