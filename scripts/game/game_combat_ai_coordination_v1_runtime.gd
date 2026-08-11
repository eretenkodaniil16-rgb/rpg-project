extends "res://scripts/game/game_advanced_party_tactics_v1_runtime.gd"

# Combat AI Coordination v1 deliberately reuses the already-active squad
# blackboard inherited through game_squad_tactical_plans_runtime.gd.
# This layer only adapts generic party-target context/movement to that system.


func _build_party_tactical_context_v1(
	actor_node: Node2D,
	actor: Node,
	target: Node,
	profile: Dictionary,
	guard_anchor: Vector2,
	perceived_target_position: Vector2,
	target_visible: bool,
	target_memory: Dictionary,
	casualty_observation: Dictionary
) -> Dictionary:
	var context: Dictionary = super._build_party_tactical_context_v1(
		actor_node,
		actor,
		target,
		profile,
		guard_anchor,
		perceived_target_position,
		target_visible,
		target_memory,
		casualty_observation
	)
	return _apply_inherited_squad_plan_to_party_context_v1(
		actor,
		profile,
		context,
		true
	)


func _apply_inherited_squad_plan_to_party_context_v1(
	actor: Node,
	profile: Dictionary,
	context: Dictionary,
	announce: bool
) -> Dictionary:
	if _squad_ai == null or _squad_plans == null:
		return context
	var actor_id: String = actor_id_for_party_tactics_v1(actor)
	var squad_id: String = str(profile.get("squad_id", ""))
	if actor_id.is_empty() or squad_id.is_empty():
		return context

	_reset_reservations_if_new_round()
	var squad_context: Dictionary = _build_squad_plan_context(
		actor,
		actor_id,
		profile,
		context
	)
	var plan: Dictionary = _squad_plans.evaluate_squad_plan(
		squad_id,
		_turn_system.round_number,
		squad_context
	)
	if plan.is_empty():
		_squad_assignment_by_actor.erase(actor_id)
		_squad_objective_by_actor.erase(actor_id)
		context.erase("squad_plan")
		context.erase("squad_plan_assignment")
		context.erase("squad_plan_id")
		context.erase("squad_plan_phase")
		return context

	var actor_ids: Array[String] = []
	var member_ids_value: Variant = squad_context.get("member_ids", [])
	if member_ids_value is Array:
		for member_id_value: Variant in member_ids_value as Array:
			actor_ids.append(str(member_id_value))
	actor_ids.sort()
	var actor_index: int = actor_ids.find(actor_id)
	if actor_index < 0:
		actor_index = 0
	var assignment: Dictionary = _squad_plans.get_actor_assignment(
		squad_id,
		actor_id,
		str(profile.get("role", NpcCombatAiSystem.ROLE_MELEE)),
		actor_index,
		_turn_system.round_number
	)
	if assignment.is_empty():
		return context

	context["squad_plan"] = plan.duplicate(true)
	context["squad_plan_assignment"] = assignment.duplicate(true)
	context["squad_plan_id"] = str(plan.get("plan_id", ""))
	context["squad_plan_phase"] = str(plan.get("phase", ""))
	_squad_assignment_by_actor[actor_id] = assignment.duplicate(true)
	_environment_context_by_actor[actor_id] = context.duplicate(true)
	if announce:
		_announce_squad_plan_if_needed(squad_id, plan, actor)
	return context


func _plan_advanced_party_movement_v1(
	actor_node: Node2D,
	actor: Node,
	target: Node,
	profile: Dictionary,
	guard_anchor: Vector2,
	objective_position: Vector2,
	intent_id: String,
	movement_feet: int
) -> Dictionary:
	_reset_reservations_if_new_round()
	_active_planning_actor_id = actor_id_for_party_tactics_v1(actor)
	var selected: Dictionary = super._plan_advanced_party_movement_v1(
		actor_node,
		actor,
		target,
		profile,
		guard_anchor,
		objective_position,
		intent_id,
		movement_feet
	)
	var planning_actor_id: String = _active_planning_actor_id
	_active_planning_actor_id = ""
	if planning_actor_id.is_empty() or selected.is_empty():
		return selected
	var cell_value: Variant = selected.get("cell", null)
	if not cell_value is Vector2i:
		return selected
	var squad_id: String = str(profile.get("squad_id", ""))
	if squad_id.is_empty():
		return selected
	var reservations_value: Variant = _squad_reserved_cells.get(squad_id, {})
	var reservations: Dictionary = {}
	if reservations_value is Dictionary:
		reservations = (reservations_value as Dictionary).duplicate(true)
	reservations[planning_actor_id] = cell_value
	_squad_reserved_cells[squad_id] = reservations
	return selected


