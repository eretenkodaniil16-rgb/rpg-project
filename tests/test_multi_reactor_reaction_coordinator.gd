extends SceneTree


class TestCaster:
	extends Node2D

	func get_combat_name() -> String:
		return "Маг-источник"


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _casting_context(token: String) -> Dictionary:
	return {
		"can_speak": true,
		"armor_trained": true,
		"free_hands": 1,
		"focus_in_hand": false,
		"has_component_pouch": false,
		"has_required_material": true,
		"turn_token": token
	}


func _make_wizard(name: String) -> PlayerCharacter:
	var wizard := PlayerCharacter.new()
	wizard.character_name = name
	wizard.character_class_id = "wizard"
	wizard.character_class_name = "Волшебник"
	wizard.level = 5
	wizard.maximum_health = 40
	wizard.current_health = 40
	wizard.abilities["intelligence"] = 18
	wizard.base_abilities["intelligence"] = 18
	wizard.starter_loadout_granted = true
	var spellcasting := SpellcastingSystem.new()
	spellcasting.ensure_character(wizard, true)
	var prepared: Dictionary = spellcasting.prepare_spell(wizard, "counterspell")
	if not bool(prepared.get("success", false)):
		return null
	return wizard


func _candidate(
	id: String,
	actor: Node,
	character: PlayerCharacter,
	name: String,
	initiative: int,
	controller: String,
	turn_token: String
) -> ReactionCandidate:
	var candidate := ReactionCandidate.new(id, actor, character)
	candidate.display_name = name
	candidate.team_id = ReactionCandidate.TEAM_PARTY if controller == ReactionCandidate.CONTROLLER_PLAYER else ReactionCandidate.TEAM_HOSTILE
	candidate.controller_id = controller
	candidate.initiative = initiative
	candidate.reaction_available = true
	candidate.can_react = true
	candidate.context_overrides = {
		"can_see_caster": true,
		"distance_feet": 30,
		"casting_context": _casting_context(turn_token)
	}
	return candidate


