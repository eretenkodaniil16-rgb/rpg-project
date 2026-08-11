extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var system := SquadTacticalPlanSystem.new()
	var initial: Dictionary = system.evaluate_squad_plan("test_squad", 1, _combined_arms_context())
	_assert_plan(initial, SquadTacticalPlanSystem.PLAN_SUPPRESS_AND_FLANK, "Initial combined-arms plan")
	if int(initial.get("replan_count", -1)) != 0:
		_fail("Initial plan unexpectedly counted as replan: %s" % JSON.stringify(initial))
		return

	var repeated: Dictionary = system.evaluate_squad_plan("test_squad", 1, _combined_arms_context())
	_assert_plan(repeated, SquadTacticalPlanSystem.PLAN_SUPPRESS_AND_FLANK, "Repeated same-round evaluation")
	if int(repeated.get("replan_count", -1)) != 0:
		_fail("Stable plan thrashed on identical context: %s" % JSON.stringify(repeated))
		return

	var casualty: Dictionary = _combined_arms_context()
	casualty["recent_casualty"] = true
	casualty["casualty_count"] = 1
	casualty["latest_casualty_actor_id"] = "fallen_guard"
	casualty["latest_casualty_position"] = Vector2(420.0, 360.0)
	var regroup: Dictionary = system.evaluate_squad_plan("test_squad", 1, casualty)
	_assert_plan(regroup, SquadTacticalPlanSystem.PLAN_CASUALTY_REGROUP, "Casualty priority interrupt")
	if str(regroup.get("switch_reason", "")) != "priority_interrupt":
		_fail("Casualty did not interrupt through priority: %s" % JSON.stringify(regroup))
		return
	if str(regroup.get("focus_actor_id", "")) != "fallen_guard":
		_fail("Casualty regroup lost stable casualty focus: %s" % JSON.stringify(regroup))
		return

	var wounded: Dictionary = _combined_arms_context()
	wounded["casualty_count"] = 1
	wounded["recent_casualty"] = false
	wounded["wounded_ally_count"] = 1
	wounded["critical_ally_count"] = 1
	wounded["lowest_health_ratio"] = 0.20
	wounded["wounded_ally_actor_id"] = "wounded_marksman"
	wounded["wounded_ally_position"] = Vector2(460.0, 330.0)
	var protect: Dictionary = system.evaluate_squad_plan("test_squad", 2, wounded)
	_assert_plan(protect, SquadTacticalPlanSystem.PLAN_PROTECT_WOUNDED_ALLY, "Critical wounded protection")
	if str(protect.get("focus_actor_id", "")) != "wounded_marksman":
		_fail("Wounded protection did not track the wounded actor: %s" % JSON.stringify(protect))
		return

	var collapse: Dictionary = wounded.duplicate(true)
	collapse["casualty_count"] = 2
	collapse["average_health_ratio"] = 0.30
	var withdrawal: Dictionary = system.evaluate_squad_plan("test_squad", 2, collapse)
	_assert_plan(withdrawal, SquadTacticalPlanSystem.PLAN_ORDERLY_WITHDRAWAL, "Emergency withdrawal")
	if str(withdrawal.get("switch_reason", "")) != "priority_interrupt":
		_fail("Emergency withdrawal did not interrupt lower-priority protection: %s" % JSON.stringify(withdrawal))
		return

	system.clear()
	var visible: Dictionary = _combined_arms_context()
	var assault: Dictionary = system.evaluate_squad_plan("search_squad", 1, visible)
	_assert_plan(assault, SquadTacticalPlanSystem.PLAN_SUPPRESS_AND_FLANK, "Visible target plan")
	var lost: Dictionary = visible.duplicate(true)
	lost["target_visible"] = false
	lost["has_target_memory"] = true
	lost["memory_confidence"] = 0.8
	var search: Dictionary = system.evaluate_squad_plan("search_squad", 1, lost)
	_assert_plan(search, SquadTacticalPlanSystem.PLAN_SECTOR_SEARCH, "Immediate contact-loss search")
	if str(search.get("switch_reason", "")) != "existing_invalid":
		_fail("Lost target did not invalidate offensive plan immediately: %s" % JSON.stringify(search))
		return
	var reacquired: Dictionary = system.evaluate_squad_plan("search_squad", 1, visible)
	_assert_plan(reacquired, SquadTacticalPlanSystem.PLAN_SUPPRESS_AND_FLANK, "Immediate target reacquisition")

	system.clear()
	var simple: Dictionary = _combined_arms_context()
	simple["has_ranged"] = false
	simple["has_caster"] = false
	simple["flank_route_count"] = 0
	var baseline: Dictionary = system.evaluate_squad_plan("hysteresis_squad", 1, simple)
	_assert_plan(baseline, SquadTacticalPlanSystem.PLAN_COORDINATED_ASSAULT, "Baseline assault without combined arms")
	var improved: Dictionary = _combined_arms_context()
	var same_round: Dictionary = system.evaluate_squad_plan("hysteresis_squad", 1, improved)
	_assert_plan(same_round, SquadTacticalPlanSystem.PLAN_COORDINATED_ASSAULT, "Same-round hysteresis")
	var next_round: Dictionary = system.evaluate_squad_plan("hysteresis_squad", 2, improved)
	_assert_plan(next_round, SquadTacticalPlanSystem.PLAN_SUPPRESS_AND_FLANK, "Next-round score-margin replan")
	if str(next_round.get("switch_reason", "")) != "score_margin":
		_fail("Score-margin replan did not record its reason: %s" % JSON.stringify(next_round))
		return

	print("Combat AI Coordination v2 replanning, interrupts, wounded protection, search transitions and hysteresis passed.")
	quit(0)


func _combined_arms_context() -> Dictionary:
	return {
		"ally_count": 4,
		"casualty_count": 0,
		"average_health_ratio": 0.90,
		"average_morale": 0.75,
		"target_visible": true,
		"has_target_memory": true,
		"memory_confidence": 1.0,
		"has_melee": true,
		"has_ranged": true,
		"has_defender": true,
		"has_caster": true,
		"flank_route_count": 2,
		"bound_ally_visible": false,
		"passage_relevant": false,
		"recent_casualty": false,
		"wounded_ally_count": 0,
		"critical_ally_count": 0,
		"lowest_health_ratio": 0.90
	}


func _assert_plan(plan: Dictionary, expected_id: String, label: String) -> void:
	if str(plan.get("plan_id", "")) != expected_id:
		_fail("%s selected wrong plan: %s" % [label, JSON.stringify(plan)])


func _fail(message: String) -> void:
	push_error(message)
	quit(1)