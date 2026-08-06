extends RefCounted

const PROFILE_STANDARD: StringName = &"standard"
const PROFILE_CLIMAX: StringName = &"climax"
const PROFILE_SCRIPTED: StringName = &"scripted"

var _scene_instance_id: int = 0
var _eligible: bool = false
var _combat_active: bool = false
var _applied_profile: StringName = PROFILE_STANDARD
var _pending_profile: StringName = &""


func sample(
	scene_instance_id: int,
	eligible: bool,
	combat_active: bool,
	desired_profile: StringName
) -> void:
	var normalized_desired: StringName = _normalize(desired_profile)
	if scene_instance_id != _scene_instance_id:
		_scene_instance_id = scene_instance_id
		_eligible = eligible
		_combat_active = combat_active
		_applied_profile = PROFILE_STANDARD
		_pending_profile = &""
		if eligible and combat_active and normalized_desired != PROFILE_STANDARD:
			_pending_profile = normalized_desired
		return
	if not eligible:
		if _applied_profile != PROFILE_STANDARD:
			_pending_profile = PROFILE_STANDARD
		_eligible = false
		_combat_active = false
		return
	if not combat_active:
		if _combat_active and _applied_profile != PROFILE_STANDARD:
			_pending_profile = PROFILE_STANDARD
		_combat_active = false
		_eligible = true
		return
	_eligible = true
	_combat_active = true
	if normalized_desired != _applied_profile:
		_pending_profile = normalized_desired


func has_pending() -> bool:
	return not String(_pending_profile).is_empty()


func consume_pending() -> StringName:
	var result: StringName = _pending_profile
	_pending_profile = &""
	return result


func mark_applied(profile_id: StringName) -> void:
	_applied_profile = _normalize(profile_id)


func get_applied_profile() -> StringName:
	return _applied_profile


func reset() -> void:
	_scene_instance_id = 0
	_eligible = false
	_combat_active = false
	_applied_profile = PROFILE_STANDARD
	_pending_profile = &""


func _normalize(profile_id: StringName) -> StringName:
	if profile_id in [PROFILE_STANDARD, PROFILE_CLIMAX, PROFILE_SCRIPTED]:
		return profile_id
	return PROFILE_STANDARD
