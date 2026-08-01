class_name ThrowablePropSystem
extends RefCounted

const DATA_PATH: String = "res://data/world/throwable_props.json"
const REGISTRY_FLAG: String = "guard_post_prop_registry_v1"
const SCHEMA_VERSION: int = 1
const STATE_WORLD: String = "world"
const STATE_HELD: String = "held"
const STATE_BROKEN: String = "broken"

var _definitions: Dictionary = {}


func _init() -> void:
	_load_definitions()


func get_definition(prop_type_id: String) -> Dictionary:
	var value: Variant = _definitions.get(prop_type_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func has_definition(prop_type_id: String) -> bool:
	return not get_definition(prop_type_id).is_empty()


func make_registry(initial_props: Array[Dictionary]) -> Dictionary:
	var props: Dictionary = {}
	for initial: Dictionary in initial_props:
		var prop_id: String = str(initial.get("prop_id", ""))
		var prop_type_id: String = str(initial.get("prop_type_id", ""))
		var position_value: Variant = initial.get("position", Vector2.ZERO)
		if prop_id.is_empty() or not has_definition(prop_type_id):
			continue
		props[prop_id] = {
			"prop_id": prop_id,
			"prop_type_id": prop_type_id,
			"state": STATE_WORLD,
			"position": vector_to_value(position_value as Vector2 if position_value is Vector2 else Vector2.ZERO)
		}
	return {
		"schema_version": SCHEMA_VERSION,
		"held_prop_id": "",
		"props": props
	}


func normalize_registry(value: Variant, initial_props: Array[Dictionary]) -> Dictionary:
	var fallback: Dictionary = make_registry(initial_props)
	if not value is Dictionary:
		return fallback
	var registry: Dictionary = (value as Dictionary).duplicate(true)
	registry["schema_version"] = SCHEMA_VERSION
	var props_value: Variant = registry.get("props", {})
	var props: Dictionary = props_value as Dictionary if props_value is Dictionary else {}
	var fallback_props: Dictionary = fallback.get("props", {}) as Dictionary
	for prop_id_value: Variant in fallback_props.keys():
		var prop_id: String = str(prop_id_value)
		if not props.has(prop_id) or not props[prop_id] is Dictionary:
			props[prop_id] = (fallback_props[prop_id] as Dictionary).duplicate(true)
			continue
		var record: Dictionary = (props[prop_id] as Dictionary).duplicate(true)
		record["prop_id"] = prop_id
		var fallback_record: Dictionary = fallback_props[prop_id] as Dictionary
		var prop_type_id: String = str(record.get("prop_type_id", fallback_record.get("prop_type_id", "")))
		if not has_definition(prop_type_id):
			prop_type_id = str(fallback_record.get("prop_type_id", ""))
		record["prop_type_id"] = prop_type_id
		var state: String = str(record.get("state", STATE_WORLD))
		if state not in [STATE_WORLD, STATE_HELD, STATE_BROKEN]:
			state = STATE_WORLD
		record["state"] = state
		if not record.get("position", null) is Array:
			record["position"] = fallback_record.get("position", [0.0, 0.0])
		props[prop_id] = record
	registry["props"] = props
	var held_prop_id: String = str(registry.get("held_prop_id", ""))
	if not held_prop_id.is_empty():
		var held_value: Variant = props.get(held_prop_id, {})
		if not held_value is Dictionary or str((held_value as Dictionary).get("state", "")) != STATE_HELD:
			held_prop_id = ""
	registry["held_prop_id"] = held_prop_id
	return registry


func pickup(registry: Dictionary, prop_id: String) -> Dictionary:
	var result: Dictionary = registry.duplicate(true)
	if not str(result.get("held_prop_id", "")).is_empty():
		return _failure("Герой уже держит другой предмет.", "hands_occupied", result)
	var props: Dictionary = result.get("props", {}) as Dictionary
	var value: Variant = props.get(prop_id, {})
	if not value is Dictionary:
		return _failure("Предмет не найден.", "missing_prop", result)
	var record: Dictionary = (value as Dictionary).duplicate(true)
	if str(record.get("state", "")) != STATE_WORLD:
		return _failure("Этот предмет нельзя поднять.", "prop_unavailable", result)
	record["state"] = STATE_HELD
	props[prop_id] = record
	result["props"] = props
	result["held_prop_id"] = prop_id
	return {"success": true, "registry": result, "record": record.duplicate(true)}


func throw_held(registry: Dictionary, landing_position: Vector2) -> Dictionary:
	var result: Dictionary = registry.duplicate(true)
	var prop_id: String = str(result.get("held_prop_id", ""))
	if prop_id.is_empty():
		return _failure("В руках нет метаемого предмета.", "nothing_held", result)
	var props: Dictionary = result.get("props", {}) as Dictionary
	var value: Variant = props.get(prop_id, {})
	if not value is Dictionary:
		return _failure("Состояние переносимого предмета повреждено.", "missing_held_prop", result)
	var record: Dictionary = (value as Dictionary).duplicate(true)
	var definition: Dictionary = get_definition(str(record.get("prop_type_id", "")))
	var breaks_on_impact: bool = bool(definition.get("breaks_on_impact", false))
	record["state"] = STATE_BROKEN if breaks_on_impact else STATE_WORLD
	record["position"] = vector_to_value(landing_position)
	props[prop_id] = record
	result["props"] = props
	result["held_prop_id"] = ""
	return {
		"success": true,
		"registry": result,
		"record": record.duplicate(true),
		"definition": definition,
		"prop_id": prop_id,
		"broken": breaks_on_impact
	}


func get_held_record(registry: Dictionary) -> Dictionary:
	var prop_id: String = str(registry.get("held_prop_id", ""))
	var props_value: Variant = registry.get("props", {})
	if prop_id.is_empty() or not props_value is Dictionary:
		return {}
	var value: Variant = (props_value as Dictionary).get(prop_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func get_world_records(registry: Dictionary) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	var props_value: Variant = registry.get("props", {})
	if not props_value is Dictionary:
		return result
	for value: Variant in (props_value as Dictionary).values():
		if value is Dictionary and str((value as Dictionary).get("state", "")) == STATE_WORLD:
			result.append((value as Dictionary).duplicate(true))
	result.sort_custom(func(left: Dictionary, right: Dictionary) -> bool: return str(left.get("prop_id", "")) < str(right.get("prop_id", "")))
	return result


func vector_to_value(value: Vector2) -> Array[float]:
	return [value.x, value.y]


func vector_from_value(value: Variant) -> Vector2:
	if value is Array and (value as Array).size() >= 2:
		return Vector2(float((value as Array)[0]), float((value as Array)[1]))
	return Vector2.ZERO


func _load_definitions() -> void:
	_definitions.clear()
	if not FileAccess.file_exists(DATA_PATH):
		push_error("Каталог метаемых предметов не найден: %s" % DATA_PATH)
		return
	var file: FileAccess = FileAccess.open(DATA_PATH, FileAccess.READ)
	if file == null:
		push_error("Не удалось открыть каталог метаемых предметов: %s" % DATA_PATH)
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		push_error("Каталог метаемых предметов содержит некорректный JSON.")
		return
	var props_value: Variant = (parsed as Dictionary).get("props", {})
	if props_value is Dictionary:
		_definitions = (props_value as Dictionary).duplicate(true)


func _failure(message: String, code: String, registry: Dictionary) -> Dictionary:
	return {"success": false, "code": code, "message": message, "registry": registry.duplicate(true)}
