extends "res://scripts/game/game_party_field_support_runtime.gd"

const PARTY_FOLLOW_AGENT_NAME: String = "PartyFollowNavigationAgent"
const PARTY_FOLLOW_PORTAL_GROUP: StringName = &"party_follow_portals"
const PARTY_FOLLOW_REPATH_SECONDS: float = 0.25
const PARTY_FOLLOW_TARGET_DELTA_PIXELS: float = 24.0
const PARTY_FOLLOW_PATH_DISTANCE_PIXELS: float = 10.0
const PARTY_FOLLOW_TARGET_DISTANCE_PIXELS: float = 32.0
const PARTY_FOLLOW_AGENT_RADIUS_PIXELS: float = 20.0
const PARTY_FOLLOW_PORTAL_REACHED_PIXELS: float = 22.0

var _party_follow_agent: NavigationAgent2D
var _party_follow_last_target: Vector2 = Vector2.INF
var _party_follow_repath_remaining: float = 0.0
var _party_follow_portal_waypoints: PackedVector2Array = PackedVector2Array()
var _party_follow_portal_index: int = 0
var _party_follow_portal_goal: Vector2 = Vector2.INF
var _party_follow_portal_provider_id: int = 0


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
	var agent: NavigationAgent2D = _ensure_party_follow_agent(ally)
	if agent == null:
		_stop_external_follow_motion(ally)
		return

	var follow_target: Dictionary = _resolve_party_follow_target(ally, player)
	if not bool(follow_target.get("reachable", true)):
		_stop_external_follow_motion(ally)
		return
	var desired_target: Vector2 = follow_target.get("target", player.global_position) as Vector2
	_party_follow_repath_remaining = maxf(_party_follow_repath_remaining - delta, 0.0)
	if (
		_party_follow_last_target == Vector2.INF
		or _party_follow_last_target.distance_to(desired_target) >= PARTY_FOLLOW_TARGET_DELTA_PIXELS
	):
		_set_party_follow_target(agent, desired_target)

	var distance_to_leader: float = ally.global_position.distance_to(player.global_position)
	if (
		distance_to_leader <= FOLLOW_STOP_DISTANCE_PIXELS
		and _party_follow_portal_waypoints.is_empty()
		and _follow_line_is_clear(ally, player)
	):
		_stop_external_follow_motion(ally)
		return

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
	if (
		ally.velocity.length_squared() > 0.001
		and ally.get_real_velocity().length() <= 1.0
		and _party_follow_repath_remaining <= 0.0
	):
		_set_party_follow_target(agent, desired_target)


func _claim_external_follow_control() -> void:
	var was_owned: bool = _field_follow_owns_physics
	super._claim_external_follow_control()
	if not was_owned and _field_follow_owns_physics and is_instance_valid(_controllable_ally):
		_ensure_party_follow_agent(_controllable_ally as CharacterBody2D)
		_party_follow_last_target = Vector2.INF
		_party_follow_repath_remaining = 0.0
		_clear_party_follow_portal_route()


func _release_external_follow_control() -> void:
	super._release_external_follow_control()
	_party_follow_last_target = Vector2.INF
	_party_follow_repath_remaining = 0.0
	_clear_party_follow_portal_route()
	if is_instance_valid(_party_follow_agent):
		var parent_actor: Node2D = _party_follow_agent.get_parent() as Node2D
		if parent_actor != null:
			_party_follow_agent.target_position = parent_actor.global_position


func _ensure_party_follow_agent(ally: CharacterBody2D) -> NavigationAgent2D:
	if is_instance_valid(_party_follow_agent) and _party_follow_agent.get_parent() == ally:
		return _party_follow_agent
	_party_follow_agent = ally.get_node_or_null(PARTY_FOLLOW_AGENT_NAME) as NavigationAgent2D
	if _party_follow_agent == null:
		_party_follow_agent = NavigationAgent2D.new()
		_party_follow_agent.name = PARTY_FOLLOW_AGENT_NAME
		ally.add_child(_party_follow_agent)
	_party_follow_agent.path_desired_distance = PARTY_FOLLOW_PATH_DISTANCE_PIXELS
	_party_follow_agent.target_desired_distance = PARTY_FOLLOW_TARGET_DISTANCE_PIXELS
	_party_follow_agent.radius = PARTY_FOLLOW_AGENT_RADIUS_PIXELS
	_party_follow_agent.avoidance_enabled = false
	return _party_follow_agent


