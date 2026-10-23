extends Control

const PROGRESS_CYCLE_SECONDS: float = 8.0
const REDUCED_MOTION_SETTING: StringName = &"accessibility/reduced_motion"

var _elapsed: float = 0.0

@onready var _loading_progress_bar: Control = %LoadingProgressBar


func _ready() -> void:
	var reduced_motion: bool = bool(ProjectSettings.get_setting(REDUCED_MOTION_SETTING, false))
	if _loading_progress_bar == null or not _loading_progress_bar.has_method("set_progress"):
		set_process(false)
		return

	if reduced_motion:
		_loading_progress_bar.call("set_progress", 72.0)
		set_process(false)
		return

	_loading_progress_bar.call("set_progress", 0.0)
	set_process(true)


func _process(delta: float) -> void:
	_elapsed = fmod(_elapsed + delta, PROGRESS_CYCLE_SECONDS)
	var ratio: float = _elapsed / PROGRESS_CYCLE_SECONDS
	if _loading_progress_bar != null and _loading_progress_bar.has_method("set_progress"):
		_loading_progress_bar.call("set_progress", ratio * 100.0)
