extends SceneTree


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	await process_frame
	var registry: Node = root.get_node_or_null("CombatMusicProfileRegistry")
	if registry == null:
		_fail("CombatMusicProfileRegistry autoload missing.")
		return
	registry.call("clear_all_for_testing")
	var initial: StringName = StringName(str(registry.call("begin_combat", 101, "training_construct")))
	if initial != &"standard":
		_fail("Existing encounters must start with standard combat music.")
		return
	if not bool(registry.call("request_climax", 101, &"boss_phase_02", "training_construct")):
		_fail("Explicit climax request was rejected.")
		return
	if StringName(str(registry.call("get_profile", 101, "training_construct"))) != &"climax":
		_fail("Climax profile was not stored.")
		return
	var record: Dictionary = registry.call("get_record", 101) as Dictionary
	if int(record.get("sequence", 0)) != 1:
		_fail("Profile sequence must increment exactly once.")
		return
	if not bool(registry.call("request_climax", 101, &"boss_phase_02", "training_construct")):
		_fail("Idempotent climax request failed.")
		return
	record = registry.call("get_record", 101) as Dictionary
	if int(record.get("sequence", 0)) != 1:
		_fail("Repeated climax request must not increment sequence.")
		return
	registry.call("forget_runtime_for_testing")
	var restored: StringName = StringName(str(registry.call("begin_combat", 202, "training_construct")))
	if restored != &"climax":
		_fail("Saved climax profile was not restored.")
		return
	if not bool(registry.call("set_profile", 202, &"scripted", &"cutscene_takeover", "test")):
		_fail("Scripted profile handoff failed.")
		return
	if bool(registry.call("set_profile", 202, &"invalid", &"bad", "test")):
		_fail("Invalid profile must be rejected.")
		return
	registry.call("end_combat", 202, true)
	var fresh: StringName = StringName(str(registry.call("begin_combat", 303, "training_construct")))
	if fresh != &"standard":
		_fail("Completed combat must clear persisted climax state.")
		return
	registry.call("clear_all_for_testing")
	print("Combat music profile registry tests passed.")
	quit(0)


func _init() -> void:
	call_deferred("_run")
