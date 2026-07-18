extends SceneTree

const RACES_PATH: String = "res://data/races/races.json"
const ABILITY_IDS: Array[String] = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]


func _init() -> void:
	assert(FileAccess.file_exists(RACES_PATH))
	var file: FileAccess = FileAccess.open(RACES_PATH, FileAccess.READ)
	assert(file != null)
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	assert(parsed is Dictionary)
	var races_value: Variant = (parsed as Dictionary).get("races", [])
	assert(races_value is Array)
	var races: Array = races_value as Array
	assert(races.size() == 9)
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
		assert(race_value is Dictionary)
		var race_data: Dictionary = race_value as Dictionary
		var race_id: String = str(race_data.get("id", ""))
		assert(expected.has(race_id))
		assert(not seen.has(race_id))
		seen[race_id] = true
		assert(not str(race_data.get("selection_symbol", "")).is_empty())
		assert(not str(race_data.get("ability_bonus_description", "")).is_empty())
		var bonuses_value: Variant = race_data.get("ability_bonuses", {})
		assert(bonuses_value is Dictionary)
		var bonuses: Dictionary = bonuses_value as Dictionary
		assert(bonuses == expected[race_id])
		for ability_id: String in ABILITY_IDS:
			assert(int(bonuses.get(ability_id, 0)) >= 0)
	for race_id: Variant in expected.keys():
		assert(seen.has(str(race_id)))

	var capped_score: int = mini(18 + int((expected["elf"] as Dictionary).get("dexterity", 0)), 20)
	assert(capped_score == 20)
	print("Racial ability bonus data tests passed.")
	quit(0)