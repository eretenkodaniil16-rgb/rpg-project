class_name RaceDataSystem
extends RefCounted

const RACES_PATH: String = "res://data/races/races.json"
const DEFAULT_RACE_ID: String = "human"

var _races: Dictionary = {}


func _init() -> void:
	_load_races()


func get_races() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for value: Variant in _races.values():
		if value is Dictionary:
			result.append((value as Dictionary).duplicate(true))
	result.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return str(a.get("name", "")) < str(b.get("name", "")))
	return result


func get_race(race_id: String) -> Dictionary:
	var value: Variant = _races.get(race_id, _races.get(DEFAULT_RACE_ID, {}))
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func apply_race(character: PlayerCharacter, race_id: String, preserve_health_ratio: bool = false) -> void:
	if character == null:
		return
	var race: Dictionary = get_race(race_id)
	if race.is_empty():
		return
	var old_maximum: int = maxi(character.maximum_health, 1)
	var old_current: int = clampi(character.current_health, 0, old_maximum)
	character.race_id = str(race.get("id", DEFAULT_RACE_ID))
	character.race_name = str(race.get("name", "Человек"))
	character.appearance_color_hex = str(race.get("color_hex", PlayerCharacter.DEFAULT_APPEARANCE_COLOR_HEX))
	character.size_category = str(race.get("size", "medium"))
	character.base_speed_feet = maxi(int(race.get("speed_ft", 30)), 0)
	character.darkvision_feet = maxi(int(race.get("darkvision_ft", 0)), 0)
	character.racial_features.clear()
	var traits_value: Variant = race.get("traits", [])
	if traits_value is Array:
		for trait_value: Variant in traits_value:
			if trait_value is Dictionary:
				character.racial_features.append(str((trait_value as Dictionary).get("id", "")))
	character.racial_ability_id = str(race.get("active_ability_id", ""))
	character.racial_damage_resistances = _string_array(race.get("damage_resistances", []))
	character.racial_condition_save_advantage = _string_array(race.get("condition_save_advantage", []))
	character.racial_magical_save_advantage_abilities = _string_array(race.get("magical_save_advantage_abilities", []))
	character.reroll_natural_one = bool(race.get("reroll_natural_one", false))
	_initialize_resources(character, race)
	var racial_bonus: int = get_hit_point_bonus(character)
	character.maximum_health = maxi(character.maximum_health + racial_bonus - character.applied_racial_hit_point_bonus, 1)
	character.applied_racial_hit_point_bonus = racial_bonus
	if preserve_health_ratio:
		character.current_health = clampi(roundi(float(old_current) / float(old_maximum) * float(character.maximum_health)), 0, character.maximum_health)
	else:
		character.current_health = character.maximum_health


func ensure_character_race(character: PlayerCharacter) -> void:
	if character == null:
		return
	var race_id: String = character.race_id if not character.race_id.is_empty() else DEFAULT_RACE_ID
	var stored_current: int = character.current_health
	var stored_maximum: int = character.maximum_health
	apply_race(character, race_id, true)
	if stored_maximum > 0:
		character.current_health = clampi(stored_current, 0, character.maximum_health)


func get_hit_point_bonus(character: PlayerCharacter) -> int:
	if character == null:
		return 0
	var race: Dictionary = get_race(character.race_id)
	return maxi(int(race.get("hp_bonus_per_level", 0)), 0) * maxi(character.level, 1)


func get_feature_views(character: PlayerCharacter) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	if character == null:
		return result
	var race: Dictionary = get_race(character.race_id)
	var traits_value: Variant = race.get("traits", [])
	if traits_value is Array:
		for value: Variant in traits_value:
			if value is Dictionary:
				result.append((value as Dictionary).duplicate(true))
	return result


func get_racial_ability_id(character: PlayerCharacter) -> String:
	return character.racial_ability_id if character != null else ""


func get_racial_damage_resistances(character: PlayerCharacter) -> Array[String]:
	return character.racial_damage_resistances.duplicate() if character != null else []


func _initialize_resources(character: PlayerCharacter, race: Dictionary) -> void:
	var resources_value: Variant = race.get("resources", {})
	if not resources_value is Dictionary:
		return
	for key_value: Variant in (resources_value as Dictionary).keys():
		var key: String = str(key_value)
		var maximum: int = maxi(int((resources_value as Dictionary)[key_value]), 0)
		character.set_resource(key, maximum, maximum)


func _load_races() -> void:
	_races.clear()
	if not FileAccess.file_exists(RACES_PATH):
		push_error("Файл рас не найден: %s" % RACES_PATH)
		return
	var file: FileAccess = FileAccess.open(RACES_PATH, FileAccess.READ)
	if file == null:
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		push_error("Файл рас содержит некорректный JSON.")
		return
	var races_value: Variant = (parsed as Dictionary).get("races", [])
	if not races_value is Array:
		return
	for value: Variant in races_value:
		if value is Dictionary:
			var race: Dictionary = value as Dictionary
			_races[str(race.get("id", ""))] = race


static func _string_array(value: Variant) -> Array[String]:
	var result: Array[String] = []
	if value is Array:
		for item: Variant in value:
			result.append(str(item))
	return result
