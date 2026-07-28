class_name FighterSubclassSystem
extends RefCounted

const DATA_PATH: String = "res://data/abilities/fighter_subclass_abilities.json"

const GUARDIAN_SUBCLASS_ID: String = "guardian_vanguard"
const TACTICAL_SUBCLASS_ID: String = "tactical_blade"
const GUARDIAN_ABILITY_ID: String = "guardian_stance"
const TACTICAL_ABILITY_ID: String = "tactical_focus"
const GUARDIAN_RESOURCE_KEY: String = "guardian_stance_uses"
const TACTICAL_RESOURCE_KEY: String = "tactical_focus_uses"
const GUARDIAN_ACTIVE_KEY: String = "guardian_stance_active"
const GUARDIAN_ROUND_KEY: String = "guardian_stance_round"
const TACTICAL_READY_KEY: String = "tactical_focus_ready"

var _subclasses: Dictionary = {}
var _abilities: Dictionary = {}


func _init() -> void:
	_load_data()


func ensure_character(character: PlayerCharacter) -> bool:
	if character == null:
		return false
	var changed: bool = false
	var selected_ability_id: String = ability_id_for_character(character)
	var selected_resource_key: String = resource_key_for_ability(selected_ability_id)
	for ability_id: String in [GUARDIAN_ABILITY_ID, TACTICAL_ABILITY_ID]:
		if ability_id == selected_ability_id:
			if ability_id not in character.known_features:
				character.known_features.append(ability_id)
				changed = true
			continue
		if ability_id in character.known_features:
			character.known_features.erase(ability_id)
			changed = true
	for resource_key: String in [GUARDIAN_RESOURCE_KEY, TACTICAL_RESOURCE_KEY]:
		if resource_key == selected_resource_key:
			continue
		if character.class_resources.erase(resource_key):
			changed = true
		if character.class_resource_maximums.erase(resource_key):
			changed = true
	if selected_resource_key.is_empty():
		changed = _clear_runtime_effects(character) or changed
		return changed
	var maximum: int = character.get_proficiency_bonus()
	var had_resource: bool = character.class_resource_maximums.has(selected_resource_key)
	var old_maximum: int = character.get_resource_maximum(selected_resource_key)
	var spent: int = maxi(old_maximum - character.get_resource(selected_resource_key), 0)
	var next_current: int = maximum if not had_resource else clampi(maximum - spent, 0, maximum)
	if old_maximum != maximum or character.get_resource(selected_resource_key) != next_current:
		character.set_resource(selected_resource_key, next_current, maximum)
		changed = true
	return changed


func recharge_short_rest(character: PlayerCharacter) -> bool:
	if character == null:
		return false
	var ability_id: String = ability_id_for_character(character)
	var resource_key: String = resource_key_for_ability(ability_id)
	if resource_key.is_empty():
		return false
	var maximum: int = character.get_resource_maximum(resource_key)
	if maximum <= 0 or character.get_resource(resource_key) == maximum:
		return false
	character.set_resource(resource_key, maximum, maximum)
	return true


func get_ability_definition(ability_id: String) -> Dictionary:
	var value: Variant = _abilities.get(ability_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func get_active_ability_definitions(character: PlayerCharacter) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	var ability_id: String = ability_id_for_character(character)
	var definition: Dictionary = get_ability_definition(ability_id)
	if not definition.is_empty():
		result.append(definition)
	return result


func is_subclass_ability(ability_id: String) -> bool:
	return ability_id in [GUARDIAN_ABILITY_ID, TACTICAL_ABILITY_ID]


func ability_id_for_character(character: PlayerCharacter) -> String:
	if character == null or character.character_class_id != "fighter" or character.level < 3:
		return ""
	match character.subclass_id:
		GUARDIAN_SUBCLASS_ID:
			return GUARDIAN_ABILITY_ID
		TACTICAL_SUBCLASS_ID:
			return TACTICAL_ABILITY_ID
	return ""


func resource_key_for_ability(ability_id: String) -> String:
	match ability_id:
		GUARDIAN_ABILITY_ID:
			return GUARDIAN_RESOURCE_KEY
		TACTICAL_ABILITY_ID:
			return TACTICAL_RESOURCE_KEY
	return ""


func guardian_temporary_hit_points(character: PlayerCharacter) -> int:
	if character == null:
		return 1
	return maxi(character.get_proficiency_bonus() + character.get_ability_modifier("constitution"), 1)


func clear_guardian_stance(character: PlayerCharacter) -> bool:
	if character == null:
		return false
	var changed: bool = false
	for key: String in [GUARDIAN_ACTIVE_KEY, GUARDIAN_ROUND_KEY]:
		if character.active_effects.erase(key):
			changed = true
	return changed


func clear_combat_effects(character: PlayerCharacter) -> bool:
	if character == null:
		return false
	var changed: bool = clear_guardian_stance(character)
	if character.active_effects.erase(TACTICAL_READY_KEY):
		changed = true
	return changed


func _clear_runtime_effects(character: PlayerCharacter) -> bool:
	return clear_combat_effects(character)


func _load_data() -> void:
	if not FileAccess.file_exists(DATA_PATH):
		push_error("Файл способностей подклассов Воина не найден: %s" % DATA_PATH)
		return
	var file: FileAccess = FileAccess.open(DATA_PATH, FileAccess.READ)
	if file == null:
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		push_error("Некорректный JSON способностей подклассов Воина.")
		return
	var root: Dictionary = parsed as Dictionary
	var subclasses_value: Variant = root.get("subclasses", {})
	if subclasses_value is Dictionary:
		_subclasses = (subclasses_value as Dictionary).duplicate(true)
	var abilities_value: Variant = root.get("abilities", {})
	if abilities_value is Dictionary:
		_abilities = (abilities_value as Dictionary).duplicate(true)
