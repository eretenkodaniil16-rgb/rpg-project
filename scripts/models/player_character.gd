class_name PlayerCharacter
extends RefCounted

const DEFAULT_APPEARANCE_COLOR_HEX: String = "#4DA3E8"
const DEFAULT_RACE_ID: String = "human"
const DEFAULT_RULESET_ID: String = "srd_5_2_1"
const DEFAULT_ABILITIES: Dictionary = {
	"strength": 10,
	"dexterity": 10,
	"constitution": 10,
	"intelligence": 10,
	"charisma": 10,
	"wisdom": 10
}
const SKILL_ABILITIES: Dictionary = {
	"acrobatics": "dexterity",
	"animal_handling": "wisdom",
	"arcana": "intelligence",
	"athletics": "strength",
	"deception": "charisma",
	"history": "intelligence",
	"insight": "wisdom",
	"intimidation": "charisma",
	"investigation": "intelligence",
	"medicine": "wisdom",
	"nature": "intelligence",
	"perception": "wisdom",
	"performance": "charisma",
	"persuasion": "charisma",
	"religion": "intelligence",
	"sleight_of_hand": "dexterity",
	"stealth": "dexterity",
	"survival": "wisdom"
}

var character_name: String = ""
var character_class_id: String = ""
var character_class_name: String = ""
var race_id: String = DEFAULT_RACE_ID
var race_name: String = "Человек"
var ruleset_id: String = DEFAULT_RULESET_ID
var background_id: String = ""
var background_name: String = ""
var background_ability_bonuses: Dictionary = {}
var origin_feat_id: String = ""
var origin_applied: bool = false
var skill_proficiencies: Array[String] = []
var saving_throw_proficiencies: Array[String] = []
var tool_proficiencies: Array[String] = []
var weapon_proficiencies: Array[String] = []
var armor_training: Array[String] = []
var language_proficiencies: Array[String] = ["common"]
var expertise_skills: Array[String] = []
var appearance_color_hex: String = DEFAULT_APPEARANCE_COLOR_HEX
var size_category: String = "medium"
var base_speed_feet: int = 30
var darkvision_feet: int = 0
var racial_features: Array[String] = []
var racial_ability_id: String = ""
var racial_damage_resistances: Array[String] = []
var racial_condition_save_advantage: Array[String] = []
var racial_save_advantage_abilities: Array[String] = []
var racial_magical_save_advantage_abilities: Array[String] = []
var racial_short_rest_resources: Array[String] = []
var reroll_natural_one: bool = false
var immune_to_magical_sleep: bool = false
var long_rest_hours: int = 8
var can_move_through_larger_creatures: bool = false
var naturally_stealthy: bool = false
var grapple_escape_advantage: bool = false
var carrying_size_bonus: int = 0
var applied_racial_hit_point_bonus: int = 0
var level: int = 1
var experience: int = 0
var base_abilities: Dictionary = DEFAULT_ABILITIES.duplicate(true)
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


func get_proficiency_bonus() -> int:
	var safe_level: int = maxi(level, 1)
	return clampi(2 + floori(float(safe_level - 1) / 4.0), 2, 6)


func get_skill_ability(skill_id: String) -> String:
	return str(SKILL_ABILITIES.get(skill_id, ""))


func get_skill_modifier(skill_id: String) -> int:
	var ability_id: String = get_skill_ability(skill_id)
	if ability_id.is_empty():
		return 0
	var result: int = get_ability_modifier(ability_id)
	if skill_id in skill_proficiencies:
		result += get_proficiency_bonus()
		if skill_id in expertise_skills:
			result += get_proficiency_bonus()
	return result


func get_saving_throw_modifier(ability_id: String) -> int:
	var result: int = get_ability_modifier(ability_id)
	if ability_id in saving_throw_proficiencies:
		result += get_proficiency_bonus()
	return result


func get_passive_skill(skill_id: String) -> int:
	return 10 + get_skill_modifier(skill_id)


func is_proficient_with_tool(tool_id: String) -> bool:
	return tool_id in tool_proficiencies


