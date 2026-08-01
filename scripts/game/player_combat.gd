extends "res://scripts/game/player.gd"

const GRID_MOVE_REPEAT_SECONDS: float = 0.18
const CLICK_PATH_REACHED_DISTANCE_PIXELS: float = 8.0
const CLICK_PATH_BLOCKED_FRAME_LIMIT: int = 10
const SOCIAL_TERRAIN_CONTROLLER_SCRIPT: Script = preload("res://scripts/game/combat_social_terrain_controller.gd")
const RACIAL_TRAIT_CONTROLLER_SCRIPT: Script = preload("res://scripts/game/racial_trait_controller.gd")

var _facing_direction: Vector2 = Vector2.RIGHT
var _facing_indicator: Polygon2D = null
var _turn_based_mode: bool = false
var _grid_move_cooldown: float = 0.0
var _terrain_class_data: ClassDataSystem = ClassDataSystem.new()
var _origin_feat_data: OriginFeatSystem = OriginFeatSystem.new()
var _mobile_facing_vector: Vector2 = Vector2.ZERO
var _exploration_click_path: Array[Vector2] = []
var _exploration_click_path_index: int = 0
var _click_path_blocked_frames: int = 0


func _ready() -> void:
	super._ready()
	_build_facing_indicator()
	_update_facing_indicator()
	call_deferred("_install_runtime_controllers")


