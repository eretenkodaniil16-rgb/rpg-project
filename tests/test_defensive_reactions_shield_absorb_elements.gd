extends SceneTree

var _failed: bool = false


func _init() -> void:
	call_deferred("_run")


func _expect(condition: bool, message: String) -> void:
	if condition:
		return
	_failed = true
	push_error(message)


func _make_wizard(level: int = 3) -> PlayerCharacter:
	var character := PlayerCharacter.new()
	character.character_name = "Защитный маг"
	character.character_class_id = "wizard"
	character.character_class_name = "Волшебник"
	character.race_name = "Человек"
	character.level = level
	character.maximum_health = 40
	character.current_health = 40
	character.abilities["intelligence"] = 18
	character.base_abilities["intelligence"] = 18
	character.abilities["dexterity"] = 14
	character.base_abilities["dexterity"] = 14
	character.starter_loadout_granted = true
	var spellcasting := SpellcastingSystem.new()
	spellcasting.ensure_character(character, true)
	character.class_resources[SpellcastingSystem.PREPARED_SPELLS_STATE_KEY] = [
		DefensiveReactionSystem.SHIELD_SPELL_ID,
		DefensiveReactionSystem.ABSORB_ELEMENTS_SPELL_ID
	]
	return character


func _base_casting_context(turn_token: String = "enemy:1") -> Dictionary:
	return {
		"can_speak": true,
		"armor_trained": true,
		"free_hands": 1,
		"focus_in_hand": true,
		"has_component_pouch": true,
		"has_required_material": true,
		"turn_token": turn_token
	}


