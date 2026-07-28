class_name EncounterSystem
extends RefCounted

const DATA_PATH: String = "res://data/encounters/encounters.json"
const REGISTRY_FLAG: String = "encounter_registry_v1"
const SCHEMA_VERSION: int = 1

const STATUS_AVAILABLE: String = "available"
const STATUS_ACTIVE: String = "active"
const STATUS_RESOLVED: String = "resolved"
const STATUS_REWARDED: String = "rewarded"
const STATUS_FAILED: String = "failed"
const STATUS_ABANDONED: String = "abandoned"

var _definitions: Dictionary = {}


func _init() -> void:
	_load_definitions()


func ensure_state(state: Node) -> bool:
	if state == null or not state.has_method("get_flag") or not state.has_method("set_flag"):
		return false
	var current_value: Variant = state.call("get_flag", REGISTRY_FLAG, {})
	var registry: Dictionary = current_value as Dictionary if current_value is Dictionary else {}
	var changed: bool = false
	if int(registry.get("schema_version", 0)) != SCHEMA_VERSION:
		registry["schema_version"] = SCHEMA_VERSION
		changed = true
	var encounters_value: Variant = registry.get("encounters", {})
	if not encounters_value is Dictionary:
		registry["encounters"] = {}
		changed = true
	if changed or not current_value is Dictionary:
		state.call("set_flag", REGISTRY_FLAG, registry)
	return changed


