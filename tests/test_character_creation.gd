extends SceneTree

const CLASSES_PATH: String = "res://data/classes/classes.json"
const RACES_PATH: String = "res://data/races/races.json"


func _init() -> void:
	_test_modifiers()
	_test_ability_rolls()
	_test_character_race_and_appearance()
	_test_classes_file()
	_test_races_file()
	_test_racial_mechanics()
	print("Character creation and racial mechanics tests passed.")
	quit(0)


func _test_modifiers() -> void:
	assert(PlayerCharacter.modifier_for_score(8) == -1)
	assert(PlayerCharacter.modifier_for_score(10) == 0)
	assert(PlayerCharacter.modifier_for_score(15) == 2)
	assert(PlayerCharacter.modifier_for_score(18) == 4)


func _test_ability_rolls() -> void:
	var roller: DiceRoller = DiceRoller.new()
	for _iteration: int in range(200):
		var result: Dictionary = roller.roll_ability_score()
		var dice: Array = result.get("dice", []) as Array
		assert(dice.size() == 4)
		assert(int(result.get("discarded_index", -1)) >= 0)
		assert(int(result.get("discarded_index", -1)) < 4)
		assert(int(result.get("total", 0)) >= 3)
		assert(int(result.get("total", 0)) <= 18)


func _test_character_race_and_appearance() -> void:
	var character: PlayerCharacter = _character()
	var race_data := RaceDataSystem.new()
	race_data.apply_race(character, "dwarf")
	assert(character.race_id == "dwarf")
	assert(character.race_name == "Дворф")
	assert(character.maximum_health == 11)
	assert("poison" in character.racial_damage_resistances)
	var restored: PlayerCharacter = PlayerCharacter.from_dict(character.to_dict())
	assert(restored.race_id == "dwarf")
	assert(restored.race_name == "Дворф")
	assert(restored.appearance_color_hex == character.appearance_color_hex)
	assert(restored.maximum_health == 11)
	var legacy: PlayerCharacter = PlayerCharacter.from_dict({"name":"Старый герой", "class_id":"fighter", "class_name":"Воин", "maximum_health":10, "current_health":10})
	assert(legacy.race_id == "human")
	assert(legacy.race_name == "Человек")
	assert(PlayerCharacter.normalize_color_hex("4fb878") == "#4FB878")
	assert(PlayerCharacter.normalize_color_hex("invalid") == PlayerCharacter.DEFAULT_APPEARANCE_COLOR_HEX)


func _test_classes_file() -> void:
	assert(FileAccess.file_exists(CLASSES_PATH))
	var file: FileAccess = FileAccess.open(CLASSES_PATH, FileAccess.READ)
	assert(file != null)
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	assert(parsed is Dictionary)
	var classes_value: Variant = (parsed as Dictionary).get("classes", [])
	assert(classes_value is Array)
	var classes: Array = classes_value as Array
	assert(classes.size() == 12)
	var ids: Dictionary = {}
	for class_value: Variant in classes:
		assert(class_value is Dictionary)
		var class_data: Dictionary = class_value as Dictionary
		var class_id: String = str(class_data.get("id", ""))
		assert(not class_id.is_empty())
		assert(not ids.has(class_id))
		ids[class_id] = true
		assert(int(class_data.get("hit_die", 0)) in [6, 8, 10, 12])


func _test_races_file() -> void:
	assert(FileAccess.file_exists(RACES_PATH))
	var race_data := RaceDataSystem.new()
	var races: Array[Dictionary] = race_data.get_races()
	assert(races.size() == 9)
	var required_ids: Array[String] = ["human", "elf", "dwarf", "halfling", "dragonborn", "gnome", "goliath", "orc", "tiefling"]
	var seen: Dictionary = {}
	for race: Dictionary in races:
		var race_id: String = str(race.get("id", ""))
		assert(race_id in required_ids)
		assert(not seen.has(race_id))
		seen[race_id] = true
		assert(not str(race.get("name", "")).is_empty())
		assert(not str(race.get("color_hex", "")).is_empty())
		assert(int(race.get("speed_ft", 0)) > 0)
		assert((race.get("traits", []) as Array).size() >= 2)
	for race_id: String in required_ids:
		assert(seen.has(race_id))


