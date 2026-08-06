extends "res://scripts/game/game_party_field_support_runtime.gd"

const PARTY_FOLLOW_AGENT_NAME: String = "PartyFollowNavigationAgent"
const PARTY_FOLLOW_REPATH_SECONDS: float = 0.25
const PARTY_FOLLOW_TARGET_DELTA_PIXELS: float = 24.0
const PARTY_FOLLOW_PATH_DISTANCE_PIXELS: float = 10.0
const PARTY_FOLLOW_AGENT_RADIUS_PIXELS: float = 20.0

var _party_follow_agent: NavigationAgent2D
var _party_follow_last_target: Vector2 = Vector2.INF
var _party_follow_repath_remaining: float = 0.0


func _process_party_follow_navigation(delta: float) -> void:
	if not is_instance_valid(_controllable_ally) or not _controllable_ally is CharacterBody2D:
		_release_external_follow_control()
		return
	var ally_state: CombatantState = _ally_state()
	var should_follow: bool = (
		not is_party_combat_active()
		and _exploration_mode_id == EXPLORATION_MODE_PARTY
		and _ally_current_health() > 0
		and ally_state != null
		and not ally_state.dead
		and is_instance_valid(player)
	)
	if not should_follow:
		_release_external_follow_control()
		return

	_claim_external_follow_control()
	var ally: CharacterBody2D = _controllable_ally as CharacterBody2D
	var distance_to_leader: float = ally.global_position.distance_to(player.global_position)
	if distance_to_leader <= FOLLOW_STOP_DISTANCE_PIXELS:
		_stop_external_follow_motion(ally)
		return

	var agent: NavigationAgent2D = _ensure_party_follow_agent(ally)
	if agent == null:
		_stop_external_follow_motion(ally)
		return
	_party_follow_repath_remaining = maxf(_party_follow_repath_remaining - delta, 0.0)
	if (
		_party_follow_last_target == Vector2.INF
		or _party_follow_last_target.distance_to(player.global_position) >= PARTY_FOLLOW_TARGET_DELTA_PIXELS
		or _party_follow_repath_remaining <= 0.0
	):
		agent.target_position = player.global_position
		_party_follow_last_target = player.global_position
		_party_follow_repath_remaining = PARTY_FOLLOW_REPATH_SECONDS

	var next_position: Vector2 = agent.get_next_path_position()
	var offset: Vector2 = next_position - ally.global_position
	if offset.length_squared() <= 0.001:
		_stop_external_follow_motion(ally)
		return
	var direction: Vector2 = offset.normalized()
	ally.call("set_facing_direction", direction)
	ally.velocity = direction * FOLLOW_SPEED_PIXELS
	ally.move_and_slide()
	_update_follow_stuck_state(ally, delta)
	if _field_follow_stuck_elapsed >= FOLLOW_STUCK_SECONDS * 0.8:
		agent.target_position = player.global_position
		_party_follow_repath_remaining = PARTY_FOLLOW_REPATH_SECONDS


func _claim_external_follow_control() -> void:
	var was_owned: bool = _field_follow_owns_physics
	super._claim_external_follow_control()
	if not was_owned and _field_follow_owns_physics and is_instance_valid(_controllable_ally):
		_ensure_party_follow_agent(_controllable_ally as CharacterBody2D)
		_party_follow_last_target = Vector2.INF
		_party_follow_repath_remaining = 0.0


func _release_external_follow_control() -> void:
	super._release_external_follow_control()
	_party_follow_last_target = Vector2.INF
	_party_follow_repath_remaining = 0.0
	if is_instance_valid(_party_follow_agent):
		_party_follow_agent.target_position = _party_follow_agent.global_position


func _ensure_party_follow_agent(ally: CharacterBody2D) -> NavigationAgent2D:
	if is_instance_valid(_party_follow_agent) and _party_follow_agent.get_parent() == ally:
		return _party_follow_agent
	_party_follow_agent = ally.get_node_or_null(PARTY_FOLLOW_AGENT_NAME) as NavigationAgent2D
	if _party_follow_agent == null:
		_party_follow_agent = NavigationAgent2D.new()
		_party_follow_agent.name = PARTY_FOLLOW_AGENT_NAME
		ally.add_child(_party_follow_agent)
	_party_follow_agent.path_desired_distance = PARTY_FOLLOW_PATH_DISTANCE_PIXELS
	_party_follow_agent.target_desired_distance = FOLLOW_STOP_DISTANCE_PIXELS
	_party_follow_agent.radius = PARTY_FOLLOW_AGENT_RADIUS_PIXELS
	_party_follow_agent.avoidance_enabled = false
	return _party_follow_agent


func get_field_follow_path_for_testing() -> Array[Vector2i]:
	var result: Array[Vector2i] = []
	if not is_instance_valid(_party_follow_agent):
		return result
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return result
	for point: Vector2 in _party_follow_agent.get_current_navigation_path():
		result.append(grid.world_to_cell(point))
	return result


func get_navigation_follow_path_for_testing() -> PackedVector2Array:
	if not is_instance_valid(_party_follow_agent):
		return PackedVector2Array()
	return _party_follow_agent.get_current_navigation_path()
