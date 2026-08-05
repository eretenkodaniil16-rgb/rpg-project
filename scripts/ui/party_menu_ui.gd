class_name PartyMenuUI
extends Control

signal member_control_requested(character_id: String)

const PLAYER_MEMBER_ID: String = "player_character"
const IRINA_MEMBER_ID: String = "companion_irna_guard_01"

var _panel: PanelContainer = null
var _title_label: Label = null
var _status_label: Label = null
var _player_button: Button = null
var _irina_button: Button = null
var _button_group: ButtonGroup = ButtonGroup.new()
var _active_member_id: String = PLAYER_MEMBER_ID
var _combat_active: bool = false
var _enemy_turn: bool = false


func _ready() -> void:
	_build_ui()
	refresh_party_state({})


func _build_ui() -> void:
	set_anchors_preset(Control.PRESET_TOP_LEFT)
	position = Vector2(18.0, 108.0)
	size = Vector2(224.0, 190.0)
	mouse_filter = Control.MOUSE_FILTER_PASS

	_panel = PanelContainer.new()
	_panel.name = "Panel"
	_panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_panel.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(_panel)

	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 10)
	margin.add_theme_constant_override("margin_top", 8)
	margin.add_theme_constant_override("margin_right", 10)
	margin.add_theme_constant_override("margin_bottom", 8)
	_panel.add_child(margin)

	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 6)
	margin.add_child(column)

	_title_label = Label.new()
	_title_label.text = "ОТРЯД"
	_title_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_title_label.add_theme_font_size_override("font_size", 17)
	column.add_child(_title_label)

	_status_label = Label.new()
	_status_label.text = "Исследование"
	_status_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_status_label.add_theme_font_size_override("font_size", 13)
	column.add_child(_status_label)

	_button_group.allow_unpress = false
	_player_button = _create_member_button("Герой", PLAYER_MEMBER_ID)
	_irina_button = _create_member_button("Ирина", IRINA_MEMBER_ID)
	column.add_child(_player_button)
	column.add_child(_irina_button)


func _create_member_button(member_name: String, member_id: String) -> Button:
	var button := Button.new()
	button.custom_minimum_size = Vector2(196.0, 58.0)
	button.toggle_mode = true
	button.button_group = _button_group
	button.focus_mode = Control.FOCUS_NONE
	button.action_mode = BaseButton.ACTION_MODE_BUTTON_RELEASE
	button.add_theme_font_size_override("font_size", 15)
	button.text = member_name
	button.pressed.connect(func() -> void:
		member_control_requested.emit(member_id)
	)
	return button


func refresh_party_state(state: Dictionary) -> void:
	_active_member_id = str(state.get("active_member_id", _active_member_id))
	_combat_active = bool(state.get("combat_active", false))
	_enemy_turn = bool(state.get("enemy_turn", false))
	var player_hp: int = int(state.get("player_hp", 0))
	var player_max_hp: int = maxi(int(state.get("player_max_hp", 1)), 1)
	var irina_hp: int = int(state.get("irina_hp", 0))
	var irina_max_hp: int = maxi(int(state.get("irina_max_hp", 1)), 1)
	var irina_following: bool = bool(state.get("irina_following", true))
	var irina_available: bool = bool(state.get("irina_available", true))

	if _status_label != null:
		if _combat_active:
			_status_label.text = "Ход противника" if _enemy_turn else "Инициатива"
		else:
			_status_label.text = "Выберите активного персонажа"

	if _player_button != null:
		_player_button.button_pressed = _active_member_id == PLAYER_MEMBER_ID
		_player_button.disabled = _combat_active and _active_member_id != PLAYER_MEMBER_ID
		var player_state: String = _member_state_label(PLAYER_MEMBER_ID, false)
		_player_button.text = "ГЕРОЙ  HP %d/%d\n%s" % [player_hp, player_max_hp, player_state]

	if _irina_button != null:
		_irina_button.button_pressed = _active_member_id == IRINA_MEMBER_ID
		_irina_button.disabled = (not irina_available) or (_combat_active and _active_member_id != IRINA_MEMBER_ID)
		var irina_state: String = _member_state_label(IRINA_MEMBER_ID, irina_following)
		_irina_button.text = "ИРИНА  HP %d/%d\n%s" % [irina_hp, irina_max_hp, irina_state]


func _member_state_label(member_id: String, following: bool) -> String:
	if _combat_active:
		if _enemy_turn:
			return "ОЖИДАЕТ"
		return "ХОД" if _active_member_id == member_id else "ОЖИДАЕТ"
	if _active_member_id == member_id:
		return "РУЧНОЕ УПРАВЛЕНИЕ"
	if member_id == IRINA_MEMBER_ID and following:
		return "СЛЕДУЕТ ЗА ГЕРОЕМ"
	return "ОЖИДАЕТ"


func request_member_for_testing(character_id: String) -> void:
	member_control_requested.emit(character_id)


func get_snapshot_for_testing() -> Dictionary:
	return {
		"active_member_id": _active_member_id,
		"combat_active": _combat_active,
		"enemy_turn": _enemy_turn,
		"player_pressed": _player_button.button_pressed if _player_button != null else false,
		"irina_pressed": _irina_button.button_pressed if _irina_button != null else false,
		"player_disabled": _player_button.disabled if _player_button != null else true,
		"irina_disabled": _irina_button.disabled if _irina_button != null else true,
		"status": _status_label.text if _status_label != null else ""
	}
