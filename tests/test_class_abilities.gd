extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	assert(state != null)
	var classes := ClassDataSystem.new()
	var abilities := ClassAbilitySystem.new()
	var combat := CombatSystem.new()

	var barbarian := _prepared_character(state, classes, "barbarian")
	var rage: Dictionary = classes.get_signature_ability(barbarian)
	var rage_response: Dictionary = abilities.use_self_ability(barbarian, rage)
	assert(bool(rage_response.get("success", false)))
	assert(barbarian.get_resource("rage") == 1)
	var axe: Dictionary = classes.get_equipped_weapon(barbarian)
	var rage_attack: AttackResult = combat.perform_basic_attack(barbarian, 10, axe, 12, [6])
	assert(rage_attack.hit)
	assert(rage_attack.bonus_damage == 2)
	assert(int(barbarian.active_effects.get("rage_attacks", 0)) == 2)

	var fighter := _prepared_character(state, classes, "fighter")
	fighter.current_health = 1
	var wind_response: Dictionary = abilities.use_self_ability(fighter, classes.get_signature_ability(fighter))
	assert(bool(wind_response.get("success", false)))
	assert(fighter.current_health > 1)
	assert(fighter.get_resource("second_wind") == 1)

	var monk := _prepared_character(state, classes, "monk")
	monk.abilities["strength"] = 8
	monk.abilities["dexterity"] = 16
	var spear: Dictionary = classes.get_equipped_weapon(monk)
	var monk_attack: AttackResult = combat.perform_basic_attack(monk, 10, spear, 10, [4])
	assert(monk_attack.ability_name == "Ловкость")
	assert(monk_attack.damage == 7)

	var ranger := _prepared_character(state, classes, "ranger")
	ranger.abilities["wisdom"] = 14
	var mark_response: Dictionary = abilities.apply_target_ability(ranger, classes.get_signature_ability(ranger))
	assert(bool(mark_response.get("success", false)))
	assert(int(ranger.active_effects.get("hunters_mark_hits", 0)) == 3)

	var wizard := _prepared_character(state, classes, "wizard")
	var missile: AttackResult = abilities.perform_offensive_ability(
		wizard, classes.get_signature_ability(wizard), 99, -1, [1, 1, 1]
	)
	assert(missile.automatic_hit)
	assert(missile.hit)
	assert(missile.damage == 6)
	assert(wizard.get_resource("spell_slots_1") == 1)

	var paladin := _prepared_character(state, classes, "paladin")
	paladin.current_health = paladin.maximum_health - 3
	var hands_response: Dictionary = abilities.use_self_ability(paladin, classes.get_signature_ability(paladin))
	assert(bool(hands_response.get("success", false)))
	assert(paladin.current_health == paladin.maximum_health)
	assert(paladin.get_resource("lay_on_hands_pool") == 2)

	classes.long_rest(paladin)
	assert(paladin.get_resource("lay_on_hands_pool") == 5)
	assert(paladin.current_health == paladin.maximum_health)

	print("Class ability tests passed.")
	quit(0)


func _prepared_character(state: Node, service: ClassDataSystem, class_id: String) -> PlayerCharacter:
	state.call("new_game")
	var character := PlayerCharacter.new()
	character.character_name = "Тестер"
	character.character_class_id = class_id
	character.character_class_name = str(service.get_class_definition(class_id).get("name", class_id))
	character.maximum_health = 20
	character.current_health = 20
	character.abilities["strength"] = 16
	character.abilities["dexterity"] = 14
	character.abilities["wisdom"] = 14
	character.abilities["charisma"] = 14
	state.set("player_character", character)
	assert(service.ensure_starting_loadout(character))
	return character
