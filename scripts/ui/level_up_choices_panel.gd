class_name LevelUpChoicesPanel
extends LevelUpPanel

var _choice_system: LevelUpChoiceSystem = LevelUpChoiceSystem.new()
var _choice_box: VBoxContainer


func _ready() -> void:
	_system = _choice_system
	super._ready()
	_inject_choice_box()


func _refresh() -> void:
	super._refresh()
	_refresh_choice_box()
	if _hero == null or _state == null:
		return
	var validation: Dictionary = _choice_system.validate_transaction(_hero, _state)
	_confirm.disabled = not bool(validation.get("success", false))
	_show_message(
		str(validation.get("message", "")),
		not bool(validation.get("success", false))
	)


func _inject_choice_box() -> void:
	if _message == null or _message.get_parent() == null:
		return
	var page: VBoxContainer = _message.get_parent() as VBoxContainer
	if page == null:
		return
	_choice_box = VBoxContainer.new()
	_choice_box.name = "LevelChoiceContainer"
	_choice_box.add_theme_constant_override("separation", 10)
	page.add_child(_choice_box)
	page.move_child(_choice_box, _message.get_index())


func _refresh_choice_box() -> void:
	if _choice_box == null or _hero == null or _state == null:
		return
	_clear_children(_choice_box)
	var transaction: Dictionary = _choice_system.get_transaction(_state)
	var target_level: int = int(transaction.get("target_level", _hero.level + 1))
	var definitions: Array[Dictionary] = _choice_system.get_level_choice_definitions(
		_hero,
		target_level
	)
	_choice_box.visible = not definitions.is_empty()
	if definitions.is_empty():
		return

	_choice_box.add_child(HSeparator.new())
	_choice_box.add_child(_choice_label("РЕШЕНИЯ УРОВНЯ", 22))
	for definition: Dictionary in definitions:
		var choice_id: String = str(definition.get("choice_id", ""))
		var choice_type: String = str(definition.get("type", ""))
		var card := PanelContainer.new()
		card.name = "LevelChoiceCard_%s" % choice_id
		_choice_box.add_child(card)
		var margin := MarginContainer.new()
		margin.add_theme_constant_override("margin_left", 12)
		margin.add_theme_constant_override("margin_top", 10)
		margin.add_theme_constant_override("margin_right", 12)
		margin.add_theme_constant_override("margin_bottom", 10)
		card.add_child(margin)
		var box := VBoxContainer.new()
		box.add_theme_constant_override("separation", 8)
		margin.add_child(box)
		box.add_child(_choice_label(str(definition.get("title", choice_id)), 20))
		var description := _choice_label(str(definition.get("description", "")), 16)
		description.modulate = Color(0.86, 0.88, 0.94, 1.0)
		box.add_child(description)
		match choice_type:
			LevelChoiceSystem.CHOICE_SUBCLASS:
				_build_subclass_choice(box, definition, transaction)
			LevelChoiceSystem.CHOICE_ADVANCEMENT:
				_build_advancement_choice(box, definition, transaction)
			_:
				box.add_child(_choice_label("Тип выбора пока не поддерживается.", 16))


func _build_subclass_choice(
	parent: VBoxContainer,
	definition: Dictionary,
	transaction: Dictionary
) -> void:
	var choice_id: String = str(definition.get("choice_id", ""))
	var selection: Dictionary = _choice_system.get_level_choice_selection(_state, choice_id)
	var selected_id: String = str(selection.get("option_id", ""))
	var option := OptionButton.new()
	option.name = "LevelChoice_%s" % choice_id
	option.custom_minimum_size = Vector2(0.0, 58.0)
	option.add_theme_font_size_override("font_size", 18)
	option.add_item("Выберите воинский путь")
	option.set_item_metadata(0, "")
	var selected_index: int = 0
	for option_id: String in _string_array(definition.get("options", [])):
		option.add_item(
			_choice_system.get_level_choice_option_name(
				LevelChoiceSystem.CHOICE_SUBCLASS,
				option_id
			)
		)
		var index: int = option.item_count - 1
		option.set_item_metadata(index, option_id)
		if option_id == selected_id:
			selected_index = index
	option.select(selected_index)
	option.item_selected.connect(_on_subclass_selected.bind(choice_id, option))
	parent.add_child(option)
	var note := _choice_label(
		_choice_system.get_level_choice_option_description(
			LevelChoiceSystem.CHOICE_SUBCLASS,
			selected_id
		),
		16
	)
	note.name = "LevelChoiceDescription_%s" % choice_id
	note.visible = not note.text.is_empty()
	parent.add_child(note)


