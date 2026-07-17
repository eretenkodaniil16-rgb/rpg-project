extends "res://scripts/game/game_base.gd"

const CHARACTER_SHEET_SCENE: PackedScene = preload("res://scenes/ui/character_sheet.tscn")
const ATTACK_RESULT_SCENE: PackedScene = preload("res://scenes/ui/attack_result_popup.tscn")
const TRAINING_DUMMY_SCENE: PackedScene = preload("res://scenes/game/training_dummy.tscn")

var _character_button: Button
var _character_sheet: CharacterSheet
var _attack_popup: AttackResultPopup
var _training_dummy: TrainingDummy


func _ready() -> void:
	super._ready()
	_build_character_ui()
	_build_combat_training()


func _unhandled_input(event: InputEvent) -> void:
	if _character_sheet != null and _character_sheet.visible:
		return
	if event is InputEventKey:
		var key_event := event as InputEventKey
		if key_event.pressed and not key_event.echo and key_event.keycode == KEY_C:
			_open_character_sheet()
			get_viewport().set_input_as_handled()
			return
	super._unhandled_input(event)


func _build_character_ui() -> void:
	var interface: CanvasLayer = $Interface
	_character_button = Button.new()
	_character_button.name = "CharacterButton"
	_character_button.text = "ПЕРСОНАЖ"
	_character_button.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	_character_button.offset_left = -390.0
	_character_button.offset_top = 20.0
	_character_button.offset_right = -190.0
	_character_button.offset_bottom = 78.0
	_character_button.add_theme_font_size_override("font_size", 18)
	_character_button.pressed.connect(_open_character_sheet)
	interface.add_child(_character_button)

	_character_sheet = CHARACTER_SHEET_SCENE.instantiate() as CharacterSheet
	_character_sheet.name = "CharacterSheet"
	interface.add_child(_character_sheet)


func _build_combat_training() -> void:
	var interface: CanvasLayer = $Interface
	_attack_popup = ATTACK_RESULT_SCENE.instantiate() as AttackResultPopup
	_attack_popup.name = "AttackResultPopup"
	interface.add_child(_attack_popup)

	_training_dummy = TRAINING_DUMMY_SCENE.instantiate() as TrainingDummy
	_training_dummy.name = "TrainingDummy"
	_training_dummy.position = Vector2(1080.0, 470.0)
	add_child(_training_dummy)


func _open_character_sheet() -> void:
	if GameState.input_locked or _character_sheet == null:
		return
	_character_sheet.open_sheet(GameState.player_character)
