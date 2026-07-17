extends SceneTree

const CLASS_IDS: Array[String] = [
	"barbarian", "bard", "cleric", "druid", "fighter", "monk",
	"paladin", "ranger", "rogue", "sorcerer", "warlock", "wizard"
]


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	var service := ClassDataSystem.new()

	for class_id: String in CLASS_IDS:
		var class_data: Dictionary = service.get_class_definition(class_id)
		if class_data.is_empty():
			_fail("Class definition is missing: %s" % class_id)
			return
		var starting_items: Dictionary = class_data.get("starting_items", {}) as Dictionary
		if starting_items.is_empty():
			_fail("Starting items are empty: %s" % class_id)
			return
		for item_id_value: Variant in starting_items.keys():
			var item_id: String = str(item_id_value)
			if state.call("get_item_definition", item_id).is_empty():
				_fail("%s references missing item: %s" % [class_id, item_id])
				return
		var signature_id: String = str(class_data.get("signature_ability", ""))
		if signature_id.is_empty() or service.get_ability_definition(signature_id).is_empty():
			_fail("Signature ability is missing: %s" % class_id)
			return
		var features: Array = class_data.get("features", []) as Array
		if features.is_empty():
			_fail("Feature list is empty: %s" % class_id)
			return
		for feature_value: Variant in features:
			if service.get_ability_definition(str(feature_value)).is_empty():
				_fail("%s references missing feature: %s" % [class_id, str(feature_value)])
				return

	state.call("new_game")
	var fighter := PlayerCharacter.new()
	fighter.character_class_id = "fighter"
	fighter.abilities["dexterity"] = 6
	state.set("player_character", fighter)
	if not service.ensure_starting_loadout(fighter):
		_fail("Fighter loadout was not granted.")
		return
	if int(state.call("get_item_count", "greatsword")) != 1 or fighter.equipped_weapon_id != "greatsword":
		_fail("Fighter weapon was not granted or equipped.")
		return
	var gold_before: int = int(state.call("get_item_count", "gold_coin"))
	if service.ensure_starting_loadout(fighter) or int(state.call("get_item_count", "gold_coin")) != gold_before:
		_fail("Starter loadout was duplicated.")
		return
	if service.get_armor_class(fighter) != 17:
		_fail("Heavy armor or Defense style AC is incorrect.")
		return

	state.call("new_game")
	var monk := PlayerCharacter.new()
	monk.character_class_id = "monk"
	monk.abilities["dexterity"] = 16
	monk.abilities["wisdom"] = 14
	state.set("player_character", monk)
	service.ensure_starting_loadout(monk)
	if service.get_armor_class(monk) != 15:
		_fail("Monk Unarmored Defense AC is incorrect.")
		return

	print("Class loadout tests passed.")
	quit(0)
