class_name EncounterMusicPhaseSystem
extends RefCounted

const DATA_PATH: String = "res://data/audio/encounter_music_phase_events.json"
const SCHEMA_VERSION: int = 1

var _catalog: Dictionary = {}


func _init() -> void:
	_load_catalog()


func evaluate_event(
	encounter_id: String,
	event_id: String,
	context: Dictionary,
	current_profile: StringName = &"standard"
) -> Dictionary:
	if encounter_id.is_empty() or event_id.is_empty():
		return _not_triggered("missing_context")
	if current_profile == &"climax" or current_profile == &"scripted":
		return _not_triggered("profile_already_controls_music")
	var phases: Array[Dictionary] = _phase_definitions(encounter_id)
	for phase: Dictionary in phases:
		if str(phase.get("event_id", "")) != event_id:
			continue
		if not _matches_context(phase, context):
			continue
		return {
			"triggered": true,
			"encounter_id": encounter_id,
			"phase_id": str(phase.get("phase_id", "")),
			"profile_id": StringName(str(phase.get("profile_id", "climax"))),
			"trigger_id": StringName(str(phase.get("trigger_id", "dangerous_ability"))),
			"source_id": str(phase.get("source_id", context.get("actor_id", ""))),
			"message": str(phase.get("message", ""))
		}
	return _not_triggered("no_matching_phase")


func get_phase_definitions(encounter_id: String) -> Array[Dictionary]:
	return _phase_definitions(encounter_id)


func _matches_context(phase: Dictionary, context: Dictionary) -> bool:
	var required_actor_id: String = str(phase.get("source_actor_id", ""))
	if not required_actor_id.is_empty() and str(context.get("actor_id", "")) != required_actor_id:
		return false
	var minimum_round: int = maxi(int(phase.get("minimum_round", 1)), 1)
	if int(context.get("round_number", 0)) < minimum_round:
		return false
	var minimum_spell_level: int = maxi(int(phase.get("minimum_spell_level", 0)), 0)
	if int(context.get("spell_level", 0)) < minimum_spell_level:
		return false
	var allowed_spell_ids: Array[String] = []
	var spell_ids_value: Variant = phase.get("spell_ids", [])
	if spell_ids_value is Array:
		for value: Variant in spell_ids_value:
			allowed_spell_ids.append(str(value))
	if not allowed_spell_ids.is_empty() and not allowed_spell_ids.has(str(context.get("spell_id", ""))):
		return false
	return true


func _phase_definitions(encounter_id: String) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	var encounters_value: Variant = _catalog.get("encounters", {})
	if not encounters_value is Dictionary:
		return result
	var definition_value: Variant = (encounters_value as Dictionary).get(encounter_id, {})
	if not definition_value is Dictionary:
		return result
	var phases_value: Variant = (definition_value as Dictionary).get("phases", [])
	if not phases_value is Array:
		return result
	for value: Variant in phases_value:
		if value is Dictionary:
			result.append((value as Dictionary).duplicate(true))
	return result


func _load_catalog() -> void:
	_catalog.clear()
	if not FileAccess.file_exists(DATA_PATH):
		push_error("Каталог музыкальных фаз столкновений не найден: %s" % DATA_PATH)
		return
	var file: FileAccess = FileAccess.open(DATA_PATH, FileAccess.READ)
	if file == null:
		push_error("Не удалось открыть каталог музыкальных фаз: %s" % DATA_PATH)
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		push_error("Каталог музыкальных фаз имеет неверный формат.")
		return
	if int((parsed as Dictionary).get("schema_version", 0)) != SCHEMA_VERSION:
		push_error("Неподдерживаемая версия каталога музыкальных фаз.")
		return
	_catalog = (parsed as Dictionary).duplicate(true)


static func _not_triggered(reason: String) -> Dictionary:
	return {"triggered": false, "reason": reason}
