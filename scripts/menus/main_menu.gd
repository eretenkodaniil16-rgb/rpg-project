extends Control

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const CHARACTER_CREATOR_SCENE: String = "res://scenes/character_creation/character_creator.tscn"
const SAVE_SLOTS_PANEL_SCRIPT: Script = preload("res://scripts/ui/save_slots_panel.gd")

@onready var continue_button: Button = $CenterContainer/MenuPanel/MarginContainer/VBoxContainer/ContinueButton
@onready var status_label: Label = $CenterContainer/MenuPanel/MarginContainer/VBoxContainer/StatusLabel

var _save_slots_panel: SaveSlotsPanel


func _ready() -> void:
	_install_save_slots_panel()
	_refresh_save_status()
	if not GameState.save_slots_changed.is_connected(_refresh_save_status):
		GameState.save_slots_changed.connect(_refresh_save_status)


func _exit_tree() -> void:
	if GameState.save_slots_changed.is_connected(_refresh_save_status):
		GameState.save_slots_changed.disconnect(_refresh_save_status)


func _on_new_game_pressed() -> void:
	get_tree().change_scene_to_file(CHARACTER_CREATOR_SCENE)


func _on_continue_pressed() -> void:
	if not GameState.has_save():
		_refresh_save_status()
		return
	_save_slots_panel.open_for_load()


func _on_quit_pressed() -> void:
	get_tree().quit()


func _install_save_slots_panel() -> void:
	_save_slots_panel = SAVE_SLOTS_PANEL_SCRIPT.new() as SaveSlotsPanel
	_save_slots_panel.name = "SaveSlotsPanel"
	_save_slots_panel.load_completed.connect(_on_save_loaded)
	add_child(_save_slots_panel)


func _on_save_loaded(success: bool, _kind: String, _slot_id: int) -> void:
	if success:
		get_tree().change_scene_to_file(GAME_SCENE)
		return
	status_label.text = "Не удалось загрузить выбранное сохранение."


func _refresh_save_status() -> void:
	var manual_count: int = 0
	for entry: Dictionary in GameState.list_manual_save_slots():
		if bool(entry.get("exists", false)):
			manual_count += 1
	var has_autosave: bool = bool(GameState.get_autosave_entry().get("exists", false))
	continue_button.disabled = manual_count == 0 and not has_autosave
	if continue_button.disabled:
		status_label.text = "Сохранения пока не созданы."
	elif manual_count > 0 and has_autosave:
		status_label.text = "Доступно ручных сохранений: %d · есть автосохранение." % manual_count
	elif manual_count > 0:
		status_label.text = "Доступно ручных сохранений: %d." % manual_count
	else:
		status_label.text = "Доступно автосохранение."
