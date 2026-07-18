extends "res://scripts/game/player.gd"

const GRID_MOVE_REPEAT_SECONDS: float = 0.18
const SOCIAL_TERRAIN_CONTROLLER_SCRIPT: Script = preload("res://scripts/game/combat_social_terrain_controller.gd")

var _facing_direction: Vector2 = Vector2.RIGHT
var _facing_indicator: Polygon2D = null
var _turn_based_mode: bool = false
var _grid_move_cooldown: float = 0.0
var _terrain_class_data: ClassDataSystem = ClassDataSystem.new()


func _ready() -> void:
	super._ready()
	_build_facing_indicator()
	_update_facing_indicator()
	call_deferred("_install_combat_social_terrain_controller")


func _physics_process(delta: float) -> void:
	if not _turn_based_mode:
		_process_exploration_movement(delta)
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


func _process_exploration_movement(delta: float) -> void:
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


func _install_combat_social_terrain_controller() -> void:
	var game: Node = get_parent()
	if game == null or game.get_node_or_null("CombatSocialTerrainController") != null:
		return
	var controller: Node = SOCIAL_TERRAIN_CONTROLLER_SCRIPT.new()
	controller.name = "CombatSocialTerrainController"
	game.add_child(controller)
