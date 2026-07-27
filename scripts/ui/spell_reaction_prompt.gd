class_name SpellReactionPrompt
extends Control

signal decision_resolved(use_counterspell: bool)

var _panel: PanelContainer
var _title: Label
var _details: Label
var _cast_button: Button
var _skip_button: Button
var _waiting: bool = false


func _ready() -> void:
	_build_ui()
	hide()


func request_counterspell(attempt: SpellCastAttempt, offer: Dictionary) -> bool:
	if attempt == null or not bool(offer.get("available", false)):
		return false
	if _waiting:
		return false
	_waiting = true
	_title.text = "РЕАКЦИЯ: КОНТРЗАКЛИНАНИЕ"
	_details.text = "%s начинает сотворять «%s».
Дистанция: %d футов
Будет потрачена реакция и ячейка %d уровня.
При провале спасброска Телосложения исходное заклинание рассеется без расхода его ячейки." % [
		attempt.caster_name,
		attempt.get_spell_name(),
		int(offer.get("range_feet", 0)),
		int(offer.get("slot_level", 3))
	]
	_cast_button.disabled = false
	_skip_button.disabled = false
	show()
	move_to_front()
	_cast_button.grab_focus()
	var use_counterspell: bool = await decision_resolved
	_waiting = false
	hide()
	return use_counterspell


func is_waiting_for_decision() -> bool:
	return _waiting


func choose_counterspell() -> void:
	_resolve(true)


func skip_reaction() -> void:
	_resolve(false)


func _unhandled_input(event: InputEvent) -> void:
	if not visible or not _waiting:
		return
	if event.is_action_pressed("ui_cancel"):
		skip_reaction()
		get_viewport().set_input_as_handled()


func _resolve(use_counterspell: bool) -> void:
	if not _waiting:
		return
	_cast_button.disabled = true
	_skip_button.disabled = true
	decision_resolved.emit(use_counterspell)


func _build_ui() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	z_index = 230
	var dim := ColorRect.new()
	dim.color = Color(0.0, 0.0, 0.0, 0.72)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	dim.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(dim)

	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	margin.add_theme_constant_override("margin_left", 180)
	margin.add_theme_constant_override("margin_top", 120)
	margin.add_theme_constant_override("margin_right", 180)
	margin.add_theme_constant_override("margin_bottom", 120)
	add_child(margin)

	_panel = PanelContainer.new()
	margin.add_child(_panel)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 16)
	_panel.add_child(box)

	_title = Label.new()
	_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_title.add_theme_font_size_override("font_size", 28)
	box.add_child(_title)

	_details = Label.new()
	_details.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_details.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_details.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_details.add_theme_font_size_override("font_size", 20)
	box.add_child(_details)

	var buttons := HBoxContainer.new()
	buttons.add_theme_constant_override("separation", 18)
	box.add_child(buttons)
	_cast_button = Button.new()
	_cast_button.name = "CounterspellButton"
	_cast_button.text = "КОНТРЗАКЛИНАНИЕ"
	_cast_button.custom_minimum_size = Vector2(0.0, 72.0)
	_cast_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_cast_button.add_theme_font_size_override("font_size", 21)
	_cast_button.pressed.connect(choose_counterspell)
	buttons.add_child(_cast_button)
	_skip_button = Button.new()
	_skip_button.name = "SkipReactionButton"
	_skip_button.text = "ПРОПУСТИТЬ"
	_skip_button.custom_minimum_size = Vector2(0.0, 72.0)
	_skip_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_skip_button.add_theme_font_size_override("font_size", 21)
	_skip_button.pressed.connect(skip_reaction)
	buttons.add_child(_skip_button)
