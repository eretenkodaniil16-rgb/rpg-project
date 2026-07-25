extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _casting_context(can_speak: bool = true) -> Dictionary:
	return {
		"can_speak": can_speak,
		"armor_trained": true,
		"free_hands": 0,
		"focus_in_hand": false,
		"has_component_pouch": false,
		"has_required_material": true,
		"turn_token": "test-turn"
	}


func _run() -> void:
	var system := ViciousMockerySystem.new()
	var bard := PlayerCharacter.new()
	bard.character_class_id = "bard"
	bard.character_class_name = "Бард"
	bard.level = 1
	bard.abilities["charisma"] = 16
	bard.base_abilities["charisma"] = 16
	var target_state := CombatantState.new()

	var definition: Dictionary = system.get_definition()
	if int(definition.get("spell_level", -1)) != 0 or int(definition.get("range_ft", 0)) != 60:
		_fail("Vicious Mockery definition did not expose cantrip level and 60-foot range.")
		return
	if str(definition.get("save_ability", "")) != "wisdom" or str(definition.get("damage_type", "")) != "psychic":
		_fail("Vicious Mockery definition did not use Wisdom save and Psychic damage.")
		return
	if definition.get("components", []) != ["v"]:
		_fail("Vicious Mockery did not use only the verbal component.")
		return

	var failed: Dictionary = system.resolve(
		bard,
		"Учебный конструкт",
		target_state,
		0,
		30,
		true,
		_casting_context(),
		[1],
		[6]
	)
	var failed_result: AttackResult = failed.get("result") as AttackResult
	if not bool(failed.get("success", false)) or not bool(failed.get("failed_save", false)) or failed_result == null:
		_fail("Failed Wisdom save did not resolve Vicious Mockery.")
		return
	if failed_result.damage != 6 or not failed_result.hit or failed_result.note.find("помех") < 0:
		_fail("Level-one Vicious Mockery did not deal 1d6 and apply the next-attack disadvantage rider.")
		return

	bard.level = 5
	var scaled: Dictionary = system.resolve(
		bard,
		"Учебный конструкт",
		target_state,
		0,
		30,
		true,
		_casting_context(),
		[1],
		[6, 5]
	)
	var scaled_result: AttackResult = scaled.get("result") as AttackResult
	if scaled_result == null or scaled_result.damage != 11 or system.cantrip_dice_count(5) != 2:
		_fail("Vicious Mockery did not scale to 2d6 at character level five.")
		return
	if system.cantrip_dice_count(11) != 3 or system.cantrip_dice_count(17) != 4:
		_fail("Vicious Mockery cantrip scaling at levels eleven or seventeen was incorrect.")
		return

	var succeeded: Dictionary = system.resolve(
		bard,
		"Учебный конструкт",
		target_state,
		25,
		30,
		true,
		_casting_context(),
		[20],
		[6, 6]
	)
	var succeeded_result: AttackResult = succeeded.get("result") as AttackResult
	if bool(succeeded.get("failed_save", true)) or succeeded_result == null or succeeded_result.damage != 0 or succeeded_result.hit:
		_fail("Successful Wisdom save did not negate Vicious Mockery damage and rider.")
		return

	var muted: Dictionary = system.validate_cast(bard, 30, true, _casting_context(false))
	if bool(muted.get("success", true)):
		_fail("Vicious Mockery was available while the caster could not speak.")
		return
	var distant: Dictionary = system.validate_cast(bard, 65, true, _casting_context())
	if bool(distant.get("success", true)):
		_fail("Vicious Mockery was available beyond 60 feet.")
		return
	var undetected: Dictionary = system.validate_cast(bard, 30, false, _casting_context())
	if bool(undetected.get("success", true)):
		_fail("Vicious Mockery was available when the target could neither be seen nor heard.")
		return

	var opportunities := ReactionOpportunitySystem.new()
	var opportunity_options: Array[Dictionary] = opportunities.collect_options(
		ReactionOpportunitySystem.TRIGGER_ENEMY_LEAVES_REACH,
		{
			"reaction_available": true,
			"target_leaves_reach": true,
			"can_make_weapon_attack": true
		}
	)
	if opportunity_options.size() != 1 or str(opportunity_options[0].get("id", "")) != ReactionOpportunitySystem.OPTION_OPPORTUNITY_ATTACK:
		_fail("Opportunity-attack trigger did not produce a selectable reaction option.")
		return
	var readied_options: Array[Dictionary] = opportunities.collect_options(
		ReactionOpportunitySystem.TRIGGER_READIED_ACTION,
		{
			"reaction_available": true,
			"readied_trigger_matches": true,
			"readied_description": "Выстрелить, когда противник войдёт в комнату."
		}
	)
	if readied_options.size() != 1 or str(readied_options[0].get("id", "")) != ReactionOpportunitySystem.OPTION_READIED_ATTACK:
		_fail("Readied-action trigger did not produce a selectable reaction option.")
		return
	var unavailable: Array[Dictionary] = opportunities.collect_options(
		ReactionOpportunitySystem.TRIGGER_ENEMY_LEAVES_REACH,
		{"reaction_available": false, "target_leaves_reach": true, "can_make_weapon_attack": true}
	)
	if not unavailable.is_empty():
		_fail("Reaction options were offered after the reaction had been spent.")
		return

	print("Vicious Mockery SRD 5.2 damage, scaling, verbal component, Wisdom save, debuff rider, and generic reaction opportunity collection tests passed.")
	quit(0)
