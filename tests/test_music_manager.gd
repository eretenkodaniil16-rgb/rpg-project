extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	await process_frame
	if MusicManager.get_catalog_error() != "":
		_fail("Music catalog failed to load: %s" % MusicManager.get_catalog_error())
		return
	for context_id: StringName in [
		&"main_menu",
		&"character_creation",
		&"world_exploration",
		&"combat_standard",
		&"aftermath"
	]:
		if not MusicManager.has_context(context_id):
			_fail("Missing music context: %s" % String(context_id))
			return
	if not MusicManager.has_track(&"main_theme") or not MusicManager.has_track(&"combat_standard"):
		_fail("Required placeholder tracks are missing.")
		return
	if MusicManager.play_context(&"missing_context", 0.0):
		_fail("Unknown context must be rejected.")
		return
	if MusicManager.play_context(&"main_menu", 0.0):
		_fail("Disabled placeholder track must not report successful playback.")
		return
	if MusicManager.get_current_context_id() != &"main_menu":
		_fail("Requested context was not retained while its placeholder is disabled.")
		return
	for bus_name: StringName in MusicManager.get_managed_bus_names():
		if AudioServer.get_bus_index(bus_name) < 0:
			_fail("Managed audio bus was not created: %s" % String(bus_name))
			return
	var original_music_volume: float = MusicManager.get_bus_volume_linear(&"Music")
	if not MusicManager.set_bus_volume_linear(&"Music", 0.37, false):
		_fail("Music bus volume could not be changed.")
		return
	if absf(MusicManager.get_bus_volume_linear(&"Music") - 0.37) > 0.001:
		_fail("Music bus volume did not retain the requested value.")
		return
	MusicManager.set_bus_volume_linear(&"Music", original_music_volume, false)
	if MusicManager.play_stinger(&"missing_stinger"):
		_fail("Unknown stinger must be rejected.")
		return
	print("Music manager tests passed.")
	quit(0)
