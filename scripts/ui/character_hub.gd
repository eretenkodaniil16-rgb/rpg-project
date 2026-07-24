class_name CharacterHub
extends CharacterSheet

signal prepared_action_changed(ability_id: String)

const PREPARED_FLAG: String = "prepared_ability_id"

var _hero: PlayerCharacter
var _tabs: TabContainer
var _close: Button
var _character_box: VBoxContainer
var _inventory_box: VBoxContainer
var _powers_box: VBoxContainer
var _details: Label
var _prepare: Button
var _spell_prepare: Button
var _slot_level: OptionButton
var _ritual: Button
var _selected_power: String = ""
var _spellcasting: SpellcastingSystem = SpellcastingSystem.new()
var _world_time: WorldTimeSystem = WorldTimeSystem.new()


func open_sheet(character: PlayerCharacter) -> void:
	open_tab(character, 0)


func open_tab(character: PlayerCharacter, tab_index: int = 0) -> void:
	_hero = character
	var state: Node = _game_state()
	_spellcasting.ensure_character(_hero, false)
	_spellcasting.cleanup_expired_effects(_hero, _world_time.get_minutes(state))
	_refresh_all()
	_tabs.current_tab = clampi(tab_index, 0, 2)
	if state != null:
		state.set("input_locked", true)
	show()
	_close.grab_focus()


func close_sheet() -> void:
	if not visible:
		return
	hide()
	var state: Node = _game_state()
	if state != null:
		state.set("input_locked", false)
	closed.emit()


func _unhandled_input(event: InputEvent) -> void:
	if visible and event.is_action_pressed("ui_cancel"):
		close_sheet()
		get_viewport().set_input_as_handled()


func _build_ui() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	var background := ColorRect.new()
	background.color = Color(0.0, 0.0, 0.0, 0.78)
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(background)
	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	margin.add_theme_constant_override("margin_left", 42)
	margin.add_theme_constant_override("margin_top", 26)
	margin.add_theme_constant_override("margin_right", 42)
	margin.add_theme_constant_override("margin_bottom", 26)
	add_child(margin)
	var panel := PanelContainer.new()
	margin.add_child(panel)
	var page := VBoxContainer.new()
	page.add_theme_constant_override("separation", 10)
	panel.add_child(page)
	var header := HBoxContainer.new()
	page.add_child(header)
	var title := Label.new()
	title.text = "ПЕРСОНАЖ"
	title.add_theme_font_size_override("font_size", 28)
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(title)
	_close = Button.new()
	_close.text = "ЗАКРЫТЬ"
	_close.custom_minimum_size = Vector2(160.0, 50.0)
	_close.pressed.connect(close_sheet)
	header.add_child(_close)
	_tabs = TabContainer.new()
	_tabs.name = "CharacterTabs"
	_tabs.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_tabs.add_theme_font_size_override("font_size", 18)
	page.add_child(_tabs)
	_character_box = _make_tab("ПЕРСОНАЖ")
	_inventory_box = _make_tab("ИНВЕНТАРЬ")
	_build_powers_tab()


func _make_tab(tab_name: String) -> VBoxContainer:
	var scroll := ScrollContainer.new()
	scroll.name = tab_name
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_tabs.add_child(scroll)
	var box := VBoxContainer.new()
	box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	box.add_theme_constant_override("separation", 9)
	scroll.add_child(box)
	return box


func _build_powers_tab() -> void:
	var split := HSplitContainer.new()
	split.name = "ЗАКЛИНАНИЯ И СПОСОБНОСТИ"
	split.split_offset = 520
	_tabs.add_child(split)
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	split.add_child(scroll)
	_powers_box = VBoxContainer.new()
	_powers_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(_powers_box)
	var right := VBoxContainer.new()
	right.add_theme_constant_override("separation", 8)
	split.add_child(right)
	_details = _label("Выберите заклинание или способность.", 18)
	_details.size_flags_vertical = Control.SIZE_EXPAND_FILL
	right.add_child(_details)
	_prepare = Button.new()
	_prepare.text = "НА БЫСТРУЮ КНОПКУ"
	_prepare.custom_minimum_size = Vector2(0.0, 56.0)
	_prepare.pressed.connect(_prepare_selected)
	_prepare.hide()
	right.add_child(_prepare)
	_spell_prepare = Button.new()
	_spell_prepare.text = "ПОДГОТОВИТЬ ЗАКЛИНАНИЕ"
	_spell_prepare.custom_minimum_size = Vector2(0.0, 56.0)
	_spell_prepare.pressed.connect(_toggle_spell_prepared)
	_spell_prepare.hide()
	right.add_child(_spell_prepare)
	_slot_level = OptionButton.new()
	_slot_level.name = "SpellSlotLevel"
	_slot_level.custom_minimum_size = Vector2(0.0, 52.0)
	_slot_level.item_selected.connect(_slot_level_selected)
	_slot_level.hide()
	right.add_child(_slot_level)
	_ritual = Button.new()
	_ritual.text = "СОТВОРИТЬ КАК РИТУАЛ"
	_ritual.custom_minimum_size = Vector2(0.0, 56.0)
	_ritual.pressed.connect(_cast_selected_ritual)
	_ritual.hide()
	right.add_child(_ritual)


