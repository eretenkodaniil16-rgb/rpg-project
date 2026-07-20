class_name CharacterHubInventory
extends CharacterHub

var _selected_inventory_entry: Dictionary = {}
var _inventory_details: Label
var _inventory_equip: Button

func _refresh_inventory() -> void:
	_clear(_inventory_box)
	_selected_inventory_entry.clear()
	var entries: Array = GameState.get_inventory_entries()
	if entries.is_empty():
		_inventory_box.add_child(_label("Инвентарь пуст.", 19))
		return
	entries.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return str(a.get("type", "")) < str(b.get("type", "")))
	for value: Variant in entries:
		if not value is Dictionary:
			continue
		var entry: Dictionary = value as Dictionary
		var equipped: bool = _class_data.is_equipped(_hero, str(entry.get("id", "")))
		var button := Button.new()
		button.text = "%s%s ×%d" % ["★ " if equipped else "", str(entry.get("name", "Предмет")), int(entry.get("quantity", 0))]
		button.custom_minimum_size = Vector2(0.0, 52.0)
		button.alignment = HORIZONTAL_ALIGNMENT_LEFT
		button.pressed.connect(_select_inventory_entry.bind(entry))
		_inventory_box.add_child(button)
	_inventory_box.add_child(HSeparator.new())
	_inventory_details = _label("Выберите предмет.", 18)
	_inventory_box.add_child(_inventory_details)
	_inventory_equip = Button.new()
	_inventory_equip.text = "ЭКИПИРОВАТЬ"
	_inventory_equip.custom_minimum_size = Vector2(0.0, 54.0)
	_inventory_equip.pressed.connect(_equip_inventory_entry)
	_inventory_equip.hide()
	_inventory_box.add_child(_inventory_equip)
	if entries[0] is Dictionary:
		_select_inventory_entry(entries[0] as Dictionary)

func _select_inventory_entry(entry: Dictionary) -> void:
	_selected_inventory_entry = entry.duplicate(true)
	var item_type: String = str(entry.get("type", "misc"))
	var item_id: String = str(entry.get("id", ""))
	var equipped: bool = _class_data.is_equipped(_hero, item_id)
	var state_text: String = "\nСостояние: ЭКИПИРОВАНО" if equipped else ""
	_inventory_details.text = "%s\n\nКоличество: %d%s%s\n\n%s" % [str(entry.get("name", "Предмет")), int(entry.get("quantity", 0)), state_text, _inventory_stats(entry), str(entry.get("description", "Описание отсутствует."))]
	_inventory_equip.visible = item_type in ["weapon", "armor", "shield"]
	_inventory_equip.disabled = equipped
	_inventory_equip.text = "ЭКИПИРОВАНО" if equipped else "ЭКИПИРОВАТЬ"

func _equip_inventory_entry() -> void:
	var item_id: String = str(_selected_inventory_entry.get("id", ""))
	if item_id.is_empty():
		return
	if _class_data.equip_item(_hero, item_id):
		_refresh_all()

func _inventory_stats(entry: Dictionary) -> String:
	match str(entry.get("type", "")):
		"weapon":
			var dice: Array = entry.get("damage_dice", [1, 1]) as Array
			return "\nУрон: %dd%d %s" % [int(dice[0]), int(dice[1]), str(entry.get("damage_type", "физический"))]
		"armor":
			return "\nБазовый КД: %d" % int(entry.get("base_ac", 10))
		"shield":
			return "\nБонус КД: +%d" % int(entry.get("ac_bonus", 2))
	return ""