func _build_advancement_choice(
	parent: VBoxContainer,
	definition: Dictionary,
	transaction: Dictionary
) -> void:
	var choice_id: String = str(definition.get("choice_id", ""))
	var selection: Dictionary = _choice_system.get_level_choice_selection(_state, choice_id)
	var mode: String = str(selection.get("mode", ""))

	var mode_option := OptionButton.new()
	mode_option.name = "LevelChoice_%s_Mode" % choice_id
	mode_option.custom_minimum_size = Vector2(0.0, 58.0)
	mode_option.add_theme_font_size_override("font_size", 18)
	mode_option.add_item("Выберите способ развития")
	mode_option.set_item_metadata(0, "")
	for mode_id: String in [
		LevelChoiceSystem.ADVANCEMENT_PLUS_TWO,
		LevelChoiceSystem.ADVANCEMENT_SPLIT,
		LevelChoiceSystem.ADVANCEMENT_FEAT
	]:
		mode_option.add_item(_choice_system.get_advancement_mode_name(mode_id))
		mode_option.set_item_metadata(mode_option.item_count - 1, mode_id)
		if mode_id == mode:
			mode_option.select(mode_option.item_count - 1)
	mode_option.item_selected.connect(_on_advancement_mode_selected.bind(choice_id, mode_option))
	parent.add_child(mode_option)

	var primary := _make_ability_option(
		"LevelChoice_%s_PrimaryAbility" % choice_id,
		str(selection.get("primary_ability_id", "")),
		"Первая характеристика"
	)
	primary.item_selected.connect(
		_on_advancement_value_selected.bind(
			choice_id,
			"primary_ability_id",
			primary
		)
	)
	primary.visible = mode in [
		LevelChoiceSystem.ADVANCEMENT_PLUS_TWO,
		LevelChoiceSystem.ADVANCEMENT_SPLIT
	]
	parent.add_child(primary)

	var secondary := _make_ability_option(
		"LevelChoice_%s_SecondaryAbility" % choice_id,
		str(selection.get("secondary_ability_id", "")),
		"Вторая характеристика"
	)
	secondary.item_selected.connect(
		_on_advancement_value_selected.bind(
			choice_id,
			"secondary_ability_id",
			secondary
		)
	)
	secondary.visible = mode == LevelChoiceSystem.ADVANCEMENT_SPLIT
	parent.add_child(secondary)

	var feat := OptionButton.new()
	feat.name = "LevelChoice_%s_Feat" % choice_id
	feat.custom_minimum_size = Vector2(0.0, 58.0)
	feat.add_theme_font_size_override("font_size", 18)
	feat.add_item("Выберите черту")
	feat.set_item_metadata(0, "")
	var selected_feat_id: String = str(selection.get("feat_id", ""))
	var selected_feat_index: int = 0
	for feat_id: String in _choice_system.get_available_level_feat_ids(_hero):
		feat.add_item(_choice_system.get_level_choice_option_name("feat", feat_id))
		var feat_index: int = feat.item_count - 1
		feat.set_item_metadata(feat_index, feat_id)
		if feat_id == selected_feat_id:
			selected_feat_index = feat_index
	feat.select(selected_feat_index)
	feat.item_selected.connect(
		_on_advancement_value_selected.bind(choice_id, "feat_id", feat)
	)
	feat.visible = mode == LevelChoiceSystem.ADVANCEMENT_FEAT
	parent.add_child(feat)

	var note := _choice_label(_advancement_summary(selection), 16)
	note.name = "LevelChoiceDescription_%s" % choice_id
	note.visible = not note.text.is_empty()
	parent.add_child(note)


