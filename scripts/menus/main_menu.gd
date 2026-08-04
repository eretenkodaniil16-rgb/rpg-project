extends Control

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const CHARACTER_CREATOR_SCENE: String = "res://scenes/character_creation/character_creator.tscn"
const SAVE_SLOTS_PANEL_SCRIPT: Script = preload("res://scripts/ui/save_slots_panel.gd")
const MAIN_MENU_BACKGROUND_PATH: String = "res://assets/branding/main_menu/approved/main_menu_tower_down_title_v01.webp"
const BUTTON_HOVER_SCALE: Vector2 = Vector2(1.022, 1.022)
const BUTTON_TWEEN_DURATION: float = 0.16

@onready var approved_background: TextureRect = $ApprovedBackground
@onready var continue_button: Button = $CenterContainer/MenuPanel/MarginContainer/VBoxContainer/ContinueButton
@onready var new_game_button: Button = $CenterContainer/MenuPanel/MarginContainer/VBoxContainer/NewGameButton
@onready var quit_button: Button = $CenterContainer/MenuPanel/MarginContainer/VBoxContainer/QuitButton
@onready var status_label: Label = $CenterContainer/MenuPanel/MarginContainer/VBoxContainer/StatusLabel

var _save_slots_panel: SaveSlotsPanel
var _button_tweens: Dictionary = {}


func _ready() -> void:
	_install_branding_background()
	_configure_menu_buttons()
	_install_save_slots_panel()
	_refresh_save_status()
	if not GameState.save_slots_changed.is_connected(_refresh_save_status):
		GameState.save_slots_changed.connect(_refresh_save_status)
	call_deferred("_refresh_button_pivots")


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


func _install_branding_background() -> void:
	approved_background.visible = false
	approved_background.texture = null
	if not ResourceLoader.exists(MAIN_MENU_BACKGROUND_PATH, "Texture2D"):
		return
	var resource: Resource = load(MAIN_MENU_BACKGROUND_PATH)
	if resource is Texture2D:
		approved_background.texture = resource as Texture2D
		approved_background.visible = true


func _configure_menu_buttons() -> void:
	for button: Button in _menu_buttons():
		button.mouse_entered.connect(_animate_menu_button.bind(button, true))
		button.mouse_exited.connect(_animate_menu_button.bind(button, false))
		button.focus_entered.connect(_animate_menu_button.bind(button, true))
		button.focus_exited.connect(_animate_menu_button.bind(button, false))


func _menu_buttons() -> Array[Button]:
	return [continue_button, new_game_button, quit_button]


func _refresh_button_pivots() -> void:
	for button: Button in _menu_buttons():
		button.pivot_offset = button.size * 0.5


func _animate_menu_button(button: Button, highlighted: bool) -> void:
	if not is_instance_valid(button):
		return
	var key: int = button.get_instance_id()
	if _button_tweens.has(key):
		var previous: Tween = _button_tweens[key] as Tween
		if previous != null and previous.is_valid():
			previous.kill()
	var target_scale: Vector2 = BUTTON_HOVER_SCALE if highlighted and not button.disabled else Vector2.ONE
	var target_modulate: Color = Color(1.08, 1.1, 1.12, 1.0) if highlighted and not button.disabled else Color.WHITE
	var tween: Tween = create_tween()
	_button_tweens[key] = tween
	tween.set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.tween_property(button, "scale", target_scale, BUTTON_TWEEN_DURATION)
	tween.parallel().tween_property(button, "modulate", target_modulate, BUTTON_TWEEN_DURATION)


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
