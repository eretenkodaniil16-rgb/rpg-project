extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	state.call("new_game")
	var subclasses := FighterSubclassSystem.new()
	var class_data := ClassDataSubclassSystem.new()
	var ability_system := ClassAbilitySubclassSystem.new()

	var guardian: PlayerCharacter = _fighter(
		FighterSubclassSystem.GUARDIAN_SUBCLASS_ID
	)
	state.set("player_character", guardian)
	if not subclasses.ensure_character(guardian):
		_fail("Guardian subclass was not initialized.")
		return
	if FighterSubclassSystem.GUARDIAN_ABILITY_ID not in guardian.known_features:
		_fail("Guardian ability was not granted.")
		return
	if guardian.get_resource_maximum(FighterSubclassSystem.GUARDIAN_RESOURCE_KEY) != 2:
		_fail("Guardian resource does not scale from proficiency bonus.")
		return
	guardian.consume_resource(FighterSubclassSystem.GUARDIAN_RESOURCE_KEY, 1)
	subclasses.ensure_character(guardian)
	if guardian.get_resource(FighterSubclassSystem.GUARDIAN_RESOURCE_KEY) != 1:
		_fail("Subclass synchronization restored a spent use for free.")
		return

	var guardian_ability: Dictionary = subclasses.get_ability_definition(
		FighterSubclassSystem.GUARDIAN_ABILITY_ID
	)
	var guardian_result: Dictionary = ability_system.use_self_ability(
		guardian,
		guardian_ability
	)
	if not bool(guardian_result.get("success", false)):
		_fail("Guardian stance could not be activated.")
		return
	if not bool(guardian.active_effects.get(FighterSubclassSystem.GUARDIAN_ACTIVE_KEY, false)):
		_fail("Guardian stance did not create its active effect.")
		return
	var armor_without_stance: int
	guardian.active_effects.erase(FighterSubclassSystem.GUARDIAN_ACTIVE_KEY)
	armor_without_stance = class_data.get_armor_class(guardian)
	guardian.active_effects[FighterSubclassSystem.GUARDIAN_ACTIVE_KEY] = true
	if class_data.get_armor_class(guardian) != armor_without_stance + 1:
		_fail("Guardian stance did not increase armor class by one.")
		return
	var rest_result: Dictionary = class_data.short_rest(guardian, 1)
	if not bool(rest_result.get("success", false)):
		_fail("Short rest failed for guardian subclass test.")
		return
	if guardian.get_resource(FighterSubclassSystem.GUARDIAN_RESOURCE_KEY) != 2:
		_fail("Short rest did not recharge guardian uses.")
		return
	if guardian.active_effects.has(FighterSubclassSystem.GUARDIAN_ACTIVE_KEY):
		_fail("Short rest did not clear guardian combat stance.")
		return

	state.call("new_game")
	var tactical: PlayerCharacter = _fighter(
		FighterSubclassSystem.TACTICAL_SUBCLASS_ID
	)
	state.set("player_character", tactical)
	subclasses.ensure_character(tactical)
	if FighterSubclassSystem.TACTICAL_ABILITY_ID not in tactical.known_features:
		_fail("Tactical ability was not granted.")
		return
	var tactical_ability: Dictionary = subclasses.get_ability_definition(
		FighterSubclassSystem.TACTICAL_ABILITY_ID
	)
	var tactical_activation: Dictionary = ability_system.use_self_ability(
		tactical,
		tactical_ability
	)
	if not bool(tactical_activation.get("success", false)):
		_fail("Tactical preparation could not be activated.")
		return
	var weapon: Dictionary = {
		"id": "test_sword",
		"name": "Испытательный меч",
		"damage_dice": [1, 8],
		"damage_type": "slashing",
		"ability": "strength",
		"properties": []
	}
	var combat := CombatSubclassSystem.new()
	var attack: AttackResult = combat.perform_basic_attack(
		tactical,
		15,
		weapon,
		5,
		[4],
		{
			"distance_feet": 5,
			"second_roll_override": 18,
			"turn_based": true
		}
	)
	if not attack.advantage or attack.natural_roll != 18 or not attack.hit:
		_fail("Tactical preparation did not grant advantage to the next weapon attack.")
		return
	var expected_damage: int = 4 + tactical.get_ability_modifier("strength") + tactical.get_proficiency_bonus()
	if attack.damage != expected_damage:
		_fail("Tactical preparation applied incorrect bonus damage: %d instead of %d." % [attack.damage, expected_damage])
		return
	if tactical.active_effects.has(FighterSubclassSystem.TACTICAL_READY_KEY):
		_fail("Tactical preparation was not consumed after the attack roll.")
		return

	tactical.subclass_id = FighterSubclassSystem.GUARDIAN_SUBCLASS_ID
	subclasses.ensure_character(tactical)
	if FighterSubclassSystem.TACTICAL_ABILITY_ID in tactical.known_features:
		_fail("Changing subclass left the previous active ability on the character.")
		return
	if tactical.class_resource_maximums.has(FighterSubclassSystem.TACTICAL_RESOURCE_KEY):
		_fail("Changing subclass left the previous subclass resource behind.")
		return

	print("Fighter subclass resources, guardian stance, tactical attack and rest tests passed.")
	quit(0)


func _fighter(subclass_id: String) -> PlayerCharacter:
	var character := PlayerCharacter.new()
	character.character_name = "Испытатель подкласса"
	character.character_class_id = "fighter"
	character.character_class_name = "Воин"
	character.subclass_id = subclass_id
	character.subclass_name = (
		"Страж передовой"
		if subclass_id == FighterSubclassSystem.GUARDIAN_SUBCLASS_ID
		else "Тактический клинок"
	)
	character.level = 3
	character.experience = ProgressionSystem.total_experience_for_level(3)
	character.abilities["strength"] = 16
	character.base_abilities["strength"] = 16
	character.abilities["dexterity"] = 14
	character.base_abilities["dexterity"] = 14
	character.abilities["constitution"] = 14
	character.base_abilities["constitution"] = 14
	character.maximum_health = 30
	character.current_health = 30
	character.hit_die_size = 10
	character.hit_dice_maximum = 3
	character.hit_dice_current = 3
	return character