func _make_ability_option(
	node_name: String,
	selected_id: String,
	empty_label: String
) -> OptionButton:
	var option := OptionButton.new()
	option.name = node_name
	option.custom_minimum_size = Vector2(0.0, 58.0)
	option.add_theme_font_size_override("font_size", 18)
	option.add_item(empty_label)
	option.set_item_metadata(0, "")
	var selected_index: int = 0
	for ability_id: String in _choice_system.get_ability_choice_ids():
		option.add_item(
			"%s — %d" % [
				_choice_system.get_ability_choice_name(ability_id),
				_hero.get_ability_score(ability_id)
			]
		)
		var index: int = option.item_count - 1
		option.set_item_metadata(index, ability_id)
		if ability_id == selected_id:
			selected_index = index
	option.select(selected_index)
	return option


func _on_subclass_selected(
	_index: int,
	choice_id: String,
	option: OptionButton
) -> void:
	_choice_system.set_level_choice(
		_hero,
		_state,
		choice_id,
		{"option_id": _selected_metadata(option)}
	)
	_refresh()


func _on_advancement_mode_selected(
	_index: int,
	choice_id: String,
	option: OptionButton
) -> void:
	var mode: String = _selected_metadata(option)
	var selection: Dictionary = {}
	if not mode.is_empty():
		selection["mode"] = mode
	_choice_system.set_level_choice(_hero, _state, choice_id, selection)
	_refresh()


func _on_advancement_value_selected(
	_index: int,
	choice_id: String,
	key: String,
	option: OptionButton
) -> void:
	var selection: Dictionary = _choice_system.get_level_choice_selection(
		_state,
		choice_id
	)
	var value: String = _selected_metadata(option)
	if value.is_empty():
		selection.erase(key)
	else:
		selection[key] = value
	_choice_system.set_level_choice(_hero, _state, choice_id, selection)
	_refresh()


func _advancement_summary(selection: Dictionary) -> String:
	var mode: String = str(selection.get("mode", ""))
	if mode == LevelChoiceSystem.ADVANCEMENT_PLUS_TWO:
		var ability_id: String = str(selection.get("primary_ability_id", ""))
		return (
			"Итог: +2 к характеристике «%s»."
			% _choice_system.get_ability_choice_name(ability_id)
			if not ability_id.is_empty()
			else ""
		)
	if mode == LevelChoiceSystem.ADVANCEMENT_SPLIT:
		var primary_id: String = str(selection.get("primary_ability_id", ""))
		var secondary_id: String = str(selection.get("secondary_ability_id", ""))
		if primary_id.is_empty() or secondary_id.is_empty():
			return ""
		return "+1 к «%s» и +1 к «%s»." % [
			_choice_system.get_ability_choice_name(primary_id),
			_choice_system.get_ability_choice_name(secondary_id)
		]
	if mode == LevelChoiceSystem.ADVANCEMENT_FEAT:
		var feat_id: String = str(selection.get("feat_id", ""))
		return _choice_system.get_level_choice_option_description("feat", feat_id)
	return ""


func _selected_metadata(option: OptionButton) -> String:
	if option == null or option.selected < 0:
		return ""
	return str(option.get_item_metadata(option.selected))


func _choice_label(text_value: String, font_size: int) -> Label:
	var label := Label.new()
	label.text = text_value
	label.add_theme_font_size_override("font_size", font_size)
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return label


func _clear_children(parent: Node) -> void:
	for child: Node in parent.get_children():
		parent.remove_child(child)
		child.queue_free()


func _string_array(value: Variant) -> Array[String]:
	var result: Array[String] = []
	if value is Array:
		for item: Variant in value:
			result.append(str(item))
	return result
