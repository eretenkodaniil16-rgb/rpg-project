extends RefCounted

var _initialized: bool = false
var _scene_instance_id: int = 0
var _previous_combat_active: bool = false
var _last_encounter_id: String = ""
var _pending_transition: Dictionary = {}


func sample(
	scene_instance_id: int,
	eligible: bool,
	combat_active: bool,
	encounter_id: String = ""
) -> void:
	if not eligible or scene_instance_id <= 0:
		reset()
		return
	if not _initialized or _scene_instance_id != scene_instance_id:
		_initialized = true
		_scene_instance_id = scene_instance_id
		_previous_combat_active = combat_active
		_last_encounter_id = encounter_id if combat_active else ""
		_pending_transition.clear()
		return
	if combat_active and not encounter_id.is_empty():
		_last_encounter_id = encounter_id
	if _previous_combat_active and not combat_active:
		_pending_transition = {
			"scene_instance_id": _scene_instance_id,
			"encounter_id": _last_encounter_id,
		}
	_previous_combat_active = combat_active


func is_pending() -> bool:
	return not _pending_transition.is_empty()


func consume_transition() -> Dictionary:
	var result: Dictionary = _pending_transition.duplicate(true)
	_pending_transition.clear()
	_last_encounter_id = ""
	return result


func reset() -> void:
	_initialized = false
	_scene_instance_id = 0
	_previous_combat_active = false
	_last_encounter_id = ""
	_pending_transition.clear()
