class_name SpellcastingProgressionSystem
extends RefCounted

const DATA_PATH: String = "res://data/rules/spellcasting_progression.json"
const MIN_LEVEL: int = 1
const MAX_LEVEL: int = 20

var _data: Dictionary = {}


func _init() -> void:
	_data = _load_json(DATA_PATH)


func get_prepared_limit(class_id: String, class_level: int, fallback: int = 0) -> int:
	var class_data: Dictionary = _class_data(class_id)
	var prepared_value: Variant = class_data.get("prepared", [])
	if not prepared_value is Array or (prepared_value as Array).is_empty():
		return maxi(fallback, 0)
	var index: int = clampi(class_level, MIN_LEVEL, MAX_LEVEL) - 1
	var prepared: Array = prepared_value as Array
	if index >= prepared.size():
		return maxi(fallback, 0)
	return maxi(int(prepared[index]), 0)


func get_slot_maximums(class_id: String, class_level: int) -> Dictionary:
	var class_data: Dictionary = _class_data(class_id)
	if class_data.is_empty():
		return {}
	var level: int = clampi(class_level, MIN_LEVEL, MAX_LEVEL)
	if class_id == "warlock":
		var slot_level: int = get_pact_slot_level(class_id, level)
		var slot_count: int = _array_level_value(class_data.get("pact_slots", []), level)
		return {str(slot_level): slot_count} if slot_level > 0 and slot_count > 0 else {}
	var table_id: String = str(class_data.get("slot_table", ""))
	var tables_value: Variant = _data.get("slot_tables", {})
	if not tables_value is Dictionary:
		return {}
	var table_value: Variant = (tables_value as Dictionary).get(table_id, {})
	if not table_value is Dictionary:
		return {}
	var row_value: Variant = (table_value as Dictionary).get(str(level), {})
	return (row_value as Dictionary).duplicate(true) if row_value is Dictionary else {}


func get_pact_slot_level(class_id: String, class_level: int) -> int:
	if class_id != "warlock":
		return 0
	return _array_level_value(_class_data(class_id).get("pact_slot_level", []), class_level)


func uses_pact_magic(class_id: String) -> bool:
	return class_id == "warlock" and not _class_data(class_id).is_empty()


func _class_data(class_id: String) -> Dictionary:
	var classes_value: Variant = _data.get("classes", {})
	if not classes_value is Dictionary:
		return {}
	var value: Variant = (classes_value as Dictionary).get(class_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func _array_level_value(value: Variant, class_level: int) -> int:
	if not value is Array or (value as Array).is_empty():
		return 0
	var values: Array = value as Array
	var index: int = clampi(class_level, MIN_LEVEL, MAX_LEVEL) - 1
	return maxi(int(values[index]), 0) if index < values.size() else 0


func _load_json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		push_error("Файл прогрессии заклинаний не найден: %s" % path)
		return {}
	var file: FileAccess = FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {}
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	return parsed as Dictionary if parsed is Dictionary else {}
