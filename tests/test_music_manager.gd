extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	await process_frame
	var music_manager: Node = root.get_node_or_null("MusicManager")
	if music_manager == null:
		_fail("MusicManager autoload was not instantiated.")
		return
	var catalog_error: String = str(music_manager.call("get_catalog_error"))
	if not catalog_error.is_empty():
		_fail("Music catalog failed to load: %s" % catalog_error)
		return
	for context_id: StringName in [
		&"main_menu",
		&"character_creation",
		&"world_exploration",
		&"combat_standard",
		&"aftermath"
	]:
		if not bool(music_manager.call("has_context", context_id)):
			_fail("Missing music context: %s" % String(context_id))
			return
	if not bool(music_manager.call("has_track", &"main_theme")):
		_fail("Required main_theme track is missing.")
		return
	if bool(music_manager.call("play_context", &"missing_context", 0.0)):
		_fail("Unknown context must be rejected.")
		return
	if not bool(music_manager.call("play_context", &"main_menu", 0.0)):
		_fail("Enabled main menu theme failed to start.")
		return
	await process_frame
	if StringName(str(music_manager.call("get_current_context_id"))) != &"main_menu":
		_fail("Main menu context was not retained.")
		return
	if StringName(str(music_manager.call("get_current_track_id"))) != &"main_theme":
		_fail("Main menu did not select main_theme.")
		return
	var player: AudioStreamPlayer = music_manager.get_node_or_null("MusicPlayer1") as AudioStreamPlayer
	if player == null or player.stream == null:
		player = music_manager.get_node_or_null("MusicPlayer2") as AudioStreamPlayer
	if player == null or player.stream == null:
		_fail("Main menu theme was not assigned to a music player.")
		return
	if not (player.stream is AudioStreamOggVorbis):
		_fail("Main menu resource must import as AudioStreamOggVorbis.")
		return
	if not (player.stream as AudioStreamOggVorbis).loop:
		_fail("Native Ogg loop was not enabled.")
		return
	var managed_buses: Array = music_manager.call("get_managed_bus_names") as Array
	for bus_value: Variant in managed_buses:
		var bus_name: StringName = StringName(str(bus_value))
		if AudioServer.get_bus_index(bus_name) < 0:
			_fail("Managed audio bus was not created: %s" % String(bus_name))
			return
	var original_music_volume: float = float(music_manager.call("get_bus_volume_linear", &"Music"))
	if not bool(music_manager.call("set_bus_volume_linear", &"Music", 0.37, false)):
		_fail("Music bus volume could not be changed.")
		return
	var updated_music_volume: float = float(music_manager.call("get_bus_volume_linear", &"Music"))
	if absf(updated_music_volume - 0.37) > 0.001:
		_fail("Music bus volume did not retain the requested value.")
		return
	music_manager.call("set_bus_volume_linear", &"Music", original_music_volume, false)
	music_manager.call("stop_music", 0.0, true)
	if bool(music_manager.call("play_stinger", &"missing_stinger")):
		_fail("Unknown stinger must be rejected.")
		return
	print("Music manager tests passed.")
	quit(0)
