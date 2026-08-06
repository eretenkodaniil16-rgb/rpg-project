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
	if not bool(music_manager.call("has_context", &"aftermath")):
		_fail("aftermath context is missing from the catalog.")
		return
	if not bool(music_manager.call("play_context", &"aftermath", 0.0)):
		_fail("aftermath context failed to start.")
		return
	await process_frame
	if StringName(music_manager.call("get_current_track_id")) != &"aftermath":
		_fail("aftermath track did not become current.")
		return
	var players: Array[Node] = []
	for child: Node in music_manager.get_children():
		if child is AudioStreamPlayer and child.name.begins_with("MusicPlayer"):
			players.append(child)
	var active_player: AudioStreamPlayer = null
	for candidate: Node in players:
		var player: AudioStreamPlayer = candidate as AudioStreamPlayer
		if player.playing:
			active_player = player
			break
	if active_player == null or not (active_player.stream is AudioStreamOggVorbis):
		_fail("aftermath must import and play as AudioStreamOggVorbis.")
		return
	if (active_player.stream as AudioStreamOggVorbis).loop:
		_fail("aftermath must be a one-shot track.")
		return
	if active_player.bus != &"Music":
		_fail("aftermath must use the Music bus.")
		return
	if absf(active_player.volume_db - (-6.0)) > 0.001:
		_fail("aftermath playback volume changed.")
		return
	music_manager.call("stop_music", 0.0, true)
	print("Aftermath music tests passed.")
	quit(0)


func _init() -> void:
	call_deferred("_run")
