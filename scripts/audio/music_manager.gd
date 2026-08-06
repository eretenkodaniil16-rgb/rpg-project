extends Node

signal catalog_loaded(schema_version: int)
signal catalog_rejected(reason: String)
signal context_changed(context_id: StringName, track_id: StringName)
signal track_started(track_id: StringName)
signal track_stopped(track_id: StringName)
signal stinger_started(stinger_id: StringName)

const CATALOG_PATH: String = "res://data/audio/music_catalog.json"
const SETTINGS_PATH: String = "user://audio_settings.cfg"
const SETTINGS_SECTION: String = "audio"
const SILENCE_DB: float = -80.0
const DEFAULT_CROSSFADE_SECONDS: float = 1.5
const AUTO_CONTEXT_INTERVAL_SECONDS: float = 0.25
const MAIN_MENU_SCENE_PATH: String = "res://scenes/menus/main_menu.tscn"
const CHARACTER_CREATION_PREFIX: String = "res://scenes/character_creation/"
const GAME_SCENE_PREFIX: String = "res://scenes/game/"

const MANAGED_BUSES: Array[StringName] = [
	&"Music",
	&"Ambience",
	&"SFX",
	&"UI",
	&"Voice"
]
const SETTINGS_BUSES: Array[StringName] = [
	&"Master",
	&"Music",
	&"Ambience",
	&"SFX",
	&"UI",
	&"Voice"
]
const DEFAULT_BUS_VOLUMES: Dictionary = {
	"Master": 1.0,
	"Music": 0.8,
	"Ambience": 0.8,
	"SFX": 0.9,
	"UI": 0.9,
	"Voice": 1.0
}

var _catalog: Dictionary = {}
var _catalog_error: String = ""
var _music_players: Array[AudioStreamPlayer] = []
var _stinger_player: AudioStreamPlayer
var _active_player_index: int = 0
var _transition_tween: Tween
var _current_context_id: StringName = &""
var _current_track_id: StringName = &""
var _context_override_id: StringName = &""
var _automatic_context_enabled: bool = true
var _context_timer: Timer


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_ensure_audio_buses()
	_create_audio_players()
	reload_catalog()
	_load_audio_settings()
	_create_context_timer()
	call_deferred("_refresh_automatic_context")


func reload_catalog() -> bool:
	_catalog.clear()
	_catalog_error = ""
	var file: FileAccess = FileAccess.open(CATALOG_PATH, FileAccess.READ)
	if file == null:
		return _reject_catalog("Не удалось открыть каталог музыки: %s" % CATALOG_PATH)
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not (parsed is Dictionary):
		return _reject_catalog("Каталог музыки должен содержать JSON-объект.")
	var parsed_catalog: Dictionary = parsed as Dictionary
	var schema_version: int = int(parsed_catalog.get("schema_version", 0))
	if schema_version < 1:
		return _reject_catalog("Не поддерживается schema_version каталога музыки: %d" % schema_version)
	for section_name: String in ["contexts", "tracks", "stingers"]:
		if not (parsed_catalog.get(section_name, {}) is Dictionary):
			return _reject_catalog("Раздел '%s' каталога музыки должен быть объектом." % section_name)
	_catalog = parsed_catalog
	catalog_loaded.emit(schema_version)
	return true


func has_context(context_id: StringName) -> bool:
	return _section("contexts").has(String(context_id))


func has_track(track_id: StringName) -> bool:
	return _section("tracks").has(String(track_id))


func has_stinger(stinger_id: StringName) -> bool:
	return _section("stingers").has(String(stinger_id))


func get_catalog_error() -> String:
	return _catalog_error


func get_current_context_id() -> StringName:
	return _current_context_id


func get_current_track_id() -> StringName:
	return _current_track_id


func get_managed_bus_names() -> Array[StringName]:
	var result: Array[StringName] = []
	for bus_name: StringName in SETTINGS_BUSES:
		result.append(bus_name)
	return result


func play_context(context_id: StringName, fade_seconds: float = -1.0) -> bool:
	var context: Dictionary = _definition("contexts", context_id)
	if context.is_empty():
		push_warning("Неизвестный music context: %s" % String(context_id))
		return false
	var track_id: StringName = StringName(str(context.get("track_id", "")))
	_current_context_id = context_id
	context_changed.emit(context_id, track_id)
	var resolved_fade: float = fade_seconds
	if resolved_fade < 0.0:
		resolved_fade = maxf(float(context.get("fade_seconds", DEFAULT_CROSSFADE_SECONDS)), 0.0)
	if String(track_id).is_empty():
		stop_music(resolved_fade)
		return true
	return play_music(track_id, resolved_fade)


