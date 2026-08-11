extends "res://scripts/game/game_combat_ai_coordination_v1_runtime.gd"

const COORDINATION_V2_WOUNDED_HEALTH_RATIO: float = 0.50
const COORDINATION_V2_CRITICAL_HEALTH_RATIO: float = 0.25
const COORDINATION_V2_FRONT_OFFSET_PIXELS: float = 58.0
const COORDINATION_V2_REAR_OFFSET_PIXELS: float = 132.0
const COORDINATION_V2_LATERAL_OFFSET_PIXELS: float = 44.0


func _build_squad_plan_context(
	actor: Node,
	actor_id: String,
	profile: Dictionary,
	actor_context: Dictionary
) -> Dictionary:
	var context: Dictionary = super._build_squad_plan_context(
		actor,
		actor_id,
		profile,
		actor_context
	)
	var squad_id: String = str(profile.get("squad_id", ""))
	var members: Array[Node] = _living_squad_members(squad_id, actor)
	var wounded_count: int = 0
	var critical_count: int = 0
	var lowest_health_ratio: float = 1.0
	var wounded_actor_id: String = ""
	var wounded_position: Vector2 = Vector2.ZERO

	for member: Node in members:
		if not is_instance_valid(member):
			continue
		var health_ratio: float = clampf(_actor_health_ratio(member), 0.0, 1.0)
		if health_ratio <= COORDINATION_V2_WOUNDED_HEALTH_RATIO:
			wounded_count += 1
		if health_ratio <= COORDINATION_V2_CRITICAL_HEALTH_RATIO:
			critical_count += 1
		if health_ratio < lowest_health_ratio:
			lowest_health_ratio = health_ratio
			wounded_actor_id = str(member.call("get_actor_id")) if member.has_method("get_actor_id") else member.name.to_snake_case()
			if member is Node2D:
				wounded_position = (member as Node2D).global_position

	var casualty_context: Dictionary = _casualty_ai.get_context(actor_id, squad_id, _turn_system.round_number) if _casualty_ai != null else {}
	var latest_value: Variant = casualty_context.get("latest_casualty", {})
	var latest_casualty: Dictionary = latest_value as Dictionary if latest_value is Dictionary else {}
	var latest_round: int = int(latest_casualty.get("round", -1))
	var recent_casualty: bool = not latest_casualty.is_empty() and latest_round >= _turn_system.round_number

	context["wounded_ally_count"] = wounded_count
	context["critical_ally_count"] = critical_count
	context["lowest_health_ratio"] = lowest_health_ratio
	context["wounded_ally_actor_id"] = wounded_actor_id
	context["wounded_ally_position"] = wounded_position
	context["recent_casualty"] = recent_casualty
	context["latest_casualty_actor_id"] = str(latest_casualty.get("body_actor_id", ""))
	context["latest_casualty_position"] = latest_casualty.get("position", Vector2.ZERO)
	context["casualty_count"] = maxi(
		int(context.get("casualty_count", 0)),
		int(casualty_context.get("casualty_count", 0))
	)
	context["memory_confidence"] = clampf(
		float(actor_context.get("memory_confidence", context.get("memory_confidence", 0.0))),
		0.0,
		1.0
	)

	# Explicit overrides are intentionally accepted by the test-only context
	# builders inherited from v1. Production paths do not provide these keys.
	for key: String in [
		"wounded_ally_count",
		"critical_ally_count",
		"lowest_health_ratio",
		"wounded_ally_actor_id",
		"wounded_ally_position",
		"recent_casualty",
		"latest_casualty_actor_id",
		"latest_casualty_position"
	]:
		if actor_context.has(key):
			context[key] = actor_context[key]
	return context


func _objective_for_advanced_intent(
	actor: Node,
	guard_anchor: Vector2,
	target_position: Vector2,
	intent_id: String
) -> Vector2:
	if actor == null or not actor.has_method("get_actor_id") or not actor is Node2D:
		return super._objective_for_advanced_intent(actor, guard_anchor, target_position, intent_id)
	var actor_id: String = str(actor.call("get_actor_id"))
	var assignment_value: Variant = _squad_assignment_by_actor.get(actor_id, {})
	if not assignment_value is Dictionary:
		return super._objective_for_advanced_intent(actor, guard_anchor, target_position, intent_id)
	var assignment: Dictionary = assignment_value as Dictionary
	var objective_id: String = str(assignment.get("objective", ""))
	if objective_id not in [
		"squad_center",
		"casualty_front",
		"casualty_rear",
		"wounded_front",
		"wounded_rear"
	]:
		return super._objective_for_advanced_intent(actor, guard_anchor, target_position, intent_id)

	var squad_id: String = str(assignment.get("squad_id", ""))
	var plan: Dictionary = _squad_plans.get_active_plan(squad_id) if _squad_plans != null else {}
	var focus_position: Vector2 = guard_anchor
	if plan.get("focus_position", null) is Vector2:
		focus_position = plan.get("focus_position", guard_anchor) as Vector2
	var slot: String = str(assignment.get("slot", "front"))
	var objective: Vector2 = guard_anchor
	match objective_id:
		"squad_center":
			objective = _squad_center_position_v2(squad_id, actor, guard_anchor)
		"casualty_front", "wounded_front":
			objective = _relative_support_position_v2(
				focus_position,
				target_position,
				slot,
				COORDINATION_V2_FRONT_OFFSET_PIXELS,
				true
			)
		"casualty_rear", "wounded_rear":
			objective = _relative_support_position_v2(
				focus_position,
				target_position,
				slot,
				COORDINATION_V2_REAR_OFFSET_PIXELS,
				false
			)
	_squad_objective_by_actor[actor_id] = objective
	return objective


func _squad_center_position_v2(squad_id: String, actor: Node, fallback: Vector2) -> Vector2:
	var members: Array[Node] = _living_squad_members(squad_id, actor)
	var total: Vector2 = Vector2.ZERO
	var count: int = 0
	for member: Node in members:
		if member is Node2D:
			total += (member as Node2D).global_position
			count += 1
	return total / float(count) if count > 0 else fallback


func _relative_support_position_v2(
	anchor: Vector2,
	threat: Vector2,
	slot: String,
	distance_pixels: float,
	front: bool
) -> Vector2:
	var toward_threat: Vector2 = threat - anchor
	if toward_threat.length_squared() <= 0.0001:
		toward_threat = Vector2.RIGHT
	else:
		toward_threat = toward_threat.normalized()
	var lateral: Vector2 = Vector2(-toward_threat.y, toward_threat.x)
	var lateral_sign: float = 0.0
	if slot.contains("left"):
		lateral_sign = -1.0
	elif slot.contains("right"):
		lateral_sign = 1.0
	var forward_sign: float = 1.0 if front else -1.0
	return (
		anchor
		+ toward_threat * distance_pixels * forward_sign
		+ lateral * COORDINATION_V2_LATERAL_OFFSET_PIXELS * lateral_sign
	)


func get_coordination_plan_v2_for_testing(squad_id: String) -> Dictionary:
	return get_coordination_plan_v1_for_testing(squad_id)


func build_coordination_context_v2_for_testing(
	actor: Node,
	target: Node,
	overrides: Dictionary = {}
) -> Dictionary:
	return build_coordination_context_v1_for_testing(actor, target, overrides)


func choose_coordination_intent_v2_for_testing(
	actor: Node,
	target: Node,
	overrides: Dictionary = {}
) -> Dictionary:
	return choose_coordination_intent_v1_for_testing(actor, target, overrides)


func clear_coordination_runtime_v2_for_testing() -> void:
	clear_coordination_runtime_v1_for_testing()