extends SceneTree

const CLASSES_PATH: String = "res://data/classes/classes.json"
const RACES_PATH: String = "res://data/races/races.json"


func _init() -> void:
	_test_modifiers()
	_test_ability_rolls()
	_test_character_race_and_appearance()
	_test_classes_file()
	_test_races_file()
	print("Character creation and race tests passed.")
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
	var character: PlayerCharacter = PlayerCharacter.new()
	character.character_name = "Тест"
	character.character_class_id = "fighter"
	character.character_class_name = "Воин"
	character.maximum_health = 10
	character.current_health = 10
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
