class_name PlayerControlModes
extends "res://scripts/game/player_combat.gd"

var _party_input_enabled: bool = true


func _process_exploration_movement(delta: float) -> void:
	if GameState.input_locked or not _party_input_enabled:
		velocity = Vector2.ZERO
		return
	var keyboard_direction: Vector2 = Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	var mobile_direction: Vector2 = get_mobile_direction()
	var direction: Vector2 = keyboard_direction + mobile_direction
	if direction.length_squared() > 1.0:
		direction = direction.normalized()
	if direction.length_squared() > 0.04:
		_cancel_exploration_click_path()
		_move_exploration_direction(direction.normalized(), delta)
		return
	# Exploration tap-to-move is intentionally disabled. Outside combat the
	# joystick is the movement control; combat route planning remains handled by
	# GamePlannedCombat._unhandled_input().
	_cancel_exploration_click_path()
	velocity = Vector2.ZERO


func set_party_input_enabled(value: bool) -> void:
	_party_input_enabled = value
	if not value:
		velocity = Vector2.ZERO
		set_mobile_vector(Vector2.ZERO)
		clear_mobile_facing_input()


func is_party_input_enabled() -> bool:
	return _party_input_enabled


func set_exploration_click_path(_world_points: Array[Vector2]) -> void:
	_cancel_exploration_click_path()
