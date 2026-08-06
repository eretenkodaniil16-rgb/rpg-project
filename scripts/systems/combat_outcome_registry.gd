extends Node

signal outcome_reported(outcome_id: StringName, scene_instance_id: int, encounter_id: String, context: Dictionary)
signal outcome_consumed(outcome_id: StringName, scene_instance_id: int)

const OUTCOME_VICTORY: StringName = &"victory"
const OUTCOME_ESCAPE: StringName = &"escape"
const OUTCOME_DEFEAT: StringName = &"defeat"
const OUTCOME_SCRIPTED_END: StringName = &"scripted_end"
const SUPPORTED_OUTCOMES: Array[StringName] = [
	OUTCOME_VICTORY,
	OUTCOME_ESCAPE,
	OUTCOME_DEFEAT,
	OUTCOME_SCRIPTED_END,
]

var _pending_by_scene: Dictionary = {}
var _sequence: int = 0


func report_outcome(
	outcome_id: StringName,
	scene_instance_id: int = 0,
	encounter_id: String = "",
	context: Dictionary = {}
) -> bool:
	if outcome_id not in SUPPORTED_OUTCOMES:
		push_warning("Unsupported combat outcome: %s" % String(outcome_id))
		return false
	var resolved_scene_id: int = scene_instance_id
	if resolved_scene_id <= 0:
		var current_scene: Node = get_tree().current_scene
		resolved_scene_id = int(current_scene.get_instance_id()) if current_scene != null else 0
	if resolved_scene_id <= 0:
		push_warning("Combat outcome requires a valid scene instance id.")
		return false
	_sequence += 1
	_pending_by_scene[resolved_scene_id] = {
		"outcome_id": outcome_id,
		"scene_instance_id": resolved_scene_id,
		"encounter_id": encounter_id,
		"context": context.duplicate(true),
		"sequence": _sequence,
	}
	outcome_reported.emit(outcome_id, resolved_scene_id, encounter_id, context.duplicate(true))
	return true


func consume_outcome(scene_instance_id: int) -> Dictionary:
	var value: Variant = _pending_by_scene.get(scene_instance_id, {})
	if not value is Dictionary:
		return {}
	var result: Dictionary = (value as Dictionary).duplicate(true)
	_pending_by_scene.erase(scene_instance_id)
	outcome_consumed.emit(
		StringName(str(result.get("outcome_id", ""))),
		scene_instance_id
	)
	return result


func peek_outcome(scene_instance_id: int) -> Dictionary:
	var value: Variant = _pending_by_scene.get(scene_instance_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func clear_scene(scene_instance_id: int) -> void:
	_pending_by_scene.erase(scene_instance_id)


func clear_all() -> void:
	_pending_by_scene.clear()


func is_supported_outcome(outcome_id: StringName) -> bool:
	return outcome_id in SUPPORTED_OUTCOMES
