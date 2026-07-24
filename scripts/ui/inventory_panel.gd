class_name InventoryPanel
extends Control

var _class_data: ClassDataSystem = ClassDataSystem.new()
var _spellbook_system: WizardSpellbookSystem = WizardSpellbookSystem.new()
var _item_list: VBoxContainer
var _details_label: Label
var _equip_button: Button
var _copy_scroll_button: Button
var _selected_entry: Dictionary = {}


func _ready() -> void:
	_build_layout()
	hide()


func open_inventory() -> void:
	GameState.input_locked = true
	show()
	_refresh()


func close_inventory() -> void:
	hide()
	GameState.input_locked = false


func _unhandled_input(event: InputEvent) -> void:
	if visible and event.is_action_pressed("ui_cancel"):
		close_inventory()
		get_viewport().set_input_as_handled()


func _build_layout() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	var dimmer := ColorRect.new()
	dimmer.color = Color(0.0, 0.0, 0.0, 0.72)
	dimmer.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	dimmer.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(dimmer)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(center)
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(980.0, 580.0)
	center.add_child(panel)
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 30)
	margin.add_theme_constant_override("margin_top", 24)
	margin.add_theme_constant_override("margin_right", 30)
	margin.add_theme_constant_override("margin_bottom", 24)
	panel.add_child(margin)
	var root_column := VBoxContainer.new()
	root_column.add_theme_constant_override("separation", 16)
	margin.add_child(root_column)
	var header := HBoxContainer.new()
	root_column.add_child(header)
	var title := Label.new()
	title.text = "ИНВЕНТАРЬ"
	title.add_theme_font_size_override("font_size", 27)
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(title)
	var close_button := Button.new()
	close_button.text = "Закрыть"
	close_button.custom_minimum_size = Vector2(140.0, 48.0)
	close_button.pressed.connect(close_inventory)
	header.add_child(close_button)
	root_column.add_child(HSeparator.new())
	var body := HSplitContainer.new()
	body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.split_offset = 350
	root_column.add_child(body)
	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(330.0, 0.0)
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	body.add_child(scroll)
	_item_list = VBoxContainer.new()
	_item_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_item_list.add_theme_constant_override("separation", 8)
	scroll.add_child(_item_list)
	var detail_column := VBoxContainer.new()
	detail_column.custom_minimum_size = Vector2(520.0, 0.0)
	detail_column.add_theme_constant_override("separation", 12)
	body.add_child(detail_column)
	_details_label = Label.new()
	_details_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_details_label.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_details_label.add_theme_font_size_override("font_size", 20)
	_details_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_details_label.text = "Выберите предмет слева."
	detail_column.add_child(_details_label)
	_equip_button = Button.new()
	_equip_button.text = "ЭКИПИРОВАТЬ"
	_equip_button.custom_minimum_size = Vector2(0.0, 58.0)
	_equip_button.add_theme_font_size_override("font_size", 19)
	_equip_button.pressed.connect(_equip_selected)
	_equip_button.hide()
	detail_column.add_child(_equip_button)
	_copy_scroll_button = Button.new()
	_copy_scroll_button.name = "CopyScrollButton"
	_copy_scroll_button.text = "ПЕРЕПИСАТЬ В КНИГУ"
	_copy_scroll_button.custom_minimum_size = Vector2(0.0, 58.0)
	_copy_scroll_button.add_theme_font_size_override("font_size", 19)
	_copy_scroll_button.pressed.connect(_copy_selected_scroll)
	_copy_scroll_button.hide()
	detail_column.add_child(_copy_scroll_button)


func _refresh() -> void:
	_clear_container(_item_list)
	var entries: Array = GameState.get_inventory_entries()
	if entries.is_empty():
		var empty_label := Label.new()
		empty_label.text = "Инвентарь пуст."
		empty_label.add_theme_font_size_override("font_size", 20)
		_item_list.add_child(empty_label)
		_details_label.text = "Предметы появятся здесь после получения наград, находок или добычи."
		_equip_button.hide()
		_copy_scroll_button.hide()
		return
	entries.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return str(a.get("type", "")) < str(b.get("type", "")))
	for entry_value: Variant in entries:
		if not entry_value is Dictionary:
			continue
		var entry := entry_value as Dictionary
		var equipped: bool = _class_data.is_equipped(GameState.player_character, str(entry.get("id", "")))
		var button := Button.new()
		button.text = "%s%s ×%d" % ["★ " if equipped else "", str(entry.get("name", "Предмет")), int(entry.get("quantity", 0))]
		button.custom_minimum_size = Vector2(0.0, 58.0)
		button.alignment = HORIZONTAL_ALIGNMENT_LEFT
		button.pressed.connect(_show_details.bind(entry))
		_item_list.add_child(button)
	var first_entry: Variant = entries[0]
	if first_entry is Dictionary:
		_show_details(first_entry as Dictionary)