func _refresh_all() -> void:
	if _hero == null:
		return
	_refresh_character()
	_refresh_inventory()
	_refresh_powers()


func _refresh_character() -> void:
	_clear(_character_box)
	_character_box.add_child(_label("%s — %s, уровень %d" % [_hero.character_name, _hero.character_class_name, _hero.level], 25))
	_character_box.add_child(_label("Здоровье %d/%d · КД %d · Опыт %d" % [_hero.current_health, _hero.maximum_health, _class_data.get_armor_class(_hero), _hero.experience], 19))
	_character_box.add_child(_label("Время мира: %s" % _world_time.format_current(_game_state()), 18))
	var names: Dictionary = {"strength":"Сила", "dexterity":"Ловкость", "constitution":"Телосложение", "intelligence":"Интеллект", "wisdom":"Мудрость", "charisma":"Харизма"}
	for ability_id: String in names.keys():
		var modifier: int = _hero.get_ability_modifier(ability_id)
		_character_box.add_child(_label("%s: %d (%s)" % [str(names[ability_id]), _hero.get_ability_score(ability_id), "+%d" % modifier if modifier >= 0 else str(modifier)], 18))
	var concentration_id: String = _spellcasting.get_concentration_spell_id(_hero)
	if not concentration_id.is_empty():
		var concentration_spell: Dictionary = _class_data.get_ability_definition(concentration_id)
		_character_box.add_child(_label("Концентрация: %s" % str(concentration_spell.get("name", concentration_id)), 18))
	var rest_row := HBoxContainer.new()
	_character_box.add_child(rest_row)
	var short_rest := Button.new()
	short_rest.text = "КОРОТКИЙ ОТДЫХ"
	short_rest.pressed.connect(_rest.bind(false))
	rest_row.add_child(short_rest)
	var long_rest := Button.new()
	long_rest.text = "ДОЛГИЙ ОТДЫХ"
	long_rest.pressed.connect(_rest.bind(true))
	rest_row.add_child(long_rest)


func _refresh_inventory() -> void:
	_clear(_inventory_box)
	var state: Node = _game_state()
	var entries: Array = state.call("get_inventory_entries") as Array if state != null else []
	if entries.is_empty():
		_inventory_box.add_child(_label("Инвентарь пуст.", 19))
		return
	for value: Variant in entries:
		if value is Dictionary:
			var entry: Dictionary = value as Dictionary
			_inventory_box.add_child(_label("%s ×%d\n%s" % [str(entry.get("name", "Предмет")), int(entry.get("quantity", 0)), str(entry.get("description", ""))], 18))


func _refresh_powers() -> void:
	_clear(_powers_box)
	_spellcasting.ensure_character(_hero, false)
	var entries: Array[Dictionary] = _active_entries()
	var prepared_id: String = _prepared_id(entries)
	var prepared: Dictionary = _class_data.get_ability_definition(prepared_id)
	_powers_box.add_child(_label("БЫСТРАЯ КНОПКА: %s" % str(prepared.get("name", "ничего")), 20))
	var prepared_spells: Array[String] = _spellcasting.get_prepared_spell_ids(_hero)
	var prepared_limit: int = _spellcasting.get_prepared_limit(_hero)
	if prepared_limit > 0:
		_powers_box.add_child(_label("Подготовлено заклинаний: %d/%d" % [_count_changeable_prepared(prepared_spells), prepared_limit], 17))
	for ability: Dictionary in entries:
		var id: String = str(ability.get("id", ""))
		var button := Button.new()
		var prepared_mark: String = "◆ " if id == prepared_id else ""
		var spell_mark: String = " ✦" if _is_spell(ability) and _spellcasting.is_prepared(_hero, id) else ""
		button.text = "%s%s · %s%s" % [prepared_mark, "ЗАКЛИНАНИЕ" if _is_spell(ability) else "СПОСОБНОСТЬ", str(ability.get("name", "Действие")), spell_mark]
		button.custom_minimum_size = Vector2(0.0, 52.0)
		button.alignment = HORIZONTAL_ALIGNMENT_LEFT
		button.pressed.connect(_select_power.bind(ability))
		_powers_box.add_child(button)
	if not entries.is_empty():
		_select_power(entries[0])
	else:
		_prepare.hide()
		_spell_prepare.hide()
		_slot_level.hide()
		_ritual.hide()


