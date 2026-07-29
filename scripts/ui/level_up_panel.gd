class_name LevelUpPanel
extends Control

signal level_up_completed(result: Dictionary)

var _system: LevelUpSystem = LevelUpSystem.new()
var _hero: PlayerCharacter
var _state: Node

var _title: Label
var _summary: Label
var _features: Label
var _message: Label
var _fixed_hp: Button
var _roll_hp: Button
var _new_spell: OptionButton
var _class_old: OptionButton
var _class_new: OptionButton
var _magic_cantrip_old: OptionButton
var _magic_cantrip_new: OptionButton
var _magic_spell_old: OptionButton
var _magic_spell_new: OptionButton
var _confirm: Button
var _defer: Button


func _ready() -> void:
	name = "LevelUpPanel"
	z_index = 4095
	process_mode = Node.PROCESS_MODE_ALWAYS
	_build_ui()
	hide()


func open_for(character: PlayerCharacter, state: Node) -> Dictionary:
	_hero = character
	_state = state
	var result: Dictionary = _system.begin_transaction(_hero, _state)
	if not bool(result.get("success", false)):
		_show_message(str(result.get("message", "Повышение уровня недоступно.")), true)
		return result
	if _state != null:
		_state.set("input_locked", true)
	_refresh()
	show()
	_confirm.grab_focus()
	return result


func close_panel() -> void:
	hide()
	if _state != null:
		_state.set("input_locked", false)


func _unhandled_input(event: InputEvent) -> void:
	if visible and event.is_action_pressed("ui_cancel"):
		close_panel()
		get_viewport().set_input_as_handled()


func _build_ui() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP

	var dimmer := ColorRect.new()
	dimmer.color = Color(0.0, 0.0, 0.0, 0.82)
	dimmer.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(dimmer)

	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	margin.add_theme_constant_override("margin_left", 32)
	margin.add_theme_constant_override("margin_top", 22)
	margin.add_theme_constant_override("margin_right", 32)
	margin.add_theme_constant_override("margin_bottom", 22)
	add_child(margin)

	var panel := PanelContainer.new()
	panel.name = "LevelUpPanelCard"
	margin.add_child(panel)

	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	panel.add_child(scroll)

	var page := VBoxContainer.new()
	page.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	page.add_theme_constant_override("separation", 12)
	scroll.add_child(page)

	_title = _label("ПОВЫШЕНИЕ УРОВНЯ", 30)
	_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	page.add_child(_title)

	_summary = _label("", 20)
	_summary.name = "LevelUpSummaryLabel"
	page.add_child(_summary)

	var hp_title := _label("ЗДОРОВЬЕ", 22)
	page.add_child(hp_title)

	var hp_row := HBoxContainer.new()
	hp_row.add_theme_constant_override("separation", 10)
	page.add_child(hp_row)

	_fixed_hp = Button.new()
	_fixed_hp.name = "LevelUpFixedHpButton"
	_fixed_hp.custom_minimum_size = Vector2(310.0, 64.0)
	_fixed_hp.pressed.connect(_on_fixed_hp_pressed)
	hp_row.add_child(_fixed_hp)

	_roll_hp = Button.new()
	_roll_hp.name = "LevelUpRollHpButton"
	_roll_hp.custom_minimum_size = Vector2(310.0, 64.0)
	_roll_hp.pressed.connect(_on_roll_hp_pressed)
	hp_row.add_child(_roll_hp)

	_features = _label("", 18)
	_features.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART