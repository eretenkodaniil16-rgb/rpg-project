class_name RaceDataSystem
extends RefCounted

const RACES_PATH: String = "res://data/races/races.json"
const DEFAULT_RACE_ID: String = "human"
const SIZE_RANKS: Dictionary = {"tiny": 0, "small": 1, "medium": 2, "large": 3, "huge": 4, "gargantuan": 5}

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

func apply_race(character: PlayerCharacter, race_id: String, preserve_health_ratio: bool = false, refill_resources: bool = true) -> void:
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
	character.racial_save_advantage_abilities = _string_array(race.get("save_advantage_abilities", []))
	character.racial_magical_save_advantage_abilities = _string_array(race.get("magical_save_advantage_abilities", []))
	character.racial_short_rest_resources = _string_array(race.get("short_rest_resources", []))
	character.reroll_natural_one = bool(race.get("reroll_natural_one", false))
	character.immune_to_magical_sleep = bool(race.get("immune_to_magical_sleep", false))
	character.long_rest_hours = clampi(int(race.get("long_rest_hours", 8)), 1, 24)
	character.can_move_through_larger_creatures = bool(race.get("can_move_through_larger_creatures", false))
	character.naturally_stealthy = bool(race.get("naturally_stealthy", false))
	character.grapple_escape_advantage = bool(race.get("grapple_escape_advantage", false))
	character.carrying_size_bonus = maxi(int(race.get("carrying_size_bonus", 0)), 0)
	_remove_obsolete_racial_resources(character, race)
	_initialize_resources(character, race, refill_resources)
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
	var selected_id: String = character.race_id if not character.race_id.is_empty() else DEFAULT_RACE_ID
	var stored_current: int = character.current_health
	apply_race(character, selected_id, true, false)
	character.current_health = clampi(stored_current, 0, character.maximum_health)

func recharge_short_rest_resources(character: PlayerCharacter) -> void:
	if character == null:
		return
	for resource_key: String in character.racial_short_rest_resources:
		var maximum: int = character.get_resource_maximum(resource_key)
		if maximum > 0:
			character.set_resource(resource_key, maximum, maximum)

func get_hit_point_bonus(character: PlayerCharacter) -> int:
	if character == null:
		return 0
	var race: Dictionary = get_race(character.race_id)
	return maxi(int(race.get("hp_bonus_per_level", 0)), 0) * maxi(character.level, 1)

func get_feature_views(character: PlayerCharacter) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	if character == null:
		return result
	var traits_value: Variant = get_race(character.race_id).get("traits", [])
	if traits_value is Array:
		for value: Variant in traits_value:
			if value is Dictionary:
				result.append((value as Dictionary).duplicate(true))
	return result

func get_racial_ability_id(character: PlayerCharacter) -> String:
	return character.racial_ability_id if character != null else ""

func get_racial_damage_resistances(character: PlayerCharacter) -> Array[String]:
	return character.racial_damage_resistances.duplicate() if character != null else []

static func size_rank(size_category: String) -> int:
	return int(SIZE_RANKS.get(size_category.strip_edges().to_lower(), 2))

func _remove_obsolete_racial_resources(character: PlayerCharacter, selected_race: Dictionary) -> void:
	var selected_resources: Dictionary = {}
	var selected_value: Variant = selected_race.get("resources", {})
	if selected_value is Dictionary:
		selected_resources = selected_value as Dictionary
	var all_racial_keys: Dictionary = {}
	for race_value: Variant in _races.values():
		if not race_value is Dictionary:
			continue
		var resources_value: Variant = (race_value as Dictionary).get("resources", {})
		if not resources_value is Dictionary:
			continue
		for key_value: Variant in (resources_value as Dictionary).keys():
			all_racial_keys[str(key_value)] = true
	for key_value: Variant in all_racial_keys.keys():
		var key: String = str(key_value)
		if selected_resources.has(key):
			continue
		character.class_resources.erase(key)
		character.class_resource_maximums.erase(key)

func _initialize_resources(character: PlayerCharacter, race: Dictionary, refill_resources: bool) -> void:
	var resources_value: Variant = race.get("resources", {})
	if not resources_value is Dictionary:
		return
	for key_value: Variant in (resources_value as Dictionary).keys():
		var key: String = str(key_value)
		var maximum: int = _resource_maximum(character, (resources_value as Dictionary)[key_value])
		var had_resource: bool = character.class_resources.has(key)
		var stored_current: int = character.get_resource(key)
		var current: int = maximum if refill_resources or not had_resource else mini(stored_current, maximum)
		character.set_resource(key, current, maximum)

func _resource_maximum(character: PlayerCharacter, specification: Variant) -> int:
	if specification is Dictionary:
		var data: Dictionary = specification as Dictionary
		var formula: String = str(data.get("formula", "fixed"))
		var value: int = int(data.get("value", 0))
		if formula == "proficiency_bonus":
			value = CombatSystem.proficiency_bonus_for_level(character.level)
		return maxi(value, int(data.get("minimum", 0)))
	return maxi(int(specification), 0)

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
