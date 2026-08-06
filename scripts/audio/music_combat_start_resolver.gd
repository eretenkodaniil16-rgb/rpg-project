extends Node

signal combat_start_cue_emitted(stinger_id: StringName)

const TRACKER_SCRIPT: Script = preload("res://scripts/audio/music_combat_transition_tracker.gd")
const GAME_SCENE_PREFIX: String = "res://scenes/game/"
const COMBAT_CONTEXT_ID: StringName = &"combat_standard"
const COMBAT_START_STINGER_ID: StringName = &"combat_start"
const COMBAT_CROSSFADE_SECONDS: float = 0.75
const POLL_INTERVAL_SECONDS: float = 0.10
const REQUIRED_INACTIVE_SAMPLES: int = 3

var _tracker: RefCounted
var _poll_timer: Timer
var _polling_enabled: bool = true


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_tracker = TRACKER_SCRIPT.new(REQUIRED_INACTIVE_SAMPLES)
	_create_poll_timer()
	call_deferred("_refresh_state")


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
	_poll_timer.name = "CombatStartMusicPollTimer"
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
	if eligible:
		combat_active = bool(current_scene.call("is_turn_based_combat_active"))
	_tracker.call("sample", scene_instance_id, eligible, combat_active)
	if not bool(_tracker.call("is_pending")):
		return
	_emit_pending_combat_start_cue()


func _emit_pending_combat_start_cue() -> void:
	var root: Window = get_tree().root
	var threat_resolver: Node = root.get_node_or_null("MusicThreatStateResolver")
	if threat_resolver != null and threat_resolver.has_method("refresh_now"):
		threat_resolver.call("refresh_now")
	var music_manager: Node = root.get_node_or_null("MusicManager")
	if music_manager == null:
		return
	if not music_manager.has_method("play_context") or not music_manager.has_method("play_stinger"):
		return
	if not bool(music_manager.call("play_context", COMBAT_CONTEXT_ID, COMBAT_CROSSFADE_SECONDS)):
		return
	if not bool(music_manager.call("play_stinger", COMBAT_START_STINGER_ID)):
		return
	_tracker.call("mark_emitted")
	combat_start_cue_emitted.emit(COMBAT_START_STINGER_ID)
