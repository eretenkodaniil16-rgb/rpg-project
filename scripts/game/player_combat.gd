extends "res://scripts/game/player.gd"

const GRID_MOVE_REPEAT_SECONDS: float = 0.18

var _facing_direction: Vector2 = Vector2.RIGHT
var _facing_indicator: Polygon2D = null
var _turn_based_mode: bool = false
var _grid_move_cooldown: float = 0.0


func _ready() -> void:
	super._ready()
	_build_facing_indicator()
	_update_facing_indicator()


func _physics_process(delta: float) -> void:
	if not _turn_based_mode:
		super._physics_process(delta)
		if velocity.length_squared() > 1.0:
			set_facing_direction(velocity)
		return

	velocity = Vector2.ZERO
	_grid_move_cooldown = maxf(_grid_move_cooldown - delta, 0.0)
	if GameState.input_locked:
		return
	var keyboard_direction: Vector2 = Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	var direction: Vector2 = keyboard_direction + get_mobile_direction()
	if direction.length_squared() <= 0.04:
		_grid_move_cooldown = 0.0
		return
	if _grid_move_cooldown > 0.0:
		return
	var step := Vector2i(
		int(signf(direction.x)) if absf(direction.x) >= 0.25 else 0,
		int(signf(direction.y)) if absf(direction.y) >= 0.25 else 0
	)
	if step == Vector2i.ZERO:
		return
	set_facing_direction(Vector2(step))
	get_tree().call_group("game_world", "request_combat_move", step)
	_grid_move_cooldown = GRID_MOVE_REPEAT_SECONDS


func set_turn_based_mode(value: bool) -> void:
	_turn_based_mode = value
	_grid_move_cooldown = 0.0
	velocity = Vector2.ZERO
	if value:
		clear_mobile_input()


func is_turn_based_mode() -> bool:
	return _turn_based_mode


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
