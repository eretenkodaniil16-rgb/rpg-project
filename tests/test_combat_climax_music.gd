extends SceneTree


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	await process_frame
	var music_manager: Node = root.get_node_or_null("MusicManager")
	if music_manager == null:
		_fail("MusicManager autoload missing.")
		return
	if not bool(music_manager.call("has_context", &"combat_climax")):
		_fail("combat_climax context missing.")
		return
	if not bool(music_manager.call("has_track", &"combat_climax")):
		_fail("combat_climax track missing.")
		return
	if not bool(music_manager.call("play_context", &"combat_standard", 0.0)):
		_fail("combat_standard failed to start.")
		return
	if not bool(music_manager.call("set_context_override", &"combat_climax", 0.0)):
		_fail("combat_climax override failed to start.")
		return
	await process_frame
	if StringName(str(music_manager.call("get_current_context_id"))) != &"combat_climax":
		_fail("combat_climax context was not retained.")
		return
	if StringName(str(music_manager.call("get_current_track_id"))) != &"combat_climax":
		_fail("combat_climax track was not retained.")
		return
	var player: AudioStreamPlayer = music_manager.get_node_or_null("MusicPlayer1") as AudioStreamPlayer
	var second_player: AudioStreamPlayer = music_manager.get_node_or_null("MusicPlayer2") as AudioStreamPlayer
	if player == null or not player.playing:
		player = second_player
	if player == null or not player.playing:
		_fail("No active music player after climax start.")
		return
	if not (player.stream is AudioStreamOggVorbis):
		_fail("combat_climax must import as AudioStreamOggVorbis.")
		return
	if not (player.stream as AudioStreamOggVorbis).loop:
		_fail("combat_climax must loop.")
		return
	if player.bus != &"Music":
		_fail("combat_climax must use Music bus.")
		return
	if absf(player.volume_db - (-5.5)) > 0.001:
		_fail("combat_climax playback volume changed.")
		return
	music_manager.call("clear_context_override", 0.0)
	music_manager.call("play_context", &"combat_standard", 0.0)
	music_manager.call("stop_music", 0.0, true)
	print("Combat climax music tests passed.")
	quit(0)


func _init() -> void:
	call_deferred("_run")