func is_proficient_with_weapon(weapon_id_or_category: String) -> bool:
	return weapon_id_or_category in weapon_proficiencies


func has_armor_training(category_id: String) -> bool:
	return category_id in armor_training


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
		"race_id": race_id,
		"race_name": race_name,
		"ruleset_id": ruleset_id,
		"background_id": background_id,
		"background_name": background_name,
		"background_ability_bonuses": background_ability_bonuses.duplicate(true),
		"origin_feat_id": origin_feat_id,
		"origin_applied": origin_applied,
		"skill_proficiencies": skill_proficiencies.duplicate(),
		"saving_throw_proficiencies": saving_throw_proficiencies.duplicate(),
		"tool_proficiencies": tool_proficiencies.duplicate(),
		"weapon_proficiencies": weapon_proficiencies.duplicate(),
		"armor_training": armor_training.duplicate(),
		"language_proficiencies": language_proficiencies.duplicate(),
		"expertise_skills": expertise_skills.duplicate(),
		"appearance_color_hex": appearance_color_hex,
		"size_category": size_category,
		"base_speed_feet": base_speed_feet,
		"darkvision_feet": darkvision_feet,
		"racial_features": racial_features.duplicate(),
		"racial_ability_id": racial_ability_id,
		"racial_damage_resistances": racial_damage_resistances.duplicate(),
		"racial_condition_save_advantage": racial_condition_save_advantage.duplicate(),
		"racial_save_advantage_abilities": racial_save_advantage_abilities.duplicate(),
		"racial_magical_save_advantage_abilities": racial_magical_save_advantage_abilities.duplicate(),
		"racial_short_rest_resources": racial_short_rest_resources.duplicate(),
		"reroll_natural_one": reroll_natural_one,
		"immune_to_magical_sleep": immune_to_magical_sleep,
		"long_rest_hours": long_rest_hours,
		"can_move_through_larger_creatures": can_move_through_larger_creatures,
		"naturally_stealthy": naturally_stealthy,
		"grapple_escape_advantage": grapple_escape_advantage,
		"carrying_size_bonus": carrying_size_bonus,
		"applied_racial_hit_point_bonus": applied_racial_hit_point_bonus,
		"level": level,
		"experience": experience,
		"base_abilities": base_abilities.duplicate(true),
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
	character.race_id = str(data.get("race_id", DEFAULT_RACE_ID))
	character.race_name = str(data.get("race_name", "Человек"))
	character.ruleset_id = str(data.get("ruleset_id", DEFAULT_RULESET_ID))
	character.background_id = str(data.get("background_id", ""))
	character.background_name = str(data.get("background_name", ""))
	var bonus_value: Variant = data.get("background_ability_bonuses", {})
	character.background_ability_bonuses = (bonus_value as Dictionary).duplicate(true) if bonus_value is Dictionary else {}
	character.origin_feat_id = str(data.get("origin_feat_id", ""))
	character.origin_applied = bool(data.get("origin_applied", false))
	character.skill_proficiencies = _unique_string_array(data.get("skill_proficiencies", []))
	character.saving_throw_proficiencies = _unique_string_array(data.get("saving_throw_proficiencies", []))
	character.tool_proficiencies = _unique_string_array(data.get("tool_proficiencies", []))
	character.weapon_proficiencies = _unique_string_array(data.get("weapon_proficiencies", []))
	character.armor_training = _unique_string_array(data.get("armor_training", []))
	character.language_proficiencies = _unique_string_array(data.get("language_proficiencies", ["common"]))
	if character.language_proficiencies.is_empty():
		character.language_proficiencies.append("common")
	character.expertise_skills = _unique_string_array(data.get("expertise_skills", []))
	character.appearance_color_hex = normalize_color_hex(str(data.get("appearance_color_hex", DEFAULT_APPEARANCE_COLOR_HEX)))
	character.size_category = str(data.get("size_category", "medium"))
	character.base_speed_feet = maxi(int(data.get("base_speed_feet", 30)), 0)
	character.darkvision_feet = maxi(int(data.get("darkvision_feet", 0)), 0)
	character.racial_features = _string_array(data.get("racial_features", []))
	character.racial_ability_id = str(data.get("racial_ability_id", ""))
	character.racial_damage_resistances = _string_array(data.get("racial_damage_resistances", []))
	character.racial_condition_save_advantage = _string_array(data.get("racial_condition_save_advantage", []))
	character.racial_save_advantage_abilities = _string_array(data.get("racial_save_advantage_abilities", []))
	character.racial_magical_save_advantage_abilities = _string_array(data.get("racial_magical_save_advantage_abilities", []))
	character.racial_short_rest_resources = _string_array(data.get("racial_short_rest_resources", []))
	character.reroll_natural_one = bool(data.get("reroll_natural_one", false))
	character.immune_to_magical_sleep = bool(data.get("immune_to_magical_sleep", false))
	character.long_rest_hours = clampi(int(data.get("long_rest_hours", 8)), 1, 24)
	character.can_move_through_larger_creatures = bool(data.get("can_move_through_larger_creatures", false))
	character.naturally_stealthy = bool(data.get("naturally_stealthy", false))
	character.grapple_escape_advantage = bool(data.get("grapple_escape_advantage", false))
	character.carrying_size_bonus = maxi(int(data.get("carrying_size_bonus", 0)), 0)
	character.applied_racial_hit_point_bonus = maxi(int(data.get("applied_racial_hit_point_bonus", 0)), 0)
	character.level = maxi(int(data.get("level", 1)), 1)
	character.experience = maxi(int(data.get("experience", 0)), 0)
	var loaded_abilities: Variant = data.get("abilities", {})
	if loaded_abilities is Dictionary:
		for ability_id_value: Variant in DEFAULT_ABILITIES.keys():
			var ability_id: String = str(ability_id_value)
			character.abilities[ability_id] = clampi(int((loaded_abilities as Dictionary).get(ability_id, 10)), 1, 30)
	var loaded_base_abilities: Variant = data.get("base_abilities", character.abilities)
	if loaded_base_abilities is Dictionary:
		for ability_id_value: Variant in DEFAULT_ABILITIES.keys():
			var ability_id: String = str(ability_id_value)
			character.base_abilities[ability_id] = clampi(int((loaded_base_abilities as Dictionary).get(ability_id, character.abilities.get(ability_id, 10))), 1, 30)
	else:
		character.base_abilities = character.abilities.duplicate(true)
	character.maximum_health = maxi(int(data.get("maximum_health", 1)), 1)
	character.current_health = clampi(int(data.get("current_health", character.maximum_health)), 0, character.maximum_health)
	character.hit_die_size = maxi(int(data.get("hit_die_size", 8)), 2)
	character.hit_dice_maximum = maxi(int(data.get("hit_dice_maximum", character.level)), 1)
	character.hit_dice_current = clampi(int(data.get("hit_dice_current", character.hit_dice_maximum)), 0, character.hit_dice_maximum)
	character.equipped_weapon_id = str(data.get("equipped_weapon_id", ""))
	character.equipped_armor_id = str(data.get("equipped_armor_id", ""))
	character.equipped_shield_id = str(data.get("equipped_shield_id", ""))
	character.known_features = _string_array(data.get("known_features", []))
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
	character.race_id = DEFAULT_RACE_ID
	character.race_name = "Человек"
	character.ruleset_id = DEFAULT_RULESET_ID
	character.background_id = "legacy_origin"
	character.background_name = "Наследие прежней версии"
	character.origin_applied = true
	character.appearance_color_hex = DEFAULT_APPEARANCE_COLOR_HEX
	character.maximum_health = 10
	character.current_health = 10
	character.hit_die_size = 10
	character.hit_dice_maximum = 1
	character.hit_dice_current = 1
	character.base_abilities = character.abilities.duplicate(true)
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


static func _string_array(value: Variant) -> Array[String]:
	var result: Array[String] = []
	if value is Array:
		for item: Variant in value:
			result.append(str(item))
	return result


static func _unique_string_array(value: Variant) -> Array[String]:
	var result: Array[String] = []
	for item: String in _string_array(value):
		if not item.is_empty() and item not in result:
			result.append(item)
	return result
