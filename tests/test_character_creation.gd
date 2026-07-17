extends SceneTree

const CLASSES_PATH: String = "res://data/classes/classes.json"


func _init() -> void:
	_test_modifiers()
	_test_ability_rolls()
	_test_classes_file()
	print("Character creation tests passed.")
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