func _run() -> void:
	var spellcasting := SpellcastingSystem.new()
	var opportunities := ReactionOpportunitySystem.new()
	var wizard: PlayerCharacter = _make_wizard(3)
	spellcasting.ensure_character(wizard, false)

	_expect(DefensiveReactionSystem.SHIELD_SPELL_ID in spellcasting.get_known_spell_ids(wizard), "Wizard did not learn Shield from class spell data.")
	_expect(DefensiveReactionSystem.ABSORB_ELEMENTS_SPELL_ID in spellcasting.get_known_spell_ids(wizard), "Wizard did not learn Absorb Elements from class spell data.")
	_expect(spellcasting.is_prepared(wizard, DefensiveReactionSystem.SHIELD_SPELL_ID), "Shield was not recognized as prepared.")
	_expect(spellcasting.is_prepared(wizard, DefensiveReactionSystem.ABSORB_ELEMENTS_SPELL_ID), "Absorb Elements was not recognized as prepared.")

	var shield_context: Dictionary = {
		"reactor": wizard,
		"reaction_available": true,
		"trigger_id": ReactionOpportunitySystem.TRIGGER_ATTACK_ROLL_HIT,
		"attack_hit": true,
		"attack_total": 15,
		"natural_roll": 12,
		"current_ac": 13,
		"shield_already_active": false,
		"casting_context": _base_casting_context("enemy:1")
	}
	var shield_options: Array[Dictionary] = opportunities.collect_options(
		ReactionOpportunitySystem.TRIGGER_ATTACK_ROLL_HIT,
		shield_context
	)
	_expect(shield_options.size() == 1, "A legal hit did not offer exactly one Shield reaction.")
	if not shield_options.is_empty():
		_expect(str(shield_options[0].get("id", "")) == ReactionOpportunitySystem.OPTION_SHIELD, "The hit reaction option was not Shield.")
		_expect(bool((shield_options[0].get("offer", {}) as Dictionary).get("prevents_triggering_hit", false)), "Shield did not recognize that +5 AC would prevent the triggering hit.")

	var slots_before_shield: int = wizard.get_resource("spell_slots_1")
	var shield_result: Dictionary = opportunities.resolve_defensive_option(ReactionOpportunitySystem.OPTION_SHIELD, shield_context)
	_expect(bool(shield_result.get("resolved", false)), "Shield failed to resolve: %s" % str(shield_result.get("message", "")))
	_expect(bool(shield_result.get("consume_reaction", false)), "Shield did not request reaction consumption.")
	_expect(int(shield_result.get("armor_class_bonus", 0)) == 5, "Shield did not grant +5 AC.")
	_expect(wizard.get_resource("spell_slots_1") == slots_before_shield - 1, "Shield did not spend exactly one spell slot.")

	spellcasting.ensure_character(wizard, true)
	var magic_missile_context: Dictionary = shield_context.duplicate(true)
	magic_missile_context["trigger_id"] = ReactionOpportunitySystem.TRIGGER_MAGIC_MISSILE_TARGETED
	magic_missile_context.erase("attack_hit")
	magic_missile_context["casting_context"] = _base_casting_context("enemy:missile")
	var missile_options: Array[Dictionary] = opportunities.collect_options(
		ReactionOpportunitySystem.TRIGGER_MAGIC_MISSILE_TARGETED,
		magic_missile_context
	)
	_expect(missile_options.size() == 1, "Magic Missile targeting did not offer Shield.")
	if not missile_options.is_empty():
		_expect(bool((missile_options[0].get("offer", {}) as Dictionary).get("blocks_magic_missile", false)), "Shield was not marked as fully blocking Magic Missile.")

	var active_shield_context: Dictionary = shield_context.duplicate(true)
	active_shield_context["shield_already_active"] = true
	_expect(opportunities.collect_options(ReactionOpportunitySystem.TRIGGER_ATTACK_ROLL_HIT, active_shield_context).is_empty(), "Shield was offered while the same Shield effect was already active.")

	spellcasting.ensure_character(wizard, true)
	var select_level_two: Dictionary = spellcasting.set_selected_slot_level(wizard, DefensiveReactionSystem.ABSORB_ELEMENTS_SPELL_ID, 2)
	_expect(bool(select_level_two.get("success", false)), "Could not select a level-two slot for Absorb Elements upcasting.")
	var absorb_context: Dictionary = {
		"reactor": wizard,
		"reaction_available": true,
		"trigger_id": ReactionOpportunitySystem.TRIGGER_ELEMENTAL_DAMAGE_TAKEN,
		"incoming_damage": 17,
		"damage_type": "fire",
		"same_absorption_active": false,
		"casting_context": _base_casting_context("enemy:2")
	}
	var absorb_options: Array[Dictionary] = opportunities.collect_options(
		ReactionOpportunitySystem.TRIGGER_ELEMENTAL_DAMAGE_TAKEN,
		absorb_context
	)
	_expect(absorb_options.size() == 1, "Fire damage did not offer Absorb Elements.")
	var level_two_slots_before: int = wizard.get_resource("spell_slots_2")
	var absorb_result: Dictionary = opportunities.resolve_defensive_option(ReactionOpportunitySystem.OPTION_ABSORB_ELEMENTS, absorb_context)
	_expect(bool(absorb_result.get("resolved", false)), "Absorb Elements failed to resolve: %s" % str(absorb_result.get("message", "")))
	_expect(str(absorb_result.get("damage_type", "")) == "fire", "Absorb Elements stored the wrong damage type.")
	_expect(int(absorb_result.get("bonus_dice_count", 0)) == 2, "A level-two Absorb Elements did not charge 2d6 bonus damage.")
	_expect(wizard.get_resource("spell_slots_2") == level_two_slots_before - 1, "Upcast Absorb Elements did not spend one level-two slot.")

	var poison_context: Dictionary = absorb_context.duplicate(true)
	poison_context["damage_type"] = "poison"
	_expect(opportunities.collect_options(ReactionOpportunitySystem.TRIGGER_ELEMENTAL_DAMAGE_TAKEN, poison_context).is_empty(), "Absorb Elements was incorrectly offered for poison damage.")
	var force_context: Dictionary = absorb_context.duplicate(true)
	force_context["damage_type"] = "force"
	_expect(opportunities.collect_options(ReactionOpportunitySystem.TRIGGER_ELEMENTAL_DAMAGE_TAKEN, force_context).is_empty(), "Absorb Elements was incorrectly offered for force damage.")
	var zero_context: Dictionary = absorb_context.duplicate(true)
	zero_context["incoming_damage"] = 0
	_expect(opportunities.collect_options(ReactionOpportunitySystem.TRIGGER_ELEMENTAL_DAMAGE_TAKEN, zero_context).is_empty(), "Absorb Elements was offered when no damage would be taken.")

	spellcasting.ensure_character(wizard, true)
	var occupied_hands_context: Dictionary = shield_context.duplicate(true)
	var blocked_casting_context: Dictionary = _base_casting_context("enemy:hands")
	blocked_casting_context["free_hands"] = 0
	blocked_casting_context["focus_in_hand"] = false
	occupied_hands_context["casting_context"] = blocked_casting_context
	_expect(opportunities.collect_options(ReactionOpportunitySystem.TRIGGER_ATTACK_ROLL_HIT, occupied_hands_context).is_empty(), "Shield was offered without a hand for its somatic component.")
	var no_reaction_context: Dictionary = shield_context.duplicate(true)
	no_reaction_context["reaction_available"] = false
	_expect(opportunities.collect_options(ReactionOpportunitySystem.TRIGGER_ATTACK_ROLL_HIT, no_reaction_context).is_empty(), "Shield was offered after the reaction was spent.")

	if _failed:
		quit(1)
		return
	print("Shield and Absorb Elements obey preparation, components, slots, triggers, +5 AC, Magic Missile immunity, elemental filtering, and upcasting.")
	quit(0)
