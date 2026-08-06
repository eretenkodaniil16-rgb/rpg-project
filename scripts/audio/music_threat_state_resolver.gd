extends Node

signal tension_changed(active: bool)
signal threat_level_changed(level: int)
signal threat_source_changed(source_id: StringName, active: bool, intensity: int)

const STEALTH_ALERT_REGISTRY_FLAG: String = "stealth_alert_registry_v1"
const TENSION_CONTEXT_ID: StringName = &"world_tension"
const EXPLORATION_CONTEXT_ID: StringName = &"world_exploration"
const GAME_SCENE_PREFIX: String = "res://scenes/game/"
const DEFAULT_RELEASE_DELAY_SECONDS: float = 8.0
const DEFAULT_TENSION_FADE_SECONDS: float = 1.25
const DEFAULT_CALM_FADE_SECONDS: float = 2.0
const POLL_INTERVAL_SECONDS: float = 0.25
const MIN_INTENSITY: int = 1
const MAX_INTENSITY: int = 3

const STEALTH_STATE_INTENSITY: Dictionary = {
	"suspicious": 1,
	"investigating": 2,
	"searching": 2,
	"alerted": 3,
	"combat": 3
}

var _manual_sources: Dictionary = {}
var _registry_sources: Dictionary = {}
var _tension_applied: bool = false
var _last_effective_level: int = 0
var _release_delay_seconds: float = DEFAULT_RELEASE_DELAY_SECONDS
var _automatic_runtime_gate_enabled: bool = true
var _registry_polling_enabled: bool = true
var _release_timer: Timer
var _poll_timer: Timer


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_create_timers()
	call_deferred("_refresh_state")


func set_threat_source(source_id: StringName, active: bool, intensity: int = MIN_INTENSITY) -> bool:
	var key: String = String(source_id)
	if key.is_empty():
		push_warning("Music threat source_id must not be empty.")
		return false
	var safe_intensity: int = clampi(intensity, MIN_INTENSITY, MAX_INTENSITY)
	if active:
		_manual_sources[key] = safe_intensity
	else:
		_manual_sources.erase(key)
	threat_source_changed.emit(source_id, active, safe_intensity if active else 0)
	_refresh_state()
	return true


func clear_threat_source(source_id: StringName) -> void:
	set_threat_source(source_id, false)


func clear_all_threat_sources() -> void:
	var previous_ids: Array = _manual_sources.keys()
	_manual_sources.clear()
	for source_value: Variant in previous_ids:
		threat_source_changed.emit(StringName(str(source_value)), false, 0)
	_refresh_state()


func get_active_source_count() -> int:
	return _combined_sources().size()


func get_effective_threat_level() -> int:
	var level: int = 0
	for value: Variant in _combined_sources().values():
		level = maxi(level, int(value))
	return level


func is_tension_active() -> bool:
	return _tension_applied


func get_release_seconds_remaining() -> float:
	if _release_timer == null or _release_timer.is_stopped():
		return 0.0
	return _release_timer.time_left


func set_release_delay_seconds(seconds: float) -> void:
	_release_delay_seconds = maxf(seconds, 0.0)
	if _release_timer != null and not _release_timer.is_stopped():
		if _release_delay_seconds <= 0.0:
			_release_timer.stop()
			_finish_release()
		else:
			_release_timer.start(_release_delay_seconds)


func get_release_delay_seconds() -> float:
	return _release_delay_seconds


func set_automatic_runtime_gate_enabled(enabled: bool) -> void:
	_automatic_runtime_gate_enabled = enabled
	_refresh_state()


func set_registry_polling_enabled(enabled: bool) -> void:
	_registry_polling_enabled = enabled
	if not enabled:
		_registry_sources.clear()
	_refresh_state()


func refresh_now() -> void:
	_refresh_state()


