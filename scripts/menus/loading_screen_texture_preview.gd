class_name LoadingScreenTexturePreview
extends Control

const PREVIEW_CYCLE_SECONDS: float = 8.0
const REDUCED_MOTION_VALUE: float = 72.0

@onready var _progress_bar: LoadingProgressBarV03 = $LoadingProgressBar

var _elapsed: float = 0.0
var _reduced_motion: bool = false


func _ready() -> void:
	_reduced_motion = bool(ProjectSettings.get_setting("accessibility/reduced_motion", false))
	if _reduced_motion:
		_progress_bar.set_progress(REDUCED_MOTION_VALUE)
		set_process(false)


func _process(delta: float) -> void:
	_elapsed = fmod(_elapsed + delta, PREVIEW_CYCLE_SECONDS)
	_progress_bar.set_progress((_elapsed / PREVIEW_CYCLE_SECONDS) * 100.0)


func progress_bar() -> LoadingProgressBarV03:
	return _progress_bar