func _select_power(ability: Dictionary) -> void:
	_selected_power = str(ability.get("id", ""))
	var resource_text: String = _class_data.get_resource_text(_hero, ability)
	var mechanics_text: String = ""
	if _is_spell(ability):
		mechanics_text = "%s\n\n" % _spellcasting.describe_spell(_hero, ability)
		resource_text = _spell_resource_text(ability)
	_details.text = "%s%s\n\nРесурс: %s\n\n%s" % [mechanics_text, str(ability.get("name", "Действие")), resource_text, str(ability.get("description", ""))]
	_prepare.show()
	var state: Node = _game_state()
	var saved_id: String = str(state.call("get_flag", PREPARED_FLAG, "")) if state != null else ""
	_prepare.disabled = _selected_power == saved_id
	_prepare.text = "НА БЫСТРОЙ КНОПКЕ" if _prepare.disabled else "НА БЫСТРУЮ КНОПКУ"
	_refresh_spell_buttons(ability)


func _refresh_spell_buttons(ability: Dictionary) -> void:
	_spell_prepare.hide()
	_slot_level.hide()
	_ritual.hide()
	if not _is_spell(ability):
		return
	var spell_level: int = maxi(int(ability.get("spell_level", 0)), 0)
	var always_prepared: bool = spell_level == 0 or bool(ability.get("always_prepared", false))
	if spell_level > 0:
		_refresh_slot_level_selector(ability, spell_level)
	if spell_level > 0 and not always_prepared:
		_spell_prepare.show()
		var prepared: bool = _spellcasting.is_prepared(_hero, _selected_power)
		_spell_prepare.text = "СНЯТЬ С ПОДГОТОВКИ" if prepared else "ПОДГОТОВИТЬ ЗАКЛИНАНИЕ"
	if bool(ability.get("ritual", false)):
		_ritual.show()
		_ritual.disabled = not _spellcasting.can_cast_spell(_hero, ability, true, _is_combat_active())
		_ritual.text = "РИТУАЛ НЕДОСТУПЕН" if _ritual.disabled else "СОТВОРИТЬ КАК РИТУАЛ"


func _refresh_slot_level_selector(ability: Dictionary, spell_level: int) -> void:
	var levels: Array[int] = _spellcasting.get_available_slot_levels(_hero, spell_level, false)
	if levels.is_empty():
		return
	var selected_level: int = _spellcasting.get_selected_slot_level(_hero, _selected_power)
	if selected_level not in levels:
		selected_level = levels[0]
		_spellcasting.set_selected_slot_level(_hero, _selected_power, selected_level)
	_slot_level.set_block_signals(true)
	_slot_level.clear()
	var selected_index: int = 0
	for index: int in range(levels.size()):
		var level: int = levels[index]
		var resource_key: String = _spellcasting.slot_resource_key(_hero, level)
		_slot_level.add_item("ЯЧЕЙКА %d УРОВНЯ · %d/%d" % [level, _hero.get_resource(resource_key), _hero.get_resource_maximum(resource_key)])
		_slot_level.set_item_metadata(index, level)
		if level == selected_level:
			selected_index = index
	_slot_level.select(selected_index)
	_slot_level.set_block_signals(false)
	_slot_level.show()


func _slot_level_selected(index: int) -> void:
	if _hero == null or _selected_power.is_empty() or index < 0 or index >= _slot_level.item_count:
		return
	var level: int = int(_slot_level.get_item_metadata(index))
	var response: Dictionary = _spellcasting.set_selected_slot_level(_hero, _selected_power, level)
	if not bool(response.get("success", false)):
		_details.text = str(response.get("message", "Уровень ячейки недоступен."))
		return
	var state: Node = _game_state()
	if state != null:
		state.call("save_game")
	var ability: Dictionary = _class_data.get_ability_definition(_selected_power)
	_select_power(ability)


func _prepare_selected() -> void:
	if _selected_power.is_empty():
		return
	var state: Node = _game_state()
	if state == null:
		return
	state.call("set_flag", PREPARED_FLAG, _selected_power)
	state.call("save_game")
	prepared_action_changed.emit(_selected_power)
	_refresh_powers()


