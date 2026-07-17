extends Node2D

const MAIN_MENU_SCENE: String = "res://scenes/menus/main_menu.tscn"

@onready var player: CharacterBody2D = $Player
@onready var help_label: Label = $Interface/HelpLabel
@onready var interaction_label: Label = $Interface/InteractionLabel
@onready var status_label: Label = $Interface/StatusLabel


func _ready() -> void:
	player.global_position = GameState.player_position
	if player.has_method("apply_character_appearance"):
		player.call("apply_character_appearance")
	var dialogue_ui: Node = get_tree().get_first_node_in_group("dialogue_ui")
	if dialogue_ui != null and dialogue_ui.has_signal("dialogue_closed"):
		dialogue_ui.connect("dialogue_closed", Callable(self, "_on_dialogue_closed"))
	_configure_platform_prompts()
	_update_status()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel") and not GameState.input_locked:
		return_to_menu()
		get_viewport().set_input_as_handled()


func return_to_menu() -> void:
	if GameState.input_locked:
		return
	GameState.save_game()
	get_tree().change_scene_to_file(MAIN_MENU_SCENE)


func set_interaction_hint(is_visible: bool) -> void:
	interaction_label.visible = is_visible and not GameState.input_locked


func _on_dialogue_closed() -> void:
	_update_status()


func _configure_platform_prompts() -> void:
	if _uses_touch_controls():
		help_label.text = "Движение: экранное управление · Разговор: ДЕЙСТВИЕ · Выход: МЕНЮ"
		interaction_label.text = "Нажмите ДЕЙСТВИЕ для разговора"


func _update_status() -> void:
	var identity: String = "%s · %s · ур. %d" % [
		GameState.player_character.character_name,
		GameState.player_character.character_class_name,
		GameState.player_character.level
	]
	var objective: String
	if bool(GameState.get_flag("met_caretaker", false)):
		objective = "Сюжетный флаг: вы поговорили со Смотрителем."
	elif bool(GameState.get_flag("accepted_exploration", false)):
		objective = "Задача: осмотреть тестовую комнату."
	elif _uses_touch_controls():
		objective = "Подойдите к Смотрителю и нажмите ДЕЙСТВИЕ."
	else:
		objective = "Подойдите к Смотрителю и нажмите Enter или Пробел."
	status_label.text = "%s\n%s" % [identity, objective]


func _uses_touch_controls() -> bool:
	return OS.get_name() == "Android" or OS.get_name() == "iOS" or OS.has_feature("mobile") or DisplayServer.is_touchscreen_available()
