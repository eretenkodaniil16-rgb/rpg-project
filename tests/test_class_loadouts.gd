extends SceneTree

const CLASS_IDS: Array[String] = [
	"barbarian", "bard", "cleric", "druid", "fighter", "monk",
	"paladin", "ranger", "rogue", "sorcerer", "warlock", "wizard"
]


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	assert(state != null)
	var service := ClassDataSystem.new()

	for class_id: String in CLASS_IDS:
		state.call("new_game")
		var character := PlayerCharacter.new()
		character.character_name = "Тестер"
		character.character_class_id = class_id
		character.character_class_name = str(service.get_class_definition(class_id).get("name", class_id))
		state.set("player_character", character)
		assert(service.ensure_starting_loadout(character))
		assert(character.starter_loadout_granted)
		assert(not character.signature_ability_id.is_empty())
		assert(not character.known_features.is_empty())
		assert(not service.get_signature_ability(character).is_empty())
		var class_data: Dictionary = service.get_class_definition(class_id)
		var starting_items: Dictionary = class_data.get("starting_items", {}) as Dictionary
		assert(not starting_items.is_empty())
		for item_id_value: Variant in starting_items.keys():
			var item_id: String = str(item_id_value)
			assert(int(state.call("get_item_count", item_id)) == int(starting_items[item_id_value]))
		var snapshot: Dictionary = (state.get("inventory") as Dictionary).duplicate(true)
		assert(not service.ensure_starting_loadout(character))
		assert(state.get("inventory") == snapshot)

	var fighter := PlayerCharacter.new()
	fighter.character_class_id = "fighter"
	fighter.abilities["dexterity"] = 6
	state.call("new_game")
	state.set("player_character", fighter)
	service.ensure_starting_loadout(fighter)
	assert(service.get_armor_class(fighter) == 17)

	var monk := PlayerCharacter.new()
	monk.character_class_id = "monk"
	monk.abilities["dexterity"] = 16
	monk.abilities["wisdom"] = 14
	state.call("new_game")
	state.set("player_character", monk)
	service.ensure_starting_loadout(monk)
	assert(service.get_armor_class(monk) == 15)

	print("Class loadout tests passed.")
	quit(0)
