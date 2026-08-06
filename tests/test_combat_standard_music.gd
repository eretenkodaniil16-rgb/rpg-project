extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _find_active_player(music_manager: Node) -> AudioStreamPlayer:
	for player_name: String in ["MusicPlayer1", "MusicPlayer2"]:
		var player: AudioStreamPlayer = music_manager.get_node_or_null(player_name) as AudioStreamPlayer
		if player != null and player.playing and player.stream != null:
			return player
	return null


func _run() -> void:
	await process_frame
	var music_manager: Node = root.get_node_or_null("MusicManager")
	if music_manager == null:
		_fail("MusicManager autoload was not instantiated.")
		return
	music_manager.call("set_automatic_context_enabled", false)
	if not bool(music_manager.call("has_track", &"combat_standard")):
		_fail("combat_standard track is missing.")
		return
	if not bool(music_manager.call("play_context", &"combat_standard", 0.0)):
		_fail("combat_standard context failed to start.")
		return
	await process_frame
	if StringName(str(music_manager.call("get_current_context_id"))) != &"combat_standard":
		_fail("combat_standard context was not retained.")
		return
	if StringName(str(music_manager.call("get_current_track_id"))) != &"combat_standard":
		_fail("combat_standard context selected the wrong track.")
		return
	var player: AudioStreamPlayer = _find_active_player(music_manager)
	if player == null or not (player.stream is AudioStreamOggVorbis):
		_fail("Combat resource must import as AudioStreamOggVorbis.")
		return
	if not (player.stream as AudioStreamOggVorbis).loop:
		_fail("Native Ogg loop was not enabled for combat_standard.")
		return
	if absf(player.volume_db - (-4.5)) > 0.01:
		_fail("Combat track volume is incorrect: %s" % player.volume_db)
		return
	if not bool(music_manager.call("play_context", &"world_exploration", 0.0)):
		_fail("Transition back to world_exploration failed.")
		return
	await process_frame
	if StringName(str(music_manager.call("get_current_track_id"))) != &"exploration_calm":
		_fail("Combat release did not return to exploration_calm.")
		return
	music_manager.call("stop_music", 0.0, true)
	print("Combat standard music tests passed.")
	quit(0)
