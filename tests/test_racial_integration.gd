extends SceneTree


func _init() -> void:
	var races := RaceDataSystem.new()
	var character := PlayerCharacter.new()
	character.level = 5
	character.maximum_health = 20
	character.current_health = 20
	character.class_resources["class_test_resource"] = 1
	character.class_resource_maximums["class_test_resource"] = 1

	races.apply_race(character, "goliath")
	assert(character.get_resource_maximum("stone_endurance") == 3)
	character.consume_resource("stone_endurance", 1)

	races.apply_race(character, "orc")
	assert(not character.class_resources.has("stone_endurance"))
	assert(not character.class_resource_maximums.has("stone_endurance"))
	assert(character.get_resource_maximum("adrenaline_rush") == 3)
	assert(character.get_resource("relentless_endurance") == 1)
	assert(character.get_resource("class_test_resource") == 1)

	races.apply_race(character, "human")
	assert(not character.class_resources.has("adrenaline_rush"))
	assert(not character.class_resources.has("relentless_endurance"))
	assert(character.get_resource("human_inspiration") == 1)
	assert(character.get_resource("class_test_resource") == 1)

	var social := CombatSocialActionSystem.new()
	var human_actions: Array[Dictionary] = social.get_actions(character.race_id)
	assert(not _contains_action(human_actions, "thaumaturgy_booming_voice"))

	races.apply_race(character, "tiefling")
	var tiefling_actions: Array[Dictionary] = social.get_actions(character.race_id)
	assert(_contains_action(tiefling_actions, "thaumaturgy_booming_voice"))

	print("Racial integration tests passed.")
	quit(0)


func _contains_action(actions: Array[Dictionary], action_id: String) -> bool:
	for action: Dictionary in actions:
		if str(action.get("id", "")) == action_id:
			return true
	return false
