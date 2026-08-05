extends Control

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const CHARACTER_CREATOR_SCENE: String = "res://scenes/character_creation/character_creator.tscn"
const SAVE_SLOTS_PANEL_SCRIPT: Script = preload("res://scripts/ui/save_slots_panel.gd")
const BUTTON_HOVER_SCALE: Vector2 = Vector2(1.022, 1.022)
const BUTTON_TWEEN_DURATION: float = 0.16

@onready var approved_background: MainMenuTiledBackground = $ApprovedBackground
@onready var atmosphere: MainMenuAtmosphere = $Atmosphere
@onready var title_glow: MainMenuTitleGlow = $TitleGlow
@onready var menu_container: CenterContainer = $CenterContainer
@onready var continue_button: Button = $CenterContainer/MenuPanel/MarginContainer/VBoxContainer/ContinueButton
@onready var new_game_button: Button = $CenterContainer/MenuPanel/MarginContainer/VBoxContainer/NewGameButton
@onready var settings_button: Button = $CenterContainer/MenuPanel/MarginContainer/VBoxContainer/SettingsButton
@onready var quit_button: Button = $CenterContainer/MenuPanel/MarginContainer/VBoxContainer/QuitButton
@onready var status_label: Label = $CenterContainer/MenuPanel/MarginContainer/VBoxContainer/StatusLabel
@onready var settings_panel: MainMenuSettingsPanel = $SettingsLayer

var _save_slots_panel: SaveSlotsPanel
var _button_tweens: Dictionary = {}
var _reduced_motion: bool = false


func _enter_tree() -> void:
	_reduced_motion = InterfaceSettingsStore.load_and_apply()


func _ready() -> void:
	approved_background.visible = approved_background.has_complete_tiles()
	_configure_menu_buttons()
	_install_save_slots_panel()
	_connect_settings_panel()
	_apply_reduced_motion(_reduced_motion)
	_refresh_save_status()
	if not GameState.save_slots_changed.is_connected(_refresh_save_status):
		GameState.save_slots_changed.connect(_refresh_save_status)
	call_deferred("_refresh_button_pivots")
	call_deferred("_restore_menu_focus")


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


func _on_settings_pressed() -> void:
	_set_menu_interaction_enabled(false)
	settings_panel.open()


func _on_quit_pressed() -> void:
	get_tree().quit()


func _configure_menu_buttons() -> void:
	for button: Button in _menu_buttons():
		button.mouse_entered.connect(_animate_menu_button.bind(button, true))
		button.mouse_exited.connect(_animate_menu_button.bind(button, false))
		button.focus_entered.connect(_animate_menu_button.bind(button, true))
		button.focus_exited.connect(_animate_menu_button.bind(button, false))


func _menu_buttons() -> Array[Button]:
	var buttons: Array[Button] = []
	buttons.append(continue_button)
	buttons.append(new_game_button)
	buttons.append(settings_button)
	buttons.append(quit_button)
	return buttons


func _refresh_button_pivots() -> void:
	for button: Button in _menu_buttons():
		button.pivot_offset = button.size * 0.5


func _animate_menu_button(button: Button, highlighted: bool) -> void:
	if not is_instance_valid(button):
		return
	var key: int = button.get_instance_id()
	_kill_button_tween(key)
	var active: bool = highlighted and not button.disabled
	var target_modulate: Color = Color(1.08, 1.1, 1.12, 1.0) if active else Color.WHITE
	if _reduced_motion:
		button.scale = Vector2.ONE
		button.modulate = target_modulate
		return
	var target_scale: Vector2 = BUTTON_HOVER_SCALE if active else Vector2.ONE
	var tween: Tween = create_tween()
	_button_tweens[key] = tween
	tween.set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.tween_property(button, "scale", target_scale, BUTTON_TWEEN_DURATION)
	tween.parallel().tween_property(button, "modulate", target_modulate, BUTTON_TWEEN_DURATION)


func _kill_button_tween(key: int) -> void:
	if not _button_tweens.has(key):
		return
	var previous: Tween = _button_tweens[key] as Tween
	if previous != null and previous.is_valid():
		previous.kill()
	_button_tweens.erase(key)


func _connect_settings_panel() -> void:
	if not settings_panel.closed.is_connected(_on_settings_closed):
		settings_panel.closed.connect(_on_settings_closed)
	if not settings_panel.reduced_motion_changed.is_connected(_on_reduced_motion_changed):
		settings_panel.reduced_motion_changed.connect(_on_reduced_motion_changed)


func _on_settings_closed() -> void:
	_set_menu_interaction_enabled(true)
	settings_button.grab_focus()


func _on_reduced_motion_changed(enabled: bool) -> void:
	_apply_reduced_motion(enabled)


func _apply_reduced_motion(enabled: bool) -> void:
	_reduced_motion = enabled
	atmosphere.set_reduced_motion(enabled)
	title_glow.set_reduced_motion(enabled)
	if enabled:
		for button: Button in _menu_buttons():
			_kill_button_tween(button.get_instance_id())
			button.scale = Vector2.ONE
			button.modulate = Color.WHITE


func _set_menu_interaction_enabled(enabled: bool) -> void:
	menu_container.mouse_filter = (
		Control.MOUSE_FILTER_PASS if enabled else Control.MOUSE_FILTER_IGNORE
	)
	for button: Button in _menu_buttons():
		button.focus_mode = Control.FOCUS_ALL if enabled else Control.FOCUS_NONE


func _restore_menu_focus() -> void:
	if continue_button.disabled:
		new_game_button.grab_focus()
	else:
		continue_button.grab_focus()


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
