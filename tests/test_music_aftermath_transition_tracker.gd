extends SceneTree

const TRACKER_SCRIPT: Script = preload("res://scripts/audio/music_aftermath_transition_tracker.gd")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var tracker: RefCounted = TRACKER_SCRIPT.new()
	tracker.call("sample", 101, true, false, "")
	if bool(tracker.call("is_pending")):
		_fail("Inactive scene baseline must not emit aftermath.")
		return
	tracker.call("sample", 101, true, true, "encounter_a")
	tracker.call("sample", 101, true, true, "encounter_a")
	if bool(tracker.call("is_pending")):
		_fail("Combat polling must not emit aftermath while combat is active.")
		return
	tracker.call("sample", 101, true, false, "")
	if not bool(tracker.call("is_pending")):
		_fail("True-to-false combat transition must become pending.")
		return
	var transition: Dictionary = tracker.call("consume_transition") as Dictionary
	if str(transition.get("encounter_id", "")) != "encounter_a":
		_fail("Tracker must retain the encounter id captured during combat.")
		return
	if bool(tracker.call("is_pending")):
		_fail("Consumed transition must not repeat.")
		return
	tracker.call("sample", 202, true, false, "")
	if bool(tracker.call("is_pending")):
		_fail("Loading a new inactive scene must establish a silent baseline.")
		return
	tracker.call("sample", 303, true, true, "encounter_loaded")
	tracker.call("sample", 0, false, false, "")
	if bool(tracker.call("is_pending")):
		_fail("Leaving a combat scene must reset without aftermath replay.")
		return
	print("Music aftermath transition tracker tests passed.")
	quit(0)


func _init() -> void:
	call_deferred("_run")
