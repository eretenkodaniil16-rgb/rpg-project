class_name PlayerCharacter
extends RefCounted

const DEFAULT_APPEARANCE_COLOR_HEX: String = "#4DA3E8"
const DEFAULT_ABILITIES: Dictionary = {
	"strength": 10,
	"dexterity": 10,
	"constitution": 10,
	"intelligence": 10,
	"charisma": 10,
	"wisdom": 10
}

var character_name: String = ""
var character_class_id: String = ""
var character_class_name: String = ""
var appearance_color_hex: String = DEFAULT_APPEARANCE_COLOR_HEX
var level: int = 1
var experience: int = 0
var abilities: Dictionary = DEFAULT_ABILITIES.duplicate(true)
var maximum_health: int = 1
var current_health: int = 1
var hit_die_size: int = 8
var hit_dice_current: int = 0
var hit_dice_maximum: int = 0

var equipped_weapon_id: String = ""
var equipped_armor_id: String = ""
var equipped_shield_id: String = ""
var known_features: Array[String] = []
var signature_ability_id: String = ""
var class_resources: Dictionary = {}
var class_resource_maximums: Dictionary = {}
var active_effects: Dictionary = {}
var starter_loadout_granted: bool = false


func get_ability_score(ability_id: String) -> int:
	return int(abilities.get(ability_id, 10))


func get_ability_modifier(ability_id: String) -> int:
	return modifier_for_score(get_ability_score(ability_id))


func get_resource(resource_key: String) -> int:
	return int(class_resources.get(resource_key, 0))


func get_resource_maximum(resource_key: String) -> int:
	return int(class_resource_maximums.get(resource_key, 0))


func set_resource(resource_key: String, current: int, maximum: int = -1) -> void:
	if resource_key.is_empty() or resource_key == "unlimited":
		return
	if maximum >= 0:
		class_resource_maximums[resource_key] = maximum
	var safe_maximum: int = maxi(get_resource_maximum(resource_key), 0)
	class_resources[resource_key] = clampi(current, 0, safe_maximum)


func consume_resource(resource_key: String, amount: int = 1) -> bool:
	if resource_key.is_empty() or resource_key == "unlimited":
		return true
	var safe_amount: int = maxi(amount, 1)
	if get_resource(resource_key) < safe_amount:
		return false
	class_resources[resource_key] = get_resource(resource_key) - safe_amount
	return true


func restore_class_resources() -> void:
	for key_value: Variant in class_resource_maximums.keys():
		var key: String = str(key_value)
		class_resources[key] = maxi(int(class_resource_maximums[key]), 0)
	active_effects.clear()


func initialize_hit_dice(die_size: int) -> void:
	hit_die_size = maxi(die_size, 2)
	hit_dice_maximum = maxi(level, 1)
	if hit_dice_current <= 0:
		hit_dice_current = hit_dice_maximum
	else:
		hit_dice_current = clampi(hit_dice_current, 0, hit_dice_maximum)


func to_dict() -> Dictionary:
	return {
		"name": character_name,
		"class_id": character_class_id,
		"class_name": character_class_name,
		"appearance_color_hex": appearance_color_hex,
		"level": level,
		"experience": experience,
		"abilities": abilities.duplicate(true),
		"maximum_health": maximum_health,
		"current_health": current_health,
		"hit_die_size": hit_die_size,
		"hit_dice_current": hit_dice_current,
		"hit_dice_maximum": hit_dice_maximum,
		"equipped_weapon_id": equipped_weapon_id,
		"equipped_armor_id": equipped_armor_id,
		"equipped_shield_id": equipped_shield_id,
		"known_features": known_features.duplicate(),
		"signature_ability_id": signature_ability_id,
		"class_resources": class_resources.duplicate(true),
		"class_resource_maximums": class_resource_maximums.duplicate(true),
		"active_effects": active_effects.duplicate(true),
		"starter_loadout_granted": starter_loadout_granted
	}


static func from_dict(data: Dictionary) -> PlayerCharacter:
	var character: PlayerCharacter = PlayerCharacter.new()
	character.character_name = str(data.get("name", "Путник"))
	character.character_class_id = str(data.get("class_id", "fighter"))
	character.character_class_name = str(data.get("class_name", "Воин"))
	character.appearance_color_hex = normalize_color_hex(str(data.get("appearance_color_hex", DEFAULT_APPEARANCE_COLOR_HEX)))
	character.level = maxi(int(data.get("level", 1)), 1)
	character.experience = maxi(int(data.get("experience", 0)), 0)
	var loaded_abilities: Variant = data.get("abilities", {})
	if loaded_abilities is Dictionary:
		for ability_id_value: Variant in DEFAULT_ABILITIES.keys():
			var ability_id: String = str(ability_id_value)
			character.abilities[ability_id] = clampi(int(loaded_abilities.get(ability_id, 10)), 1, 30)
	character.maximum_health = maxi(int(data.get("maximum_health", 1)), 1)
	character.current_health = clampi(int(data.get("current_health", character.maximum_health)), 0, character.maximum_health)
	character.hit_die_size = maxi(int(data.get("hit_die_size", 8)), 2)
	character.hit_dice_maximum = maxi(int(data.get("hit_dice_maximum", character.level)), 1)
	character.hit_dice_current = clampi(int(data.get("hit_dice_current", character.hit_dice_maximum)), 0, character.hit_dice_maximum)
	character.equipped_weapon_id = str(data.get("equipped_weapon_id", ""))
	character.equipped_armor_id = str(data.get("equipped_armor_id", ""))
	character.equipped_shield_id = str(data.get("equipped_shield_id", ""))
	var features_value: Variant = data.get("known_features", [])
	if features_value is Array:
		for feature_value: Variant in features_value:
			character.known_features.append(str(feature_value))
	character.signature_ability_id = str(data.get("signature_ability_id", ""))
	var resources_value: Variant = data.get("class_resources", {})
	character.class_resources = (resources_value as Dictionary).duplicate(true) if resources_value is Dictionary else {}
	var maximums_value: Variant = data.get("class_resource_maximums", {})
	character.class_resource_maximums = (maximums_value as Dictionary).duplicate(true) if maximums_value is Dictionary else {}
	var effects_value: Variant = data.get("active_effects", {})
	character.active_effects = (effects_value as Dictionary).duplicate(true) if effects_value is Dictionary else {}
	character.starter_loadout_granted = bool(data.get("starter_loadout_granted", false))
	return character


static func create_legacy_default() -> PlayerCharacter:
	var character: PlayerCharacter = PlayerCharacter.new()
	character.character_name = "Путник"
	character.character_class_id = "fighter"
	character.character_class_name = "Воин"
	character.appearance_color_hex = DEFAULT_APPEARANCE_COLOR_HEX
	character.maximum_health = 10
	character.current_health = 10
	character.hit_die_size = 10
	character.hit_dice_maximum = 1
	character.hit_dice_current = 1
	return character


static func normalize_color_hex(value: String) -> String:
	var normalized: String = value.strip_edges().to_upper()
	if normalized.length() == 6:
		normalized = "#" + normalized
	if normalized.length() != 7 or not normalized.begins_with("#"):
		return DEFAULT_APPEARANCE_COLOR_HEX
	for index: int in range(1, normalized.length()):
		var character: String = normalized.substr(index, 1)
		if "0123456789ABCDEF".find(character) < 0:
			return DEFAULT_APPEARANCE_COLOR_HEX
	return normalized


static func modifier_for_score(score: int) -> int:
	return floori((float(score) - 10.0) / 2.0)
