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


func _make_wizard(name: String, prepared_spell_id: String) -> PlayerCharacter:
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
	var prepared: Dictionary = spellcasting.prepare_spell(wizard, prepared_spell_id)
	if not bool(prepared.get("success", false)):
		return null
	return wizard


func _counterspell_candidate(
	id: String,
	actor: Node,
	character: PlayerCharacter,
	initiative: int,
	save_override: int
) -> ReactionCandidate:
	var candidate := ReactionCandidate.new(id, actor, character)
	candidate.display_name = character.character_name
	candidate.team_id = ReactionCandidate.TEAM_PARTY
	candidate.controller_id = ReactionCandidate.CONTROLLER_PLAYER
	candidate.initiative = initiative
	candidate.reaction_available = true
	candidate.can_react = true
	candidate.context_overrides = {
		"can_see_caster": true,
		"distance_feet": 30,
		"casting_context": _casting_context("enemy_turn"),
		"save_roll_overrides": [save_override]
	}
	return candidate


func _run() -> void:
	var first_wizard: PlayerCharacter = _make_wizard("Первый контрмаг", "counterspell")
	var second_wizard: PlayerCharacter = _make_wizard("Второй контрмаг", "counterspell")
	if first_wizard == null or second_wizard == null:
		_fail("Test Wizards could not prepare Counterspell.")
		return

	var first_actor := Node.new()
	var second_actor := Node.new()
	var caster := TestCaster.new()
	root.add_child(first_actor)
	root.add_child(second_actor)
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
			"eligible_reactor_team_ids": [ReactionCandidate.TEAM_PARTY]
		},
		caster,
		first_actor,
		"sequential_counterspells"
	)
	var candidates: Array[ReactionCandidate] = [
		_counterspell_candidate("first", first_actor, first_wizard, 18, 20),
		_counterspell_candidate("second", second_actor, second_wizard, 12, 1)
	]
	var first_options: Array[Dictionary] = coordinator.collect_options(event, candidates)
	if first_options.size() != 2:
		_fail("Two allied Counterspells were not offered for the same event.")
		return
	var first_slots_before: int = first_wizard.get_resource("spell_slots_3")
	var first_result: Dictionary = coordinator.resolve_selection(event, "first::counterspell")
	if not bool(first_result.get("resolved", false)) or bool(first_result.get("countered", true)):
		_fail("The first Counterspell did not resolve as an unsuccessful interruption.")
		return
	if first_wizard.get_resource("spell_slots_3") != first_slots_before - 1:
		_fail("The first failed Counterspell did not spend its own slot.")
		return
	if event.stop_processing or not coordinator.should_continue(event):
		_fail("A failed Counterspell incorrectly stopped the reaction event.")
		return

	var remaining_options: Array[Dictionary] = coordinator.collect_options(event, candidates)
	if remaining_options.size() != 1 or str(remaining_options[0].get("reactor_id", "")) != "second":
		_fail("The second ally was not offered Counterspell after the first ally failed.")
		return
	var second_slots_before: int = second_wizard.get_resource("spell_slots_3")
	var second_selection_id: String = str(remaining_options[0].get("id", ""))
	var second_result: Dictionary = coordinator.resolve_selection(event, second_selection_id)
	if not bool(second_result.get("countered", false)) or not event.stop_processing:
		_fail("The second Counterspell did not stop the original spell event.")
		return
	if second_wizard.get_resource("spell_slots_3") != second_slots_before - 1:
		_fail("The second Counterspell did not spend the selected ally's slot.")
		return

	var shield_wizard_a: PlayerCharacter = _make_wizard("Цель Щита", "shield_spell")
	var shield_wizard_b: PlayerCharacter = _make_wizard("Союзник", "shield_spell")
	if shield_wizard_a == null or shield_wizard_b == null:
		_fail("Test Wizards could not prepare Shield.")
		return
	var shield_actor_a := Node.new()
	var shield_actor_b := Node.new()
	root.add_child(shield_actor_a)
	root.add_child(shield_actor_b)
	var shield_candidate_a := ReactionCandidate.new("shield_target", shield_actor_a, shield_wizard_a)
	shield_candidate_a.display_name = shield_wizard_a.character_name
	shield_candidate_a.team_id = ReactionCandidate.TEAM_PARTY
	shield_candidate_a.controller_id = ReactionCandidate.CONTROLLER_PLAYER
	shield_candidate_a.reaction_available = true
	shield_candidate_a.context_overrides = {"casting_context": _casting_context("attack_event")}
	var shield_candidate_b := ReactionCandidate.new("shield_ally", shield_actor_b, shield_wizard_b)
	shield_candidate_b.display_name = shield_wizard_b.character_name
	shield_candidate_b.team_id = ReactionCandidate.TEAM_PARTY
	shield_candidate_b.controller_id = ReactionCandidate.CONTROLLER_PLAYER
	shield_candidate_b.reaction_available = true
	shield_candidate_b.context_overrides = {"casting_context": _casting_context("attack_event")}
	var shield_event: ReactionEvent = coordinator.create_event(
		ReactionOpportunitySystem.TRIGGER_ATTACK_ROLL_HIT,
		{
			"attack_hit": true,
			"attack_total": 16,
			"natural_roll": 12,
			"current_ac": 13,
			"shield_already_active": false,
			"eligible_reactor_actor_ids": [shield_actor_a.get_instance_id()]
		},
		caster,
		shield_actor_a,
		"self_only_shield"
	)
	var shield_options: Array[Dictionary] = coordinator.collect_options(
		shield_event,
		[shield_candidate_a, shield_candidate_b]
	)
	if shield_options.size() != 1 or str(shield_options[0].get("reactor_id", "")) != "shield_target":
		_fail("Shield was offered to an ally who was not the target of the attack.")
		return

	print("Coordinated reaction migration continues after a failed Counterspell, stops after a successful second reaction, spends only selected resources, and limits self-only defenses to the affected actor.")
	quit(0)
