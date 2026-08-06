class_name MusicCombatTransitionTracker
extends RefCounted

const DEFAULT_REQUIRED_INACTIVE_SAMPLES: int = 3

var _scene_instance_id: int = 0
var _initialized: bool = false
var _last_combat_active: bool = false
var _armed: bool = false
var _pending: bool = false
var _inactive_samples: int = 0
var _required_inactive_samples: int = DEFAULT_REQUIRED_INACTIVE_SAMPLES


func _init(required_inactive_samples: int = DEFAULT_REQUIRED_INACTIVE_SAMPLES) -> void:
	_required_inactive_samples = maxi(required_inactive_samples, 1)


func sample(scene_instance_id: int, eligible: bool, combat_active: bool) -> void:
	if not eligible or scene_instance_id <= 0:
		reset()
		return
	if not _initialized or scene_instance_id != _scene_instance_id:
		_scene_instance_id = scene_instance_id
		_initialized = true
		_last_combat_active = combat_active
		_armed = not combat_active
		_pending = false
		_inactive_samples = 0
		return

	if combat_active:
		if not _last_combat_active and _armed:
			_pending = true
			_armed = false
			_inactive_samples = 0
	else:
		_pending = false
		_inactive_samples += 1
		if _inactive_samples >= _required_inactive_samples:
			_armed = true
	_last_combat_active = combat_active


func is_pending() -> bool:
	return _pending


func is_armed() -> bool:
	return _armed


func mark_emitted() -> void:
	_pending = false


func reset() -> void:
	_scene_instance_id = 0
	_initialized = false
	_last_combat_active = false
	_armed = false
	_pending = false
	_inactive_samples = 0
