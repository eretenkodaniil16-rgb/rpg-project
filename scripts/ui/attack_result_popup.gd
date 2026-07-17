class_name AttackResultPopup
extends Control

signal dismissed(result: AttackResult)

var _result: AttackResult = null
var _title_label: Label
var _details_label: Label
var _outcome_label: Label
var _continue_button: Button


func _ready() -> void:
	_build_layout()
	hide()


func show_result(result: AttackResult) -> void:
	_result = result
	GameState.input_locked = true
	_title_label.text = result.attack_name.to_upper()
	var lines: Array[String] = []
	if result.automatic_hit:
		lines.append("Автоматическое попадание")
	else:
		lines.append("Бросок d20: %d" % result.natural_roll)
		lines.append("%s: %s" % [result.ability_name, _format_modifier(result.ability_modifier)])
		lines.append("Бонус мастерства: %s" % _format_modifier(result.proficiency_bonus))
		lines.append("Итого: %d" % result.total)
		lines.append("КД цели: %d" % result.target_armor_class)
	lines.append("Урон: %d %s" % [result.damage, result.damage_type])
	lines.append("Прочность цели: %d / %d" % [result.target_health_after, result.target_max_health])
	if not result.note.is_empty():
		lines.append(result.note)
	_details_label.text = "\n".join(lines)

	if result.automatic_miss:
		_outcome_label.text = "АВТОМАТИЧЕСКИЙ ПРОМАХ"
		_outcome_label.add_theme_color_override("font_color", Color(1.0, 0.48, 0.42, 1.0))
	elif result.critical:
		_outcome_label.text = "КРИТИЧЕСКОЕ ПОПАДАНИЕ"
		_outcome_label.add_theme_color_override("font_color", Color(1.0, 0.82, 0.32, 1.0))
	elif result.hit:
		_outcome_label.text = "ПОПАДАНИЕ" if result.damage > 0 else "ПОПАДАНИЕ · 0 УРОНА"
		_outcome_label.add_theme_color_override("font_color", Color(0.45, 0.92, 0.58, 1.0))
	else:
		_outcome_label.text = "ПРОМАХ"
		_outcome_label.add_theme_color_override("font_color", Color(1.0, 0.48, 0.42, 1.0))
	show()
	_continue_button.grab_focus()


func _unhandled_input(event: InputEvent) -> void:
	if visible and (event.is_action_pressed("ui_accept") or event.is_action_pressed("ui_cancel")):
		_on_continue_pressed()
		get_viewport().set_input_as_handled()


func _build_layout() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	var dimmer: ColorRect = ColorRect.new()
	dimmer.color = Color(0.0, 0.0, 0.0, 0.62)
	dimmer.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	dimmer.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(dimmer)
	var center: CenterContainer = CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(center)
	var panel: PanelContainer = PanelContainer.new()
	panel.custom_minimum_size = Vector2(600.0, 500.0)
	center.add_child(panel)
	var margin: MarginContainer = MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 34)
	margin.add_theme_constant_override("margin_top", 26)
	margin.add_theme_constant_override("margin_right", 34)
	margin.add_theme_constant_override("margin_bottom", 26)
	panel.add_child(margin)
	var column: VBoxContainer = VBoxContainer.new()
	column.add_theme_constant_override("separation", 16)
	margin.add_child(column)
	_title_label = Label.new()
	_title_label.add_theme_font_size_override("font_size", 28)
	_title_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	column.add_child(_title_label)
	_details_label = Label.new()
	_details_label.add_theme_font_size_override("font_size", 20)
	_details_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_details_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_details_label.size_flags_vertical = Control.SIZE_EXPAND_FILL
	column.add_child(_details_label)
	_outcome_label = Label.new()
	_outcome_label.add_theme_font_size_override("font_size", 30)
	_outcome_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	column.add_child(_outcome_label)
	_continue_button = Button.new()
	_continue_button.text = "Продолжить"
	_continue_button.custom_minimum_size = Vector2(0.0, 58.0)
	_continue_button.add_theme_font_size_override("font_size", 21)
	_continue_button.pressed.connect(_on_continue_pressed)
	column.add_child(_continue_button)


func _on_continue_pressed() -> void:
	if _result == null:
		return
	var completed_result: AttackResult = _result
	_result = null
	hide()
	GameState.input_locked = false
	dismissed.emit(completed_result)


func _format_modifier(value: int) -> String:
	return "+%d" % value if value >= 0 else str(value)