func _execute_party_target_path_v1(
	actor: Node2D,
	target: Node,
	path: Array,
	intent_id: String
) -> void:
	var actor_id: String = actor_id_for_party_tactics_v1(actor)
	var start_position: Vector2 = actor.global_position if actor != null else Vector2.ZERO
	await super._execute_party_target_path_v1(actor, target, path, intent_id)
	if actor_id.is_empty() or _squad_plans == null or not is_instance_valid(actor):
		return
	var assignment: Dictionary = get_squad_assignment_for_testing(actor_id)
	if assignment.is_empty():
		return
	var objective_value: Variant = _squad_objective_by_actor.get(actor_id, null)
	var moved: bool = actor.global_position.distance_to(start_position) >= 8.0
	var reached: bool = false
	if objective_value is Vector2:
		reached = DistanceSystem.distance_feet(
			actor.global_position,
			objective_value as Vector2
		) <= 15
	var stationary_success: bool = intent_id in [
		AdvancedNpcCombatAiSystem.INTENT_CAST_SPELL,
		AdvancedNpcCombatAiSystem.INTENT_TAKE_COVER,
		NpcCombatAiSystem.INTENT_GUARD
	]
	_squad_plans.record_actor_outcome(
		str(assignment.get("squad_id", "")),
		actor_id,
		str(assignment.get("action", "")),
		_turn_system.round_number,
		moved or reached or stationary_success
	)


func get_coordination_plan_v1_for_testing(squad_id: String) -> Dictionary:
	return get_squad_plan_for_testing(squad_id)


func get_coordination_assignment_v1_for_testing(actor_id: String) -> Dictionary:
	return get_squad_assignment_for_testing(actor_id)


func get_coordination_objective_v1_for_testing(actor_id: String) -> Vector2:
	var invalid_position: Vector2 = Vector2(INF, INF)
	var value: Variant = _squad_objective_by_actor.get(actor_id, invalid_position)
	return value as Vector2 if value is Vector2 else invalid_position


func get_coordination_reserved_cells_v1_for_testing(squad_id: String) -> Dictionary:
	var value: Variant = _squad_reserved_cells.get(squad_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func build_coordination_context_v1_for_testing(
	actor: Node,
	target: Node,
	overrides: Dictionary = {}
) -> Dictionary:
	if _squad_ai == null or not actor is Node2D or not target is Node2D:
		return {}
	var actor_id: String = actor_id_for_party_tactics_v1(actor)
	if actor_id.is_empty():
		return {}
	var profile: Dictionary = _squad_ai.get_profile(actor_id)
	if profile.is_empty():
		return {}
	var actor_node: Node2D = actor as Node2D
	var guard_anchor: Vector2 = _ensure_combat_ai_guard_anchor(
		actor_id,
		actor_node.global_position
	)
	var visible: bool = _enemy_can_see_party_target_from(
		actor_node.global_position,
		target
	)
	if visible:
		_record_party_target_sighting_v1(actor, profile, target)
	var memory: Dictionary = _get_party_target_memory_v1(actor, profile)
	var perceived_position: Vector2 = guard_anchor
	if visible:
		perceived_position = (target as Node2D).global_position
	elif memory.get("position", null) is Vector2:
		perceived_position = memory.get("position", guard_anchor) as Vector2
	var context: Dictionary = super._build_party_tactical_context_v1(
		actor_node,
		actor,
		target,
		profile,
		guard_anchor,
		perceived_position,
		visible,
		memory,
		{"new": false}
	)
	context.merge(overrides, true)
	return _apply_inherited_squad_plan_to_party_context_v1(
		actor,
		profile,
		context,
		false
	)


func choose_coordination_intent_v1_for_testing(
	actor: Node,
	target: Node,
	overrides: Dictionary = {}
) -> Dictionary:
	if _squad_ai == null:
		return {}
	var actor_id: String = actor_id_for_party_tactics_v1(actor)
	if actor_id.is_empty():
		return {}
	var context: Dictionary = build_coordination_context_v1_for_testing(
		actor,
		target,
		overrides
	)
	if context.is_empty():
		return {}
	return _squad_ai.choose_combat_intent(actor_id, context)


func clear_coordination_runtime_v1_for_testing() -> void:
	_clear_squad_plan_runtime()
