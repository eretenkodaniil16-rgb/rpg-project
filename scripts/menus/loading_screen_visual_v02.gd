class_name LoadingScreenVisualV02
extends CanvasLayer

const REDUCED_MOTION_SETTING: StringName = &"accessibility/reduced_motion"
const PULSE_PERIOD_SECONDS: float = 2.6

@onready var _progress_bar: Control = %LoadingProgressBar
@onready var _progress_label: Label = %ProgressLabel
@onready var _status_label: Label = %LoadingLabel
@onready var _ambient_glow: ColorRect = %AmbientGlow
@onready var _approved_background: Control = %ApprovedBackground

var _elapsed: float = 0.0
var _reduced_motion: bool = false


func _ready() -> void:
	layer = 1000
	_reduced_motion = bool(ProjectSettings.get_setting(REDUCED_MOTION_SETTING, false))
	if _approved_background.has_method("has_background_texture"):
		_approved_background.visible = bool(_approved_background.call("has_background_texture"))
	set_progress(0.0)
	set_process(not _reduced_motion)
	if _reduced_motion:
		_ambient_glow.modulate.a = 0.18


func _process(delta: float) -> void:
	_elapsed = fmod(_elapsed + delta, PULSE_PERIOD_SECONDS)
	var phase: float = _elapsed / PULSE_PERIOD_SECONDS
	var pulse: float = 0.18 + (sin(phase * TAU) * 0.5 + 0.5) * 0.10
	_ambient_glow.modulate.a = pulse


func set_progress(value: float) -> void:
	var clamped: float = clampf(value, 0.0, 100.0)
	if _progress_bar != null and _progress_bar.has_method("set_progress"):
		_progress_bar.call("set_progress", clamped)
	if _progress_label != null:
		_progress_label.text = "%d%%" % roundi(clamped)


func set_status_text(value: String) -> void:
	if _status_label != null:
		_status_label.text = value


func uses_reduced_motion() -> bool:
	return _reduced_motion


func has_runtime_progress_bar() -> bool:
	return _progress_bar != null and _progress_bar.has_method("set_progress")


func has_approved_background() -> bool:
	return (
		_approved_background != null
		and _approved_background.has_method("has_background_texture")
		and bool(_approved_background.call("has_background_texture"))
	)
