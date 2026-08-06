extends SceneTree


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	await process_frame
	var registry: Node = root.get_node_or_null("CombatOutcomeRegistry")
	if registry == null:
		_fail("CombatOutcomeRegistry autoload was not instantiated.")
		return
	registry.call("clear_all")
	if bool(registry.call("report_outcome", &"unknown", 101, "", {})):
		_fail("Unsupported outcomes must be rejected.")
		return
	if not bool(registry.call("report_outcome", &"scripted_end", 101, "scene_event", {"music_owned_by_scene": true})):
		_fail("Supported scripted outcome was rejected.")
		return
	var preview: Dictionary = registry.call("peek_outcome", 101) as Dictionary
	if str(preview.get("outcome_id", "")) != "scripted_end":
		_fail("Registry did not retain the scripted outcome.")
		return
	var consumed: Dictionary = registry.call("consume_outcome", 101) as Dictionary
	if str(consumed.get("encounter_id", "")) != "scene_event":
		_fail("Registry lost the encounter id.")
		return
	if not (registry.call("consume_outcome", 101) as Dictionary).is_empty():
		_fail("Outcome must be consumed exactly once.")
		return
	print("Combat outcome registry tests passed.")
	quit(0)


func _init() -> void:
	call_deferred("_run")