func _create_timers() -> void:
	_release_timer = Timer.new()
	_release_timer.name = "ThreatReleaseTimer"
	_release_timer.one_shot = true
	_release_timer.process_callback = Timer.TIMER_PROCESS_IDLE
	_release_timer.timeout.connect(_finish_release)
	add_child(_release_timer)

	_poll_timer = Timer.new()
	_poll_timer.name = "ThreatPollTimer"
	_poll_timer.wait_time = POLL_INTERVAL_SECONDS
	_poll_timer.one_shot = false
	_poll_timer.autostart = true
	_poll_timer.process_callback = Timer.TIMER_PROCESS_IDLE
	_poll_timer.timeout.connect(_refresh_state)
	add_child(_poll_timer)


func _refresh_state() -> void:
	if _registry_polling_enabled:
		_refresh_registry_sources()
	var level: int = get_effective_threat_level()
	if level != _last_effective_level:
		_last_effective_level = level
		threat_level_changed.emit(level)

	if not _runtime_allows_tension():
		_cancel_release_timer()
		_deactivate_tension(0.35)
		return
	if level > 0:
		_cancel_release_timer()
		_activate_tension()
		return
	if not _tension_applied:
		return
	if _release_delay_seconds <= 0.0:
		_finish_release()
	elif _release_timer.is_stopped():
		_release_timer.start(_release_delay_seconds)


func _refresh_registry_sources() -> void:
	_registry_sources.clear()
	var state: Node = get_tree().root.get_node_or_null("GameState")
	if state == null or not state.has_method("get_flag"):
		return
	var registry_value: Variant = state.call("get_flag", STEALTH_ALERT_REGISTRY_FLAG, {})
	if not registry_value is Dictionary:
		return
	var actors_value: Variant = (registry_value as Dictionary).get("actors", {})
	if not actors_value is Dictionary:
		return
	for actor_id_value: Variant in (actors_value as Dictionary).keys():
		var record_value: Variant = (actors_value as Dictionary)[actor_id_value]
		if not record_value is Dictionary:
			continue
		var alert_state: String = str((record_value as Dictionary).get("state", "calm"))
		var intensity: int = int(STEALTH_STATE_INTENSITY.get(alert_state, 0))
		if intensity > 0:
			_registry_sources["stealth:%s" % str(actor_id_value)] = intensity


func _combined_sources() -> Dictionary:
	var result: Dictionary = _registry_sources.duplicate()
	for source_value: Variant in _manual_sources.keys():
		var key: String = str(source_value)
		result[key] = maxi(int(result.get(key, 0)), int(_manual_sources[source_value]))
	return result


func _runtime_allows_tension() -> bool:
	if not _automatic_runtime_gate_enabled:
		return true
	var current_scene: Node = get_tree().current_scene
	if current_scene == null or not current_scene.scene_file_path.begins_with(GAME_SCENE_PREFIX):
		return false
	if current_scene.has_method("is_turn_based_combat_active"):
		return not bool(current_scene.call("is_turn_based_combat_active"))
	return true


func _activate_tension() -> void:
	var music_manager: Node = get_tree().root.get_node_or_null("MusicManager")
	if music_manager == null or not music_manager.has_method("set_context_override"):
		return
	if not bool(music_manager.call("set_context_override", TENSION_CONTEXT_ID, DEFAULT_TENSION_FADE_SECONDS)):
		return
	if not _tension_applied:
		_tension_applied = true
		tension_changed.emit(true)


func _deactivate_tension(fade_seconds: float) -> void:
	if not _tension_applied:
		return
	var music_manager: Node = get_tree().root.get_node_or_null("MusicManager")
	if music_manager != null and music_manager.has_method("clear_context_override"):
		music_manager.call("clear_context_override", maxf(fade_seconds, 0.0))
		# Isolated runtime tests have no current game scene, so provide the same
		# deterministic fallback that automatic context resolution would choose.
		if not _automatic_runtime_gate_enabled and music_manager.has_method("play_context"):
			music_manager.call("play_context", EXPLORATION_CONTEXT_ID, maxf(fade_seconds, 0.0))
	_tension_applied = false
	tension_changed.emit(false)


func _finish_release() -> void:
	if get_effective_threat_level() > 0 or not _runtime_allows_tension():
		return
	_deactivate_tension(DEFAULT_CALM_FADE_SECONDS)


func _cancel_release_timer() -> void:
	if _release_timer != null and not _release_timer.is_stopped():
		_release_timer.stop()
