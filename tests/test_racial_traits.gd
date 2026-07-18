extends SceneTree


func _init() -> void:
	var races := RaceDataSystem.new()
	var abilities := ClassDataSystem.new()
	var ability_system := ClassAbilitySystem.new()
	var checks := SkillCheckSystem.new()
	var combat := CombatSystem.new()
	var rules := SrdCombatRules.new()

	_test_human(races, abilities, ability_system, checks)
	_test_elf(races)
	_test_dwarf(races, rules)
	_test_halfling(races, checks, combat, rules)
	_test_dragonborn(races, abilities, ability_system)
	_test_gnome(races, rules)
	_test_goliath(races)
	_test_orc(races, abilities, ability_system)
	_test_tiefling(races, rules)
	_test_serialization(races)

	print("Racial trait tests passed.")
	quit(0)


func _test_human(races: RaceDataSystem, abilities: ClassDataSystem, ability_system: ClassAbilitySystem, checks: SkillCheckSystem) -> void:
	var human := _character()
	races.apply_race(human, "human")
	var human_ability: Dictionary = abilities.get_racial_ability(human)
	assert(str(human_ability.get("id", "")) == "human_inspiration")
	var human_result: Dictionary = ability_system.use_self_ability(human, human_ability)
	assert(bool(human_result.get("success", false)))
	assert(bool(human.active_effects.get("racial_advantage_next_d20", false)))
	var inspired_check: SkillCheckResult = checks.perform_check(human, "wisdom", 10, 0, 4, 18)
	assert(inspired_check.natural_roll == 18)
	assert(not human.active_effects.has("racial_advantage_next_d20"))


func _test_elf(races: RaceDataSystem) -> void:
	var elf := _character()
	races.apply_race(elf, "elf")
	assert(elf.darkvision_feet == 60)
	assert(elf.immune_to_magical_sleep)
	assert(elf.long_rest_hours == 4)
	assert("charmed" in elf.racial_condition_save_advantage)


func _test_dwarf(races: RaceDataSystem, rules: SrdCombatRules) -> void:
	var dwarf := _character()
	races.apply_race(dwarf, "dwarf")
	assert(dwarf.maximum_health == 11)
	assert(dwarf.darkvision_feet == 120)
	var dwarf_state := CombatantState.new()
	dwarf_state.damage_resistances = dwarf.racial_damage_resistances.duplicate()
	var poison_damage: Dictionary = rules.resolve_damage(9, "poison", dwarf_state)
	assert(int(poison_damage.get("applied", -1)) == 4)
	var poison_save: Dictionary = rules.resolve_saving_throw("constitution", 0, 12, dwarf_state, false, false, [3, 17], {"condition_id":"poisoned"})
	assert(bool(poison_save.get("advantage", false)))
	assert(int(poison_save.get("natural", 0)) == 17)


func _test_halfling(races: RaceDataSystem, checks: SkillCheckSystem, combat: CombatSystem, rules: SrdCombatRules) -> void:
	var halfling := _character()
	races.apply_race(halfling, "halfling")
	assert(halfling.size_category == "small")
	assert(halfling.can_move_through_larger_creatures)
	assert(halfling.naturally_stealthy)
	var lucky_check: SkillCheckResult = checks.perform_check(halfling, "dexterity", 10, 0, 1, 0, 15)
	assert(lucky_check.natural_roll == 15)
	var weapon: Dictionary = {"name":"Тестовый меч", "damage_dice":[1,6], "damage_type":"slashing", "ability":"strength", "properties":[]}
	var lucky_attack: AttackResult = combat.perform_basic_attack(halfling, 10, weapon, 1, [4], {"distance_feet":5, "lucky_first_reroll_override":14})
	assert(lucky_attack.natural_roll == 14)
	assert(lucky_attack.hit)
	var halfling_state := CombatantState.new()
	halfling_state.reroll_natural_one = true
	var lucky_save: Dictionary = rules.resolve_saving_throw("dexterity", 0, 10, halfling_state, false, false, [1], {"lucky_reroll_overrides":[15]})
	assert(int(lucky_save.get("natural", 0)) == 15)
	assert(bool(lucky_save.get("success", false)))
	var death_state := CombatantState.new()
	death_state.reroll_natural_one = true
	var death_save: Dictionary = rules.resolve_death_save(death_state, 1, 16)
	assert(int(death_save.get("natural", 0)) == 16)
	assert(int(death_save.get("successes", 0)) == 1)
	assert(int(death_save.get("failures", 0)) == 0)


