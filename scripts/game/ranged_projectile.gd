class_name RangedProjectile
extends Node2D

var _style: String = "arrow"
var _accent: Color = Color(1.0, 0.78, 0.3, 1.0)
var _spin_speed: float = 0.0


func _ready() -> void:
	z_index = 40
	set_process(true)


func configure(style: String, accent: Color) -> void:
	_style = style
	_accent = accent
	_spin_speed = 8.0 if style == "magic" else 0.0
	queue_redraw()


func fly(start_position: Vector2, target_position: Vector2, hit: bool = true) -> void:
	global_position = start_position
	var direction: Vector2 = target_position - start_position
	if direction == Vector2.ZERO:
		direction = Vector2.RIGHT
	var destination: Vector2 = target_position
	if not hit:
		var perpendicular := Vector2(-direction.y, direction.x).normalized()
		destination += perpendicular * 28.0
	rotation = direction.angle()
	queue_redraw()

	var duration: float = clampf(start_position.distance_to(destination) / 1050.0, 0.16, 0.48)
	var tween: Tween = create_tween().set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	if _style == "magic":
		tween.parallel().tween_property(self, "scale", Vector2(1.3, 1.3), duration * 0.7)
	tween.tween_property(self, "global_position", destination, duration)
	await tween.finished

	var impact: Tween = create_tween().set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	impact.tween_property(self, "scale", Vector2(0.2, 0.2), 0.07)
	impact.parallel().tween_property(self, "modulate:a", 0.0, 0.07)
	await impact.finished
	queue_free()


func _process(delta: float) -> void:
	if _spin_speed != 0.0:
		rotation += _spin_speed * delta
		queue_redraw()


func _draw() -> void:
	match _style:
		"magic":
			draw_line(Vector2(-30, 0), Vector2(-8, 0), Color(_accent, 0.22), 8.0, true)
			draw_circle(Vector2.ZERO, 11.0, Color(_accent, 0.24))
			draw_circle(Vector2.ZERO, 7.0, _accent)
			draw_circle(Vector2(-2, -2), 2.8, Color(1.0, 1.0, 1.0, 0.95))
			draw_arc(Vector2.ZERO, 14.0, 0.0, TAU, 24, Color(_accent, 0.72), 2.0, true)
		"thrown":
			draw_line(Vector2(-15, 0), Vector2(13, 0), Color(0.72, 0.76, 0.8, 1.0), 5.0, true)
			draw_colored_polygon(PackedVector2Array([Vector2(16, 0), Vector2(7, -8), Vector2(7, 8)]), _accent)
			draw_line(Vector2(-12, -7), Vector2(-12, 7), Color(0.55, 0.32, 0.16, 1.0), 4.0, true)
		_:
			draw_line(Vector2(-20, 0), Vector2(15, 0), Color(0.68, 0.42, 0.2, 1.0), 4.0, true)
			draw_colored_polygon(PackedVector2Array([Vector2(20, 0), Vector2(10, -6), Vector2(10, 6)]), Color(0.82, 0.86, 0.9, 1.0))
			draw_line(Vector2(-18, 0), Vector2(-25, -7), _accent, 3.0, true)
			draw_line(Vector2(-18, 0), Vector2(-25, 7), _accent, 3.0, true)