func _test_racial_mechanics() -> void:
	var race_data := RaceDataSystem.new()
	var class_data := ClassDataSystem.new()
	var ability_system := ClassAbilitySystem.new()
	var checks := SkillCheckSystem.new()
	var combat := CombatSystem.new()
	var rules := SrdCombatRules.new()

	var human: PlayerCharacter = _character()
	race_data.apply_race(human, "human")
	var human_ability: Dictionary = class_data.get_racial_ability(human)
	assert(bool(ability_system.use_self_ability(human, human_ability).get("success", false)))
	var inspired: SkillCheckResult = checks.perform_check(human, "wisdom", 10, 0, 4, 18)
	assert(inspired.natural_roll == 18)
	assert(not human.active_effects.has("racial_advantage_next_d20"))

	var halfling: PlayerCharacter = _character()
	race_data.apply_race(halfling, "halfling")
	var lucky_check: SkillCheckResult = checks.perform_check(halfling, "dexterity", 10, 0, 1, 0, 15)
	assert(lucky_check.natural_roll == 15)
	var weapon: Dictionary = {"name":"Тестовый меч", "damage_dice":[1,6], "damage_type":"slashing", "ability":"strength", "properties":[]}
	var lucky_attack: AttackResult = combat.perform_basic_attack(halfling, 10, weapon, 1, [4], {"distance_feet":5, "lucky_first_reroll_override":14})
	assert(lucky_attack.natural_roll == 14)
	assert(lucky_attack.hit)

	var dwarf: PlayerCharacter = _character()
	race_data.apply_race(dwarf, "dwarf")
	var dwarf_state := CombatantState.new()
	dwarf_state.damage_resistances = dwarf.racial_damage_resistances.duplicate()
	assert(int(rules.resolve_damage(9, "poison", dwarf_state).get("applied", -1)) == 4)

	var elf: PlayerCharacter = _character()
	race_data.apply_race(elf, "elf")
	var elf_state := CombatantState.new()
	elf_state.saving_throw_advantage_conditions = elf.racial_condition_save_advantage.duplicate()
	var charm_save: Dictionary = rules.resolve_saving_throw("wisdom", 0, 12, elf_state, false, false, [3,17], {"condition_id":"charmed", "magical":true})
	assert(bool(charm_save.get("advantage", false)))
	assert(int(charm_save.get("natural", 0)) == 17)

	var gnome: PlayerCharacter = _character()
	race_data.apply_race(gnome, "gnome")
	var gnome_state := CombatantState.new()
	gnome_state.magical_save_advantage_abilities = gnome.racial_magical_save_advantage_abilities.duplicate()
	var magic_save: Dictionary = rules.resolve_saving_throw("intelligence", 0, 12, gnome_state, false, false, [2,16], {"magical":true})
	assert(bool(magic_save.get("advantage", false)))
	assert(int(magic_save.get("natural", 0)) == 16)

	var orc: PlayerCharacter = _character()
	race_data.apply_race(orc, "orc")
	var adrenaline: Dictionary = class_data.get_racial_ability(orc)
	var adrenaline_result: Dictionary = ability_system.use_self_ability(orc, adrenaline)
	assert(bool(adrenaline_result.get("success", false)))
	assert(int(adrenaline_result.get("movement_bonus_feet", 0)) == 30)
	assert(int(adrenaline_result.get("temporary_hit_points", 0)) == 2)
	assert(orc.get_resource("relentless_endurance") == 1)

	var dragonborn: PlayerCharacter = _character()
	race_data.apply_race(dragonborn, "dragonborn")
	assert(str(class_data.get_racial_ability(dragonborn).get("effect", "")) == "saving_throw_spell")
	assert("fire" in dragonborn.racial_damage_resistances)

	var goliath: PlayerCharacter = _character()
	race_data.apply_race(goliath, "goliath")
	assert(goliath.base_speed_feet == 35)
	assert(goliath.get_resource("stone_endurance") == 1)


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
