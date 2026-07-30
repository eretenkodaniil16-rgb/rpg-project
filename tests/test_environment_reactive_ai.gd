extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var events := EnvironmentEventSystem.new()
	var opened: Dictionary = events.report_event(
		EnvironmentEventSystem.EVENT_PASSAGE_OPENED,
		Vector2(100.0, 100.0),
		{"door_id": "test_door", "door_state": "open"},
		1.0,
		60,
		90,
		2
	)
	assert(not opened.is_empty())
	var always_visible := func(_position: Vector2) -> bool: return true
	var perceived: Dictionary = events.latest_perceived_event("caretaker", Vector2(130.0, 100.0), 2, 3, always_visible, 80, 80)
	assert(str(perceived.get("event_id", "")) == str(opened.get("event_id", "")))
	assert(bool(perceived.get("perceived_visually", false)))
	events.acknowledge("caretaker", str(opened.get("event_id", "")))
	assert(events.latest_perceived_event("caretaker", Vector2(130.0, 100.0), 2, 3, always_visible, 80, 80).is_empty())

	var hidden_check := func(_position: Vector2) -> bool: return false
	var broken: Dictionary = events.report_event(
		EnvironmentEventSystem.EVENT_DOOR_BROKEN,
		Vector2(200.0, 100.0),
		{"door_id": "test_door"},
		1.5,
		100,
		90,
		3
	)
	var heard: Dictionary = events.latest_perceived_event("service_guard", Vector2(220.0, 100.0), 3, 3, hidden_check, 80, 100)
	assert(str(heard.get("event_id", "")) == str(broken.get("event_id", "")))
	assert(not bool(heard.get("perceived_visually", false)))
	assert(bool(heard.get("perceived_audibly", false)))

	var ai := EnvironmentReactiveNpcAiSystem.new()
	var common: Dictionary = {
		"distance_feet": 25,
		"actor_health_ratio": 1.0,
		"target_visible": true,
		"has_target_memory": true,
		"memory_confidence": 1.0,
		"can_attack": true,
		"can_move": true,
		"distance_from_guard_anchor_feet": 0,
		"target_distance_from_guard_anchor_feet": 25,
		"ally_count": 2,
		"hostile_count": 1,
		"defeated_ally_count": 0,
		"escape_route_count": 4,
		"new_casualty_seen": false,
		"casualty_count": 0,
		"rally_active": false,
		"can_shove": false,
		"target_prone": false,
		"better_cover_available": true,
		"nearest_ally_distance_feet": 15,
		"no_useful_attack": false,
		"no_safe_retreat": false,
		"environment_relevance": 1.0,
		"environment_passage_relevant": true,
		"environment_cover_compromised": false,
		"actor_in_environment_hazard": false,
		"environment_same_squad": false
	}

	var defender_context: Dictionary = common.duplicate(true)
	defender_context["environment_event"] = {
		"event_id": "passage_1",
		"type": EnvironmentEventSystem.EVENT_PASSAGE_OPENED,
		"position": Vector2(300.0, 100.0),
		"severity": 1.0,
		"distance_feet": 20
	}
	var defender: Dictionary = ai.choose_combat_intent("caretaker", defender_context)
	assert(str(defender.get("intent", "")) == NpcCombatAiSystem.INTENT_INTERCEPT)
	assert(str(defender.get("environment_action", "")) == EnvironmentReactiveNpcAiSystem.ACTION_SECURE_PASSAGE)

	var melee: Dictionary = ai.choose_combat_intent("service_guard", defender_context)
	assert(str(melee.get("intent", "")) == NpcAiSystem.INTENT_ADVANCE)
	assert(str(melee.get("environment_action", "")) == EnvironmentReactiveNpcAiSystem.ACTION_EXPLOIT_OPENING)

	var cover_context: Dictionary = common.duplicate(true)
	cover_context["environment_cover_compromised"] = true
	cover_context["environment_event"] = {
		"event_id": "cover_1",
		"type": EnvironmentEventSystem.EVENT_COVER_DESTROYED,
		"position": Vector2(420.0, 140.0),
		"severity": 1.2,
		"distance_feet": 10
	}
	var marksman: Dictionary = ai.choose_combat_intent("training_marksman", cover_context)
	assert(str(marksman.get("intent", "")) == AdvancedNpcCombatAiSystem.INTENT_TAKE_COVER)
	assert(str(marksman.get("environment_action", "")) == EnvironmentReactiveNpcAiSystem.ACTION_RECOVER_COVER)

	var hazard_context: Dictionary = common.duplicate(true)
	hazard_context["actor_in_environment_hazard"] = true
	hazard_context["spell_plan_score"] = 135.0
	hazard_context["environment_event"] = {
		"event_id": "hazard_1",
		"type": EnvironmentEventSystem.EVENT_HAZARD_ADDED,
		"position": Vector2(500.0, 180.0),
		"severity": 1.7,
		"distance_feet": 0
	}
	var mage: Dictionary = ai.choose_combat_intent("training_mage", hazard_context)
	assert(str(mage.get("intent", "")) == NpcCombatAiSystem.INTENT_REPOSITION)
	assert(str(mage.get("environment_action", "")) == EnvironmentReactiveNpcAiSystem.ACTION_AVOID_HAZARD)

	var environment := CombatEnvironment.new()
	root.add_child(environment)
	await process_frame
	var before_cover: Dictionary = environment.get_cover(Vector2(590.0, 230.0), Vector2(720.0, 230.0))
	assert(int(before_cover.get("bonus", 0)) >= 2)
	assert(environment.destroy_cover_object("low_barricade"))
	var after_cover: Dictionary = environment.get_cover(Vector2(590.0, 230.0), Vector2(720.0, 230.0))
	assert(int(after_cover.get("bonus", 0)) == 0)
	assert(environment.add_hazard("test_fire", Rect2(Vector2(300.0, 300.0), Vector2(96.0, 96.0)), "fire", 1.5, false))
	assert(environment.is_hazardous_position(Vector2(340.0, 340.0)))
	assert(environment.remove_hazard("test_fire"))
	assert(not environment.is_hazardous_position(Vector2(340.0, 340.0)))
	environment.queue_free()
	await process_frame

	print("Environment events, perception, role-specific decisions, dynamic cover and hazards passed.")
	quit(0)
