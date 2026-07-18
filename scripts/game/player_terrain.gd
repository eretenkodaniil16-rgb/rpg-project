extends "res://scripts/game/player_combat.gd"

var _terrain_class_data: ClassDataSystem = ClassDataSystem.new()


func _physics_process(delta: float) -> void:
	if is_turn_based_mode():
		super._physics_process(delta)
		return
	if GameState.input_locked:
		velocity = Vector2.ZERO
		return
	var keyboard_direction: Vector2 = Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	var direction: Vector2 = keyboard_direction + get_mobile_direction()
	if direction.length_squared() > 1.0:
		direction = direction.normalized()
	var sample_position: Vector2 = global_position + direction * movement_speed * delta
	var effective_speed: float = get_effective_movement_speed_at(sample_position)
	velocity = direction * effective_speed
	move_and_slide()
	global_position.x = clampf(global_position.x, movement_bounds.position.x, movement_bounds.end.x)
	global_position.y = clampf(global_position.y, movement_bounds.position.y, movement_bounds.end.y)
	GameState.player_position = global_position
	if velocity.length_squared() > 1.0:
		set_facing_direction(velocity)


func get_effective_movement_speed_at(world_position: Vector2) -> float:
	var environment: CombatEnvironment = get_tree().get_first_node_in_group("combat_environment") as CombatEnvironment
	if environment == null:
		return movement_speed
	var difficult: bool = environment.is_difficult_position(world_position) or environment.is_difficult_position(global_position)
	var multiplier: float = _terrain_class_data.exploration_speed_multiplier(GameState.player_character, difficult, false)
	return movement_speed * multiplier


func ignores_nonmagical_difficult_terrain() -> bool:
	return _terrain_class_data.ignores_nonmagical_difficult_terrain(GameState.player_character)
