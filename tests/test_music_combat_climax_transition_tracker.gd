extends SceneTree

const TRACKER_SCRIPT: Script = preload("res://scripts/audio/music_combat_climax_transition_tracker.gd")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var tracker: RefCounted = TRACKER_SCRIPT.new()
	tracker.call("sample", 101, true, false, &"standard")
	if bool(tracker.call("has_pending")):
		_fail("Inactive baseline must not emit.")
		return
	tracker.call("sample", 101, true, true, &"standard")
	if bool(tracker.call("has_pending")):
		_fail("Standard combat start must remain silent.")
		return
	tracker.call("sample", 101, true, true, &"climax")
	if not bool(tracker.call("has_pending")):
		_fail("Explicit climax request must emit once.")
		return
	if StringName(str(tracker.call("consume_pending"))) != &"climax":
		_fail("Wrong pending climax profile.")
		return
	tracker.call("mark_applied", &"climax")
	tracker.call("sample", 101, true, true, &"climax")
	if bool(tracker.call("has_pending")):
		_fail("Stable climax must not retrigger.")
		return
	tracker.call("sample", 101, true, true, &"scripted")
	if StringName(str(tracker.call("consume_pending"))) != &"scripted":
		_fail("Scripted handoff was not emitted.")
		return
	tracker.call("mark_applied", &"scripted")
	tracker.call("sample", 101, true, true, &"standard")
	if StringName(str(tracker.call("consume_pending"))) != &"standard":
		_fail("Returning to standard profile was not emitted.")
		return
	tracker.call("mark_applied", &"climax")
	tracker.call("sample", 101, true, false, &"standard")
	if StringName(str(tracker.call("consume_pending"))) != &"standard":
		_fail("Combat end must release a non-standard profile.")
		return
	tracker.call("reset")
	tracker.call("sample", 202, true, true, &"climax")
	if StringName(str(tracker.call("consume_pending"))) != &"climax":
		_fail("Loading inside a saved climax phase must restore climax.")
		return
	print("Music combat climax transition tracker tests passed.")
	quit(0)


func _init() -> void:
	call_deferred("_run")
