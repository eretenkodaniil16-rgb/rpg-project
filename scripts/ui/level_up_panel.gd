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
	z_index = 5000
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
	page.add_child(_features)

	page.add_child(HSeparator.new())
	page.add_child(_label("КЛАССОВАЯ МАГИЯ", 22))

	_new_spell = _make_option(page, "LevelUpNewClassSpell", "Новое заклинание")
	_class_old = _make_option(page, "LevelUpReplaceClassOld", "Заменить изученное заклинание")
	_class_new = _make_option(page, "LevelUpReplaceClassNew", "Новое заклинание для замены")
	_new_spell.item_selected.connect(_on_new_class_spell_selected)
	_class_old.item_selected.connect(_on_class_replacement_selected)
	_class_new.item_selected.connect(_on_class_replacement_selected)

	page.add_child(HSeparator.new())
	page.add_child(_label("ПОСВЯЩЁННЫЙ В МАГИЮ", 22))

	_magic_cantrip_old = _make_option(page, "LevelUpMagicCantripOld", "Заменить заговор черты")
	_magic_cantrip_new = _make_option(page, "LevelUpMagicCantripNew", "Новый заговор")
	_magic_spell_old = _make_option(page, "LevelUpMagicSpellOld", "Заменить заклинание черты")
	_magic_spell_new = _make_option(page, "LevelUpMagicSpellNew", "Новое заклинание")
	_magic_cantrip_old.item_selected.connect(_on_magic_cantrip_selected)
	_magic_cantrip_new.item_selected.connect(_on_magic_cantrip_selected)
	_magic_spell_old.item_selected.connect(_on_magic_spell_selected)
	_magic_spell_new.item_selected.connect(_on_magic_spell_selected)

	_message = _label("", 18)
	_message.name = "LevelUpMessageLabel"
	_message.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	page.add_child(_message)

	var actions := HBoxContainer.new()
	actions.add_theme_constant_override("separation", 12)
	page.add_child(actions)

	_defer = Button.new()
	_defer.text = "ОТЛОЖИТЬ"
	_defer.custom_minimum_size = Vector2(220.0, 62.0)
	_defer.pressed.connect(close_panel)
	actions.add_child(_defer)

	_confirm = Button.new()
	_confirm.name = "LevelUpConfirmButton"
	_confirm.text = "ПОДТВЕРДИТЬ УРОВЕНЬ"
	_confirm.custom_minimum_size = Vector2(360.0, 62.0)
	_confirm.pressed.connect(_on_confirm_pressed)
	actions.add_child(_confirm)


func _refresh() -> void:
	if _hero == null or _state == null:
		return
	var transaction: Dictionary = _system.get_transaction(_state)
	var target_level: int = int(transaction.get("target_level", _hero.level + 1))
	_summary.text = (
		"%s · %s\nУровень %d → %d · Опыт %d / %d"
		% [
			_hero.character_name,
			_hero.character_class_name,
			_hero.level,
			target_level,
			_hero.experience,
			ProgressionSystem.total_experience_for_level(target_level)
		]
	)

	var fixed_gain: int = _system.get_fixed_hp_gain(_hero)
	var hp_mode: String = str(transaction.get("hp_mode", ""))
	var hp_roll: int = int(transaction.get("hp_roll", 0))
	var hp_gain: int = int(transaction.get("hp_gain", 0))
	_fixed_hp.text = "ФИКСИРОВАННО: +%d ЗДОРОВЬЯ%s" % [
		fixed_gain,
		" · ВЫБРАНО" if hp_mode == LevelUpSystem.HP_MODE_FIXED else ""
	]
	if hp_roll > 0:
		_roll_hp.text = "БРОСОК d%d: %d → +%d ЗДОРОВЬЯ%s" % [
			_hero.hit_die_size,
			hp_roll,
			hp_gain,
			" · ВЫБРАНО" if hp_mode == LevelUpSystem.HP_MODE_ROLL else ""
		]
	else:
		_roll_hp.text = "БРОСИТЬ d%d ОДИН РАЗ" % _hero.hit_die_size
	_roll_hp.disabled = false
	_roll_hp.tooltip_text = (
		"Результат %d уже сохранён; повторного броска не будет." % hp_roll
		if hp_roll > 0
		else "После броска результат сразу сохраняется и не может быть переброшен."
	)

	var feature_lines: Array[String] = []
	for feature_id: String in _system.get_level_features(_hero, target_level):
		feature_lines.append("• %s" % _system.describe_feature(feature_id))
	if feature_lines.is_empty():
		feature_lines.append("• Новых классовых особенностей этого уровня в текущем каталоге нет.")
	feature_lines.append("• Кости Хитов, лимиты подготовки и ячейки синхронизируются автоматически.")
	_features.text = "НОВЫЕ ВОЗМОЖНОСТИ\n%s" % "\n".join(feature_lines)

	_fill_option(
		_new_spell,
		_system.get_new_class_spell_candidates(_hero),
		str(transaction.get("new_class_spell_id", "")),
		"Без нового заклинания"
	)
	_fill_option(
		_class_old,
		_system.get_class_spell_replacement_old_candidates(_hero),
		str(transaction.get("replace_class_spell_old_id", "")),
		"Не заменять"
	)
	_fill_option(
		_class_new,
		_system.get_class_spell_replacement_new_candidates(_hero),
		str(transaction.get("replace_class_spell_new_id", "")),
		"Не заменять"
	)
	_fill_option(
		_magic_cantrip_old,
		_system.get_magic_initiate_cantrip_old_candidates(_hero),
		str(transaction.get("replace_magic_cantrip_old_id", "")),
		"Не заменять"
	)
	_fill_option(
		_magic_cantrip_new,
		_system.get_magic_initiate_cantrip_new_candidates(_hero),
		str(transaction.get("replace_magic_cantrip_new_id", "")),
		"Не заменять"
	)
	_fill_option(
		_magic_spell_old,
		_system.get_magic_initiate_spell_old_candidates(_hero),
		str(transaction.get("replace_magic_spell_old_id", "")),
		"Не заменять"
	)
	_fill_option(
		_magic_spell_new,
		_system.get_magic_initiate_spell_new_candidates(_hero),
		str(transaction.get("replace_magic_spell_new_id", "")),
		"Не заменять"
	)

	var has_class_choices: bool = (
		_new_spell.item_count > 1
		or _class_old.item_count > 1
		or _class_new.item_count > 1
	)
	_new_spell.visible = has_class_choices
	_class_old.visible = has_class_choices
	_class_new.visible = has_class_choices

	var has_magic_choices: bool = (
		_magic_cantrip_old.item_count > 1
		or _magic_cantrip_new.item_count > 1
		or _magic_spell_old.item_count > 1
		or _magic_spell_new.item_count > 1
	)
	_magic_cantrip_old.visible = has_magic_choices
	_magic_cantrip_new.visible = has_magic_choices
	_magic_spell_old.visible = has_magic_choices
	_magic_spell_new.visible = has_magic_choices

	var validation: Dictionary = _system.validate_transaction(_hero, _state)
	_confirm.disabled = not bool(validation.get("success", false))
	_show_message(str(validation.get("message", "")), not bool(validation.get("success", false)))