func play_music(track_id: StringName, fade_seconds: float = DEFAULT_CROSSFADE_SECONDS) -> bool:
	var track: Dictionary = _definition("tracks", track_id)
	if track.is_empty():
		push_warning("Неизвестный music_id: %s" % String(track_id))
		return false
	if not bool(track.get("enabled", false)):
		return false
	var stream: AudioStream = _load_audio_stream(track, "track", track_id)
	if stream == null:
		return false
	stream = _configure_stream_loop(stream, bool(track.get("loop", false)))
	if _current_track_id == track_id and _active_player().playing:
		return true
	_crossfade_to_track(stream, track_id, track, maxf(fade_seconds, 0.0))
	return true


func play_stinger(stinger_id: StringName) -> bool:
	var stinger: Dictionary = _definition("stingers", stinger_id)
	if stinger.is_empty():
		push_warning("Неизвестный stinger_id: %s" % String(stinger_id))
		return false
	if not bool(stinger.get("enabled", false)):
		return false
	var stream: AudioStream = _load_audio_stream(stinger, "stinger", stinger_id)
	if stream == null:
		return false
	_stinger_player.stop()
	_stinger_player.stream = stream
	_stinger_player.bus = _resolve_bus(stinger)
	_stinger_player.volume_db = float(stinger.get("volume_db", 0.0))
	_stinger_player.play()
	stinger_started.emit(stinger_id)
	return true


func stop_music(fade_seconds: float = DEFAULT_CROSSFADE_SECONDS, clear_context: bool = false) -> void:
	_cancel_transition()
	var safe_fade: float = maxf(fade_seconds, 0.0)
	if safe_fade <= 0.0:
		_finish_stop(clear_context)
		return
	var any_playing: bool = false
	_transition_tween = create_tween().set_parallel(true)
	for player: AudioStreamPlayer in _music_players:
		if player.playing:
			any_playing = true
			_transition_tween.tween_property(player, "volume_db", SILENCE_DB, safe_fade)
	if not any_playing:
		_cancel_transition()
		_finish_stop(clear_context)
		return
	_transition_tween.finished.connect(_finish_stop.bind(clear_context), CONNECT_ONE_SHOT)


func set_context_override(context_id: StringName, fade_seconds: float = -1.0) -> bool:
	if not has_context(context_id):
		return false
	_context_override_id = context_id
	return play_context(context_id, fade_seconds)


func clear_context_override(fade_seconds: float = -1.0) -> void:
	_context_override_id = &""
	_refresh_automatic_context(fade_seconds)


func set_automatic_context_enabled(enabled: bool) -> void:
	_automatic_context_enabled = enabled
	if enabled:
		_refresh_automatic_context()


func set_bus_volume_linear(bus_name: StringName, volume_linear: float, persist: bool = true) -> bool:
	var bus_index: int = AudioServer.get_bus_index(bus_name)
	if bus_index < 0:
		return false
	AudioServer.set_bus_volume_linear(bus_index, clampf(volume_linear, 0.0, 1.0))
	if persist:
		_save_audio_settings()
	return true


func get_bus_volume_linear(bus_name: StringName) -> float:
	var bus_index: int = AudioServer.get_bus_index(bus_name)
	if bus_index < 0:
		return 0.0
	return AudioServer.get_bus_volume_linear(bus_index)


func set_bus_muted(bus_name: StringName, muted: bool, persist: bool = true) -> bool:
	var bus_index: int = AudioServer.get_bus_index(bus_name)
	if bus_index < 0:
		return false
	AudioServer.set_bus_mute(bus_index, muted)
	if persist:
		_save_audio_settings()
	return true


func is_bus_muted(bus_name: StringName) -> bool:
	var bus_index: int = AudioServer.get_bus_index(bus_name)
	return bus_index >= 0 and AudioServer.is_bus_mute(bus_index)


func _create_audio_players() -> void:
	for player_index: int in range(2):
		var player: AudioStreamPlayer = AudioStreamPlayer.new()
		player.name = "MusicPlayer%d" % (player_index + 1)
		player.bus = &"Music"
		player.volume_db = SILENCE_DB
		player.finished.connect(_on_music_player_finished.bind(player_index))
		add_child(player)
		_music_players.append(player)
	_stinger_player = AudioStreamPlayer.new()
	_stinger_player.name = "StingerPlayer"
	_stinger_player.bus = &"Music"
	add_child(_stinger_player)