func _run() -> void:
	var first_wizard: PlayerCharacter = _make_wizard("Первый контрмаг")
	var second_wizard: PlayerCharacter = _make_wizard("Второй контрмаг")
	var enemy_wizard: PlayerCharacter = _make_wizard("Вражеский контрмаг")
	if first_wizard == null or second_wizard == null or enemy_wizard == null:
		_fail("Test Wizards could not prepare Counterspell.")
		return

	var first_actor := Node.new()
	first_actor.name = "FirstAlly"
	var second_actor := Node.new()
	second_actor.name = "SecondAlly"
	var enemy_actor := Node.new()
	enemy_actor.name = "EnemyReactor"
	var caster := TestCaster.new()
	root.add_child(first_actor)
	root.add_child(second_actor)
	root.add_child(enemy_actor)
	root.add_child(caster)

	var spellcasting := SpellcastingSystem.new()
	var burning_hands: Dictionary = spellcasting.get_spell_definition("burning_hands")
	var attempt := SpellCastAttempt.new(burning_hands, caster, 1)
	attempt.caster_constitution_modifier = 0
	attempt.caster_state = CombatantState.new()
	attempt.action_kind = "action"
	attempt.original_resource_key = "enemy_spell_slots_1"

	var coordinator := ReactionCoordinator.new()
	var event: ReactionEvent = coordinator.create_event(
		ReactionOpportunitySystem.TRIGGER_SPELL_CAST_STARTED,
		{
			"attempt": attempt,
			"save_roll_overrides": [1]
		},
		caster,
		first_actor,
		"multi_counterspell"
	)
	var candidates: Array[ReactionCandidate] = [
		_candidate("ally_first", first_actor, first_wizard, "Первый контрмаг", 18, ReactionCandidate.CONTROLLER_PLAYER, "enemy_turn_1"),
		_candidate("ally_second", second_actor, second_wizard, "Второй контрмаг", 12, ReactionCandidate.CONTROLLER_PLAYER, "enemy_turn_1"),
		_candidate("enemy_reactor", enemy_actor, enemy_wizard, "Вражеский контрмаг", 9, ReactionCandidate.CONTROLLER_AI, "enemy_turn_1")
	]
	var options: Array[Dictionary] = coordinator.collect_options(event, candidates)
	if options.size() != 3:
		_fail("Three valid reactors did not produce three Counterspell options.")
		return
	if str(options[0].get("id", "")) != "ally_first::counterspell":
		_fail("Duplicate reaction IDs were not namespaced by the highest-initiative reactor.")
		return
	if str(options[1].get("id", "")) != "ally_second::counterspell":
		_fail("The second allied Counterspell did not receive a stable composite selection ID.")
		return
	if str(options[2].get("id", "")) != "enemy_reactor::counterspell":
		_fail("The hostile Counterspell did not receive a stable composite selection ID.")
		return

	var queue: Array[Dictionary] = coordinator.build_controller_queue(options)
	if queue.size() != 2:
		_fail("Options were not grouped into one player decision and one AI decision.")
		return
	var player_group: Dictionary = queue[0]
	if str(player_group.get("controller_id", "")) != ReactionCandidate.CONTROLLER_PLAYER:
		_fail("The highest-initiative player-controlled reaction group was not first.")
		return
	var player_options: Array = player_group.get("options", []) as Array
	if player_options.size() != 2:
		_fail("Both player-controlled allies were not combined into one common prompt group.")
		return
	var ai_group: Dictionary = queue[1]
	var ai_options: Array[Dictionary] = []
	for value: Variant in ai_group.get("options", []) as Array:
		if value is Dictionary:
			ai_options.append(value as Dictionary)
	if coordinator.choose_ai_selection(ai_options) != "enemy_reactor::counterspell":
		_fail("AI did not choose its highest-priority available reaction deterministically.")
		return

	var first_slots_before: int = first_wizard.get_resource("spell_slots_3")
	var resolution: Dictionary = coordinator.resolve_selection(event, "ally_first::counterspell")
	if not bool(resolution.get("resolved", false)) or not bool(resolution.get("countered", false)):
		_fail("The selected allied Counterspell did not resolve and invalidate the spell event.")
		return
	if str(resolution.get("reactor_id", "")) != "ally_first":
		_fail("Resolution lost the identity of the selected reactor.")
		return
	if first_wizard.get_resource("spell_slots_3") != first_slots_before - 1:
		_fail("The selected reactor did not spend exactly one Counterspell slot.")
		return
	if not event.stop_processing or event.status != ReactionEvent.Status.RESOLVED:
		_fail("A countered spell did not stop the remaining reaction chain.")
		return
	if not coordinator.get_selection_payload(event, "ally_second::counterspell").is_empty():
		_fail("A second reactor remained selectable after the event was invalidated.")
		return
	if event.history.size() < 2:
		_fail("Reaction event history did not record selection and resolution.")
		return

	var opportunity_event: ReactionEvent = coordinator.create_event(
		ReactionOpportunitySystem.TRIGGER_ENEMY_LEAVES_REACH,
		{
			"target_leaves_reach": true,
			"can_make_weapon_attack": true
		},
		caster,
		first_actor,
		"multi_opportunity"
	)
	var martial_candidates: Array[ReactionCandidate] = []
	var first_martial := ReactionCandidate.new("fighter_a", first_actor, null)
	first_martial.display_name = "Воин А"
	first_martial.controller_id = ReactionCandidate.CONTROLLER_PLAYER
	first_martial.initiative = 14
	first_martial.reaction_available = true
	martial_candidates.append(first_martial)
	var second_martial := ReactionCandidate.new("fighter_b", second_actor, null)
	second_martial.display_name = "Воин Б"
	second_martial.controller_id = ReactionCandidate.CONTROLLER_PLAYER
	second_martial.initiative = 11
	second_martial.reaction_available = true
	martial_candidates.append(second_martial)
	var martial_options: Array[Dictionary] = coordinator.collect_options(opportunity_event, martial_candidates)
	if martial_options.size() != 2 or str(martial_options[0].get("id", "")) != "fighter_a::opportunity_attack":
		_fail("Non-spell reactions were not coordinated for multiple martial reactors.")
		return
	var generic_resolution: Dictionary = coordinator.resolve_selection(opportunity_event, "fighter_a::opportunity_attack")
	if str(generic_resolution.get("runtime_action", "")) != ReactionOpportunitySystem.OPTION_OPPORTUNITY_ATTACK:
		_fail("Generic coordinated reaction did not return its runtime action contract.")
		return

	var single_event: ReactionEvent = coordinator.create_event(
		ReactionOpportunitySystem.TRIGGER_ENEMY_LEAVES_REACH,
		{
			"target_leaves_reach": true,
			"can_make_weapon_attack": true
		},
		caster,
		first_actor,
		"single_backward_compatible"
	)
	var single_options: Array[Dictionary] = coordinator.collect_options(single_event, [first_martial])
	if single_options.size() != 1 or str(single_options[0].get("id", "")) != ReactionOpportunitySystem.OPTION_OPPORTUNITY_ATTACK:
		_fail("A single reactor no longer preserved the existing base option ID.")
		return

	print("Multi-reactor coordinator namespaces duplicate options, groups player-controlled allies into one prompt, orders AI deterministically, records history, stops invalidated events, and preserves single-reactor IDs.")
	quit(0)
