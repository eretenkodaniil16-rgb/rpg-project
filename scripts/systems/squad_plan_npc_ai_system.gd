class_name SquadPlanNpcAiSystem
extends EnvironmentReactiveNpcAiSystem


func choose_combat_intent(actor_id: String, context: Dictionary) -> Dictionary:
	var baseline: Dictionary = super.choose_combat_intent(actor_id, context)
	var assignment_value: Variant = context.get("squad_plan_assignment", {})
	if not assignment_value is Dictionary:
		return baseline
	var assignment: Dictionary = assignment_value as Dictionary
	if assignment.is_empty():
		return baseline
	var intent_id: String = str(assignment.get("intent", ""))
	if intent_id.is_empty():
		return baseline
	var plan_score: float = float(assignment.get("score", BLOCKED_SCORE))
	var baseline_score: float = float(baseline.get("score", BLOCKED_SCORE))
	var baseline_environment_action: String = str(baseline.get("environment_action", ""))
	if baseline_environment_action == ACTION_AVOID_HAZARD:
		return baseline
	if intent_id == INTENT_CAST_SPELL and float(context.get("spell_plan_score", BLOCKED_SCORE)) <= BLOCKED_SCORE * 0.5:
		intent_id = INTENT_REPOSITION
		plan_score -= 24.0
	if plan_score <= baseline_score + 0.0001:
		return baseline
	var profile: Dictionary = get_profile(actor_id)
	return {
		"intent": intent_id,
		"score": plan_score,
		"role": str(profile.get("role", ROLE_MELEE)),
		"reason": _squad_plan_reason(assignment),
		"attack_range_feet": int(profile.get("attack_range_feet", DistanceSystem.MELEE_REACH_FEET)),
		"minimum_range_feet": int(profile.get("minimum_range_feet", 0)),
		"preferred_range_feet": int(profile.get("preferred_range_feet", DistanceSystem.MELEE_REACH_FEET)),
		"squad_plan_id": str(assignment.get("plan_id", "")),
		"squad_plan_phase": str(assignment.get("plan_phase", "")),
		"squad_plan_action": str(assignment.get("action", "")),
		"squad_plan_objective": str(assignment.get("objective", "")),
		"squad_plan_slot": str(assignment.get("slot", "front")),
		"squad_id": str(assignment.get("squad_id", "")),
		"failure_count": int(assignment.get("failure_count", 0))
	}


func _squad_plan_reason(assignment: Dictionary) -> String:
	var plan_id: String = str(assignment.get("plan_id", ""))
	var phase: String = str(assignment.get("plan_phase", "execute"))
	var action: String = str(assignment.get("action", ""))
	if action == "recover_after_failure":
		return "NPC прекращает повторять неудачный манёвр и выбирает безопасный резервный вариант."
	match plan_id:
		SquadTacticalPlanSystem.PLAN_RESCUE_BOUND_ALLY:
			return "Отряд выполняет многоходовой план освобождения связанного союзника: %s." % phase
		SquadTacticalPlanSystem.PLAN_ORDERLY_WITHDRAWAL:
			return "Отряд организованно отходит, сохраняя прикрытие и линию сдерживания: %s." % phase
		SquadTacticalPlanSystem.PLAN_HOLD_CHOKEPOINT:
			return "Отряд распределяет роли вокруг узкого прохода: %s." % phase
		SquadTacticalPlanSystem.PLAN_SUPPRESS_AND_FLANK:
			return "Одни бойцы удерживают героя под давлением, другие обходят его с фланга: %s." % phase
		SquadTacticalPlanSystem.PLAN_SECTOR_SEARCH:
			return "NPC разделяют область последней известной позиции на сектора поиска: %s." % phase
		SquadTacticalPlanSystem.PLAN_COORDINATED_ASSAULT:
			return "Отряд синхронизирует наступление вместо независимых одиночных действий: %s." % phase
		_:
			return "NPC следует текущему многоходовому плану отряда."
