class_name ClassDataSystem
extends RefCounted

const CLASSES_PATH: String = "res://data/classes/classes.json"
const ABILITIES_PATH: String = "res://data/abilities/abilities.json"

var _classes: Dictionary = {}
var _abilities: Dictionary = {}


func _init() -> void:
	_load_databases()


func ensure_starting_loadout(character: PlayerCharacter) -> bool:
	if character.starter_loadout_granted:
		return false
	var state: Node = _get_game_state()
	if state == null:
		return false
	var class_data: Dictionary = get_class_definition(character.character_class_id)
	if class_data.is_empty():
		return false
	var items_value: Variant = class_data.get("starting_items", {})
	if items_value is Dictionary:
		for item_id_value: Variant in (items_value as Dictionary).keys():
			var item_id: String = str(item_id_value)
			state.call("add_item", item_id, int((items_value as Dictionary)[item_id_value]), false)
	var equipment_value: Variant = class_data.get("equipment", {})
	var equipment: Dictionary = equipment_value as Dictionary if equipment_value is Dictionary else {}
	character.equipped_weapon_id = str(equipment.get("weapon", ""))
	character.equipped_armor_id = str(equipment.get("armor", ""))
	character.equipped_shield_id = str(equipment.get("shield", ""))
	character.known_features.clear()
	var features_value: Variant = class_data.get("features", [])
	if features_value is Array:
		for feature_value: Variant in features_value:
			character.known_features.append(str(feature_value))
	character.signature_ability_id = str(class_data.get("signature_ability", ""))
	_initialize_signature_resource(character)
	if character.character_class_id == "rogue":
		character.active_effects["sneak_attack_ready"] = true
	character.starter_loadout_granted = true
	state.call("save_game")
	return true


func get_class_definition(class_id: String) -> Dictionary:
	var value: Variant = _classes.get(class_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func get_ability_definition(ability_id: String) -> Dictionary:
	var value: Variant = _abilities.get(ability_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func get_signature_ability(character: PlayerCharacter) -> Dictionary:
	return get_ability_definition(character.signature_ability_id)


func get_feature_views(character: PlayerCharacter) -> Array:
	var result: Array = []
	for feature_id: String in character.known_features:
		var feature: Dictionary = get_ability_definition(feature_id)
		if not feature.is_empty():
			result.append(feature)
	return result


func equip_item(character: PlayerCharacter, item_id: String) -> bool:
	var state: Node = _get_game_state()
	if state == null or not bool(state.call("has_item", item_id)):
		return false
	var item: Dictionary = state.call("get_item_definition", item_id) as Dictionary
	match str(item.get("type", "")):
		"weapon":
			character.equipped_weapon_id = item_id
		"armor":
			character.equipped_armor_id = item_id
		"shield":
			character.equipped_shield_id = item_id
		_:
			return false
	state.call("save_game")
	return true


func is_equipped(character: PlayerCharacter, item_id: String) -> bool:
	return item_id in [character.equipped_weapon_id, character.equipped_armor_id, character.equipped_shield_id]


func get_equipped_weapon(character: PlayerCharacter) -> Dictionary:
	var state: Node = _get_game_state()
	if state == null or character.equipped_weapon_id.is_empty():
		return {}
	return state.call("get_item_definition", character.equipped_weapon_id) as Dictionary


func get_armor_class(character: PlayerCharacter) -> int:
	var state: Node = _get_game_state()
	if state == null:
		return 10 + character.get_ability_modifier("dexterity")
	var dexterity: int = character.get_ability_modifier("dexterity")
	var armor: Dictionary = state.call("get_item_definition", character.equipped_armor_id) as Dictionary
	var shield: Dictionary = state.call("get_item_definition", character.equipped_shield_id) as Dictionary
	var armor_class: int
	if armor.is_empty() or str(armor.get("armor_category", "")) == "clothing":
		if character.character_class_id == "barbarian":
			armor_class = 10 + dexterity + character.get_ability_modifier("constitution")
		elif character.character_class_id == "monk" and shield.is_empty():
			armor_class = 10 + dexterity + character.get_ability_modifier("wisdom")
		else:
			armor_class = 10 + dexterity
	else:
		var dexterity_cap: int = int(armor.get("dex_cap", 99))
		var dexterity_bonus: int = 0 if dexterity_cap == 0 else mini(dexterity, dexterity_cap)
		armor_class = int(armor.get("base_ac", 10)) + dexterity_bonus
		if character.character_class_id == "fighter":
			armor_class += 1
	if not shield.is_empty():
		armor_class += int(shield.get("ac_bonus", 2))
	return maxi(armor_class, 0)


func long_rest(character: PlayerCharacter) -> void:
	character.current_health = character.maximum_health
	character.restore_class_resources()
	if character.character_class_id == "rogue":
		character.active_effects["sneak_attack_ready"] = true
	var state: Node = _get_game_state()
	if state != null:
		state.call("save_game")


func get_resource_text(character: PlayerCharacter, ability: Dictionary) -> String:
	var resource_key: String = str(ability.get("resource_key", "unlimited"))
	if resource_key == "unlimited" or resource_key.is_empty():
		return "Без ограничений"
	return "%d / %d" % [character.get_resource(resource_key), character.get_resource_maximum(resource_key)]


func _initialize_signature_resource(character: PlayerCharacter) -> void:
	var ability: Dictionary = get_signature_ability(character)
	var resource_key: String = str(ability.get("resource_key", "unlimited"))
	if resource_key == "unlimited" or resource_key.is_empty():
		return
	var maximum: int = int(ability.get("max_uses", 0))
	var formula: String = str(ability.get("max_uses_formula", ""))
	if formula == "charisma_modifier_min_1":
		maximum = maxi(character.get_ability_modifier("charisma"), 1)
	elif formula == "wisdom_modifier_min_1":
		maximum = maxi(character.get_ability_modifier("wisdom"), 1)
	character.set_resource(resource_key, maximum, maximum)


func _get_game_state() -> Node:
	var main_loop: MainLoop = Engine.get_main_loop()
	if main_loop is SceneTree:
		return (main_loop as SceneTree).root.get_node_or_null("GameState")
	return null


func _load_databases() -> void:
	var class_root: Dictionary = _load_json(CLASSES_PATH)
	var classes_value: Variant = class_root.get("classes", [])
	if classes_value is Array:
		for class_value: Variant in classes_value:
			if class_value is Dictionary:
				var class_data: Dictionary = class_value as Dictionary
				_classes[str(class_data.get("id", ""))] = class_data
	_abilities = _load_json(ABILITIES_PATH)


func _load_json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		push_error("Файл данных не найден: %s" % path)
		return {}
	var file: FileAccess = FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {}
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	return parsed as Dictionary if parsed is Dictionary else {}