func _test_dragonborn(races: RaceDataSystem, abilities: ClassDataSystem, ability_system: ClassAbilitySystem) -> void:
	var dragonborn := _character()
	dragonborn.level = 5
	races.apply_race(dragonborn, "dragonborn")
	assert(dragonborn.get_resource_maximum("dragon_breath") == 3)
	assert(dragonborn.get_resource("dragon_breath") == 3)
	var breath: Dictionary = abilities.get_racial_ability(dragonborn)
	assert(str(breath.get("effect", "")) == "saving_throw_spell")
	assert(int(breath.get("range_ft", 0)) == 15)
	assert("fire" in dragonborn.racial_damage_resistances)
	var breath_result: AttackResult = ability_system.perform_offensive_ability(
		dragonborn,
		breath,
		10,
		-1,
		[4, 5],
		{"distance_feet":10, "target_save_modifier":-100, "defender_state":CombatantState.new()}
	)
	assert(breath_result.hit)
	assert(breath_result.damage == 9)
	assert(dragonborn.get_resource("dragon_breath") == 2)
	races.ensure_character_race(dragonborn)
	assert(dragonborn.get_resource("dragon_breath") == 2)


func _test_gnome(races: RaceDataSystem, rules: SrdCombatRules) -> void:
	var gnome := _character()
	races.apply_race(gnome, "gnome")
	var gnome_state := CombatantState.new()
	gnome_state.saving_throw_advantage_abilities = gnome.racial_save_advantage_abilities.duplicate()
	var ordinary_save: Dictionary = rules.resolve_saving_throw("intelligence", 0, 12, gnome_state, false, false, [2, 16], {"magical":false})
	assert(bool(ordinary_save.get("advantage", false)))
	assert(int(ordinary_save.get("natural", 0)) == 16)
	var unaffected_save: Dictionary = rules.resolve_saving_throw("dexterity", 0, 12, gnome_state, false, false, [16])
	assert(not bool(unaffected_save.get("advantage", false)))


func _test_goliath(races: RaceDataSystem) -> void:
	var goliath := _character()
	goliath.level = 5
	races.apply_race(goliath, "goliath")
	assert(goliath.base_speed_feet == 35)
	assert(goliath.get_resource_maximum("stone_endurance") == 3)
	assert(goliath.get_resource("stone_endurance") == 3)
	assert(goliath.grapple_escape_advantage)
	assert(goliath.carrying_size_bonus == 1)


func _test_orc(races: RaceDataSystem, abilities: ClassDataSystem, ability_system: ClassAbilitySystem) -> void:
	var orc := _character()
	orc.level = 5
	races.apply_race(orc, "orc")
	assert(orc.get_resource_maximum("adrenaline_rush") == 3)
	var adrenaline: Dictionary = abilities.get_racial_ability(orc)
	var adrenaline_result: Dictionary = ability_system.use_self_ability(orc, adrenaline)
	assert(bool(adrenaline_result.get("success", false)))
	assert(int(adrenaline_result.get("movement_bonus_feet", 0)) == orc.base_speed_feet)
	assert(int(adrenaline_result.get("temporary_hit_points", 0)) == 3)
	assert(orc.get_resource("adrenaline_rush") == 2)
	assert(orc.get_resource("relentless_endurance") == 1)
	races.ensure_character_race(orc)
	assert(orc.get_resource("adrenaline_rush") == 2)
	races.recharge_short_rest_resources(orc)
	assert(orc.get_resource("adrenaline_rush") == 3)
	assert(orc.get_resource("relentless_endurance") == 1)


func _test_tiefling(races: RaceDataSystem, rules: SrdCombatRules) -> void:
	var tiefling := _character()
	races.apply_race(tiefling, "tiefling")
	assert(tiefling.darkvision_feet == 60)
	assert("fire" in tiefling.racial_damage_resistances)
	assert("thaumaturgy" in tiefling.racial_features)
	var state := CombatantState.new()
	state.damage_resistances = tiefling.racial_damage_resistances.duplicate()
	assert(int(rules.resolve_damage(11, "fire", state).get("applied", -1)) == 5)


func _test_serialization(races: RaceDataSystem) -> void:
	var original := _character()
	original.level = 5
	races.apply_race(original, "orc")
	original.consume_resource("adrenaline_rush", 1)
	var restored := PlayerCharacter.from_dict(original.to_dict())
	races.ensure_character_race(restored)
	assert(restored.race_id == "orc")
	assert(restored.get_resource_maximum("adrenaline_rush") == 3)
	assert(restored.get_resource("adrenaline_rush") == 2)
	assert("adrenaline_rush" in restored.racial_short_rest_resources)


func _character() -> PlayerCharacter:
	var character := PlayerCharacter.new()
	character.character_name = "Тест"
	character.character_class_id = "fighter"
	character.character_class_name = "Воин"
	character.level = 1
	character.maximum_health = 10
	character.current_health = 10
	character.abilities["strength"] = 14
	character.abilities["dexterity"] = 14
	character.abilities["constitution"] = 14
	character.abilities["intelligence"] = 12
	character.abilities["wisdom"] = 12
	character.abilities["charisma"] = 12
	return character
