extends Node

signal combat_outcome_detected(outcome_id: StringName, encounter_id: String)
signal aftermath_started(track_id: StringName)
signal aftermath_finished(interrupted: bool)

const TRACKER_SCRIPT: Script = preload("res://scripts/audio/music_aftermath_transition_tracker.gd")
const GAME_SCENE_PREFIX: String = "res://scenes/game/"
const AFTERMATH_CONTEXT_ID: StringName = &"aftermath"
const AFTERMATH_TRACK_ID: StringName = &"aftermath"
const POLL_INTERVAL_SECONDS: float = 0.10
const AFTERMATH_FADE_SECONDS: float = 0.55
const RETURN_FADE_SECONDS: float = 1.5

const OUTCOME_VICTORY: StringName = &"victory"
const OUTCOME_ESCAPE: StringName = &"escape"
const OUTCOME_DEFEAT: StringName = &"defeat"
const OUTCOME_SCRIPTED_END: StringName = &"scripted_end"

const STATUS_RESOLVED: String = "resolved"
const STATUS_REWARDED: String = "rewarded"
const STATUS_FAILED: String = "failed"
const STATUS_ABANDONED: String = "abandoned"

var _tracker: RefCounted
var _poll_timer: Timer
var _polling_enabled: bool = true
var _aftermath_active: bool = false
var _aftermath_scene_instance_id: int = 0


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_tracker = TRACKER_SCRIPT.new()
	_create_poll_timer()
	var music_manager: Node = get_tree().root.get_node_or_null("MusicManager")
	if music_manager != null and music_manager.has_signal("track_stopped"):
		music_manager.connect("track_stopped", _on_track_stopped)
	call_deferred("_refresh_state")


func is_aftermath_active() -> bool:
	return _aftermath_active


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
	_poll_timer.name = "AftermathMusicPollTimer"
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
	if eligible:
		combat_active = bool(current_scene.call("is_turn_based_combat_active"))
		if combat_active and current_scene.has_method("get_active_combat_encounter_id"):
			encounter_id = str(current_scene.call("get_active_combat_encounter_id"))
	_tracker.call("sample", scene_instance_id, eligible, combat_active, encounter_id)

	if _aftermath_active:
		if not eligible or scene_instance_id != _aftermath_scene_instance_id or combat_active:
			_finish_aftermath(true)
		return
	if not bool(_tracker.call("is_pending")):
		return
	var transition: Dictionary = _tracker.call("consume_transition") as Dictionary
	var outcome: Dictionary = _resolve_outcome(transition)
	var outcome_id: StringName = StringName(str(outcome.get("outcome_id", OUTCOME_VICTORY)))
	var resolved_encounter_id: String = str(outcome.get("encounter_id", transition.get("encounter_id", "")))
	combat_outcome_detected.emit(outcome_id, resolved_encounter_id)
	if outcome_id == OUTCOME_VICTORY:
		_start_aftermath(int(transition.get("scene_instance_id", 0)))
	else:
		_refresh_post_combat_context(outcome_id)


func _resolve_outcome(transition: Dictionary) -> Dictionary:
	var scene_instance_id: int = int(transition.get("scene_instance_id", 0))
	var registry: Node = get_tree().root.get_node_or_null("CombatOutcomeRegistry")
	if registry != null and registry.has_method("consume_outcome"):
		var explicit: Dictionary = registry.call("consume_outcome", scene_instance_id) as Dictionary
		if not explicit.is_empty():
			return explicit
	var encounter_id: String = str(transition.get("encounter_id", ""))
	var state: Node = get_tree().root.get_node_or_null("GameState")
	if state != null and not encounter_id.is_empty() and state.has_method("get_encounter_status"):
		var status: String = str(state.call("get_encounter_status", encounter_id))
		if status == STATUS_ABANDONED:
			return {"outcome_id": OUTCOME_ESCAPE, "encounter_id": encounter_id}
		if status == STATUS_FAILED:
			return {"outcome_id": OUTCOME_DEFEAT, "encounter_id": encounter_id}
		if status in [STATUS_RESOLVED, STATUS_REWARDED]:
			return {"outcome_id": OUTCOME_VICTORY, "encounter_id": encounter_id}
	if _player_is_defeated(state):
		return {"outcome_id": OUTCOME_DEFEAT, "encounter_id": encounter_id}
	return {"outcome_id": OUTCOME_VICTORY, "encounter_id": encounter_id}


func _player_is_defeated(state: Node) -> bool:
	if state == null:
		return false
	var character_value: Variant = state.get("player_character")
	if character_value is Object:
		var health_value: Variant = (character_value as Object).get("current_health")
		return health_value != null and int(health_value) <= 0
	return false


func _start_aftermath(scene_instance_id: int) -> void:
	var music_manager: Node = get_tree().root.get_node_or_null("MusicManager")
	if music_manager == null or not music_manager.has_method("set_context_override"):
		_refresh_post_combat_context(OUTCOME_VICTORY)
		return
	_aftermath_active = true
	_aftermath_scene_instance_id = scene_instance_id
	var threat_resolver: Node = get_tree().root.get_node_or_null("MusicThreatStateResolver")
	if threat_resolver != null and threat_resolver.has_method("release_for_external_override"):
		threat_resolver.call("release_for_external_override")
	if not bool(music_manager.call("set_context_override", AFTERMATH_CONTEXT_ID, AFTERMATH_FADE_SECONDS)):
		_aftermath_active = false
		_aftermath_scene_instance_id = 0
		_refresh_post_combat_context(OUTCOME_VICTORY)
		return
	aftermath_started.emit(AFTERMATH_TRACK_ID)


func _on_track_stopped(track_id: StringName) -> void:
	if _aftermath_active and track_id == AFTERMATH_TRACK_ID:
		_finish_aftermath(false)


func _finish_aftermath(interrupted: bool) -> void:
	if not _aftermath_active:
		return
	_aftermath_active = false
	_aftermath_scene_instance_id = 0
	var music_manager: Node = get_tree().root.get_node_or_null("MusicManager")
	if music_manager != null and music_manager.has_method("clear_context_override"):
		music_manager.call("clear_context_override", 0.15 if interrupted else RETURN_FADE_SECONDS)
	_refresh_post_combat_context(OUTCOME_SCRIPTED_END if interrupted else OUTCOME_VICTORY)
	aftermath_finished.emit(interrupted)


func _refresh_post_combat_context(outcome_id: StringName) -> void:
	if outcome_id == OUTCOME_DEFEAT or outcome_id == OUTCOME_SCRIPTED_END:
		return
	var threat_resolver: Node = get_tree().root.get_node_or_null("MusicThreatStateResolver")
	if threat_resolver != null and threat_resolver.has_method("refresh_now"):
		threat_resolver.call("refresh_now")
