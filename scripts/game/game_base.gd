extends Node2D

const MAIN_MENU_SCENE: String = "res://scenes/menus/main_menu.tscn"
const BATTLE_GRID_SCRIPT: Script = preload("res://scripts/game/battle_grid.gd")

@onready var player: CharacterBody2D = $Player
@onready var help_label: Label = $Interface/HelpLabel
@onready var interaction_label: Label = $Interface/InteractionLabel
@onready var status_label: Label = $Interface/StatusLabel
@onready var mobile_action_button: Button = $Interface/MobileControls/InteractButton

var _battle_grid: Node2D


func _ready() -> void:
	_build_battle_grid()
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
	set_interaction_action(is_visible, "поговорить со Смотрителем", "РАЗГОВОР")


func set_interaction_action(is_visible: bool, action_description: String, mobile_button_text: String = "ДЕЙСТВИЕ") -> void:
	interaction_label.visible = is_visible and not GameState.input_locked
	if is_visible:
		if _uses_touch_controls():
			interaction_label.text = "Нажмите %s, чтобы %s" % [mobile_button_text, action_description]
		else:
			interaction_label.text = "Нажмите Enter или Пробел, чтобы %s" % action_description
	mobile_action_button.text = mobile_button_text if is_visible else "ДЕЙСТВИЕ"


func _on_dialogue_closed() -> void:
	_update_status()


func _configure_platform_prompts() -> void:
	if _uses_touch_controls():
		help_label.text = "Движение задаёт направление · ЦЕЛЬ: выбор/сброс · Без цели ВЫСТРЕЛ летит вперёд"
	else:
		help_label.text = "Стрелки: движение/направление · Tab: цель/сброс · F: атака или свободный выстрел"


func _update_status() -> void:
	var identity: String = "%s · %s · ур. %d" % [
		GameState.player_character.character_name,
		GameState.player_character.character_class_name,
		GameState.player_character.level
	]
	status_label.text = "%s\n%s" % [identity, GameState.get_current_objective_text()]


func _uses_touch_controls() -> bool:
	return OS.get_name() == "Android" or OS.get_name() == "iOS" or OS.has_feature("mobile") or DisplayServer.is_touchscreen_available()


func _build_battle_grid() -> void:
	_battle_grid = BATTLE_GRID_SCRIPT.new() as Node2D
	_battle_grid.name = "BattleGrid"
	_battle_grid.z_index = 1
	add_child(_battle_grid)
	player.z_index = 10