func _create_context_timer() -> void:
	_context_timer = Timer.new()
	_context_timer.name = "AutomaticContextTimer"
	_context_timer.wait_time = AUTO_CONTEXT_INTERVAL_SECONDS
	_context_timer.one_shot = false
	_context_timer.autostart = true
	_context_timer.timeout.connect(_refresh_automatic_context)
	add_child(_context_timer)


func _refresh_automatic_context(fade_seconds: float = -1.0) -> void:
	if not _automatic_context_enabled:
		return
	var desired_context: StringName = _context_override_id
	if String(desired_context).is_empty():
		desired_context = _resolve_automatic_context()
	if String(desired_context).is_empty() or desired_context == _current_context_id:
		return
	play_context(desired_context, fade_seconds)


func _resolve_automatic_context() -> StringName:
	var current_scene: Node = get_tree().current_scene
	if current_scene == null:
		return &""
	var scene_path: String = current_scene.scene_file_path
	if scene_path == MAIN_MENU_SCENE_PATH:
		return &"main_menu"
	if scene_path.begins_with(CHARACTER_CREATION_PREFIX):
		return &"character_creation"
	if scene_path.begins_with(GAME_SCENE_PREFIX):
		if (
			current_scene.has_method("is_turn_based_combat_active")
			and bool(current_scene.call("is_turn_based_combat_active"))
		):
			return &"combat_standard"
		return &"world_exploration"
	return &""


func _crossfade_to_track(
	stream: AudioStream,
	track_id: StringName,
	track: Dictionary,
	fade_seconds: float
) -> void:
	_cancel_transition()
	var old_index: int = _active_player_index
	var old_player: AudioStreamPlayer = _music_players[old_index]
	var next_index: int = 1 - old_index if old_player.playing else old_index
	var next_player: AudioStreamPlayer = _music_players[next_index]
	if next_player.playing:
		next_player.stop()
	next_player.stream = stream
	next_player.bus = _resolve_bus(track)
	next_player.volume_db = SILENCE_DB
	next_player.play()
	var target_volume_db: float = float(track.get("volume_db", 0.0))
	_current_track_id = track_id
	_active_player_index = next_index
	track_started.emit(track_id)
	if fade_seconds <= 0.0:
		if old_index != next_index:
			old_player.stop()
			old_player.stream = null
		next_player.volume_db = target_volume_db
		return
	_transition_tween = create_tween().set_parallel(true)
	if old_index != next_index and old_player.playing:
		_transition_tween.tween_property(old_player, "volume_db", SILENCE_DB, fade_seconds)
	_transition_tween.tween_property(next_player, "volume_db", target_volume_db, fade_seconds)
	_transition_tween.finished.connect(
		_finish_crossfade.bind(old_index, next_index),
		CONNECT_ONE_SHOT
	)


func _finish_crossfade(old_index: int, next_index: int) -> void:
	if old_index != next_index:
		var old_player: AudioStreamPlayer = _music_players[old_index]
		old_player.stop()
		old_player.stream = null
	_transition_tween = null


func _finish_stop(clear_context: bool) -> void:
	var stopped_track_id: StringName = _current_track_id
	for player: AudioStreamPlayer in _music_players:
		player.stop()
		player.stream = null
		player.volume_db = SILENCE_DB
	_current_track_id = &""
	if clear_context:
		_current_context_id = &""
	if not String(stopped_track_id).is_empty():
		track_stopped.emit(stopped_track_id)
	_transition_tween = null


func _on_music_player_finished(player_index: int) -> void:
	if player_index != _active_player_index or String(_current_track_id).is_empty():
		return
	var track: Dictionary = _definition("tracks", _current_track_id)
	if bool(track.get("loop", false)):
		_music_players[player_index].play()
		return
	var stopped_track_id: StringName = _current_track_id
	_current_track_id = &""
	track_stopped.emit(stopped_track_id)


func _active_player() -> AudioStreamPlayer:
	return _music_players[_active_player_index]


func _cancel_transition() -> void:
	if _transition_tween != null and _transition_tween.is_valid():
		_transition_tween.kill()
	_transition_tween = null


