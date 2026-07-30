extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var ai := NpcCombatAiSystem.new()
	var melee_profile: Dictionary = ai.get_role_profile(NpcCombatAiSystem.ROLE_MELEE)
	var ranged_profile: Dictionary = ai.get_role_profile(NpcCombatAiSystem.ROLE_RANGED)
	var defender_profile: Dictionary = ai.get_role_profile(NpcCombatAiSystem.ROLE_DEFENDER)
	assert(int(melee_profile.get("memory_rounds", 0)) >= 2)
	assert(bool(ranged_profile.get("shares_target_information", false)))
	assert(float(defender_profile.get("morale", 0.0)) > float(ranged_profile.get("morale", 0.0)))

	_expect_intent(ai.choose_role_intent(NpcCombatAiSystem.ROLE_MELEE, {
		"distance_feet": 25,
		"actor_health_ratio": 1.0,
		"target_visible": false,
		"has_target_memory": false,
		"can_attack": false,
		"can_move": true
	}), NpcAiSystem.INTENT_WAIT, "Melee AI must not know the exact location of a lost target.")

	_expect_intent(ai.choose_role_intent(NpcCombatAiSystem.ROLE_MELEE, {
		"distance_feet": 25,
		"actor_health_ratio": 1.0,
		"target_visible": false,
		"has_target_memory": true,
		"memory_confidence": 0.75,
		"can_attack": false,
		"can_move": true
	}), NpcCombatAiSystem.INTENT_SEARCH, "Melee AI should search a recent last-known position.")

	_expect_intent(ai.choose_role_intent(NpcCombatAiSystem.ROLE_RANGED, {
		"distance_feet": 30,
		"actor_health_ratio": 0.4,
		"target_visible": true,
		"has_target_memory": true,
		"can_attack": true,
		"can_move": true,
		"ally_count": 1,
		"hostile_count": 4,
		"defeated_ally_count": 2,
		"escape_route_count": 0
	}), NpcAiSystem.INTENT_RETREAT, "A wounded and isolated ranged unit should fail morale.")

	_expect_intent(ai.choose_role_intent(NpcCombatAiSystem.ROLE_DEFENDER, {
		"distance_feet": 20,
		"actor_health_ratio": 1.0,
		"target_visible": false,
		"has_target_memory": true,
		"memory_confidence": 0.8,
		"can_attack": false,
		"can_move": true,
		"distance_from_guard_anchor_feet": 40,
		"target_distance_from_guard_anchor_feet": 20
	}), NpcCombatAiSystem.INTENT_GUARD, "A defender outside its leash must return before searching.")

	var safe_ranged_candidate: Dictionary = {
		"valid": true,
		"distance_feet": 35,
		"distance_to_objective_feet": 35,
		"distance_from_guard_anchor_feet": 0,
		"nearest_ally_distance_feet": 20,
		"mobility": 6,
		"path_cost_feet": 10,
		"target_visible": true,
		"attack_ready": true
	}
	var crowded_ranged_candidate: Dictionary = safe_ranged_candidate.duplicate(true)
	crowded_ranged_candidate["distance_feet"] = 10
	crowded_ranged_candidate["nearest_ally_distance_feet"] = 5
	crowded_ranged_candidate["attack_ready"] = true
	var safe_score: float = ai.score_candidate_position(NpcCombatAiSystem.INTENT_REPOSITION, ranged_profile, {}, safe_ranged_candidate)
	var crowded_score: float = ai.score_candidate_position(NpcCombatAiSystem.INTENT_REPOSITION, ranged_profile, {}, crowded_ranged_candidate)
	assert(safe_score > crowded_score)

	var legal_defender_candidate: Dictionary = {
		"valid": true,
		"distance_feet": 5,
		"distance_to_objective_feet": 5,
		"distance_from_guard_anchor_feet": 25,
		"nearest_ally_distance_feet": 15,
		"mobility": 4,
		"path_cost_feet": 15,
		"target_visible": true,
		"attack_ready": true
	}
	var illegal_defender_candidate: Dictionary = legal_defender_candidate.duplicate(true)
	illegal_defender_candidate["distance_from_guard_anchor_feet"] = 40
	assert(ai.score_candidate_position(NpcCombatAiSystem.INTENT_INTERCEPT, defender_profile, {}, legal_defender_candidate) > NpcCombatAiSystem.BLOCKED_SCORE)
	assert(ai.score_candidate_position(NpcCombatAiSystem.INTENT_INTERCEPT, defender_profile, {}, illegal_defender_candidate) == NpcCombatAiSystem.BLOCKED_SCORE)

	var marksman_profile: Dictionary = ai.get_profile("training_marksman")
	assert(str(marksman_profile.get("role", "")) == NpcCombatAiSystem.ROLE_RANGED)
	assert(str(marksman_profile.get("squad_id", "")) == "vault_watch")
	assert(int(marksman_profile.get("attack_range_feet", 0)) == 60)

	print("Combat AI tactical memory, morale and position scoring tests passed.")
	quit(0)


func _expect_intent(decision: Dictionary, expected: String, message: String) -> void:
	var actual: String = str(decision.get("intent", ""))
	if actual != expected:
		push_error("%s Expected %s, got %s. Decision: %s" % [message, expected, actual, JSON.stringify(decision)])
		quit(1)