func _show_details(entry: Dictionary) -> void:
	_selected_entry = entry.duplicate(true)
	var type_id: String = str(entry.get("type", "misc"))
	var type_name: String = {
		"quest":"Квестовый предмет", "material":"Материал", "consumable":"Расходуемый предмет",
		"weapon":"Оружие", "armor":"Броня", "shield":"Щит", "ammunition":"Боеприпасы",
		"currency":"Валюта", "focus":"Магический фокус", "tool":"Инструмент",
		"book":"Книга", "spell_scroll":"Свиток заклинания", "gear":"Снаряжение", "misc":"Прочее"
	}.get(type_id, "Прочее")
	var item_id: String = str(entry.get("id", ""))
	var equipped: bool = _class_data.is_equipped(GameState.player_character, item_id)
	var equipment_text: String = "
Состояние: ЭКИПИРОВАНО" if equipped else ""
	var stats_text: String = _equipment_stats(entry)
	var scroll_text: String = _scroll_transcription_text(entry) if type_id == "spell_scroll" else ""
	_details_label.text = "%s

Тип: %s
Количество: %d%s%s

%s%s" % [
		str(entry.get("name", "Предмет")), type_name, int(entry.get("quantity", 0)),
		equipment_text, stats_text, str(entry.get("description", "Описание отсутствует.")), scroll_text
	]
	_equip_button.visible = type_id in ["weapon", "armor", "shield"]
	_equip_button.disabled = equipped
	_equip_button.text = "ЭКИПИРОВАНО" if equipped else "ЭКИПИРОВАТЬ"
	_copy_scroll_button.visible = type_id == "spell_scroll"
	if type_id == "spell_scroll":
		var inspection: Dictionary = _spellbook_system.inspect_scroll(GameState.player_character, item_id, GameState)
		_copy_scroll_button.disabled = not bool(inspection.get("success", false))
		_copy_scroll_button.text = "ПЕРЕПИСАТЬ В КНИГУ"
	else:
		_copy_scroll_button.disabled = true


func _scroll_transcription_text(entry: Dictionary) -> String:
	var inspection: Dictionary = _spellbook_system.inspect_scroll(
		GameState.player_character,
		str(entry.get("id", "")),
		GameState
	)
	if not bool(inspection.get("success", false)):
		return "

Переписывание: %s" % str(inspection.get("message", "Недоступно."))
	var minutes: int = int(inspection.get("time_minutes", 0))
	var hours: int = floori(float(minutes) / 60.0)
	var remaining_minutes: int = minutes % 60
	var time_text: String = "%d ч" % hours
	if remaining_minutes > 0:
		time_text += " %d мин" % remaining_minutes
	return "

Переписывание в книгу:
Стоимость: %d зм · Время: %s · Проверка Магии: Сл %d
Свиток уничтожается при успехе и провале." % [
		int(inspection.get("cost_gp", 0)),
		time_text,
		int(inspection.get("check_dc", 0))
	]


func _copy_selected_scroll() -> void:
	var item_id: String = str(_selected_entry.get("id", ""))
	if item_id.is_empty() or str(_selected_entry.get("type", "")) != "spell_scroll":
		return
	var result: Dictionary = _spellbook_system.copy_scroll_to_spellbook(
		GameState.player_character,
		item_id,
		GameState
	)
	_refresh()
	var check_text: String = ""
	if bool(result.get("scroll_consumed", false)):
		check_text = "
Бросок: %d, итог %d против Сл %d." % [
			int(result.get("natural_roll", 0)),
			int(result.get("check_total", 0)),
			int(result.get("check_dc", 0))
		]
	_details_label.text = "%s%s" % [str(result.get("message", "Переписывание завершено.")), check_text]


func _equipment_stats(entry: Dictionary) -> String:
	var type_id: String = str(entry.get("type", ""))
	if type_id == "weapon":
		var dice: Array = entry.get("damage_dice", [1, 1]) as Array
		return "\nУрон: %dd%d %s" % [int(dice[0]), int(dice[1]), str(entry.get("damage_type", "физический"))]
	if type_id == "armor":
		return "\nБазовый КД: %d" % int(entry.get("base_ac", 10))
	if type_id == "shield":
		return "\nБонус КД: +%d" % int(entry.get("ac_bonus", 2))
	return ""


func _equip_selected() -> void:
	var item_id: String = str(_selected_entry.get("id", ""))
	if item_id.is_empty():
		return
	if _class_data.equip_item(GameState.player_character, item_id):
		_refresh()


func _clear_container(container: Container) -> void:
	for child: Node in container.get_children():
		child.queue_free()