func _toggle_spell_prepared() -> void:
	if _selected_power.is_empty():
		return
	var response: Dictionary
	if _spellcasting.is_prepared(_hero, _selected_power):
		response = _spellcasting.unprepare_spell(_hero, _selected_power)
	else:
		response = _spellcasting.prepare_spell(_hero, _selected_power)
	var state: Node = _game_state()
	if state != null:
		state.call("save_game")
	_refresh_powers()
	var selected: Dictionary = _class_data.get_ability_definition(_selected_power)
	if not selected.is_empty():
		_select_power(selected)
		_details.text += "\n\n%s" % str(response.get("message", ""))


func _cast_selected_ritual() -> void:
	if _selected_power.is_empty():
		return
	var state: Node = _game_state()
	var current_minutes: int = _world_time.get_minutes(state)
	var casting_context: Dictionary = _class_data.get_spellcasting_context(_hero)
	var response: Dictionary = _spellcasting.cast_ritual(_hero, _selected_power, current_minutes, _is_combat_active(), casting_context)
	if bool(response.get("success", false)):
		_world_time.advance(state, int(response.get("advance_minutes", 0)), false)
		_spellcasting.cleanup_expired_effects(_hero, _world_time.get_minutes(state))
		if state != null:
			state.call("save_game")
	_refresh_all()
	var selected: Dictionary = _class_data.get_ability_definition(_selected_power)
	if not selected.is_empty():
		_select_power(selected)
		_details.text += "\n\n%s\n%s" % [str(response.get("message", "")), _world_time.format_current(state)]


func _active_entries() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	var ids: Array[String] = _hero.known_features.duplicate()
	for id: String in [_hero.signature_ability_id, _hero.racial_ability_id]:
		if not id.is_empty() and id not in ids:
			ids.append(id)
	for id: String in ids:
		var ability: Dictionary = _class_data.get_ability_definition(id)
		if not ability.is_empty() and str(ability.get("kind", "")) == "active":
			result.append(ability)
	return result


func _prepared_id(entries: Array[Dictionary]) -> String:
	var state: Node = _game_state()
	var saved: String = str(state.call("get_flag", PREPARED_FLAG, "")) if state != null else ""
	for ability: Dictionary in entries:
		if str(ability.get("id", "")) == saved:
			return saved
	for ability: Dictionary in entries:
		if str(ability.get("id", "")) == _hero.signature_ability_id:
			if state != null:
				state.call("set_flag", PREPARED_FLAG, _hero.signature_ability_id)
			return _hero.signature_ability_id
	return str(entries[0].get("id", "")) if not entries.is_empty() else ""


func _is_spell(ability: Dictionary) -> bool:
	return _spellcasting.is_spell_definition(ability)


func _spell_resource_text(spell: Dictionary) -> String:
	var level: int = maxi(int(spell.get("spell_level", 0)), 0)
	if level == 0:
		return "Без ячейки"
	var key: String = _spellcasting.active_resource_key(_hero, spell)
	if key == "unlimited":
		return "Без ограничений"
	var text: String = "%d/%d" % [_hero.get_resource(key), _hero.get_resource_maximum(key)]
	if bool(spell.get("ritual", false)):
		text += " · ритуал без ячейки"
	return text


func _count_changeable_prepared(prepared: Array[String]) -> int:
	var result: int = 0
	for spell_id: String in prepared:
		var spell: Dictionary = _class_data.get_ability_definition(spell_id)
		if spell.is_empty() or int(spell.get("spell_level", 0)) == 0 or bool(spell.get("always_prepared", false)):
			continue
		result += 1
	return result


func _is_combat_active() -> bool:
	var game: Node = get_tree().get_first_node_in_group("game_world")
	return game != null and game.has_method("is_turn_based_combat_active") and bool(game.call("is_turn_based_combat_active"))


func _rest(long_rest: bool) -> void:
	var result: Dictionary = _class_data.long_rest(_hero) if long_rest else _class_data.short_rest(_hero)
	if bool(result.get("success", false)):
		var state: Node = _game_state()
		_world_time.advance(state, int(result.get("duration_hours", 1 if not long_rest else _hero.long_rest_hours)) * 60, false)
		_spellcasting.ensure_character(_hero, long_rest)
		_spellcasting.cleanup_expired_effects(_hero, _world_time.get_minutes(state))
		if state != null:
			state.call("save_game")
		rest_completed.emit("long" if long_rest else "short")
	_refresh_all()


func _label(value: String, font_size: int) -> Label:
	var label := Label.new()
	label.text = value
	label.add_theme_font_size_override("font_size", font_size)
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return label


func _clear(node: Node) -> void:
	for child: Node in node.get_children():
		child.queue_free()
