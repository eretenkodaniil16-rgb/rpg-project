extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var progression := SpellcastingProgressionSystem.new()
	var wizard_slots: Dictionary = progression.get_slot_maximums("wizard", 5)
	if int(wizard_slots.get("1", 0)) != 4 or int(wizard_slots.get("2", 0)) != 3 or int(wizard_slots.get("3", 0)) != 2:
		_fail("Level-five full-caster slot progression is incorrect.")
		return
	if progression.get_prepared_limit("wizard", 5) != 9:
		_fail("Wizard prepared-spell progression is incorrect.")
		return
	if progression.get_prepared_limit("sorcerer", 2) != 4 or progression.get_prepared_limit("paladin", 17) != 14:
		_fail("Class-specific prepared limits are incorrect.")
		return
	if progression.get_pact_slot_level("warlock", 5) != 3 or int(progression.get_slot_maximums("warlock", 5).get("3", 0)) != 2:
		_fail("Level-five Pact Magic progression is incorrect.")
		return

	var spells := SpellcastingSystem.new()
	var wizard := PlayerCharacter.new()
	wizard.character_class_id = "wizard"
	wizard.character_class_name = "Волшебник"
	wizard.level = 1
	wizard.abilities["intelligence"] = 16
	wizard.base_abilities["intelligence"] = 16
	spells.ensure_character(wizard, false)
	wizard.consume_resource("spell_slots_1", 1)
	wizard.level = 5
	spells.ensure_character(wizard, false)
	if wizard.get_resource_maximum("spell_slots_1") != 4 or wizard.get_resource("spell_slots_1") != 3:
		_fail("Level-up did not preserve one expended level-one slot.")
		return
	if wizard.get_resource("spell_slots_2") != 3 or wizard.get_resource("spell_slots_3") != 2:
		_fail("Newly unlocked spell-slot levels were not initialized.")
		return
	if spells.get_prepared_limit(wizard) != 9:
		_fail("SpellcastingSystem did not apply the level-five prepared limit.")
		return

	var magic_missile: Dictionary = spells.get_spell_definition("magic_missile")
	var select_result: Dictionary = spells.set_selected_slot_level(wizard, "magic_missile", 2)
	if not bool(select_result.get("success", false)):
		_fail("A level-two slot could not be selected for Magic Missile.")
		return
	var level_two_before: int = wizard.get_resource("spell_slots_2")
	var payment: Dictionary = spells.consume_spell_cost_detailed(wizard, magic_missile)
	if not bool(payment.get("success", false)) or int(payment.get("slot_level", 0)) != 2:
		_fail("Explicit slot selection was not used by spell payment.")
		return
	if wizard.get_resource("spell_slots_2") != level_two_before - 1:
		_fail("The selected level-two slot was not consumed.")
		return
	var missile_dice: Array[int] = spells.scale_dice_for_slot(magic_missile, [3, 4], 2, "damage")
	if missile_dice != [4, 4] or spells.damage_bonus_for_slot(magic_missile, 2) != 4:
		_fail("Magic Missile upcasting did not add one dart.")
		return
	var cure_wounds: Dictionary = spells.get_spell_definition("cure_wounds")
	if spells.scale_dice_for_slot(cure_wounds, [2, 8], 3, "healing") != [4, 8]:
		_fail("Cure Wounds upcasting did not add one d8 per extra slot level.")
		return

	var verbal_failure: Dictionary = spells.check_spell_components(magic_missile, {"can_speak": false})
	if bool(verbal_failure.get("success", false)):
		_fail("A verbal spell was allowed while the caster could not speak.")
		return
	var somatic_failure: Dictionary = spells.check_spell_components(magic_missile, {"can_speak": true, "free_hands": 0, "focus_in_hand": false, "has_component_pouch": false})
	if bool(somatic_failure.get("success", false)):
		_fail("A somatic spell was allowed without a usable hand.")
		return
	var comprehend: Dictionary = spells.get_spell_definition("comprehend_languages")
	if not bool(spells.check_spell_components(comprehend, {"free_hands": 0, "focus_in_hand": true, "has_component_pouch": false}).get("success", false)):
		_fail("A held focus did not satisfy shared somatic/material handling.")
		return
	if bool(spells.check_spell_components(comprehend, {"free_hands": 0, "focus_in_hand": false, "has_component_pouch": false}).get("success", false)):
		_fail("A material spell was allowed without focus, pouch, or free hand.")
		return

	spells.set_selected_slot_level(wizard, "magic_missile", 1)
	var turn_one: Dictionary = spells.consume_spell_cost_detailed(wizard, magic_missile, 1, {"turn_token": "round_1_actor_1"})
	if not bool(turn_one.get("success", false)):
		_fail("First slotted spell of the turn was rejected.")
		return
	var second_same_turn: Dictionary = spells.consume_spell_cost_detailed(wizard, magic_missile, 1, {"turn_token": "round_1_actor_1"})
	if bool(second_same_turn.get("success", false)):
		_fail("A second spell slot was expended during the same turn.")
		return
	var next_turn: Dictionary = spells.consume_spell_cost_detailed(wizard, magic_missile, 1, {"turn_token": "round_2_actor_1"})
	if not bool(next_turn.get("success", false)):
		_fail("A slotted spell was not allowed on the next turn.")
		return

	var warlock := PlayerCharacter.new()
	warlock.character_class_id = "warlock"
	warlock.character_class_name = "Колдун"
	warlock.level = 5
	spells.ensure_character(warlock, false)
	if warlock.get_resource_maximum("pact_slots_3") != 2 or warlock.get_resource("pact_slots_3") != 2:
		_fail("Pact slots were not migrated to their level-five key.")
		return
	if spells.slot_resource_key(warlock, 1) != "pact_slots_3":
		_fail("A lower-level Warlock spell did not resolve to the current Pact slot level.")
		return
	warlock.consume_resource("pact_slots_3", 2)
	spells.recover_after_rest(warlock, false)
	if warlock.get_resource("pact_slots_3") != 2:
		_fail("Pact slots were not restored by a short rest.")
		return

	print("Spellcasting progression, upcasting, components and per-turn slot tests passed.")
	quit(0)
