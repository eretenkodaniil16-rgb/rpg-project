extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var ai := NpcCombatAiSystem.new()
	assert(not ai.get_role_profile(NpcCombatAiSystem.ROLE_MELEE).is_empty())
	assert(not ai.get_role_profile(NpcCombatAiSystem.ROLE_RANGED).is_empty())
	assert(not ai.get_role_profile(NpcCombatAiSystem.ROLE_DEFENDER).is_empty())

	var caretaker_profile: Dictionary = ai.get_profile("caretaker")
	assert(str(caretaker_profile.get("role", "")) == NpcCombatAiSystem.ROLE_DEFENDER)
	assert(int(caretaker_profile.get("guard_radius_feet", 0)) == 25)
	assert(int(caretaker_profile.get("attack_range_feet", 0)) == 5)

	var guard_profile: Dictionary = ai.get_profile("service_guard")
	assert(str(guard_profile.get("role", "")) == NpcCombatAiSystem.ROLE_MELEE)
	assert(int(guard_profile.get("attack_range_feet", 0)) == 5)

	_expect_intent(ai.choose_role_intent(NpcCombatAiSystem.ROLE_MELEE, {
		"distance_feet": 5,
		"actor_health_ratio": 1.0,
		"target_visible": true,
		"can_attack": true,
		"can_move": true
	}), NpcAiSystem.INTENT_ATTACK, "Melee role should attack in reach.")
	_expect_intent(ai.choose_role_intent(NpcCombatAiSystem.ROLE_MELEE, {
		"distance_feet": 25,
		"actor_health_ratio": 1.0,
		"target_visible": true,
		"can_attack": false,
		"can_move": true
	}), NpcAiSystem.INTENT_ADVANCE, "Melee role should close distance.")
	_expect_intent(ai.choose_role_intent(NpcCombatAiSystem.ROLE_MELEE, {
		"distance_feet": 5,
		"actor_health_ratio": 0.1,
		"target_visible": true,
		"can_attack": true,
		"can_move": true
	}), NpcAiSystem.INTENT_RETREAT, "Wounded melee role should retreat.")

	_expect_intent(ai.choose_role_intent(NpcCombatAiSystem.ROLE_RANGED, {
		"distance_feet": 35,
		"actor_health_ratio": 1.0,
		"target_visible": true,
		"can_attack": true,
		"can_move": true
	}), NpcAiSystem.INTENT_ATTACK, "Ranged role should attack from preferred distance.")
	_expect_intent(ai.choose_role_intent(NpcCombatAiSystem.ROLE_RANGED, {
		"distance_feet": 5,
		"actor_health_ratio": 1.0,
		"target_visible": true,
		"can_attack": true,
		"can_move": true
	}), NpcCombatAiSystem.INTENT_REPOSITION, "Ranged role should create distance when threatened.")
	_expect_intent(ai.choose_role_intent(NpcCombatAiSystem.ROLE_RANGED, {
		"distance_feet": 70,
		"actor_health_ratio": 1.0,
		"target_visible": true,
		"can_attack": false,
		"can_move": true
	}), NpcAiSystem.INTENT_ADVANCE, "Ranged role should enter weapon range.")
	_expect_intent(ai.choose_role_intent(NpcCombatAiSystem.ROLE_RANGED, {
		"distance_feet": 30,
		"actor_health_ratio": 0.1,
		"target_visible": true,
		"can_attack": true,
		"can_move": true
	}), NpcAiSystem.INTENT_RETREAT, "Wounded ranged role should retreat.")

	_expect_intent(ai.choose_role_intent(NpcCombatAiSystem.ROLE_DEFENDER, {
		"distance_feet": 20,
		"actor_health_ratio": 1.0,
		"target_visible": true,
		"can_attack": false,
		"can_move": true,
		"distance_from_guard_anchor_feet": 0,
		"target_distance_from_guard_anchor_feet": 20
	}), NpcCombatAiSystem.INTENT_INTERCEPT, "Defender should intercept inside the guard zone.")
	_expect_intent(ai.choose_role_intent(NpcCombatAiSystem.ROLE_DEFENDER, {
		"distance_feet": 45,
		"actor_health_ratio": 1.0,
		"target_visible": true,
		"can_attack": false,
		"can_move": true,
		"distance_from_guard_anchor_feet": 40,
		"target_distance_from_guard_anchor_feet": 45
	}), NpcCombatAiSystem.INTENT_GUARD, "Defender should return after leaving the pursuit leash.")
	_expect_intent(ai.choose_role_intent(NpcCombatAiSystem.ROLE_DEFENDER, {
		"distance_feet": 5,
		"actor_health_ratio": 1.0,
		"target_visible": true,
		"can_attack": true,
		"can_move": true,
		"distance_from_guard_anchor_feet": 10,
		"target_distance_from_guard_anchor_feet": 10
	}), NpcAiSystem.INTENT_ATTACK, "Defender should attack a target inside the protected zone.")

	var deterministic_context: Dictionary = {
		"distance_feet": 35,
		"actor_health_ratio": 1.0,
		"target_visible": true,
		"can_attack": true,
		"can_move": true
	}
	var first_decision: Dictionary = ai.choose_role_intent(NpcCombatAiSystem.ROLE_RANGED, deterministic_context)
	var second_decision: Dictionary = ai.choose_role_intent(NpcCombatAiSystem.ROLE_RANGED, deterministic_context)
	assert(first_decision == second_decision)

	assert(ai.should_join_combat("service_guard", 40, StealthAlertSystem.STATE_INVESTIGATING))
	assert(not ai.should_join_combat("service_guard", 70, StealthAlertSystem.STATE_ALERTED))
	assert(not ai.should_join_combat("caretaker", 5, StealthAlertSystem.STATE_ALERTED))

	print("Combat AI v1 melee, ranged, defender and reinforcement rules passed.")
	quit(0)


func _expect_intent(decision: Dictionary, expected: String, message: String) -> void:
	var actual: String = str(decision.get("intent", ""))
	if actual != expected:
		push_error("%s Expected %s, got %s. Decision: %s" % [message, expected, actual, JSON.stringify(decision)])
		quit(1)
