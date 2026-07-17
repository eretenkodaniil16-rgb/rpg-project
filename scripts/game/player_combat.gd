extends "res://scripts/game/player.gd"

var _facing_direction: Vector2 = Vector2.RIGHT
var _facing_indicator: Polygon2D = null


func _ready() -> void:
	super._ready()
	_build_facing_indicator()
	_update_facing_indicator()


func _physics_process(delta: float) -> void:
	super._physics_process(delta)
	if velocity.length_squared() > 1.0:
		set_facing_direction(velocity)


func get_facing_direction() -> Vector2:
	return _facing_direction


func set_facing_direction(direction: Vector2) -> void:
	if direction.length_squared() <= 0.0001:
		return
	_facing_direction = direction.normalized()
	_update_facing_indicator()


func _build_facing_indicator() -> void:
	_facing_indicator = Polygon2D.new()
	_facing_indicator.name = "FacingIndicator"
	_facing_indicator.polygon = PackedVector2Array([
		Vector2(9.0, 0.0),
		Vector2(-5.0, -5.0),
		Vector2(-5.0, 5.0)
	])
	_facing_indicator.color = Color(1.0, 0.86, 0.36, 0.96)
	_facing_indicator.z_index = 3
	add_child(_facing_indicator)


func _update_facing_indicator() -> void:
	if _facing_indicator == null:
		return
	_facing_indicator.position = _facing_direction * 28.0
	_facing_indicator.rotation = _facing_direction.angle()
