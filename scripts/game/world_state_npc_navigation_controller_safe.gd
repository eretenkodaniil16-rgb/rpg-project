class_name SafeWorldStateNpcNavigationController
extends WorldStateNpcNavigationController


func capture_world_state_for_save() -> Dictionary:
	var snapshot: Dictionary = super.capture_world_state_for_save()
	print("WORLD_DOOR_CAPTURE %s" % JSON.stringify(snapshot.get("doors", {})))
	return snapshot


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
	if exact_position_is_valid and actor is Node2D:
		(actor as Node2D).global_position = requested_position


func _restore_doors(doors: Dictionary) -> void:
	print("WORLD_DOOR_RESTORE_INPUT %s" % JSON.stringify(doors))
	for door: Node in get_tree().get_nodes_in_group("stealth_doors"):
		if not is_instance_valid(door) or not door.has_method("get_door_id"):
			continue
		var door_id: String = str(door.call("get_door_id"))
		var value: Variant = doors.get(door_id, {})
		if not value is Dictionary:
			continue
		var desired_state: String = str((value as Dictionary).get("state", "closed"))
		if desired_state not in ["open", "closed", "locked", "blocked", "broken"]:
			desired_state = "closed"
		var before_state: String = str(door.call("get_door_state")) if door.has_method("get_door_state") else ""
		door.set("_door_state", desired_state)
		if is_instance_valid(_state) and _state.has_method("set_stealth_door_state"):
			_state.call("set_stealth_door_state", door_id, desired_state, false)
		if door.has_method("_apply_state"):
			door.call("_apply_state", false)
		var after_state: String = str(door.call("get_door_state")) if door.has_method("get_door_state") else ""
		print("WORLD_DOOR_RESTORE id=%s desired=%s before=%s after=%s" % [door_id, desired_state, before_state, after_state])


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