func _physics_process(delta: float) -> void:
	if not _turn_based_mode:
		_process_exploration_movement(delta)
		return
	velocity = Vector2.ZERO
	_grid_move_cooldown = maxf(_grid_move_cooldown - delta, 0.0)
	_apply_mobile_facing_input()
	if GameState.input_locked:
		return
	var keyboard_direction: Vector2 = Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	if keyboard_direction.length_squared() <= 0.04:
		_grid_move_cooldown = 0.0
		return
	if _grid_move_cooldown > 0.0:
		return
	var step := Vector2i(
		int(signf(keyboard_direction.x)) if absf(keyboard_direction.x) >= 0.25 else 0,
		int(signf(keyboard_direction.y)) if absf(keyboard_direction.y) >= 0.25 else 0
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
	_apply_mobile_facing_input()
	var keyboard_direction: Vector2 = Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	if keyboard_direction.length_squared() > 0.04:
		_cancel_exploration_click_path()
		_move_exploration_direction(keyboard_direction.normalized(), delta)
		return
	if _exploration_click_path_index < _exploration_click_path.size():
		_move_along_exploration_click_path(delta)
		return
	velocity = Vector2.ZERO


func _move_exploration_direction(direction: Vector2, delta: float) -> void:
	if direction.length_squared() <= 0.0001:
		velocity = Vector2.ZERO
		return
	var normalized_direction: Vector2 = direction.normalized()
	set_facing_direction(normalized_direction)
	var sample_position: Vector2 = global_position + normalized_direction * movement_speed * delta
	var effective_speed: float = get_effective_movement_speed_at(sample_position)
	velocity = normalized_direction * effective_speed
	move_and_slide()
	_clamp_and_store_player_position()


func _move_along_exploration_click_path(delta: float) -> void:
	while _exploration_click_path_index < _exploration_click_path.size():
		var current_target: Vector2 = _exploration_click_path[_exploration_click_path_index]
		if global_position.distance_to(current_target) > CLICK_PATH_REACHED_DISTANCE_PIXELS:
			break
		_exploration_click_path_index += 1
	if _exploration_click_path_index >= _exploration_click_path.size():
		_cancel_exploration_click_path()
		velocity = Vector2.ZERO
		return
	var target_position: Vector2 = _exploration_click_path[_exploration_click_path_index]
	var direction: Vector2 = target_position - global_position
	if direction.length_squared() <= 0.0001:
		_exploration_click_path_index += 1
		return
	var normalized_direction: Vector2 = direction.normalized()
	set_facing_direction(normalized_direction)
	var sample_position: Vector2 = global_position + normalized_direction * movement_speed * delta
	var effective_speed: float = get_effective_movement_speed_at(sample_position)
	var previous_position: Vector2 = global_position
	velocity = normalized_direction * effective_speed
	move_and_slide()
	_clamp_and_store_player_position()
	if global_position.distance_squared_to(previous_position) <= 0.01:
		_click_path_blocked_frames += 1
		if _click_path_blocked_frames >= CLICK_PATH_BLOCKED_FRAME_LIMIT:
			_cancel_exploration_click_path()
	else:
		_click_path_blocked_frames = 0


func set_exploration_click_path(world_points: Array) -> void:
	var normalized_path: Array[Vector2] = []
	for value: Variant in world_points:
		if value is Vector2:
			normalized_path.append(value as Vector2)
	_exploration_click_path = normalized_path
	_exploration_click_path_index = 0
	_click_path_blocked_frames = 0
	while _exploration_click_path_index < _exploration_click_path.size() and global_position.distance_to(_exploration_click_path[_exploration_click_path_index]) <= CLICK_PATH_REACHED_DISTANCE_PIXELS:
		_exploration_click_path_index += 1


func cancel_exploration_click_path() -> void:
	_cancel_exploration_click_path()


func has_exploration_click_path() -> bool:
	return _exploration_click_path_index < _exploration_click_path.size()


func get_exploration_click_path_for_testing() -> Array[Vector2]:
	var result: Array[Vector2] = []
	for index: int in range(_exploration_click_path_index, _exploration_click_path.size()):
		result.append(_exploration_click_path[index])
	return result


func set_mobile_facing_vector(direction: Vector2) -> void:
	_mobile_facing_vector = direction.limit_length(1.0)
	_apply_mobile_facing_input()


func get_mobile_facing_direction() -> Vector2:
	return _mobile_facing_vector


func clear_mobile_facing_input() -> void:
	_mobile_facing_vector = Vector2.ZERO


func clear_mobile_input() -> void:
	super.clear_mobile_input()
	clear_mobile_facing_input()


func get_effective_movement_speed_at(world_position: Vector2) -> float:
	var character: PlayerCharacter = GameState.player_character
	var racial_multiplier: float = float(maxi(character.base_speed_feet, 0)) / 30.0
	var environment: CombatEnvironment = get_tree().get_first_node_in_group("combat_environment") as CombatEnvironment
	var terrain_multiplier: float = 1.0
	if environment != null:
		var difficult: bool = environment.is_difficult_position(world_position) or environment.is_difficult_position(global_position)
		terrain_multiplier = _terrain_class_data.exploration_speed_multiplier(character, difficult, false)
	var drag_multiplier: float = 1.0
	var game: Node = get_parent()
	if game != null and game.has_method("get_body_drag_speed_multiplier"):
		drag_multiplier = clampf(float(game.call("get_body_drag_speed_multiplier")), 0.1, 1.0)
	return movement_speed * racial_multiplier * terrain_multiplier * drag_multiplier


func ignores_nonmagical_difficult_terrain() -> bool:
	return _terrain_class_data.ignores_nonmagical_difficult_terrain(GameState.player_character)


func get_initiative_proficiency_bonus() -> int:
	return _origin_feat_data.initiative_proficiency_bonus(GameState.player_character)


func on_combat_turn_started() -> void:
	_origin_feat_data.begin_turn(GameState.player_character)


func set_turn_based_mode(value: bool) -> void:
	_turn_based_mode = value
	_grid_move_cooldown = 0.0
	velocity = Vector2.ZERO
	_cancel_exploration_click_path()
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


func _apply_mobile_facing_input() -> void:
	if _mobile_facing_vector.length_squared() > 0.0001:
		set_facing_direction(_mobile_facing_vector)


func _cancel_exploration_click_path() -> void:
	_exploration_click_path.clear()
	_exploration_click_path_index = 0
	_click_path_blocked_frames = 0


func _clamp_and_store_player_position() -> void:
	global_position.x = clampf(global_position.x, movement_bounds.position.x, movement_bounds.end.x)
	global_position.y = clampf(global_position.y, movement_bounds.position.y, movement_bounds.end.y)
	GameState.player_position = global_position


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


func _install_runtime_controllers() -> void:
	var game: Node = get_parent()
	if game == null:
		return
	if game.get_node_or_null("CombatSocialTerrainController") == null:
		var social_controller: Node = SOCIAL_TERRAIN_CONTROLLER_SCRIPT.new()
		social_controller.name = "CombatSocialTerrainController"
		game.add_child(social_controller)
	if game.get_node_or_null("RacialTraitController") == null:
		var racial_controller: Node = RACIAL_TRAIT_CONTROLLER_SCRIPT.new()
		racial_controller.name = "RacialTraitController"
		game.add_child(racial_controller)
