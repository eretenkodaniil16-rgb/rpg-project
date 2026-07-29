extends SceneTree


class TestActor:
	extends Node
	var actor_name: String = "Участник"
	var active: bool = true

	func get_combat_name() -> String:
		return actor_name

	func is_combat_active() -> bool:
		return active

	func get_initiative_modifier() -> int:
		return 0


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var ai := NpcAiSystem.new()
	assert(ai.has_profile("caretaker"))
	assert(ai.has_profile("service_guard"))

	var attack: Dictionary = ai.choose_combat_intent("caretaker", {
		"distance_feet": 5,
		"actor_health_ratio": 1.0,
		"target_visible": true,
		"can_attack": true,
		"can_move": true
	})
	assert(str(attack.get("intent", "")) == NpcAiSystem.INTENT_ATTACK)

	var advance: Dictionary = ai.choose_combat_intent("service_guard", {
		"distance_feet": 30,
		"actor_health_ratio": 1.0,
		"target_visible": true,
		"can_attack": false,
		"can_move": true
	})
	assert(str(advance.get("intent", "")) == NpcAiSystem.INTENT_ADVANCE)

	var retreat: Dictionary = ai.choose_combat_intent("service_guard", {
		"distance_feet": 5,
		"actor_health_ratio": 0.1,
		"target_visible": true,
		"can_attack": true,
		"can_move": true
	})
	assert(str(retreat.get("intent", "")) == NpcAiSystem.INTENT_RETREAT)

	assert(ai.should_join_combat("service_guard", 40, StealthAlertSystem.STATE_INVESTIGATING))
	assert(not ai.should_join_combat("service_guard", 70, StealthAlertSystem.STATE_ALERTED))
	assert(not ai.should_join_combat("caretaker", 5, StealthAlertSystem.STATE_ALERTED))
	assert(not ai.should_join_combat("service_guard", 20, StealthAlertSystem.STATE_CALM))

	var player := TestActor.new()
	player.actor_name = "Герой"
	var first_enemy := TestActor.new()
	first_enemy.actor_name = "Первый"
	var joining_enemy := TestActor.new()
	joining_enemy.actor_name = "Подкрепление"
	root.add_child(player)
	root.add_child(first_enemy)
	root.add_child(joining_enemy)
	var turns := TurnBasedCombatSystemAi.new()
	var overrides: Dictionary = {
		player.get_instance_id(): 15,
		first_enemy.get_instance_id(): 10
	}
	turns.start_combat(player, [first_enemy], 2, overrides)
	assert(turns.active)
	assert(turns.has_combatant(first_enemy))
	assert(not turns.has_combatant(joining_enemy))
	assert(turns.add_combatant(joining_enemy, 1, 20))
	assert(turns.has_combatant(joining_enemy))
	assert(turns.entries[turns.entries.size() - 1].get("node") == joining_enemy)
	assert(not turns.add_combatant(joining_enemy, 1, 20))

	print("NPC AI intent, combat join and deterministic queue tests passed.")
	quit(0)
