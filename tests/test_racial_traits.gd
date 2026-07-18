extends SceneTree


func _init() -> void:
	var races := RaceDataSystem.new()
	var abilities := ClassDataSystem.new()
	var ability_system := ClassAbilitySystem.new()
	var checks := SkillCheckSystem.new()
	var combat := CombatSystem.new()
	var rules := SrdCombatRules.new()

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

	var halfling := _character()
	races.apply_race(halfling, "halfling")
	var lucky_check: SkillCheckResult = checks.perform_check(halfling, "dexterity", 10, 0, 1, 0, 15)
	assert(lucky_check.natural_roll == 15)
	var weapon: Dictionary = {"name":"Тестовый меч", "damage_dice":[1,6], "damage_type":"slashing", "ability":"strength", "properties":[]}
	var lucky_attack: AttackResult = combat.perform_basic_attack(halfling, 10, weapon, 1, [4], {"distance_feet":5, "lucky_first_reroll_override":14})
	assert(lucky_attack.natural_roll == 14)
	assert(lucky_attack.hit)

	var dwarf := _character()
	races.apply_race(dwarf, "dwarf")
	assert(dwarf.maximum_health == 11)
	var dwarf_state := CombatantState.new()
	dwarf_state.damage_resistances = dwarf.racial_damage_resistances.duplicate()
	var poison_damage: Dictionary = rules.resolve_damage(9, "poison", dwarf_state)
	assert(int(poison_damage.get("applied", -1)) == 4)

	var elf := _character()
	races.apply_race(elf, "elf")
	var elf_state := CombatantState.new()
	elf_state.saving_throw_advantage_conditions = elf.racial_condition_save_advantage.duplicate()
	var charm_save: Dictionary = rules.resolve_saving_throw("wisdom", 0, 12, elf_state, false, false, [3, 17], {"condition_id":"charmed", "magical":true})
	assert(bool(charm_save.get("advantage", false)))
	assert(int(charm_save.get("natural", 0)) == 17)
	assert(bool(charm_save.get("success", false)))

	var gnome := _character()
	races.apply_race(gnome, "gnome")
	var gnome_state := CombatantState.new()
	gnome_state.magical_save_advantage_abilities = gnome.racial_magical_save_advantage_abilities.duplicate()
	var magic_save: Dictionary = rules.resolve_saving_throw("intelligence", 0, 12, gnome_state, false, false, [2, 16], {"magical":true})
	assert(bool(magic_save.get("advantage", false)))
	assert(int(magic_save.get("natural", 0)) == 16)

	var orc := _character()
	races.apply_race(orc, "orc")
	var adrenaline: Dictionary = abilities.get_racial_ability(orc)
	var adrenaline_result: Dictionary = ability_system.use_self_ability(orc, adrenaline)
	assert(bool(adrenaline_result.get("success", false)))
	assert(int(adrenaline_result.get("movement_bonus_feet", 0)) == 30)
	assert(int(adrenaline_result.get("temporary_hit_points", 0)) == 2)
	assert(orc.get_resource("adrenaline_rush") == 1)
	assert(orc.get_resource("relentless_endurance") == 1)

	var dragonborn := _character()
	races.apply_race(dragonborn, "dragonborn")
	var breath: Dictionary = abilities.get_racial_ability(dragonborn)
	assert(str(breath.get("effect", "")) == "saving_throw_spell")
	assert(int(breath.get("range_ft", 0)) == 15)
	assert("fire" in dragonborn.racial_damage_resistances)

	var goliath := _character()
	races.apply_race(goliath, "goliath")
	assert(goliath.base_speed_feet == 35)
	assert(goliath.get_resource("stone_endurance") == 1)

	print("Racial trait tests passed.")
	quit(0)


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
