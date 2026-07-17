class_name AbilityPanel
extends Control

signal ability_requested(ability_id: String)
signal rest_requested

var _class_data: ClassDataSystem = ClassDataSystem.new()
var _ability_button: Button
var _resource_label: Label
var _message_label: Label
var _rest_button: Button
var _character: PlayerCharacter


func _ready() -> void:
	_build_ui()


func bind_character(character: PlayerCharacter) -> void:
	_character = character
	refresh()


func refresh() -> void:
	if _character == null:
		return
	var ability: Dictionary = _class_data.get_signature_ability(_character)
	if ability.is_empty():
		_ability_button.text = "СПОСОБНОСТЬ НЕ ВЫБРАНА"
		_ability_button.disabled = true
		_resource_label.text = ""
		return
	var kind: String = str(ability.get("kind", "informational"))
	_ability_button.text = str(ability.get("button", ability.get("name", "СПОСОБНОСТЬ"))).to_upper()
	_ability_button.disabled = kind != "active"
	_resource_label.text = "%s · %s" % [str(ability.get("name", "Способность")), _class_data.get_resource_text(_character, ability)]
	_ability_button.tooltip_text = str(ability.get("description", ""))


func set_message(message: String, is_success: bool = true) -> void:
	_message_label.text = message
	_message_label.add_theme_color_override("font_color", Color(0.64, 0.94, 0.68, 1.0) if is_success else Color(1.0, 0.55, 0.48, 1.0))
	refresh()


func _build_ui() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	var panel := PanelContainer.new()
	panel.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	panel.offset_left = -365.0
	panel.offset_top = -255.0
	panel.offset_right = -20.0
	panel.offset_bottom = -145.0
	panel.mouse_filter = Control.MOUSE_FILTER_STOP
	panel.modulate = Color(1.0, 1.0, 1.0, 0.92)
	add_child(panel)
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 14)
	margin.add_theme_constant_override("margin_top", 10)
	margin.add_theme_constant_override("margin_right", 14)
	margin.add_theme_constant_override("margin_bottom", 10)
	panel.add_child(margin)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 6)
	margin.add_child(column)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	column.add_child(row)
	_ability_button = Button.new()
	_ability_button.custom_minimum_size = Vector2(210.0, 52.0)
	_ability_button.add_theme_font_size_override("font_size", 17)
	_ability_button.pressed.connect(_on_ability_pressed)
	row.add_child(_ability_button)
	_rest_button = Button.new()
	_rest_button.text = "ОТДЫХ"
	_rest_button.custom_minimum_size = Vector2(90.0, 52.0)
	_rest_button.add_theme_font_size_override("font_size", 15)
	_rest_button.pressed.connect(_on_rest_pressed)
	row.add_child(_rest_button)
	_resource_label = Label.new()
	_resource_label.add_theme_font_size_override("font_size", 15)
	_resource_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	column.add_child(_resource_label)
	_message_label = Label.new()
	_message_label.add_theme_font_size_override("font_size", 14)
	_message_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_message_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_message_label.text = "Основная способность класса"
	column.add_child(_message_label)


func _on_ability_pressed() -> void:
	if _character == null or GameState.input_locked:
		return
	ability_requested.emit(_character.signature_ability_id)


func _on_rest_pressed() -> void:
	if GameState.input_locked:
		return
	rest_requested.emit()
