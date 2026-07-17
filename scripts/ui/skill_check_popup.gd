class_name SkillCheckPopup
extends Control

signal dismissed(result: SkillCheckResult)

var _result: SkillCheckResult = null
var _title_label: Label
var _details_label: Label
var _outcome_label: Label
var _continue_button: Button


func _ready() -> void:
	_build_layout()
	hide()


func show_result(result: SkillCheckResult) -> void:
	_result = result
	_title_label.text = "ПРОВЕРКА: %s" % result.ability_name.to_upper()
	var bonus_line: String = ""
	if result.bonus != 0:
		bonus_line = "\nДополнительный бонус: %s" % _format_modifier(result.bonus)
	_details_label.text = "Бросок d20: %d\nМодификатор: %s%s\nИтого: %d\nСложность: %d — %s" % [
		result.natural_roll,
		_format_modifier(result.ability_modifier),
		bonus_line,
		result.total,
		result.difficulty,
		SkillCheckSystem.difficulty_name(result.difficulty)
	]
	_outcome_label.text = "УСПЕХ" if result.success else "НЕУДАЧА"
	_outcome_label.add_theme_color_override(
		"font_color",
		Color(0.45, 0.92, 0.58, 1.0) if result.success else Color(1.0, 0.48, 0.42, 1.0)
	)
	show()
	_continue_button.grab_focus()


func _unhandled_input(event: InputEvent) -> void:
	if visible and event.is_action_pressed("ui_accept"):
		_on_continue_pressed()
		get_viewport().set_input_as_handled()


func _build_layout() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP

	var dimmer: ColorRect = ColorRect.new()
	dimmer.name = "Dimmer"
	dimmer.color = Color(0.0, 0.0, 0.0, 0.62)
	dimmer.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	dimmer.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(dimmer)

	var center: CenterContainer = CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(center)

	var panel: PanelContainer = PanelContainer.new()
	panel.custom_minimum_size = Vector2(560.0, 400.0)
	center.add_child(panel)

	var margin: MarginContainer = MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 34)
	margin.add_theme_constant_override("margin_top", 28)
	margin.add_theme_constant_override("margin_right", 34)
	margin.add_theme_constant_override("margin_bottom", 28)
	panel.add_child(margin)

	var column: VBoxContainer = VBoxContainer.new()
	column.add_theme_constant_override("separation", 18)
	margin.add_child(column)

	_title_label = Label.new()
	_title_label.name = "TitleLabel"
	_title_label.add_theme_font_size_override("font_size", 28)
	_title_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	column.add_child(_title_label)

	_details_label = Label.new()
	_details_label.name = "DetailsLabel"
	_details_label.add_theme_font_size_override("font_size", 21)
	_details_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_details_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_details_label.size_flags_vertical = Control.SIZE_EXPAND_FILL
	column.add_child(_details_label)

	_outcome_label = Label.new()
	_outcome_label.name = "OutcomeLabel"
	_outcome_label.add_theme_font_size_override("font_size", 34)
	_outcome_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	column.add_child(_outcome_label)

	_continue_button = Button.new()
	_continue_button.name = "ContinueButton"
	_continue_button.text = "Продолжить"
	_continue_button.custom_minimum_size = Vector2(0.0, 58.0)
	_continue_button.add_theme_font_size_override("font_size", 21)
	_continue_button.pressed.connect(_on_continue_pressed)
	column.add_child(_continue_button)


func _on_continue_pressed() -> void:
	if _result == null:
		return
	var completed_result: SkillCheckResult = _result
	_result = null
	hide()
	dismissed.emit(completed_result)


func _format_modifier(value: int) -> String:
	return "+%d" % value if value >= 0 else str(value)
