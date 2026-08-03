extends "res://scripts/game/game_guard_post_polish_runtime_core.gd"


func _capture_exploration_combat_candidates(trigger_target: Node) -> Array[Node]:
	var result: Array[Node] = super._capture_exploration_combat_candidates(trigger_target)
	var trigger_actor_id: String = _actor_id(trigger_target)
	var roster: Array[String] = []
	if trigger_actor_id in FIRST_ROOM_PARLEY_ACTOR_IDS:
		roster = FIRST_ROOM_PARLEY_ACTOR_IDS
	elif trigger_actor_id in SECOND_ROOM_ACTOR_IDS:
		roster = SECOND_ROOM_ACTOR_IDS
	for actor_id: String in roster:
		var actor: Node = _find_guard_post_actor(actor_id)
		if not _actor_can_join_encounter_roster(actor) or result.has(actor):
			continue
		result.append(actor)
	return result


func _snap_combatants_to_cells() -> void:
	# World placement is authoritative. Entering initiative changes turn state,
	# hostility and available actions, but it must never relocate an actor.
	# Safety repair belongs to WorldStateNpcNavigationController and runs before
	# combat; grid occupancy may map two distinct world positions to one logical
	# cell until one participant moves naturally on its turn.
	if is_instance_valid(player):
		GameState.player_position = player.global_position


func combat_start_preserves_world_positions_for_testing() -> bool:
	return true
