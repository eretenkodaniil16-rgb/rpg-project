extends "res://scripts/game/game_combat_ai_runtime.gd"

const MOVEMENT_CONTEXT_DISENGAGED: String = "disengaged"
const MOVEMENT_CONTEXT_FORCED: String = "forced_movement"
const NPC_COMBAT_STEP_SPEED_PIXELS: float = 360.0
const NPC_COMBAT_STEP_MIN_SECONDS: float = 0.16
const NPC_COMBAT_STEP_MAX_SECONDS: float = 0.30

var _player_opportunity_offer_count: int = 0
var _last_opportunity_mover_id: String = ""


func _execute_combat_ai_path(actor: Node2D, path: Array, intent_id: String) -> void:
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return
	var movement_context: Dictionary = _npc_movement_reaction_context(actor, intent_id)
	for value: Variant in path:
		if not value is Vector2i:
			continue
		var cell: Vector2i = value as Vector2i
		var current_cell: Vector2i = grid.world_to_cell(actor.global_position)
		if not _combat_ai_cell_is_available(grid, cell, _occupied_cells(actor)):
			break
		if _combat_ai_transition_is_blocked(grid, current_cell, cell):
			break
		var from_position: Vector2 = actor.global_position
		var to_position: Vector2 = grid.cell_to_world_center(cell)
		if not await _resolve_movement_reactions_before_step(actor, from_position, to_position, movement_context):
			break
		if not is_instance_valid(actor) or not _actor_remains_combat_active(actor):
			break
		if not await _animate_npc_combat_step(actor, to_position):
			break
		if intent_id == NpcCombatAiSystem.INTENT_SEARCH and _combat_ai_can_see_player_from(actor.global_position):
			break


func _animate_npc_combat_step(actor: Node2D, destination: Vector2) -> bool:
	if not is_instance_valid(actor) or not _actor_remains_combat_active(actor):
		return false
	var direction: Vector2 = destination - actor.global_position
	if direction.length_squared() <= 0.0001:
		return true
	if actor.has_method("set_facing_direction"):
		actor.call("set_facing_direction", direction)
	var duration: float = clampf(
		direction.length() / NPC_COMBAT_STEP_SPEED_PIXELS,
		NPC_COMBAT_STEP_MIN_SECONDS,
		NPC_COMBAT_STEP_MAX_SECONDS
	)
	var tween: Tween = create_tween()
	tween.set_trans(Tween.TRANS_SINE)
	tween.set_ease(Tween.EASE_IN_OUT)
	tween.tween_property(actor, "global_position", destination, duration)
	await tween.finished
	if not is_instance_valid(actor) or not _actor_remains_combat_active(actor):
		return false
	actor.global_position = destination
	return true


func _resolve_movement_reactions_before_step(
	actor: Node,
	from_position: Vector2,
	to_position: Vector2,
	movement_context: Dictionary
) -> bool:
	if not is_instance_valid(actor):
		return false
	if bool(movement_context.get(MOVEMENT_CONTEXT_FORCED, false)):
		return true
	if bool(movement_context.get(MOVEMENT_CONTEXT_DISENGAGED, false)):
		return true
	if not _step_leaves_player_reach(from_position, to_position):
		return true
	_player_opportunity_offer_count += 1
	_last_opportunity_mover_id = _actor_id_for_movement_reaction(actor)
	if has_method("offer_player_opportunity_attack_if_triggered"):
		await call("offer_player_opportunity_attack_if_triggered", actor, from_position, to_position)
	return is_instance_valid(actor) and _actor_remains_combat_active(actor)


func _npc_movement_reaction_context(actor: Node, intent_id: String) -> Dictionary:
	var disengaged: bool = false
	if is_instance_valid(actor) and actor.has_method("is_disengaging_for_current_turn"):
		disengaged = bool(actor.call("is_disengaging_for_current_turn"))
	elif is_instance_valid(actor) and actor.has_method("uses_disengage_for_intent"):
		disengaged = bool(actor.call("uses_disengage_for_intent", intent_id))
	return {
		MOVEMENT_CONTEXT_DISENGAGED: disengaged,
		MOVEMENT_CONTEXT_FORCED: false,
		"intent_id": intent_id
	}


func _step_leaves_player_reach(from_position: Vector2, to_position: Vector2) -> bool:
	if not _turn_system.active or not is_instance_valid(player):
		return false
	if not _turn_system.has_reaction(player):
		return false
	if _player_combat_state == null or not _srd_rules.can_take_reaction(_player_combat_state):
		return false
	if _combat_environment != null and not _combat_environment.has_line_of_sight(player.global_position, from_position):
		return false
	var current_distance: int = DistanceSystem.distance_feet(player.global_position, from_position)
	var future_distance: int = DistanceSystem.distance_feet(player.global_position, to_position)
	return current_distance <= DistanceSystem.MELEE_REACH_FEET and future_distance > DistanceSystem.MELEE_REACH_FEET


func _actor_remains_combat_active(actor: Node) -> bool:
	if not is_instance_valid(actor):
		return false
	if actor.has_method("is_body_interactable") and bool(actor.call("is_body_interactable")):
		return false
	return not actor.has_method("is_combat_active") or bool(actor.call("is_combat_active"))


func _actor_id_for_movement_reaction(actor: Node) -> String:
	if is_instance_valid(actor) and actor.has_method("get_actor_id"):
		return str(actor.call("get_actor_id"))
	return actor.name.to_snake_case() if is_instance_valid(actor) else ""


func resolve_movement_reaction_for_testing(
	actor: Node,
	from_position: Vector2,
	to_position: Vector2,
	disengaged: bool = false,
	forced_movement: bool = false
) -> bool:
	return await _resolve_movement_reactions_before_step(actor, from_position, to_position, {
		MOVEMENT_CONTEXT_DISENGAGED: disengaged,
		MOVEMENT_CONTEXT_FORCED: forced_movement
	})


func get_player_opportunity_offer_count_for_testing() -> int:
	return _player_opportunity_offer_count


func get_last_opportunity_mover_id_for_testing() -> String:
	return _last_opportunity_mover_id
