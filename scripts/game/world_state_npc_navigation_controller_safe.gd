class_name SafeWorldStateNpcNavigationController
extends WorldStateNpcNavigationController


func get_visibility_render_order_for_testing() -> Dictionary:
	var fog: CanvasItem = get_tree().get_first_node_in_group("player_visibility") as CanvasItem
	var wall_visual: Polygon2D = null
	var room: Node = _game.get_node_or_null("StealthTestRoom") if is_instance_valid(_game) else null
	if room != null:
		var wall: Node = room.get_node_or_null("WestPartitionTop")
		if wall != null:
			for child: Node in wall.get_children():
				if child is Polygon2D:
					wall_visual = child as Polygon2D
					break
	var door_visual: Polygon2D = null
	var doors: Array[Node] = get_tree().get_nodes_in_group("stealth_doors")
	if not doors.is_empty() and is_instance_valid(doors[0]):
		door_visual = doors[0].get_node_or_null("Visual") as Polygon2D
	return {
		"fog_z": fog.z_index if fog != null else -1,
		"wall_z": wall_visual.z_index if wall_visual != null else -1,
		"door_z": door_visual.z_index if door_visual != null else -1
	}


func _restore_actor(actor: Node, state: Dictionary) -> void:
	var requested_position: Vector2 = Vector2.ZERO
	var exact_position_is_valid: bool = false
	if actor is Node2D:
		var actor_node: Node2D = actor as Node2D
		requested_position = _vector_from_value(state.get("position", []), actor_node.global_position)
		var grid: BattleGrid = get_tree().get_first_node_in_group("battle_grid") as BattleGrid
		var environment: CombatEnvironment = get_tree().get_first_node_in_group("combat_environment") as CombatEnvironment
		exact_position_is_valid = (
			grid != null
			and environment != null
			and grid.is_cell_valid(grid.world_to_cell(requested_position))
			and not environment.is_position_blocked(
				requested_position,
				ObstacleAwareNpcNavigationSystem.ACTOR_RADIUS_PIXELS
			)
		)
	super._restore_actor(actor, state)
	# A save file represents a continuous world position, not only a coarse grid
	# cell. Preserve that exact position whenever it is physically valid. The
	# inherited nearest-cell repair remains the fallback for corrupted or legacy
	# coordinates placed inside an obstacle.
	if exact_position_is_valid and actor is Node2D:
		(actor as Node2D).global_position = requested_position


func _repair_invalid_actor_positions() -> void:
	if _navigation == null:
		return
	var environment: CombatEnvironment = get_tree().get_first_node_in_group("combat_environment") as CombatEnvironment
	if environment == null:
		return
	for actor: Node in _persistent_world_actors():
		if not actor is Node2D:
			continue
		if actor.has_method("is_body_being_dragged") and bool(actor.call("is_body_being_dragged")):
			continue
		var actor_node: Node2D = actor as Node2D
		var actor_id: String = _actor_id(actor)
		var previous: Vector2 = _last_valid_positions.get(actor_id, actor_node.global_position) as Vector2
		if environment.is_position_blocked(actor_node.global_position, ObstacleAwareNpcNavigationSystem.ACTOR_RADIUS_PIXELS):
			actor_node.global_position = (
				previous
				if not environment.is_position_blocked(previous, ObstacleAwareNpcNavigationSystem.ACTOR_RADIUS_PIXELS)
				else _navigation.resolve_safe_position(actor_node, actor_node.global_position)
			)
		_last_valid_positions[actor_id] = actor_node.global_position
