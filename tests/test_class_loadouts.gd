extends SceneTree

const CLASS_IDS: Array[String] = [
	"barbarian", "bard", "cleric", "druid", "fighter", "monk",
	"paladin", "ranger", "rogue", "sorcerer", "warlock", "wizard"
]


func _init() -> void:
	call_deferred("_run")


func _require(condition: bool, message: String) -> bool:
	if condition:
		return true
	push_error(message)
	quit(1)
	return false


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if not _require(state != null, "GameState autoload is missing."):
		return
	var service := ClassDataSystem.new()

	for class_id: String in CLASS_IDS:
		state.call("new_game")
		var class_data: Dictionary = service.get_class_definition(class_id)
		if not _require(not class_data.is_empty(), "Class definition is missing: %s" % class_id):
			return
		var character := PlayerCharacter.new()
		character.character_name = "Тестер"
		character.character_class_id = class_id
		character.character_class_name = str(class_data.get("name", class_id))
		state.set("player_character", character)
		if not _require(service.ensure_starting_loadout(character), "Loadout was not granted: %s" % class_id):
			return
		if not _require(character.starter_loadout_granted, "Loadout marker is false: %s" % class_id):
			return
		if not _require(not character.signature_ability_id.is_empty(), "Signature ability is empty: %s" % class_id):
			return
		if not _require(not character.known_features.is_empty(), "Feature list is empty: %s" % class_id):
			return
		if not _require(not service.get_signature_ability(character).is_empty(), "Signature ability data is missing: %s" % class_id):
			return
		var starting_items: Dictionary = class_data.get("starting_items", {}) as Dictionary
		if not _require(not starting_items.is_empty(), "Starting items are empty: %s" % class_id):
			return
		for item_id_value: Variant in starting_items.keys():
			var item_id: String = str(item_id_value)
			var actual: int = int(state.call("get_item_count", item_id))
			var expected: int = int(starting_items[item_id_value])
			if not _require(actual == expected, "%s: expected %d of %s, got %d" % [class_id, expected, item_id, actual]):
				return
		var snapshot: Dictionary = (state.get("inventory") as Dictionary).duplicate(true)
		if not _require(not service.ensure_starting_loadout(character), "Loadout was granted twice: %s" % class_id):
			return
		if not _require(state.get("inventory") == snapshot, "Inventory changed after duplicate loadout call: %s" % class_id):
			return

	var fighter := PlayerCharacter.new()
	fighter.character_class_id = "fighter"
	fighter.abilities["dexterity"] = 6
	state.call("new_game")
	state.set("player_character", fighter)
	service.ensure_starting_loadout(fighter)
	if not _require(service.get_armor_class(fighter) == 17, "Heavy armor or Defense style AC is incorrect."):
		return

	var monk := PlayerCharacter.new()
	monk.character_class_id = "monk"
	monk.abilities["dexterity"] = 16
	monk.abilities["wisdom"] = 14
	state.call("new_game")
	state.set("player_character", monk)
	service.ensure_starting_loadout(monk)
	if not _require(service.get_armor_class(monk) == 15, "Monk Unarmored Defense AC is incorrect."):
		return

	print("Class loadout tests passed.")
	quit(0)