func get_definition(encounter_id: String) -> Dictionary:
	var value: Variant = _definitions.get(encounter_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func get_encounter_state(state: Node, encounter_id: String) -> Dictionary:
	var registry: Dictionary = _registry(state)
	var encounters: Dictionary = registry.get("encounters", {}) as Dictionary
	var value: Variant = encounters.get(encounter_id, {})
	if value is Dictionary:
		return (value as Dictionary).duplicate(true)
	return _new_record(encounter_id)


func get_status(state: Node, encounter_id: String) -> String:
	return str(get_encounter_state(state, encounter_id).get("status", STATUS_AVAILABLE))


func is_terminal(state: Node, encounter_id: String) -> bool:
	return get_status(state, encounter_id) in [STATUS_RESOLVED, STATUS_REWARDED]


func begin_encounter(state: Node, encounter_id: String, context: Dictionary = {}) -> Dictionary:
	var definition: Dictionary = get_definition(encounter_id)
	if definition.is_empty():
		return _failure("Неизвестное столкновение: %s." % encounter_id, "unknown_encounter")
	var registry: Dictionary = _registry(state)
	var encounters: Dictionary = registry.get("encounters", {}) as Dictionary
	var record: Dictionary = _record_from(encounters.get(encounter_id, {}), encounter_id)
	var status: String = str(record.get("status", STATUS_AVAILABLE))
	var repeatable: bool = bool(definition.get("repeatable", false))
	if status in [STATUS_RESOLVED, STATUS_REWARDED] and not repeatable:
		return {
			"success": false,
			"duplicate": true,
			"code": "already_resolved",
			"encounter_id": encounter_id,
			"state": record.duplicate(true),
			"message": "Столкновение уже разрешено."
		}
	if status == STATUS_ACTIVE:
		return {
			"success": true,
			"already_active": true,
			"encounter_id": encounter_id,
			"state": record.duplicate(true),
			"definition": definition
		}
	if repeatable and status in [STATUS_RESOLVED, STATUS_REWARDED]:
		record = _new_record(encounter_id)
	record["status"] = STATUS_ACTIVE
	record["attempt_count"] = int(record.get("attempt_count", 0)) + 1
	record["resolution_id"] = ""
	record["resolution_type"] = ""
	record["reward_status"] = "pending"
	record["context"] = context.duplicate(true)
	_append_history(record, "started", context)
	encounters[encounter_id] = record
	registry["encounters"] = encounters
	_store_registry(state, registry)
	return {
		"success": true,
		"encounter_id": encounter_id,
		"state": record.duplicate(true),
		"definition": definition
	}


func resolve_encounter(
	state: Node,
	encounter_id: String,
	resolution_id: String,
	context: Dictionary = {}
) -> Dictionary:
	var definition: Dictionary = get_definition(encounter_id)
	if definition.is_empty():
		return _failure("Неизвестное столкновение: %s." % encounter_id, "unknown_encounter")
	var resolutions_value: Variant = definition.get("resolutions", {})
	var resolutions: Dictionary = resolutions_value as Dictionary if resolutions_value is Dictionary else {}
	var outcome_value: Variant = resolutions.get(resolution_id, {})
	if not outcome_value is Dictionary:
		return _failure(
			"Способ разрешения %s не определён для столкновения %s." % [resolution_id, encounter_id],
			"unknown_resolution"
		)
	var registry: Dictionary = _registry(state)
	var encounters: Dictionary = registry.get("encounters", {}) as Dictionary
	var record: Dictionary = _record_from(encounters.get(encounter_id, {}), encounter_id)
	var status: String = str(record.get("status", STATUS_AVAILABLE))
	var repeatable: bool = bool(definition.get("repeatable", false))
	if status in [STATUS_RESOLVED, STATUS_REWARDED] and not repeatable:
		return {
			"success": false,
			"duplicate": true,
			"code": "already_resolved",
			"encounter_id": encounter_id,
			"resolution_id": str(record.get("resolution_id", "")),
			"state": record.duplicate(true),
			"message": "Столкновение уже разрешено."
		}
	if status != STATUS_ACTIVE:
		if repeatable and status in [STATUS_RESOLVED, STATUS_REWARDED]:
			record = _new_record(encounter_id)
		record["attempt_count"] = int(record.get("attempt_count", 0)) + 1
		_append_history(record, "started_implicitly", context)
	record["status"] = STATUS_RESOLVED
	record["resolution_id"] = resolution_id
	record["resolution_type"] = str((outcome_value as Dictionary).get("type", "unknown"))
	record["resolution_context"] = context.duplicate(true)
	record["reward_status"] = "pending"
	_append_history(record, "resolved:%s" % resolution_id, context)
	encounters[encounter_id] = record
	registry["encounters"] = encounters
	_store_registry(state, registry)
	return {
		"success": true,
		"encounter_id": encounter_id,
		"resolution_id": resolution_id,
		"state": record.duplicate(true),
		"definition": definition,
		"outcome": (outcome_value as Dictionary).duplicate(true),
		"reward_id": str(definition.get("reward_id", ""))
	}


func mark_rewarded(state: Node, encounter_id: String, reward_status: String, reward_result: Dictionary = {}) -> Dictionary:
	var registry: Dictionary = _registry(state)
	var encounters: Dictionary = registry.get("encounters", {}) as Dictionary
	if not encounters.has(encounter_id):
		return _failure("Состояние столкновения не найдено.", "missing_state")
	var record: Dictionary = _record_from(encounters.get(encounter_id, {}), encounter_id)
	if str(record.get("status", "")) not in [STATUS_RESOLVED, STATUS_REWARDED]:
		return _failure("Награда может быть завершена только после разрешения столкновения.", "invalid_status")
	record["status"] = STATUS_REWARDED
	record["reward_status"] = reward_status
	record["reward_result"] = reward_result.duplicate(true)
	_append_history(record, "rewarded:%s" % reward_status, {})
	encounters[encounter_id] = record
	registry["encounters"] = encounters
	_store_registry(state, registry)
	return {"success": true, "encounter_id": encounter_id, "state": record.duplicate(true)}


func fail_encounter(state: Node, encounter_id: String, reason_id: String = "failed", context: Dictionary = {}) -> Dictionary:
	return _close_without_resolution(state, encounter_id, STATUS_FAILED, reason_id, context)


func abandon_encounter(state: Node, encounter_id: String, reason_id: String = "abandoned", context: Dictionary = {}) -> Dictionary:
	return _close_without_resolution(state, encounter_id, STATUS_ABANDONED, reason_id, context)


func get_active_encounter_ids(state: Node) -> Array[String]:
	var result: Array[String] = []
	var registry: Dictionary = _registry(state)
	var encounters: Dictionary = registry.get("encounters", {}) as Dictionary
	for encounter_id_value: Variant in encounters.keys():
		var encounter_id: String = str(encounter_id_value)
		var value: Variant = encounters.get(encounter_id, {})
		if value is Dictionary and str((value as Dictionary).get("status", "")) == STATUS_ACTIVE:
			result.append(encounter_id)
	return result


func get_combat_resolution_id(encounter_id: String) -> String:
	return str(get_definition(encounter_id).get("combat_resolution_id", ""))


func _close_without_resolution(
	state: Node,
	encounter_id: String,
	status: String,
	reason_id: String,
	context: Dictionary
) -> Dictionary:
	if get_definition(encounter_id).is_empty():
		return _failure("Неизвестное столкновение: %s." % encounter_id, "unknown_encounter")
	var registry: Dictionary = _registry(state)
	var encounters: Dictionary = registry.get("encounters", {}) as Dictionary
	var record: Dictionary = _record_from(encounters.get(encounter_id, {}), encounter_id)
	if str(record.get("status", "")) in [STATUS_RESOLVED, STATUS_REWARDED]:
		return {
			"success": false,
			"duplicate": true,
			"code": "already_resolved",
			"encounter_id": encounter_id,
			"state": record.duplicate(true)
		}
	record["status"] = status
	record["close_reason_id"] = reason_id
	record["close_context"] = context.duplicate(true)
	_append_history(record, "%s:%s" % [status, reason_id], context)
	encounters[encounter_id] = record
	registry["encounters"] = encounters
	_store_registry(state, registry)
	return {"success": true, "encounter_id": encounter_id, "state": record.duplicate(true)}


func _registry(state: Node) -> Dictionary:
	ensure_state(state)
	var value: Variant = state.call("get_flag", REGISTRY_FLAG, {}) if state != null and state.has_method("get_flag") else {}
	var registry: Dictionary = value as Dictionary if value is Dictionary else {}
	if not registry.has("encounters") or not registry["encounters"] is Dictionary:
		registry["encounters"] = {}
	return registry.duplicate(true)


func _store_registry(state: Node, registry: Dictionary) -> void:
	if state != null and state.has_method("set_flag"):
		state.call("set_flag", REGISTRY_FLAG, registry.duplicate(true))


func _record_from(value: Variant, encounter_id: String) -> Dictionary:
	return (value as Dictionary).duplicate(true) if value is Dictionary else _new_record(encounter_id)


func _new_record(encounter_id: String) -> Dictionary:
	return {
		"encounter_id": encounter_id,
		"status": STATUS_AVAILABLE,
		"attempt_count": 0,
		"resolution_id": "",
		"resolution_type": "",
		"reward_status": "not_started",
		"context": {},
		"history": []
	}


func _append_history(record: Dictionary, event_id: String, context: Dictionary) -> void:
	var history_value: Variant = record.get("history", [])
	var history: Array = history_value as Array if history_value is Array else []
	history.append({
		"sequence": history.size() + 1,
		"event_id": event_id,
		"context": context.duplicate(true)
	})
	record["history"] = history


func _load_definitions() -> void:
	_definitions.clear()
	if not FileAccess.file_exists(DATA_PATH):
		push_error("Каталог столкновений не найден: %s" % DATA_PATH)
		return
	var file: FileAccess = FileAccess.open(DATA_PATH, FileAccess.READ)
	if file == null:
		push_error("Не удалось открыть каталог столкновений: %s" % DATA_PATH)
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		push_error("Каталог столкновений имеет неверный формат: %s" % DATA_PATH)
		return
	var encounters_value: Variant = (parsed as Dictionary).get("encounters", {})
	if encounters_value is Dictionary:
		_definitions = (encounters_value as Dictionary).duplicate(true)


static func _failure(message: String, code: String) -> Dictionary:
	return {"success": false, "code": code, "message": message}
