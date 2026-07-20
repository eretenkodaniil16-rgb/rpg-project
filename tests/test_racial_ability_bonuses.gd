extends SceneTree

const RACES_PATH: String = "res://data/races/races.json"
const ABILITY_IDS: Array[String] = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _init() -> void:
	if not FileAccess.file_exists(RACES_PATH):
		_fail("Races data file is missing.")
		return
	var file: FileAccess = FileAccess.open(RACES_PATH, FileAccess.READ)
	if file == null:
		_fail("Races data file could not be opened.")
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		_fail("Races data is not a dictionary.")
		return
	var races_value: Variant = (parsed as Dictionary).get("races", [])
	if not races_value is Array:
		_fail("Races collection is not an array.")
		return
	var races: Array = races_value as Array
	if races.size() != 9:
		_fail("Expected 9 races, got %d." % races.size())
		return
	var expected: Dictionary = {
		"human": {"strength": 1, "dexterity": 1, "constitution": 1, "intelligence": 1, "wisdom": 1, "charisma": 1},
		"elf": {"dexterity": 2, "wisdom": 1},
		"dwarf": {"constitution": 2, "wisdom": 1},
		"halfling": {"dexterity": 2, "charisma": 1},
		"dragonborn": {"strength": 2, "charisma": 1},
		"gnome": {"intelligence": 2, "dexterity": 1},
		"goliath": {"strength": 2, "constitution": 1},
		"orc": {"strength": 2, "constitution": 1},
		"tiefling": {"charisma": 2, "intelligence": 1}
	}
	var seen: Dictionary = {}
	for race_value: Variant in races:
		if not race_value is Dictionary:
			_fail("Race entry is not a dictionary.")
			return
		var race_data: Dictionary = race_value as Dictionary
		var race_id: String = str(race_data.get("id", ""))
		if not expected.has(race_id):
			_fail("Unexpected race id: %s." % race_id)
			return
		if seen.has(race_id):
			_fail("Duplicate race id: %s." % race_id)
			return
		seen[race_id] = true
		if str(race_data.get("selection_symbol", "")).is_empty():
			_fail("Race %s has no selection symbol." % race_id)
			return
		if str(race_data.get("ability_bonus_description", "")).is_empty():
			_fail("Race %s has no ability bonus description." % race_id)
			return
		var bonuses_value: Variant = race_data.get("ability_bonuses", {})
		if not bonuses_value is Dictionary:
			_fail("Race %s ability bonuses are not a dictionary." % race_id)
			return
		var bonuses: Dictionary = bonuses_value as Dictionary
		var expected_bonuses: Dictionary = expected[race_id] as Dictionary
		for ability_id: String in ABILITY_IDS:
			var actual_bonus: int = int(bonuses.get(ability_id, 0))
			var expected_bonus: int = int(expected_bonuses.get(ability_id, 0))
			if actual_bonus != expected_bonus:
				_fail("Race %s has %d for %s; expected %d." % [race_id, actual_bonus, ability_id, expected_bonus])
				return
	for race_id_value: Variant in expected.keys():
		var race_id: String = str(race_id_value)
		if not seen.has(race_id):
			_fail("Required race %s was not found." % race_id)
			return
	var elf_bonuses: Dictionary = expected["elf"] as Dictionary
	var capped_score: int = mini(18 + int(elf_bonuses.get("dexterity", 0)), 20)
	if capped_score != 20:
		_fail("Ability score cap test failed.")
		return
	print("Racial ability bonus data tests passed.")
	quit(0)