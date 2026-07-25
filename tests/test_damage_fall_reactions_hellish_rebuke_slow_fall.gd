extends SceneTree

var _failed: bool = false


func _init() -> void:
	call_deferred("_run")


func _expect(condition: bool, message: String) -> void:
	if condition:
		return
	_failed = true
	push_error(message)


func _base_casting_context(turn_token: String) -> Dictionary:
	return {
		"can_speak": true,
		"armor_trained": true,
		"free_hands": 1,
		"focus_in_hand": true,
		"has_component_pouch": true,
		"has_required_material": true,
		"turn_token": turn_token
	}


func _make_warlock(level: int) -> PlayerCharacter:
	var character := PlayerCharacter.new()
	character.character_name = "Мстительный колдун"
	character.character_class_id = "warlock"
	character.character_class_name = "Колдун"
	character.race_name = "Человек"
	character.level = level
	character.maximum_health = 40
	character.current_health = 40
	character.abilities["charisma"] = 18
	character.base_abilities["charisma"] = 18
	character.starter_loadout_granted = true
	var spellcasting := SpellcastingSystem.new()
	spellcasting.ensure_character(character, true)
	character.class_resources[SpellcastingSystem.PREPARED_SPELLS_STATE_KEY] = [DamageFallReactionSystem.HELLISH_REBUKE_SPELL_ID]
	return character


func _make_monk(level: int) -> PlayerCharacter:
	var character := PlayerCharacter.new()
	character.character_name = "Падающий монах"
	character.character_class_id = "monk"
	character.character_class_name = "Монах"
	character.race_name = "Человек"
	character.level = level
	character.maximum_health = 50
	character.current_health = 50
	character.starter_loadout_granted = true
	return character


func _hellish_context(turn_token: String = "enemy:1") -> Dictionary:
	return {
		"trigger_id": ReactionOpportunitySystem.TRIGGER_CREATURE_DAMAGE_RECEIVED,
		"reaction_available": true,
		"reactor_can_react": true,
		"damage_applied": 7,
		"source_is_creature": true,
		"can_see_source": true,
		"distance_feet": 30,
		"casting_context": _base_casting_context(turn_token),
		"target_name": "Учебный конструкт",
		"target_state": CombatantState.new(),
		"target_dexterity_save_modifier": 1
	}


