extends SceneTree


class TestCaster:
	extends Node2D
	var combat_name: String = "Вражеский маг"

	func get_combat_name() -> String:
		return combat_name


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _casting_context(turn_token: String, free_hands: int = 1) -> Dictionary:
	return {
		"can_speak": true,
		"armor_trained": true,
		"free_hands": free_hands,
		"focus_in_hand": false,
		"has_component_pouch": false,
		"has_required_material": true,
		"turn_token": turn_token
	}


func _make_attempt(spell: Dictionary, caster: Node, constitution_modifier: int = 2) -> SpellCastAttempt:
	var attempt := SpellCastAttempt.new(spell, caster, maxi(int(spell.get("spell_level", 0)), 1))
	attempt.caster_constitution_modifier = constitution_modifier
	attempt.caster_state = CombatantState.new()
	attempt.action_kind = "action"
	attempt.original_resource_key = "enemy_spell_slots_1"
	return attempt


func _run() -> void:
	var spells := SpellcastingSystem.new()
	var reactions := SpellReactionSystem.new()

	var wizard := PlayerCharacter.new()
	wizard.character_class_id = "wizard"
	wizard.character_class_name = "Волшебник"
	wizard.level = 1
	wizard.abilities["intelligence"] = 18
	wizard.base_abilities["intelligence"] = 18
	spells.ensure_character(wizard, false)
	if "counterspell" in spells.get_known_spell_ids(wizard):
		_fail("Counterspell was unlocked before Wizard level five.")
		return

	wizard.level = 5
	spells.ensure_character(wizard, false)
	if "counterspell" not in spells.get_known_spell_ids(wizard):
		_fail("Level-five Wizard did not unlock Counterspell.")
		return
	if spells.is_prepared(wizard, "counterspell"):
		_fail("Counterspell was automatically prepared instead of using a preparation slot.")
		return
	var prepare_result: Dictionary = spells.prepare_spell(wizard, "counterspell")
	if not bool(prepare_result.get("success", false)) or not spells.is_prepared(wizard, "counterspell"):
		_fail("Level-five Wizard could not prepare Counterspell.")
		return
	var counterspell: Dictionary = reactions.get_counterspell_definition()
	if counterspell.is_empty() or int(counterspell.get("spell_level", 0)) != 3 or str(counterspell.get("casting_time_kind", "")) != "reaction":
		_fail("Counterspell data definition is incomplete.")
		return

	var player_node := Node.new()
	player_node.name = "PlayerReactor"
	var enemy_node := TestCaster.new()
	enemy_node.position = Vector2(DistanceSystem.feet_to_pixels(30), 0.0)
	root.add_child(player_node)
	root.add_child(enemy_node)
	var turns := TurnBasedCombatSystem.new()
	turns.start_combat(
		player_node,
		[enemy_node],
		0,
		{player_node.get_instance_id(): 10, enemy_node.get_instance_id(): 20}
	)
	if turns.current_actor() != enemy_node or not turns.has_reaction(player_node):
		_fail("Combat did not begin on the enemy turn with the player reaction available.")
		return
	var enemy_turn_token: String = turns.current_turn_token()

	var burning_hands: Dictionary = spells.get_spell_definition("burning_hands")
	var attempt: SpellCastAttempt = _make_attempt(burning_hands, enemy_node, 2)
	var offer: Dictionary = reactions.evaluate_counterspell(
		wizard,
		attempt,
		turns.has_reaction(player_node),
		true,
		30,
		_casting_context(enemy_turn_token)
	)
	if not bool(offer.get("available", false)) or int(offer.get("slot_level", 0)) != 3:
		_fail("A visible observable spell within 60 feet did not offer Counterspell.")
		return

	var hidden_offer: Dictionary = reactions.evaluate_counterspell(wizard, attempt, true, false, 30, _casting_context(enemy_turn_token))
	if bool(hidden_offer.get("available", false)):
		_fail("Counterspell was offered against an unseen caster.")
		return
	var distant_offer: Dictionary = reactions.evaluate_counterspell(wizard, attempt, true, true, 65, _casting_context(enemy_turn_token))
	if bool(distant_offer.get("available", false)):
		_fail("Counterspell was offered beyond 60 feet.")
		return
	var blocked_hand_offer: Dictionary = reactions.evaluate_counterspell(wizard, attempt, true, true, 30, _casting_context(enemy_turn_token, 0))
	if bool(blocked_hand_offer.get("available", false)):
		_fail("Counterspell was offered without a hand for its somatic component.")
		return
	var silent_spell: Dictionary = {
		"id": "silent_test_spell",
		"name": "Безмолвная формула",
		"is_spell": true,
		"spell_level": 1,
		"components": []
	}
	var silent_attempt: SpellCastAttempt = _make_attempt(silent_spell, enemy_node, 2)
	var silent_offer: Dictionary = reactions.evaluate_counterspell(wizard, silent_attempt, true, true, 30, _casting_context(enemy_turn_token))
	if bool(silent_offer.get("available", false)):
		_fail("Counterspell was offered for a spell without observable V/S/M components.")
		return

	var level_three_before: int = wizard.get_resource("spell_slots_3")
	var failed_save_resolution: Dictionary = reactions.resolve_counterspell(
		wizard,
		attempt,
		turns.has_reaction(player_node),
		true,
		30,
		_casting_context(enemy_turn_token),
		[1]
	)
	if not bool(failed_save_resolution.get("resolved", false)) or not bool(failed_save_resolution.get("countered", false)):
		_fail("Failed Constitution save did not counter the original spell.")
		return
	if not bool(failed_save_resolution.get("consume_reaction", false)) or not turns.consume_reaction(player_node):
		_fail("Casting Counterspell did not consume the player's reaction.")
		return
	if wizard.get_resource("spell_slots_3") != level_three_before - 1:
		_fail("Counterspell did not expend exactly one level-three slot.")
		return
	if attempt.should_expend_original_resource() or attempt.original_resource_expended or not attempt.action_wasted:
		_fail("A countered spell did not preserve its original slot while wasting its action.")
		return
	var second_same_turn: Dictionary = reactions.evaluate_counterspell(
		wizard,
		_make_attempt(burning_hands, enemy_node, 2),
		turns.has_reaction(player_node),
		true,
		30,
		_casting_context(enemy_turn_token)
	)
	if bool(second_same_turn.get("available", false)):
		_fail("A second Counterspell was offered after the reaction was spent.")
		return

	turns.advance_turn()
	if turns.current_actor() != player_node or not turns.has_reaction(player_node):
		_fail("Player reaction did not reset at the start of the player's turn.")
		return
	turns.advance_turn()
	if turns.current_actor() != enemy_node:
		_fail("Combat did not advance to the next enemy turn.")
		return
	var next_enemy_turn_token: String = turns.current_turn_token()
	var surviving_attempt: SpellCastAttempt = _make_attempt(burning_hands, enemy_node, 25)
	var second_slot_before: int = wizard.get_resource("spell_slots_3")
	var successful_save_resolution: Dictionary = reactions.resolve_counterspell(
		wizard,
		surviving_attempt,
		turns.has_reaction(player_node),
		true,
		30,
		_casting_context(next_enemy_turn_token),
		[20]
	)
	if not bool(successful_save_resolution.get("resolved", false)) or bool(successful_save_resolution.get("countered", true)):
		_fail("Successful Constitution save did not allow the original spell to proceed.")
		return
	if wizard.get_resource("spell_slots_3") != second_slot_before - 1:
		_fail("Counterspell slot was not expended when the target succeeded on its save.")
		return
	if not surviving_attempt.should_expend_original_resource() or surviving_attempt.action_wasted:
		_fail("A spell that survived Counterspell was not allowed to expend its original resource and action.")
		return
	if not turns.consume_reaction(player_node):
		_fail("Successful target save incorrectly preserved the player's reaction.")
		return

	var warlock := PlayerCharacter.new()
	warlock.character_class_id = "warlock"
	warlock.character_class_name = "Колдун"
	warlock.level = 5
	warlock.abilities["charisma"] = 18
	warlock.base_abilities["charisma"] = 18
	spells.ensure_character(warlock, false)
	if "counterspell" not in spells.get_known_spell_ids(warlock):
		_fail("Level-five Warlock did not unlock Counterspell.")
		return
	spells.prepare_spell(warlock, "counterspell")
	var pact_before: int = warlock.get_resource("pact_slots_3")
	var pact_attempt: SpellCastAttempt = _make_attempt(burning_hands, enemy_node, 0)
	var pact_resolution: Dictionary = reactions.resolve_counterspell(
		warlock,
		pact_attempt,
		true,
		true,
		30,
		_casting_context("warlock_enemy_turn"),
		[1]
	)
	if not bool(pact_resolution.get("countered", false)):
		_fail("Warlock Counterspell did not resolve through Pact Magic.")
		return
	if str(pact_resolution.get("counterspell_resource_key", "")) != "pact_slots_3" or warlock.get_resource("pact_slots_3") != pact_before - 1:
		_fail("Warlock Counterspell did not consume the current level-three Pact slot.")
		return

	print("Counterspell unlocks, trigger restrictions, reaction timing, Constitution save, original slot preservation, and Pact Magic tests passed.")
	quit(0)
