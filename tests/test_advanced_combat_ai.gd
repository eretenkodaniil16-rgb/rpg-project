extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var ai := AdvancedNpcCombatAiSystem.new()
	var caster: Dictionary = ai.get_profile("training_mage")
	assert(str(caster.get("role", "")) == AdvancedNpcCombatAiSystem.ROLE_CASTER)
	assert(int(caster.get("friendly_fire_tolerance", -1)) == 0)
	assert("magic_missile" in caster.get("spell_ids", []))

	var rally: Dictionary = ai.choose_combat_intent("caretaker", {
		"distance_feet": 20,
		"actor_health_ratio": 1.0,
		"target_visible": true,
		"has_target_memory": true,
		"memory_confidence": 1.0,
		"can_attack": false,
		"can_move": true,
		"distance_from_guard_anchor_feet": 0,
		"target_distance_from_guard_anchor_feet": 20,
		"ally_count": 2,
		"hostile_count": 1,
		"defeated_ally_count": 1,
		"escape_route_count": 4,
		"new_casualty_seen": true,
		"casualty_count": 1,
		"rally_active": false,
		"can_shove": false,
		"better_cover_available": false,
		"nearest_ally_distance_feet": 15,
		"no_useful_attack": false,
		"no_safe_retreat": false
	})
	assert(str(rally.get("intent", "")) == AdvancedNpcCombatAiSystem.INTENT_RALLY)

	var shove: Dictionary = ai.choose_combat_intent("service_guard", {
		"distance_feet": 5,
		"actor_health_ratio": 1.0,
		"target_visible": true,
		"has_target_memory": true,
		"can_attack": true,
		"can_move": true,
		"ally_count": 1,
		"hostile_count": 1,
		"defeated_ally_count": 0,
		"escape_route_count": 4,
		"new_casualty_seen": false,
		"casualty_count": 0,
		"rally_active": false,
		"can_shove": true,
		"target_prone": false,
		"target_near_hazard": true,
		"better_cover_available": false,
		"nearest_ally_distance_feet": 9999,
		"no_useful_attack": false,
		"no_safe_retreat": false
	})
	assert(str(shove.get("intent", "")) == AdvancedNpcCombatAiSystem.INTENT_SHOVE)

	var cover: Dictionary = ai.choose_combat_intent("training_marksman", {
		"distance_feet": 35,
		"actor_health_ratio": 0.7,
		"target_visible": true,
		"has_target_memory": true,
		"can_attack": true,
		"can_move": true,
		"ally_count": 1,
		"hostile_count": 1,
		"defeated_ally_count": 0,
		"escape_route_count": 4,
		"new_casualty_seen": false,
		"casualty_count": 0,
		"rally_active": false,
		"can_shove": false,
		"better_cover_available": true,
		"nearest_ally_distance_feet": 9999,
		"no_useful_attack": false,
		"no_safe_retreat": false
	})
	assert(str(cover.get("intent", "")) in [NpcAiSystem.INTENT_ATTACK, AdvancedNpcCombatAiSystem.INTENT_TAKE_COVER])

	var caster_spell: Dictionary = ai.choose_combat_intent("training_mage", {
		"distance_feet": 45,
		"actor_health_ratio": 1.0,
		"target_visible": true,
		"has_target_memory": true,
		"can_attack": true,
		"can_move": true,
		"ally_count": 2,
		"hostile_count": 1,
		"defeated_ally_count": 0,
		"escape_route_count": 4,
		"new_casualty_seen": false,
		"casualty_count": 0,
		"rally_active": false,
		"can_shove": false,
		"better_cover_available": false,
		"nearest_ally_distance_feet": 20,
		"no_useful_attack": false,
		"no_safe_retreat": false,
		"spell_plan_score": 126.0
	})
	assert(str(caster_spell.get("intent", "")) == AdvancedNpcCombatAiSystem.INTENT_CAST_SPELL)

	var casualty := NpcCasualtyAwarenessSystem.new()
	var ignored: Dictionary = casualty.observe_body("caretaker", "vault_watch", "corpse_guard", "service_guard", Vector2(10, 20), 2, false, true)
	assert(not bool(ignored.get("new", false)))
	var observed: Dictionary = casualty.observe_body("caretaker", "vault_watch", "corpse_guard", "service_guard", Vector2(10, 20), 2, true, true)
	assert(bool(observed.get("new", false)))
	var repeated: Dictionary = casualty.observe_body("caretaker", "vault_watch", "corpse_guard", "service_guard", Vector2(10, 20), 2, true, true)
	assert(not bool(repeated.get("new", false)))
	var context: Dictionary = casualty.get_context("caretaker", "vault_watch", 2)
	assert(int(context.get("casualty_count", 0)) == 1)
	assert(casualty.rally_squad("vault_watch", 2, 3))
	assert(casualty.is_rally_active("vault_watch", 4))
	assert(not casualty.is_rally_active("vault_watch", 5))

	print("Advanced AI caster role, rally, shove, cover and casualty memory passed.")
	quit(0)
