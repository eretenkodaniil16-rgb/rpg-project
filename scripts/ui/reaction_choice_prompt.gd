class_name ReactionChoicePrompt
extends Control

signal option_selected(option_id: String)

var _title_label: Label
var _trigger_label: Label
var _options_box: VBoxContainer
var _skip_button: Button
var _option_buttons: Array[Button] = []
var _option_ids: Array[String] = []
var _waiting: bool = false


func _ready() -> void:
	_build_ui()
	hide()


func request_reaction(title: String, trigger_details: String, options: Array[Dictionary]) -> String:
	if _waiting or options.is_empty():
		return ""
	_waiting = true
	_title_label.text = title if not title.is_empty() else "ВОЗМОЖНОСТЬ РЕАКЦИИ"
	_trigger_label.text = trigger_details
	_rebuild_options(options)
	_skip_button.disabled = false
	show()
	move_to_front()
	if not _option_buttons.is_empty():
		_option_buttons[0].grab_focus()
	var chosen_id: String = await option_selected
	_waiting = false
	hide()
	_clear_options()
	return chosen_id


func is_waiting_for_decision() -> bool:
	return _waiting


func get_option_count() -> int:
	return _option_ids.size()


func get_option_ids() -> Array[String]:
	return _option_ids.duplicate()


func choose_option(option_id: String) -> void:
	if option_id not in _option_ids:
		return
	_resolve(option_id)


func skip_reaction() -> void:
	_resolve("")


func _unhandled_input(event: InputEvent) -> void:
	if not visible or not _waiting:
		return
	if event.is_action_pressed("ui_cancel"):
		skip_reaction()
		get_viewport().set_input_as_handled()


func _resolve(option_id: String) -> void:
	if not _waiting:
		return
	for button: Button in _option_buttons:
		button.disabled = true
	_skip_button.disabled = true
	option_selected.emit(option_id)


func _rebuild_options(options: Array[Dictionary]) -> void:
	_clear_options()
	for option: Dictionary in options:
		var option_id: String = str(option.get("id", ""))
		if option_id.is_empty() or option_id in _option_ids:
			continue
		_option_ids.append(option_id)
		var card := VBoxContainer.new()
		card.name = "ReactionCard_%s" % _safe_node_name(option_id)
		card.add_theme_constant_override("separation", 4)
		_options_box.add_child(card)
		var button := Button.new()
		button.name = "ReactionOption_%s" % _safe_node_name(option_id)
		button.text = str(option.get("label", option.get("name", option_id))).to_upper()
		button.custom_minimum_size = Vector2(0.0, 64.0)
		button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		button.add_theme_font_size_override("font_size", 20)
		button.pressed.connect(_resolve.bind(option_id))
		card.add_child(button)
		_option_buttons.append(button)
		var description := Label.new()
		description.text = str(option.get("description", ""))
		description.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		description.add_theme_font_size_override("font_size", 16)
		card.add_child(description)
		var resource_text: String = str(option.get("resource_text", ""))
		if not resource_text.is_empty():
			var resource := Label.new()
			resource.text = resource_text
			resource.add_theme_font_size_override("font_size", 14)
			resource.add_theme_color_override("font_color", Color(0.72, 0.82, 1.0, 1.0))
			card.add_child(resource)


func _clear_options() -> void:
	_option_buttons.clear()
	_option_ids.clear()
	if _options_box == null:
		return
	for child: Node in _options_box.get_children():
		child.queue_free()


func _safe_node_name(value: String) -> String:
	var result: String = value
	for character: String in [" ", "/", "\\", ":", ".", "-"]:
		result = result.replace(character, "_")
	return result


func _build_ui() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	z_index = 240
	var dim := ColorRect.new()
	dim.color = Color(0.0, 0.0, 0.0, 0.76)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	dim.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(dim)

	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	margin.add_theme_constant_override("margin_left", 150)
	margin.add_theme_constant_override("margin_top", 72)
	margin.add_theme_constant_override("margin_right", 150)
	margin.add_theme_constant_override("margin_bottom", 72)
	add_child(margin)

	var panel := PanelContainer.new()
	panel.name = "ReactionPanel"
	margin.add_child(panel)
	var column := VBoxContainer.new()
	column.name = "ReactionColumn"
	column.add_theme_constant_override("separation", 12)
	panel.add_child(column)

	_title_label = Label.new()
	_title_label.name = "ReactionTitle"
	_title_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_title_label.add_theme_font_size_override("font_size", 28)
	column.add_child(_title_label)

	_trigger_label = Label.new()
	_trigger_label.name = "ReactionTriggerDetails"
	_trigger_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_trigger_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_trigger_label.add_theme_font_size_override("font_size", 18)
	column.add_child(_trigger_label)

	var scroll := ScrollContainer.new()
	scroll.name = "ReactionOptionsScroll"
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	column.add_child(scroll)
	_options_box = VBoxContainer.new()
	_options_box.name = "ReactionOptions"
	_options_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_options_box.add_theme_constant_override("separation", 14)
	scroll.add_child(_options_box)

	_skip_button = Button.new()
	_skip_button.name = "SkipReactionButton"
	_skip_button.text = "ПРОПУСТИТЬ РЕАКЦИЮ"
	_skip_button.custom_minimum_size = Vector2(0.0, 64.0)
	_skip_button.add_theme_font_size_override("font_size", 19)
	_skip_button.pressed.connect(skip_reaction)
	column.add_child(_skip_button)
