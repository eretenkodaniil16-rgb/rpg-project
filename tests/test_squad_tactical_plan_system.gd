extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var planner := SquadTacticalPlanSystem.new()

	var rescue: Dictionary = planner.evaluate_squad_plan("rescue_squad", 2, _context({
		"bound_ally_visible": true,
		"ally_count": 3,
		"has_defender": true
	}))
	assert(str(rescue.get("plan_id", "")) == SquadTacticalPlanSystem.PLAN_RESCUE_BOUND_ALLY)
	var rescue_assignment: Dictionary = planner.get_actor_assignment("rescue_squad", "caretaker", "defender", 0, 2)
	assert(str(rescue_assignment.get("action", "")) == "rescue")
	assert(str(rescue_assignment.get("objective", "")) == "bound_ally")

	planner.clear()
	var withdrawal: Dictionary = planner.evaluate_squad_plan("wounded_squad", 4, _context({
		"ally_count": 3,
		"casualty_count": 2,
		"average_health_ratio": 0.28,
		"average_morale": 0.25
	}))
	assert(str(withdrawal.get("plan_id", "")) == SquadTacticalPlanSystem.PLAN_ORDERLY_WITHDRAWAL)
	var rear_guard: Dictionary = planner.get_actor_assignment("wounded_squad", "caretaker", "defender", 0, 4)
	assert(str(rear_guard.get("action", "")) == "rear_guard")

	planner.clear()
	var choke: Dictionary = planner.evaluate_squad_plan("door_squad", 1, _context({
		"passage_relevant": true,
		"has_defender": true,
		"target_visible": true,
		"ally_count": 2
	}))
	assert(str(choke.get("plan_id", "")) == SquadTacticalPlanSystem.PLAN_HOLD_CHOKEPOINT)

	planner.clear()
	var flank_context: Dictionary = _context({
		"ally_count": 4,
		"target_visible": true,
		"has_melee": true,
		"has_ranged": true,
		"has_caster": true,
		"flank_route_count": 3
	})
	var flank: Dictionary = planner.evaluate_squad_plan("mixed_squad", 3, flank_context)
	assert(str(flank.get("plan_id", "")) == SquadTacticalPlanSystem.PLAN_SUPPRESS_AND_FLANK)
	var melee_left: Dictionary = planner.get_actor_assignment("mixed_squad", "guard_a", "melee", 0, 3)
	var melee_right: Dictionary = planner.get_actor_assignment("mixed_squad", "guard_b", "melee", 1, 3)
	assert(str(melee_left.get("slot", "")) != str(melee_right.get("slot", "")))
	var persisted: Dictionary = planner.evaluate_squad_plan("mixed_squad", 4, flank_context)
	assert(str(persisted.get("plan_id", "")) == SquadTacticalPlanSystem.PLAN_SUPPRESS_AND_FLANK)
	assert(str(persisted.get("phase", "")) == "execute")

	planner.clear()
	var search: Dictionary = planner.evaluate_squad_plan("search_squad", 5, _context({
		"ally_count": 3,
		"target_visible": false,
		"has_target_memory": true,
		"has_melee": true,
		"has_ranged": true
	}))
	assert(str(search.get("plan_id", "")) == SquadTacticalPlanSystem.PLAN_SECTOR_SEARCH)
	var search_left: Dictionary = planner.get_actor_assignment("search_squad", "guard_a", "melee", 0, 5)
	var search_right: Dictionary = planner.get_actor_assignment("search_squad", "guard_b", "melee", 1, 5)
	assert(str(search_left.get("slot", "")) != str(search_right.get("slot", "")))

	planner.clear()
	planner.evaluate_squad_plan("failure_squad", 1, flank_context)
	var first_assignment: Dictionary = planner.get_actor_assignment("failure_squad", "training_marksman", "ranged", 0, 1)
	var failed_action: String = str(first_assignment.get("action", ""))
	planner.record_actor_outcome("failure_squad", "training_marksman", failed_action, 1, false)
	planner.record_actor_outcome("failure_squad", "training_marksman", failed_action, 2, false)
	var fallback_assignment: Dictionary = planner.get_actor_assignment("failure_squad", "training_marksman", "ranged", 0, 2)
	assert(str(fallback_assignment.get("action", "")) == "recover_after_failure")
	assert(str(fallback_assignment.get("intent", "")) == "dodge")
	planner.record_actor_outcome("failure_squad", "training_marksman", failed_action, 2, true)
	assert(planner.get_actor_failure_count("failure_squad", "training_marksman", failed_action, 2) == 0)

	print("Squad plan priority, persistence, role slots, sector search and failure memory passed.")
	quit(0)


func _context(overrides: Dictionary) -> Dictionary:
	var result: Dictionary = {
		"ally_count": 2,
		"casualty_count": 0,
		"average_health_ratio": 1.0,
		"average_morale": 0.7,
		"bound_ally_visible": false,
		"passage_relevant": false,
		"target_visible": false,
		"has_target_memory": false,
		"has_melee": true,
		"has_ranged": false,
		"has_defender": false,
		"has_caster": false,
		"flank_route_count": 2,
		"environment_event_id": ""
	}
	result.merge(overrides, true)
	return result