func _load_audio_stream(definition: Dictionary, kind: String, audio_id: StringName) -> AudioStream:
	var resource_path: String = str(definition.get("path", ""))
	if resource_path.is_empty():
		return null
	if not resource_path.begins_with("res://assets/audio/"):
		push_warning("%s '%s' использует путь вне assets/audio: %s" % [kind, String(audio_id), resource_path])
		return null
	if not ResourceLoader.exists(resource_path):
		push_warning("Не найден ресурс %s '%s': %s" % [kind, String(audio_id), resource_path])
		return null
	var resource: Resource = ResourceLoader.load(resource_path)
	if not (resource is AudioStream):
		push_warning("Ресурс %s '%s' не является AudioStream: %s" % [kind, String(audio_id), resource_path])
		return null
	return resource as AudioStream


func _configure_stream_loop(stream: AudioStream, should_loop: bool) -> AudioStream:
	var configured_stream: AudioStream = stream.duplicate() as AudioStream
	if configured_stream == null:
		configured_stream = stream
	if configured_stream is AudioStreamOggVorbis:
		(configured_stream as AudioStreamOggVorbis).loop = should_loop
	elif configured_stream is AudioStreamWAV:
		var wav_stream: AudioStreamWAV = configured_stream as AudioStreamWAV
		wav_stream.loop_mode = (
			AudioStreamWAV.LOOP_FORWARD if should_loop else AudioStreamWAV.LOOP_DISABLED
		)
	return configured_stream


func _resolve_bus(definition: Dictionary) -> StringName:
	var requested_bus: StringName = StringName(str(definition.get("bus", "Music")))
	if AudioServer.get_bus_index(requested_bus) >= 0:
		return requested_bus
	return &"Music"


func _definition(section_name: String, definition_id: StringName) -> Dictionary:
	var section: Dictionary = _section(section_name)
	var value: Variant = section.get(String(definition_id), {})
	if value is Dictionary:
		return value as Dictionary
	return {}


func _section(section_name: String) -> Dictionary:
	var value: Variant = _catalog.get(section_name, {})
	if value is Dictionary:
		return value as Dictionary
	return {}


func _reject_catalog(reason: String) -> bool:
	_catalog_error = reason
	push_error(reason)
	catalog_rejected.emit(reason)
	return false


func _ensure_audio_buses() -> void:
	for bus_name: StringName in MANAGED_BUSES:
		if AudioServer.get_bus_index(bus_name) >= 0:
			continue
		AudioServer.add_bus()
		var bus_index: int = AudioServer.bus_count - 1
		AudioServer.set_bus_name(bus_index, bus_name)
		AudioServer.set_bus_send(bus_index, &"Master")


func _load_audio_settings() -> void:
	var settings: ConfigFile = ConfigFile.new()
	var load_result: Error = settings.load(SETTINGS_PATH)
	for bus_name: StringName in SETTINGS_BUSES:
		var bus_index: int = AudioServer.get_bus_index(bus_name)
		if bus_index < 0:
			continue
		var bus_key: String = String(bus_name).to_lower()
		var default_volume: float = float(DEFAULT_BUS_VOLUMES.get(String(bus_name), 1.0))
		var volume_linear: float = default_volume
		var muted: bool = false
		if load_result == OK:
			volume_linear = float(settings.get_value(SETTINGS_SECTION, "%s_volume" % bus_key, default_volume))
			muted = bool(settings.get_value(SETTINGS_SECTION, "%s_muted" % bus_key, false))
		AudioServer.set_bus_volume_linear(bus_index, clampf(volume_linear, 0.0, 1.0))
		AudioServer.set_bus_mute(bus_index, muted)


func _save_audio_settings() -> void:
	var settings: ConfigFile = ConfigFile.new()
	settings.load(SETTINGS_PATH)
	for bus_name: StringName in SETTINGS_BUSES:
		var bus_index: int = AudioServer.get_bus_index(bus_name)
		if bus_index < 0:
			continue
		var bus_key: String = String(bus_name).to_lower()
		settings.set_value(SETTINGS_SECTION, "%s_volume" % bus_key, AudioServer.get_bus_volume_linear(bus_index))
		settings.set_value(SETTINGS_SECTION, "%s_muted" % bus_key, AudioServer.is_bus_mute(bus_index))
	var save_result: Error = settings.save(SETTINGS_PATH)
	if save_result != OK:
		push_warning("Не удалось сохранить настройки звука: %s" % error_string(save_result))
