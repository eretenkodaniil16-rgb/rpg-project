extends Node

signal profile_changed(
	scene_instance_id: int,
	encounter_id: String,
	profile_id: StringName,
	trigger_id: StringName,
	source_id: String
)

const DATA_PATH: String = "res://data/audio/combat_music_profiles.json"
const STATE_FLAG: String = "combat_music_profile_registry_v1"
const SCHEMA_VERSION: int = 1

const PROFILE_STANDARD: StringName = &"standard"
const PROFILE_CLIMAX: StringName = &"climax"
const PROFILE_SCRIPTED: StringName = &"scripted"

var _catalog: Dictionary = {}
var _records_by_scene: Dictionary = {}


func _ready() -> void:
	_load_catalog()


func begin_combat(scene_instance_id: int, encounter_id: String) -> StringName:
	if scene_instance_id <= 0:
		return PROFILE_STANDARD
	var existing_value: Variant = _records_by_scene.get(scene_instance_id, {})
	if existing_value is Dictionary:
		var existing: Dictionary = existing_value as Dictionary
		if str(existing.get("encounter_id", "")) == encounter_id:
			return StringName(str(existing.get("profile_id", PROFILE_STANDARD)))
	var definition: Dictionary = _definition(encounter_id)
	var allowed_profiles: Array[StringName] = _allowed_profiles(definition)
	var initial_profile: StringName = _normalize_profile(
		StringName(str(definition.get("initial_profile", _default_profile())))
	)
	if not allowed_profiles.has(initial_profile):
		initial_profile = PROFILE_STANDARD
	var persisted: Dictionary = _persisted_record(encounter_id)
	var restored_profile: StringName = StringName(str(persisted.get("profile_id", initial_profile)))
	if not allowed_profiles.has(restored_profile):
		restored_profile = initial_profile
	var record: Dictionary = {
		"scene_instance_id": scene_instance_id,
		"encounter_id": encounter_id,
		"profile_id": restored_profile,
		"allowed_profiles": allowed_profiles,
		"sequence": int(persisted.get("sequence", 0)),
		"trigger_id": StringName(str(persisted.get("trigger_id", ""))),
		"source_id": str(persisted.get("source_id", ""))
	}
	_records_by_scene[scene_instance_id] = record
	return restored_profile


func set_profile(
	scene_instance_id: int,
	profile_id: StringName,
	trigger_id: StringName = &"",
	source_id: String = ""
) -> bool:
	if scene_instance_id <= 0:
		return false
	var normalized: StringName = _normalize_profile(profile_id)
	if String(normalized).is_empty():
		return false
	if not _records_by_scene.has(scene_instance_id):
		begin_combat(scene_instance_id, "")
	var record_value: Variant = _records_by_scene.get(scene_instance_id, {})
	if not record_value is Dictionary:
		return false
	var record: Dictionary = record_value as Dictionary
	var allowed_value: Variant = record.get("allowed_profiles", [])
	var allowed_profiles: Array[StringName] = []
	if allowed_value is Array:
		for value: Variant in allowed_value:
			allowed_profiles.append(StringName(str(value)))
	if not allowed_profiles.has(normalized):
		return false
	var current_profile: StringName = StringName(str(record.get("profile_id", PROFILE_STANDARD)))
	if current_profile == normalized:
		return true
	record["profile_id"] = normalized
	record["sequence"] = int(record.get("sequence", 0)) + 1
	record["trigger_id"] = trigger_id
	record["source_id"] = source_id
	_records_by_scene[scene_instance_id] = record
	_store_persisted_record(record)
	profile_changed.emit(
		scene_instance_id,
		str(record.get("encounter_id", "")),
		normalized,
		trigger_id,
		source_id
	)
	return true


func request_climax(
	scene_instance_id: int,
	trigger_id: StringName,
	source_id: String = ""
) -> bool:
	if String(trigger_id).is_empty():
		return false
	return set_profile(scene_instance_id, PROFILE_CLIMAX, trigger_id, source_id)


func get_profile(scene_instance_id: int, encounter_id: String = "") -> StringName:
	if not _records_by_scene.has(scene_instance_id):
		return begin_combat(scene_instance_id, encounter_id)
	var record: Dictionary = _records_by_scene.get(scene_instance_id, {}) as Dictionary
	if not encounter_id.is_empty() and str(record.get("encounter_id", "")) != encounter_id:
		return begin_combat(scene_instance_id, encounter_id)
	return StringName(str(record.get("profile_id", PROFILE_STANDARD)))