func _on_fixed_hp_pressed() -> void:
	var result: Dictionary = _system.choose_fixed_hp(_hero, _state)
	_show_message(str(result.get("message", "")), not bool(result.get("success", false)))
	_refresh()


func _on_roll_hp_pressed() -> void:
	var result: Dictionary = _system.roll_hp_once(_hero, _state)
	_show_message(str(result.get("message", "")), not bool(result.get("success", false)))
	_refresh()


func _on_new_class_spell_selected(_index: int) -> void:
	_system.set_new_class_spell(_hero, _state, _selected_id(_new_spell))
	_refresh()


func _on_class_replacement_selected(_index: int) -> void:
	_system.set_class_spell_replacement(
		_hero,
		_state,
		_selected_id(_class_old),
		_selected_id(_class_new)
	)
	_refresh()


func _on_magic_cantrip_selected(_index: int) -> void:
	_system.set_magic_initiate_cantrip_replacement(
		_hero,
		_state,
		_selected_id(_magic_cantrip_old),
		_selected_id(_magic_cantrip_new)
	)
	_refresh()


func _on_magic_spell_selected(_index: int) -> void:
	_system.set_magic_initiate_spell_replacement(
		_hero,
		_state,
		_selected_id(_magic_spell_old),
		_selected_id(_magic_spell_new)
	)
	_refresh()


func _on_confirm_pressed() -> void:
	var result: Dictionary = _system.commit_transaction(_hero, _state)
	if not bool(result.get("success", false)):
		_show_message(str(result.get("message", "Повышение не применено.")), true)
		_refresh()
		return
	close_panel()
	level_up_completed.emit(result)


func _make_option(parent: Control, node_name: String, tooltip: String) -> OptionButton:
	var option := OptionButton.new()
	option.name = node_name
	option.tooltip_text = tooltip
	option.custom_minimum_size = Vector2(0.0, 56.0)
	option.add_theme_font_size_override("font_size", 18)
	parent.add_child(option)
	return option


func _fill_option(
	option: OptionButton,
	values: Array[String],
	selected_id: String,
	empty_label: String
) -> void:
	option.clear()
	option.add_item(empty_label)
	option.set_item_metadata(0, "")
	var selected_index: int = 0
	for value_id: String in values:
		option.add_item(_system.spell_name(value_id))
		var index: int = option.item_count - 1
		option.set_item_metadata(index, value_id)
		if value_id == selected_id:
			selected_index = index
	option.select(selected_index)
	option.disabled = option.item_count <= 1


func _selected_id(option: OptionButton) -> String:
	if option == null or option.selected < 0:
		return ""
	return str(option.get_item_metadata(option.selected))


func _show_message(text_value: String, is_error: bool) -> void:
	if _message == null:
		return
	_message.text = text_value
	_message.add_theme_color_override(
		"font_color",
		Color(1.0, 0.56, 0.48, 1.0) if is_error else Color(0.64, 0.94, 0.68, 1.0)
	)


func _label(text_value: String, font_size: int) -> Label:
	var label := Label.new()
	label.text = text_value
	label.add_theme_font_size_override("font_size", font_size)
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return label
