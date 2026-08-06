extends Node

signal combat_music_profile_applied(profile_id: StringName, encounter_id: String)
signal climax_started(encounter_id: String)
signal climax_finished(encounter_id: String, interrupted: bool)

const TRACKER_SCRIPT: Script = preload("res://scripts/audio/music_combat_climax_transition_tracker.gd")
const GAME_SCENE_PREFIX: String = "res://scenes/game/"
const PROFILE_STANDARD: StringName = &"standard"
const PROFILE_CLIMAX: StringName = &"climax"
const PROFILE_SCRIPTED: StringName = &"scripted"
const STANDARD_CONTEXT_ID: StringName = &"combat_standard"
const CLIMAX_CONTEXT_ID: StringName = &"combat_climax"
const CLIMAX_CROSSFADE_SECONDS: float = 0.75
const RETURN_CROSSFADE_SECONDS: float = 0.75
const POLL_INTERVAL_SECONDS: float = 0.12

var _tracker: RefCounted
var _poll_timer: Timer
var _polling_enabled: bool = true
var _climax_applied: bool = false
var _active_encounter_id: String = ""


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_tracker = TRACKER_SCRIPT.new()
	_create_poll_timer()
	call_deferred("_refresh_state")


func is_climax_active() -> bool:
	return _climax_applied


func refresh_now() -> void:
	_refresh_state()


func set_polling_enabled(enabled: bool) -> void:
	_polling_enabled = enabled
	if _poll_timer != null:
		_poll_timer.paused = not enabled
	if enabled:
		_refresh_state()


func _create_poll_timer() -> void:
	_poll_timer = Timer.new()
	_poll_timer.name = "CombatClimaxMusicPollTimer"
	_poll_timer.wait_time = POLL_INTERVAL_SECONDS
	_poll_timer.one_shot = false
	_poll_timer.autostart = true
	_poll_timer.process_callback = Timer.TIMER_PROCESS_IDLE
	_poll_timer.timeout.connect(_refresh_state)
	add_child(_poll_timer)


func _refresh_state() -> void:
	if not _polling_enabled or _tracker == null:
		return
	var current_scene: Node = get_tree().current_scene
	var eligible: bool = (
		current_scene != null
		and current_scene.scene_file_path.begins_with(GAME_SCENE_PREFIX)
		and current_scene.has_method("is_turn_based_combat_active")
	)
	var scene_instance_id: int = int(current_scene.get_instance_id()) if current_scene != null else 0
	var combat_active: bool = false
	var encounter_id: String = ""
	var desired_profile: StringName = PROFILE_STANDARD
	if eligible:
		combat_active = bool(current_scene.call("is_turn_based_combat_active"))
		if current_scene.has_method("get_active_combat_encounter_id"):
			encounter_id = str(current_scene.call("get_active_combat_encounter_id"))
		if combat_active:
			var registry: Node = get_tree().root.get_node_or_null("CombatMusicProfileRegistry")
			if registry != null and registry.has_method("get_profile"):
				desired_profile = StringName(str(registry.call(
					"get_profile",
					scene_instance_id,
					encounter_id
				)))
	_tracker.call("sample", scene_instance_id, eligible, combat_active, desired_profile)
	if not bool(_tracker.call("has_pending")):
		return
	var pending_profile: StringName = StringName(str(_tracker.call("consume_pending")))
	_apply_profile(pending_profile, encounter_id, combat_active)


func _apply_profile(
	profile_id: StringName,
	encounter_id: String,
	combat_active: bool
) -> void:
	if profile_id == PROFILE_CLIMAX and combat_active:
		if _start_climax(encounter_id):
			_tracker.call("mark_applied", PROFILE_CLIMAX)
			combat_music_profile_applied.emit(PROFILE_CLIMAX, encounter_id)
		return
	if profile_id == PROFILE_SCRIPTED and combat_active:
		_tracker.call("mark_applied", PROFILE_SCRIPTED)
		combat_music_profile_applied.emit(PROFILE_SCRIPTED, encounter_id)
		return
	_release_climax(encounter_id, not combat_active)
	_tracker.call("mark_applied", PROFILE_STANDARD)
	combat_music_profile_applied.emit(PROFILE_STANDARD, encounter_id)


func _start_climax(encounter_id: String) -> bool:
	var music_manager: Node = get_tree().root.get_node_or_null("MusicManager")
	if music_manager == null or not music_manager.has_method("set_context_override"):
		return false
	var threat_resolver: Node = get_tree().root.get_node_or_null("MusicThreatStateResolver")
	if threat_resolver != null and threat_resolver.has_method("release_for_external_override"):
		threat_resolver.call("release_for_external_override")
	if not bool(music_manager.call(
		"set_context_override",
		CLIMAX_CONTEXT_ID,
		CLIMAX_CROSSFADE_SECONDS
	)):
		return false
	var was_active: bool = _climax_applied
	_climax_applied = true
	_active_encounter_id = encounter_id
	if not was_active:
		climax_started.emit(encounter_id)
	return true


func _release_climax(encounter_id: String, combat_ended: bool) -> void:
	if not _climax_applied:
		return
	if combat_ended:
		var aftermath_resolver: Node = get_tree().root.get_node_or_null("MusicAftermathResolver")
		if aftermath_resolver != null and aftermath_resolver.has_method("refresh_now"):
			aftermath_resolver.call("refresh_now")
		if (
			aftermath_resolver != null
			and aftermath_resolver.has_method("is_aftermath_active")
			and bool(aftermath_resolver.call("is_aftermath_active"))
		):
			var finished_encounter: String = _active_encounter_id
			_climax_applied = false
			_active_encounter_id = ""
			climax_finished.emit(finished_encounter, false)
			return
	var music_manager: Node = get_tree().root.get_node_or_null("MusicManager")
	if (
		music_manager != null
		and music_manager.has_method("get_current_context_id")
		and StringName(str(music_manager.call("get_current_context_id"))) == CLIMAX_CONTEXT_ID
		and music_manager.has_method("clear_context_override")
	):
		music_manager.call(
			"clear_context_override",
			0.15 if combat_ended else RETURN_CROSSFADE_SECONDS
		)
		if not combat_ended and music_manager.has_method("play_context"):
			music_manager.call("play_context", STANDARD_CONTEXT_ID, RETURN_CROSSFADE_SECONDS)
	var finished_encounter: String = _active_encounter_id if not _active_encounter_id.is_empty() else encounter_id
	_climax_applied = false
	_active_encounter_id = ""
	climax_finished.emit(finished_encounter, combat_ended)
