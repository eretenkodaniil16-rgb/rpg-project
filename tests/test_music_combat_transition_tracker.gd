extends SceneTree

const TRACKER_SCRIPT: Script = preload("res://scripts/audio/music_combat_transition_tracker.gd")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var tracker: RefCounted = TRACKER_SCRIPT.new(3)
	tracker.call("sample", 101, true, false)
	if bool(tracker.call("is_pending")) or not bool(tracker.call("is_armed")):
		_fail("Inactive game scene baseline must arm without emitting.")
		return
	tracker.call("sample", 101, true, true)
	if not bool(tracker.call("is_pending")):
		_fail("False-to-true transition must create one pending cue.")
		return
	tracker.call("mark_emitted")
	tracker.call("sample", 101, true, true)
	if bool(tracker.call("is_pending")):
		_fail("Active combat must not retrigger by turn or round polling.")
		return

	tracker.call("sample", 101, true, false)
	tracker.call("sample", 101, true, true)
	if bool(tracker.call("is_pending")):
		_fail("One transient inactive sample must not rearm the cue.")
		return
	for _index: int in range(3):
		tracker.call("sample", 101, true, false)
	if not bool(tracker.call("is_armed")):
		_fail("Stable combat end must rearm future encounters.")
		return
	tracker.call("sample", 101, true, true)
	if not bool(tracker.call("is_pending")):
		_fail("A later encounter in the same scene must emit once.")
		return

	tracker.call("sample", 202, true, true)
	if bool(tracker.call("is_pending")) or bool(tracker.call("is_armed")):
		_fail("Loading a new scene already inside combat must establish a silent baseline.")
		return
	tracker.call("sample", 0, false, false)
	if bool(tracker.call("is_pending")) or bool(tracker.call("is_armed")):
		_fail("Leaving game scenes must reset transition state.")
		return
	print("Music combat transition tracker tests passed.")
	quit(0)


func _init() -> void:
	call_deferred("_run")
