extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	await process_frame
	var music_manager: Node = root.get_node_or_null("MusicManager")
	var resolver: Node = root.get_node_or_null("MusicThreatStateResolver")
	if music_manager == null or resolver == null:
		_fail("Music autoloads were not instantiated.")
		return
	if not bool(music_manager.call("has_context", &"world_tension")):
		_fail("world_tension context is missing.")
		return
	if not bool(music_manager.call("has_track", &"exploration_tension")):
		_fail("exploration_tension track is missing.")
		return

	resolver.call("set_automatic_runtime_gate_enabled", false)
	resolver.call("set_registry_polling_enabled", false)
	resolver.call("set_release_delay_seconds", 0.06)
	resolver.call("clear_all_threat_sources")
	music_manager.call("play_context", &"world_exploration", 0.0)
	await process_frame

	if bool(resolver.call("set_threat_source", &"test_guard", true, 2)) == false:
		_fail("A valid threat source was rejected.")
		return
	await process_frame
	if not bool(resolver.call("is_tension_active")):
		_fail("Tension did not activate immediately.")
		return
	if StringName(str(music_manager.call("get_current_track_id"))) != &"exploration_tension":
		_fail("Threat source did not select exploration_tension.")
		return
	var tension_player: AudioStreamPlayer = music_manager.get_node_or_null("MusicPlayer1") as AudioStreamPlayer
	if tension_player == null or tension_player.stream == null or not tension_player.playing:
		tension_player = music_manager.get_node_or_null("MusicPlayer2") as AudioStreamPlayer
	if tension_player == null or tension_player.stream == null:
		_fail("exploration_tension was not assigned to a music player.")
		return
	if not (tension_player.stream is AudioStreamOggVorbis):
		_fail("exploration_tension must import as AudioStreamOggVorbis.")
		return
	if not (tension_player.stream as AudioStreamOggVorbis).loop:
		_fail("Native Ogg loop was not enabled for exploration_tension.")
		return

	resolver.call("set_threat_source", &"test_noise", true, 1)
	resolver.call("clear_threat_source", &"test_guard")
	await process_frame
	if int(resolver.call("get_active_source_count")) != 1:
		_fail("Multiple threat sources were not aggregated independently.")
		return
	if not bool(resolver.call("is_tension_active")):
		_fail("Clearing one of multiple sources released tension too early.")
		return

	resolver.call("clear_threat_source", &"test_noise")
	await process_frame
	if not bool(resolver.call("is_tension_active")):
		_fail("Tension did not retain its release delay.")
		return
	await create_timer(0.10).timeout
	await process_frame
	if bool(resolver.call("is_tension_active")):
		_fail("Tension did not return to calm after the release delay.")
		return
	if StringName(str(music_manager.call("get_current_track_id"))) != &"exploration_calm":
		_fail("Release did not restore exploration_calm.")
		return

	if bool(resolver.call("set_threat_source", &"", true, 1)):
		_fail("An empty source ID must be rejected.")
		return

	resolver.call("set_release_delay_seconds", 8.0)
	resolver.call("set_registry_polling_enabled", true)
	resolver.call("set_automatic_runtime_gate_enabled", true)
	resolver.call("clear_all_threat_sources")
	music_manager.call("stop_music", 0.0, true)
	print("Music threat resolver tests passed.")
	quit(0)