func get_record(scene_instance_id: int) -> Dictionary:
	var value: Variant = _records_by_scene.get(scene_instance_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func end_combat(scene_instance_id: int, clear_persisted: bool = true) -> void:
	var record: Dictionary = get_record(scene_instance_id)
	_records_by_scene.erase(scene_instance_id)
	if clear_persisted:
		_clear_persisted_record(str(record.get("encounter_id", "")))


func forget_runtime_for_testing() -> void:
	_records_by_scene.clear()


func clear_all_for_testing() -> void:
	_records_by_scene.clear()
	var state: Node = _state()
	if state != null and state.has_method("set_flag"):
		state.call("set_flag", STATE_FLAG, {
			"schema_version": SCHEMA_VERSION,
			"encounters": {}
		})


func _normalize_profile(profile_id: StringName) -> StringName:
	if profile_id in [PROFILE_STANDARD, PROFILE_CLIMAX, PROFILE_SCRIPTED]:
		return profile_id
	return &""


func _default_profile() -> String:
	return str(_catalog.get("default_profile", String(PROFILE_STANDARD)))


func _definition(encounter_id: String) -> Dictionary:
	var encounters_value: Variant = _catalog.get("encounters", {})
	if encounters_value is Dictionary:
		var definition_value: Variant = (encounters_value as Dictionary).get(encounter_id, {})
		if definition_value is Dictionary:
			return (definition_value as Dictionary).duplicate(true)
	return {
		"initial_profile": _default_profile(),
		"allowed_profiles": [
			String(PROFILE_STANDARD),
			String(PROFILE_CLIMAX),
			String(PROFILE_SCRIPTED)
		]
	}


func _allowed_profiles(definition: Dictionary) -> Array[StringName]:
	var result: Array[StringName] = []
	var values: Variant = definition.get("allowed_profiles", [])
	if values is Array:
		for value: Variant in values:
			var profile: StringName = _normalize_profile(StringName(str(value)))
			if not String(profile).is_empty() and not result.has(profile):
				result.append(profile)
	if result.is_empty():
		result.append(PROFILE_STANDARD)
	return result


func _load_catalog() -> void:
	_catalog.clear()
	if not FileAccess.file_exists(DATA_PATH):
		push_error("Каталог профилей боевой музыки не найден: %s" % DATA_PATH)
		return
	var file: FileAccess = FileAccess.open(DATA_PATH, FileAccess.READ)
	if file == null:
		push_error("Не удалось открыть каталог профилей боевой музыки: %s" % DATA_PATH)
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if parsed is Dictionary:
		_catalog = (parsed as Dictionary).duplicate(true)
	else:
		push_error("Каталог профилей боевой музыки имеет неверный формат.")


func _state() -> Node:
	return get_tree().root.get_node_or_null("GameState") if is_inside_tree() else null


func _registry() -> Dictionary:
	var state: Node = _state()
	if state == null or not state.has_method("get_flag"):
		return {"schema_version": SCHEMA_VERSION, "encounters": {}}
	var value: Variant = state.call("get_flag", STATE_FLAG, {})
	var result: Dictionary = value as Dictionary if value is Dictionary else {}
	if int(result.get("schema_version", 0)) != SCHEMA_VERSION:
		result = {"schema_version": SCHEMA_VERSION, "encounters": {}}
	if not (result.get("encounters", {}) is Dictionary):
		result["encounters"] = {}
	return result.duplicate(true)


func _persisted_record(encounter_id: String) -> Dictionary:
	if encounter_id.is_empty():
		return {}
	var encounters: Dictionary = _registry().get("encounters", {}) as Dictionary
	var value: Variant = encounters.get(encounter_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func _store_persisted_record(record: Dictionary) -> void:
	var encounter_id: String = str(record.get("encounter_id", ""))
	if encounter_id.is_empty():
		return
	var state: Node = _state()
	if state == null or not state.has_method("set_flag"):
		return
	var registry: Dictionary = _registry()
	var encounters: Dictionary = registry.get("encounters", {}) as Dictionary
	encounters[encounter_id] = {
		"profile_id": str(record.get("profile_id", PROFILE_STANDARD)),
		"sequence": int(record.get("sequence", 0)),
		"trigger_id": str(record.get("trigger_id", "")),
		"source_id": str(record.get("source_id", ""))
	}
	registry["encounters"] = encounters
	state.call("set_flag", STATE_FLAG, registry)


func _clear_persisted_record(encounter_id: String) -> void:
	if encounter_id.is_empty():
		return
	var state: Node = _state()
	if state == null or not state.has_method("set_flag"):
		return
	var registry: Dictionary = _registry()
	var encounters: Dictionary = registry.get("encounters", {}) as Dictionary
	encounters.erase(encounter_id)
	registry["encounters"] = encounters
	state.call("set_flag", STATE_FLAG, registry)