func _resolve_party_follow_target(ally: CharacterBody2D, leader: Node2D) -> Dictionary:
	var resolution: Dictionary = _resolve_party_follow_portal(
		ally.global_position,
		leader.global_position
	)
	if not bool(resolution.get("applies", false)):
		_clear_party_follow_portal_route()
		return {
			"reachable": true,
			"target": leader.global_position
		}
	if not bool(resolution.get("reachable", false)):
		_clear_party_follow_portal_route()
		return {
			"reachable": false,
			"target": ally.global_position,
			"reason": str(resolution.get("reason", "portal_blocked"))
		}

	var waypoints: PackedVector2Array = _packed_vector2_array(
		resolution.get("waypoints", PackedVector2Array())
	)
	var provider_id: int = int(resolution.get("provider_id", 0))
	var route_changed: bool = (
		_party_follow_portal_waypoints != waypoints
		or _party_follow_portal_provider_id != provider_id
		or _party_follow_portal_goal == Vector2.INF
		or _party_follow_portal_goal.distance_to(leader.global_position)
			>= PARTY_FOLLOW_TARGET_DELTA_PIXELS
	)
	if route_changed:
		_party_follow_portal_waypoints = waypoints
		_party_follow_portal_index = 0
		_party_follow_portal_goal = leader.global_position
		_party_follow_portal_provider_id = provider_id

	while (
		_party_follow_portal_index < _party_follow_portal_waypoints.size()
		and ally.global_position.distance_to(
			_party_follow_portal_waypoints[_party_follow_portal_index]
		) <= PARTY_FOLLOW_PORTAL_REACHED_PIXELS
	):
		_party_follow_portal_index += 1

	if _party_follow_portal_index < _party_follow_portal_waypoints.size():
		return {
			"reachable": true,
			"target": _party_follow_portal_waypoints[_party_follow_portal_index],
			"using_portal": true
		}
	return {
		"reachable": true,
		"target": leader.global_position,
		"using_portal": true
	}


func _resolve_party_follow_portal(from_global: Vector2, to_global: Vector2) -> Dictionary:
	for provider: Node in get_tree().get_nodes_in_group(PARTY_FOLLOW_PORTAL_GROUP):
		if not is_instance_valid(provider) or not provider.has_method(
			"resolve_party_follow_portal_route"
		):
			continue
		var value: Variant = provider.call(
			"resolve_party_follow_portal_route",
			from_global,
			to_global
		)
		if not value is Dictionary:
			continue
		var resolution: Dictionary = (value as Dictionary).duplicate(true)
		if not bool(resolution.get("applies", false)):
			continue
		resolution["provider_id"] = provider.get_instance_id()
		return resolution
	return {
		"applies": false,
		"reachable": true,
		"waypoints": PackedVector2Array()
	}


func _packed_vector2_array(value: Variant) -> PackedVector2Array:
	if typeof(value) == TYPE_PACKED_VECTOR2_ARRAY:
		return value as PackedVector2Array
	var result := PackedVector2Array()
	if value is Array:
		for point_value: Variant in value as Array:
			if point_value is Vector2:
				result.append(point_value as Vector2)
	return result


func _clear_party_follow_portal_route() -> void:
	_party_follow_portal_waypoints = PackedVector2Array()
	_party_follow_portal_index = 0
	_party_follow_portal_goal = Vector2.INF
	_party_follow_portal_provider_id = 0


func _set_party_follow_target(agent: NavigationAgent2D, target: Vector2) -> void:
	agent.target_position = target
	_party_follow_last_target = target
	_party_follow_repath_remaining = PARTY_FOLLOW_REPATH_SECONDS


func _follow_line_is_clear(ally: CharacterBody2D, leader: Node2D) -> bool:
	var query := PhysicsRayQueryParameters2D.create(ally.global_position, leader.global_position)
	query.collision_mask = ally.collision_mask
	query.collide_with_areas = false
	query.collide_with_bodies = true
	query.exclude = [ally.get_rid(), leader.get_rid()]
	return ally.get_world_2d().direct_space_state.intersect_ray(query).is_empty()


func get_field_follow_path_for_testing() -> Array[Vector2i]:
	var result: Array[Vector2i] = []
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return result
	if is_instance_valid(_party_follow_agent):
		for point: Vector2 in _party_follow_agent.get_current_navigation_path():
			_append_unique_follow_cell(result, grid.world_to_cell(point))
	for waypoint_index: int in range(
		_party_follow_portal_index,
		_party_follow_portal_waypoints.size()
	):
		_append_unique_follow_cell(
			result,
			grid.world_to_cell(_party_follow_portal_waypoints[waypoint_index])
		)
	if is_instance_valid(player):
		_append_unique_follow_cell(result, grid.world_to_cell(player.global_position))
	return result


func _append_unique_follow_cell(cells: Array[Vector2i], cell: Vector2i) -> void:
	if cells.is_empty() or cells[cells.size() - 1] != cell:
		cells.append(cell)


func get_navigation_follow_path_for_testing() -> PackedVector2Array:
	if not is_instance_valid(_party_follow_agent):
		return PackedVector2Array()
	return _party_follow_agent.get_current_navigation_path()
