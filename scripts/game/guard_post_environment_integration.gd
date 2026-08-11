class_name GuardPostEnvironmentIntegration
extends "res://scripts/game/guard_post_party_visibility.gd"

const ENVIRONMENT_PRESENTATION_SCRIPT: Script = preload(
	"res://scripts/game/environment/guard_post_environment_presentation.gd"
)

var _environment_presentation: GuardPostEnvironmentPresentation
var _environment_visual_ready: bool = false


func _ready() -> void:
	super._ready()
	_environment_presentation = ENVIRONMENT_PRESENTATION_SCRIPT.new() as GuardPostEnvironmentPresentation
	if _environment_presentation == null:
		queue_redraw()
		return
	_environment_presentation.name = "EnvironmentPresentation"
	add_child(_environment_presentation)
	_environment_visual_ready = _environment_presentation.configure(
		self,
		get_test_door(),
		get_inner_gate(),
		get_wall_visibility_overlay_for_testing()
	)
	if not _environment_visual_ready:
		push_warning("Approved environment resources are unavailable; guard post uses legacy visuals.")
		_environment_presentation.queue_free()
		_environment_presentation = null
	queue_redraw()


func get_environment_presentation_for_testing() -> GuardPostEnvironmentPresentation:
	return _environment_presentation


func is_environment_visual_ready_for_testing() -> bool:
	return _environment_visual_ready


func _draw() -> void:
	if not _environment_visual_ready:
		super._draw()
