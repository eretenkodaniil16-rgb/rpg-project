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
var _selected_power: String = ""


func open_sheet(character: PlayerCharacter) -> void:
	open_tab(character, 0)


func open_tab(character: PlayerCharacter, tab_index: int = 0) -> void:
	_hero = character
	_refresh_all()
	_tabs.current_tab = clampi(tab_index, 0, 2)
	GameState.input_locked = true
	show()
	_close.grab_focus()


func close_sheet() -> void:
	if not visible:
		return
	hide()
	GameState.input_locked = false
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
	split.add_child(right)
	_details = _label("Выберите заклинание или способность.", 18)
	_details.size_flags_vertical = Control.SIZE_EXPAND_FILL
	right.add_child(_details)
	_prepare = Button.new()
	_prepare.text = "ПОДГОТОВИТЬ"
	_prepare.custom_minimum_size = Vector2(0.0, 56.0)
	_prepare.pressed.connect(_prepare_selected)
	_prepare.hide()
	right.add_child(_prepare)


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
	var names: Dictionary = {"strength":"Сила", "dexterity":"Ловкость", "constitution":"Телосложение", "intelligence":"Интеллект", "wisdom":"Мудрость", "charisma":"Харизма"}
	for ability_id: String in names.keys():
		var modifier: int = _hero.get_ability_modifier(ability_id)
		_character_box.add_child(_label("%s: %d (%s)" % [str(names[ability_id]), _hero.get_ability_score(ability_id), "+%d" % modifier if modifier >= 0 else str(modifier)], 18))
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
	var entries: Array = GameState.get_inventory_entries()
	if entries.is_empty():
		_inventory_box.add_child(_label("Инвентарь пуст.", 19))
		return
	for value: Variant in entries:
		if value is Dictionary:
			var entry: Dictionary = value as Dictionary
			_inventory_box.add_child(_label("%s ×%d\n%s" % [str(entry.get("name", "Предмет")), int(entry.get("quantity", 0)), str(entry.get("description", ""))], 18))


func _refresh_powers() -> void:
	_clear(_powers_box)
	var entries: Array[Dictionary] = _active_entries()
	var prepared_id: String = _prepared_id(entries)
	var prepared: Dictionary = _class_data.get_ability_definition(prepared_id)
	_powers_box.add_child(_label("ПОДГОТОВЛЕНО: %s" % str(prepared.get("name", "ничего")), 20))
	for ability: Dictionary in entries:
		var id: String = str(ability.get("id", ""))
		var button := Button.new()
		button.text = "%s%s · %s" % ["◆ " if id == prepared_id else "", "ЗАКЛИНАНИЕ" if _is_spell(ability) else "СПОСОБНОСТЬ", str(ability.get("name", "Действие"))]
		button.custom_minimum_size = Vector2(0.0, 52.0)
		button.alignment = HORIZONTAL_ALIGNMENT_LEFT
		button.pressed.connect(_select_power.bind(ability))
		_powers_box.add_child(button)
	if not entries.is_empty():
		_select_power(entries[0])


func _select_power(ability: Dictionary) -> void:
	_selected_power = str(ability.get("id", ""))
	_details.text = "%s\n\nРесурс: %s\n\n%s" % [str(ability.get("name", "Действие")), _class_data.get_resource_text(_hero, ability), str(ability.get("description", ""))]
	_prepare.show()
	_prepare.disabled = _selected_power == str(GameState.get_flag(PREPARED_FLAG, ""))
	_prepare.text = "ПОДГОТОВЛЕНО" if _prepare.disabled else "ПОДГОТОВИТЬ"


func _prepare_selected() -> void:
	if _selected_power.is_empty():
		return
	GameState.set_flag(PREPARED_FLAG, _selected_power)
	GameState.save_game()
	prepared_action_changed.emit(_selected_power)
	_refresh_powers()


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
	var saved: String = str(GameState.get_flag(PREPARED_FLAG, ""))
	for ability: Dictionary in entries:
		if str(ability.get("id", "")) == saved:
			return saved
	for ability: Dictionary in entries:
		if str(ability.get("id", "")) == _hero.signature_ability_id:
			GameState.set_flag(PREPARED_FLAG, _hero.signature_ability_id)
			return _hero.signature_ability_id
	return str(entries[0].get("id", "")) if not entries.is_empty() else ""


func _is_spell(ability: Dictionary) -> bool:
	return str(ability.get("effect", "")) in ["spell_attack", "auto_hit_spell", "saving_throw_spell", "heal_2d8_wisdom"]


func _rest(long_rest: bool) -> void:
	var result: Dictionary = _class_data.long_rest(_hero) if long_rest else _class_data.short_rest(_hero)
	if bool(result.get("success", false)):
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
