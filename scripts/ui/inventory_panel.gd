class_name InventoryPanel
extends Control

signal item_use_requested(item_id: String)

var _class_data: ClassDataSystem = ClassDataSystem.new()
var _item_list: VBoxContainer
var _details_label: Label
var _use_button: Button
var _equip_button: Button
var _selected_entry: Dictionary = {}


func _ready() -> void:
	_build_layout()
	hide()


func open_inventory() -> void:
	var state: Node = _game_state()
	if state == null:
		return
	state.set("input_locked", true)
	show()
	_refresh()


func close_inventory() -> void:
	hide()
	var state: Node = _game_state()
	if state != null:
		state.set("input_locked", false)


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
	_use_button = Button.new()
	_use_button.text = "ИСПОЛЬЗОВАТЬ"
	_use_button.custom_minimum_size = Vector2(0.0, 58.0)
	_use_button.add_theme_font_size_override("font_size", 19)
	_use_button.pressed.connect(_use_selected)
	_use_button.hide()
	detail_column.add_child(_use_button)
	_equip_button = Button.new()
	_equip_button.text = "ЭКИПИРОВАТЬ"
	_equip_button.custom_minimum_size = Vector2(0.0, 58.0)
	_equip_button.add_theme_font_size_override("font_size", 19)
	_equip_button.pressed.connect(_equip_selected)
	_equip_button.hide()
	detail_column.add_child(_equip_button)


func _refresh() -> void:
	_clear_container(_item_list)
	var state: Node = _game_state()
	if state == null or not state.has_method("get_inventory_entries"):
		_show_unavailable_state()
		return
	var entries_value: Variant = state.call("get_inventory_entries")
	var entries: Array = entries_value as Array if entries_value is Array else []
	if entries.is_empty():
		var empty_label := Label.new()
		empty_label.text = "Инвентарь пуст."
		empty_label.add_theme_font_size_override("font_size", 20)
		_item_list.add_child(empty_label)
		_details_label.text = "Предметы появятся здесь после получения наград, находок или добычи."
		_use_button.hide()
		_equip_button.hide()
		return
	entries.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return str(a.get("type", "")) < str(b.get("type", "")))
	var character: PlayerCharacter = _player_character(state)
	for entry_value: Variant in entries:
		if not entry_value is Dictionary:
			continue
		var entry := entry_value as Dictionary
		var equipped: bool = character != null and _class_data.is_equipped(character, str(entry.get("id", "")))
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
		"book":"Книга", "gear":"Снаряжение", "misc":"Прочее"
	}.get(type_id, "Прочее")
	var state: Node = _game_state()
	var character: PlayerCharacter = _player_character(state)
	var item_id: String = str(entry.get("id", ""))
	var equipped: bool = character != null and _class_data.is_equipped(character, item_id)
	var equipment_text: String = "\nСостояние: ЭКИПИРОВАНО" if equipped else ""
	var stats_text: String = _equipment_stats(entry, character)
	_details_label.text = "%s\n\nТип: %s\nКоличество: %d%s%s\n\n%s" % [
		str(entry.get("name", "Предмет")), type_name, int(entry.get("quantity", 0)),
		equipment_text, stats_text, str(entry.get("description", "Описание отсутствует."))
	]
	var use_action_value: Variant = entry.get("use_action", {})
	var use_action: Dictionary = use_action_value as Dictionary if use_action_value is Dictionary else {}
	_use_button.visible = not use_action.is_empty()
	_use_button.disabled = int(entry.get("quantity", 0)) <= 0
	_use_button.text = str(use_action.get("inventory_label", "ИСПОЛЬЗОВАТЬ"))
	_equip_button.visible = type_id in ["weapon", "armor", "shield"]
	_equip_button.disabled = equipped or character == null
	_equip_button.text = "ЭКИПИРОВАНО" if equipped else "ЭКИПИРОВАТЬ"


func _equipment_stats(entry: Dictionary, character: PlayerCharacter) -> String:
	var type_id: String = str(entry.get("type", ""))
	if type_id == "weapon":
		var dice: Array = entry.get("damage_dice", [1, 1]) as Array
		var weapon_trained: bool = character != null and character.is_proficient_with_weapon_definition(entry)
		return "\nУрон: %dd%d %s\nВладение: %s%s" % [
			int(dice[0]),
			int(dice[1]),
			str(entry.get("damage_type", "физический")),
			"есть" if weapon_trained else "нет",
			"" if weapon_trained else " — бонус мастерства к атаке не добавляется"
		]
	if type_id == "armor":
		var armor_category: String = str(entry.get("armor_category", "clothing"))
		var armor_trained: bool = armor_category == "clothing" or (character != null and character.has_armor_training(armor_category))
		return "\nБазовый КД: %d\nОбучение: %s%s" % [
			int(entry.get("base_ac", 10)),
			"есть" if armor_trained else "нет",
			"" if armor_trained else " — помеха тестам Силы/Ловкости и запрет колдовства"
		]
	if type_id == "shield":
		var shield_trained: bool = character != null and character.has_armor_training("shield")
		return "\nБонус КД: +%d\nОбучение: %s%s" % [
			int(entry.get("ac_bonus", 2)),
			"есть" if shield_trained else "нет",
			"" if shield_trained else " — бонус КД не действует"
		]
	return ""


func _use_selected() -> void:
	var item_id: String = str(_selected_entry.get("id", ""))
	if item_id.is_empty():
		return
	item_use_requested.emit(item_id)


func _equip_selected() -> void:
	var state: Node = _game_state()
	var character: PlayerCharacter = _player_character(state)
	var item_id: String = str(_selected_entry.get("id", ""))
	if item_id.is_empty() or character == null:
		return
	if _class_data.equip_item(character, item_id):
		_refresh()


func _show_unavailable_state() -> void:
	var error_label := Label.new()
	error_label.text = "Игровое состояние инвентаря недоступно."
	error_label.add_theme_font_size_override("font_size", 20)
	_item_list.add_child(error_label)
	_details_label.text = "Закройте окно и повторите попытку после загрузки игрового состояния."
	_use_button.hide()
	_equip_button.hide()


func _game_state() -> Node:
	return get_tree().root.get_node_or_null("GameState") if is_inside_tree() else null


func _player_character(state: Node) -> PlayerCharacter:
	if state == null:
		return null
	var value: Variant = state.get("player_character")
	return value as PlayerCharacter if value is PlayerCharacter else null


func _clear_container(container: Container) -> void:
	for child: Node in container.get_children():
		child.queue_free()