func _run() -> void:
	var spellcasting := SpellcastingSystem.new()
	var opportunities := ReactionOpportunitySystem.new()
	var rules := DamageFallReactionSystem.new()

	var warlock_level_one: PlayerCharacter = _make_warlock(1)
	spellcasting.ensure_character(warlock_level_one, false)
	_expect(DamageFallReactionSystem.HELLISH_REBUKE_SPELL_ID in spellcasting.get_known_spell_ids(warlock_level_one), "Warlock did not learn Hellish Rebuke from class data.")
	_expect(spellcasting.is_prepared(warlock_level_one, DamageFallReactionSystem.HELLISH_REBUKE_SPELL_ID), "Hellish Rebuke was not recognized as prepared.")
	var context: Dictionary = _hellish_context()
	context["reactor"] = warlock_level_one
	var options: Array[Dictionary] = opportunities.collect_options(ReactionOpportunitySystem.TRIGGER_CREATURE_DAMAGE_RECEIVED, context)
	_expect(options.size() == 1, "Receiving creature damage did not offer Hellish Rebuke.")
	if not options.is_empty():
		_expect(str(options[0].get("id", "")) == ReactionOpportunitySystem.OPTION_HELLISH_REBUKE, "The damage reaction option was not Hellish Rebuke.")
		_expect(int((options[0].get("offer", {}) as Dictionary).get("damage_dice_count", 0)) == 2, "Level-one Hellish Rebuke was not 2d10.")
	var slot_before: int = warlock_level_one.get_resource("pact_slots_1")
	context["save_roll_overrides"] = [1]
	context["damage_roll_overrides"] = [10, 10]
	var failed_save_result: Dictionary = opportunities.resolve_damage_fall_option(ReactionOpportunitySystem.OPTION_HELLISH_REBUKE, context)
	_expect(bool(failed_save_result.get("resolved", false)), "Hellish Rebuke failed to resolve after a failed save.")
	_expect(bool(failed_save_result.get("consume_reaction", false)), "Hellish Rebuke did not request reaction consumption.")
	_expect(int(failed_save_result.get("damage", 0)) == 20, "Failed-save Hellish Rebuke did not deal 20 damage from two overridden d10 rolls.")
	_expect(warlock_level_one.get_resource("pact_slots_1") == slot_before - 1, "Hellish Rebuke did not spend one pact slot.")

	var saving_warlock: PlayerCharacter = _make_warlock(1)
	var saving_context: Dictionary = _hellish_context("enemy:2")
	saving_context["reactor"] = saving_warlock
	saving_context["save_roll_overrides"] = [20]
	saving_context["damage_roll_overrides"] = [9, 9]
	var successful_save_result: Dictionary = rules.resolve_hellish_rebuke(saving_warlock, saving_context)
	_expect(bool(successful_save_result.get("save_succeeded", false)), "A natural 20 did not succeed on the Hellish Rebuke save.")
	_expect(int(successful_save_result.get("damage", 0)) == 9, "Successful Hellish Rebuke save did not halve 18 damage to 9.")

	var upcast_warlock: PlayerCharacter = _make_warlock(3)
	var upcast_context: Dictionary = _hellish_context("enemy:3")
	upcast_context["reactor"] = upcast_warlock
	upcast_context["save_roll_overrides"] = [1]
	upcast_context["damage_roll_overrides"] = [10, 10, 10]
	var upcast_options: Array[Dictionary] = opportunities.collect_options(ReactionOpportunitySystem.TRIGGER_CREATURE_DAMAGE_RECEIVED, upcast_context)
	_expect(upcast_options.size() == 1, "Level-three Warlock did not receive a pact-slot Hellish Rebuke option.")
	if not upcast_options.is_empty():
		_expect(int((upcast_options[0].get("offer", {}) as Dictionary).get("slot_level", 0)) == 2, "Warlock pact slot did not cast Hellish Rebuke at level 2.")
	var upcast_result: Dictionary = rules.resolve_hellish_rebuke(upcast_warlock, upcast_context)
	_expect(int(upcast_result.get("damage", 0)) == 30, "Level-two Hellish Rebuke did not roll 3d10.")

	var blocked_context: Dictionary = _hellish_context("enemy:4")
	blocked_context["reactor"] = _make_warlock(1)
	blocked_context["distance_feet"] = 65
	_expect(opportunities.collect_options(ReactionOpportunitySystem.TRIGGER_CREATURE_DAMAGE_RECEIVED, blocked_context).is_empty(), "Hellish Rebuke was offered beyond 60 feet.")
	blocked_context["distance_feet"] = 30
	blocked_context["can_see_source"] = false
	_expect(opportunities.collect_options(ReactionOpportunitySystem.TRIGGER_CREATURE_DAMAGE_RECEIVED, blocked_context).is_empty(), "Hellish Rebuke was offered against an unseen source.")
	blocked_context["can_see_source"] = true
	blocked_context["damage_applied"] = 0
	_expect(opportunities.collect_options(ReactionOpportunitySystem.TRIGGER_CREATURE_DAMAGE_RECEIVED, blocked_context).is_empty(), "Hellish Rebuke was offered when no damage was taken.")
	blocked_context["damage_applied"] = 7
	blocked_context["reaction_available"] = false
	_expect(opportunities.collect_options(ReactionOpportunitySystem.TRIGGER_CREATURE_DAMAGE_RECEIVED, blocked_context).is_empty(), "Hellish Rebuke was offered after the reaction was spent.")

	var monk_four: PlayerCharacter = _make_monk(4)
	var fall_context: Dictionary = {
		"reactor": monk_four,
		"reaction_available": true,
		"reactor_can_react": true,
		"trigger_id": ReactionOpportunitySystem.TRIGGER_FALL_DAMAGE_PENDING,
		"pending_fall_damage": 24,
		"fall_distance_feet": 40
	}
	var fall_options: Array[Dictionary] = opportunities.collect_options(ReactionOpportunitySystem.TRIGGER_FALL_DAMAGE_PENDING, fall_context)
	_expect(fall_options.size() == 1, "A level-four Monk was not offered Slow Fall.")
	if not fall_options.is_empty():
		_expect(str(fall_options[0].get("id", "")) == ReactionOpportunitySystem.OPTION_SLOW_FALL, "The fall reaction option was not Slow Fall.")
	var slow_fall_result: Dictionary = opportunities.resolve_damage_fall_option(ReactionOpportunitySystem.OPTION_SLOW_FALL, fall_context)
	_expect(bool(slow_fall_result.get("resolved", false)), "Slow Fall failed to resolve.")
	_expect(int(slow_fall_result.get("reduction", 0)) == 20, "Level-four Slow Fall did not reduce damage by 20.")
	_expect(int(slow_fall_result.get("final_damage", -1)) == 4, "Slow Fall did not reduce 24 falling damage to 4.")
	var monk_three_context: Dictionary = fall_context.duplicate(true)
	monk_three_context["reactor"] = _make_monk(3)
	_expect(opportunities.collect_options(ReactionOpportunitySystem.TRIGGER_FALL_DAMAGE_PENDING, monk_three_context).is_empty(), "Slow Fall was offered before Monk level 4.")
	var no_reaction_fall: Dictionary = fall_context.duplicate(true)
	no_reaction_fall["reaction_available"] = false
	_expect(opportunities.collect_options(ReactionOpportunitySystem.TRIGGER_FALL_DAMAGE_PENDING, no_reaction_fall).is_empty(), "Slow Fall was offered after the reaction was spent.")

	if _failed:
		quit(1)
		return
	print("Hellish Rebuke obeys damage, sight, range, Dexterity save, pact-slot upcasting and half damage; Slow Fall obeys Monk level and 5x-level reduction.")
	quit(0)
