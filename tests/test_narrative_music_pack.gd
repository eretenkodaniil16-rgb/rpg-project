extends SceneTree

const CONTEXTS: Array[StringName] = [
	&"mad_wizard_theme",
	&"tavern_commonroom",
	&"elevator_descent_floor01",
	&"act01_plan_broken",
]

const TRACK_BY_CONTEXT: Dictionary = {
	"mad_wizard_theme": &"mad_wizard_theme",
	"tavern_commonroom": &"tavern_commonroom",
	"elevator_descent_floor01": &"elevator_descent_floor01",
	"act01_plan_broken": &"act01_plan_broken",
}


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	await process_frame
	var manager: Node = root.get_node_or_null("MusicManager")
	if manager == null:
		_fail("MusicManager autoload missing.")
		return
	manager.call("set_automatic_context_enabled", false)
	if not bool(manager.call("reload_catalog")):
		_fail("Music catalog reload failed: %s" % str(manager.call("get_catalog_error")))
		return

	for context_id: StringName in CONTEXTS:
		if not bool(manager.call("has_context", context_id)):
			_fail("Narrative context missing: %s" % String(context_id))
			return
		var track_id: StringName = TRACK_BY_CONTEXT[String(context_id)] as StringName
		if not bool(manager.call("has_track", track_id)):
			_fail("Narrative track missing: %s" % String(track_id))
			return
		if not bool(manager.call("play_context", context_id, 0.0)):
			_fail("Narrative context failed to play: %s" % String(context_id))
			return
		await process_frame
		if StringName(str(manager.call("get_current_context_id"))) != context_id:
			_fail("Current context mismatch for %s" % String(context_id))
			return
		if StringName(str(manager.call("get_current_track_id"))) != track_id:
			_fail("Current track mismatch for %s" % String(context_id))
			return

	manager.call("stop_music", 0.0, true)
	manager.call("set_automatic_context_enabled", true)
	print("Narrative music pack v01 runtime tests passed.")
	quit(0)


func _init() -> void:
	call_deferred("_run")
