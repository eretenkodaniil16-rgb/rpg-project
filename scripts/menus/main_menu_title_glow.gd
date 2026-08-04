class_name MainMenuTitleGlow
extends ColorRect

const MIN_WAIT_SECONDS: float = 5.0
const MAX_WAIT_SECONDS: float = 10.0
const FADE_IN_SECONDS: float = 0.82
const HOLD_SECONDS: float = 0.56
const FADE_OUT_SECONDS: float = 1.18
const MAX_INTENSITY: float = 0.58

enum GlowState {
	WAITING,
	FADING_IN,
	HOLDING,
	FADING_OUT,
}

var _rng: RandomNumberGenerator = RandomNumberGenerator.new()
var _reduced_motion: bool = false
var _state: int = GlowState.WAITING
var _state_elapsed: float = 0.0
var _wait_duration: float = MIN_WAIT_SECONDS
var _intensity: float = 0.0
var _shader_material: ShaderMaterial


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_reduced_motion = bool(ProjectSettings.get_setting("accessibility/reduced_motion", false))
	_rng.randomize()
	_shader_material = material as ShaderMaterial
	_schedule_next_pulse()
	_apply_intensity(0.0)
	set_process(_shader_material != null and not _reduced_motion)


func _process(delta: float) -> void:
	_state_elapsed += delta
	match _state:
		GlowState.WAITING:
			_apply_intensity(0.0)
			if _state_elapsed >= _wait_duration:
				_enter_state(GlowState.FADING_IN)
		GlowState.FADING_IN:
			var progress: float = clampf(_state_elapsed / FADE_IN_SECONDS, 0.0, 1.0)
			_apply_intensity(_smoothstep01(progress))
			if progress >= 1.0:
				_enter_state(GlowState.HOLDING)
		GlowState.HOLDING:
			_apply_intensity(1.0)
			if _state_elapsed >= HOLD_SECONDS:
				_enter_state(GlowState.FADING_OUT)
		GlowState.FADING_OUT:
			var progress: float = clampf(_state_elapsed / FADE_OUT_SECONDS, 0.0, 1.0)
			_apply_intensity(1.0 - _smoothstep01(progress))
			if progress >= 1.0:
				_schedule_next_pulse()


func has_glow_material() -> bool:
	return _shader_material != null


func wait_interval_range() -> Vector2:
	return Vector2(MIN_WAIT_SECONDS, MAX_WAIT_SECONDS)


func _schedule_next_pulse() -> void:
	_state = GlowState.WAITING
	_state_elapsed = 0.0
	_wait_duration = _rng.randf_range(MIN_WAIT_SECONDS, MAX_WAIT_SECONDS)
	_apply_intensity(0.0)


func _enter_state(next_state: int) -> void:
	_state = next_state
	_state_elapsed = 0.0


func _apply_intensity(value: float) -> void:
	_intensity = clampf(value, 0.0, 1.0)
	if _shader_material != null:
		_shader_material.set_shader_parameter("intensity", _intensity * MAX_INTENSITY)


func _smoothstep01(value: float) -> float:
	return value * value * (3.0 - 2.0 * value)
