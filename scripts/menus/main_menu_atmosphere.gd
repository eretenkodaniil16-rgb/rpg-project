class_name MainMenuAtmosphere
extends Control

const PARTICLE_COUNT: int = 28
const MAGIC_CENTER: Vector2 = Vector2(0.385, 0.79)
const LEFT_TORCH_CENTER: Vector2 = Vector2(0.055, 0.765)
const RIGHT_TORCH_CENTER: Vector2 = Vector2(0.842, 0.765)

var _elapsed: float = 0.0
var _particles: Array[Dictionary] = []
var _rng: RandomNumberGenerator = RandomNumberGenerator.new()
var _reduced_motion: bool = false


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_rng.seed = 0x5EED_BA57
	_reduced_motion = bool(ProjectSettings.get_setting("accessibility/reduced_motion", false))
	_build_particles()
	set_process(not _reduced_motion)
	queue_redraw()


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		queue_redraw()


func _process(delta: float) -> void:
	_elapsed += delta
	for particle: Dictionary in _particles:
		var position: Vector2 = particle["position"]
		var speed: float = float(particle["speed"])
		var frequency: float = float(particle["frequency"])
		var phase: float = float(particle["phase"])
		var amplitude: float = float(particle["amplitude"])
		position.y -= speed * delta
		position.x += sin(_elapsed * frequency + phase) * amplitude * delta
		if position.y < -0.04 or position.x < -0.06 or position.x > 1.06:
			_reset_particle(particle, true)
		else:
			particle["position"] = position
	queue_redraw()


func set_reduced_motion(enabled: bool) -> void:
	_reduced_motion = enabled
	if _reduced_motion:
		_elapsed = 0.0
	set_process(not _reduced_motion)
	queue_redraw()


func is_reduced_motion_enabled() -> bool:
	return _reduced_motion


func _draw() -> void:
	var viewport_size: Vector2 = size
	if viewport_size.x <= 1.0 or viewport_size.y <= 1.0:
		return

	var magic_center: Vector2 = MAGIC_CENTER * viewport_size
	var magic_pulse: float = 0.5 + 0.5 * sin(_elapsed * 1.65)
	var slow_pulse: float = 0.5 + 0.5 * sin(_elapsed * 0.73 + 0.9)
	var base_radius: float = viewport_size.y * (0.068 + magic_pulse * 0.006)
	draw_circle(magic_center, base_radius * 1.75, Color(0.04, 0.38, 0.95, 0.022 + magic_pulse * 0.018))
	draw_circle(magic_center, base_radius * 1.18, Color(0.05, 0.62, 1.0, 0.035 + magic_pulse * 0.025))
	draw_circle(magic_center, base_radius * 0.58, Color(0.18, 0.82, 1.0, 0.045 + slow_pulse * 0.04))

	var beam_width: float = viewport_size.x * (0.011 + magic_pulse * 0.0025)
	var beam_top: float = viewport_size.y * 0.11
	var beam_bottom: float = magic_center.y
	var beam_points := PackedVector2Array([
		Vector2(magic_center.x - beam_width * 0.35, beam_top),
		Vector2(magic_center.x + beam_width * 0.35, beam_top),
		Vector2(magic_center.x + beam_width, beam_bottom),
		Vector2(magic_center.x - beam_width, beam_bottom),
	])
	draw_colored_polygon(beam_points, Color(0.08, 0.56, 1.0, 0.018 + magic_pulse * 0.025))

	_draw_torch_glow(LEFT_TORCH_CENTER * viewport_size, viewport_size.y * 0.073, 0.0)
	_draw_torch_glow(RIGHT_TORCH_CENTER * viewport_size, viewport_size.y * 0.073, 1.7)
	_draw_particles(viewport_size)


func _draw_torch_glow(center: Vector2, radius: float, phase: float) -> void:
	var flicker: float = 0.5 + 0.5 * sin(_elapsed * 5.1 + phase)
	var secondary: float = 0.5 + 0.5 * sin(_elapsed * 8.7 + phase * 1.8)
	var combined: float = flicker * 0.65 + secondary * 0.35
	draw_circle(center, radius * (1.0 + combined * 0.08), Color(1.0, 0.33, 0.035, 0.018 + combined * 0.018))
	draw_circle(center, radius * 0.48, Color(1.0, 0.57, 0.11, 0.025 + combined * 0.025))


func _draw_particles(viewport_size: Vector2) -> void:
	for particle: Dictionary in _particles:
		var position: Vector2 = particle["position"] * viewport_size
		var radius: float = float(particle["radius"]) * viewport_size.y
		var alpha: float = float(particle["alpha"])
		var phase: float = float(particle["phase"])
		var shimmer: float = 0.72 + 0.28 * sin(_elapsed * 1.8 + phase)
		if bool(particle["magic"]):
			draw_circle(position, radius, Color(0.16, 0.72, 1.0, alpha * shimmer))
		else:
			draw_circle(position, radius, Color(0.72, 0.67, 0.58, alpha * 0.45 * shimmer))


func _build_particles() -> void:
	_particles.clear()
	for index: int in range(PARTICLE_COUNT):
		var particle: Dictionary = {
			"magic": index < 11,
			"position": Vector2.ZERO,
			"speed": 0.0,
			"frequency": 0.0,
			"phase": 0.0,
			"amplitude": 0.0,
			"radius": 0.0,
			"alpha": 0.0,
		}
		_reset_particle(particle, false)
		_particles.append(particle)


func _reset_particle(particle: Dictionary, at_bottom: bool) -> void:
	var magic: bool = bool(particle["magic"])
	if magic:
		particle["position"] = Vector2(
			_rng.randf_range(0.30, 0.47),
			_rng.randf_range(0.79, 0.94) if at_bottom else _rng.randf_range(0.42, 0.94)
		)
		particle["speed"] = _rng.randf_range(0.018, 0.045)
		particle["radius"] = _rng.randf_range(0.0013, 0.0027)
		particle["alpha"] = _rng.randf_range(0.10, 0.28)
	else:
		particle["position"] = Vector2(
			_rng.randf_range(0.03, 0.97),
			_rng.randf_range(0.92, 1.04) if at_bottom else _rng.randf_range(0.08, 1.0)
		)
		particle["speed"] = _rng.randf_range(0.006, 0.019)
		particle["radius"] = _rng.randf_range(0.0007, 0.0018)
		particle["alpha"] = _rng.randf_range(0.05, 0.14)
	particle["frequency"] = _rng.randf_range(0.55, 1.6)
	particle["phase"] = _rng.randf_range(0.0, TAU)
	particle["amplitude"] = _rng.randf_range(0.0012, 0.0045)
