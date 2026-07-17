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


func get_ability_score(ability_id: String) -> int:
	return int(abilities.get(ability_id, 10))


func get_ability_modifier(ability_id: String) -> int:
	return modifier_for_score(get_ability_score(ability_id))


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
		"current_health": current_health
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
	return character


static func create_legacy_default() -> PlayerCharacter:
	var character: PlayerCharacter = PlayerCharacter.new()
	character.character_name = "Путник"
	character.character_class_id = "fighter"
	character.character_class_name = "Воин"
	character.appearance_color_hex = DEFAULT_APPEARANCE_COLOR_HEX
	character.maximum_health = 10
	character.current_health = 10
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
