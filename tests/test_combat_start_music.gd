extends SceneTree


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	await process_frame
	var music_manager: Node = root.get_node_or_null("MusicManager")
	if music_manager == null:
		_fail("MusicManager autoload was not instantiated.")
		return
	if not bool(music_manager.call("has_stinger", &"combat_start")):
		_fail("combat_start stinger is missing from the catalog.")
		return
	if not bool(music_manager.call("play_context", &"combat_standard", 0.0)):
		_fail("combat_standard context failed to start.")
		return
	if not bool(music_manager.call("play_stinger", &"combat_start")):
		_fail("combat_start stinger failed to play.")
		return
	await process_frame
	var player: AudioStreamPlayer = music_manager.get_node_or_null("StingerPlayer") as AudioStreamPlayer
	if player == null or not player.playing:
		_fail("StingerPlayer did not start playback.")
		return
	if not (player.stream is AudioStreamOggVorbis):
		_fail("combat_start must import as AudioStreamOggVorbis.")
		return
	if (player.stream as AudioStreamOggVorbis).loop:
		_fail("combat_start stinger must never loop.")
		return
	if player.bus != &"Music":
		_fail("combat_start stinger must use the Music bus.")
		return
	if absf(player.volume_db - (-4.5)) > 0.001:
		_fail("combat_start playback volume changed.")
		return
	music_manager.call("stop_music", 0.0, true)
	player.stop()
	print("Combat start music tests passed.")
	quit(0)


func _init() -> void:
	call_deferred("_run")
