class_name SafeWorldStateNpcNavigationController
extends WorldStateNpcNavigationController


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
