class_name OriginFeatSystem
extends RefCounted

const ALERT_FEAT_ID: String = "alert"
const SAVAGE_ATTACKER_FEAT_ID: String = "savage_attacker"
const MAGIC_INITIATE_CLERIC_FEAT_ID: String = "magic_initiate_cleric"
const MAGIC_INITIATE_WIZARD_FEAT_ID: String = "magic_initiate_wizard"
const SAVAGE_ATTACKER_READY_KEY: String = "savage_attacker_available"

const MAGIC_INITIATE_ABILITIES: Dictionary = {
	MAGIC_INITIATE_CLERIC_FEAT_ID: ["sacred_flame", "toll_the_dead", "origin_cure_wounds"],
	MAGIC_INITIATE_WIZARD_FEAT_ID: ["fire_bolt", "poison_spray", "origin_magic_missile"]
}
const MAGIC_INITIATE_RESOURCES: Dictionary = {
	MAGIC_INITIATE_CLERIC_FEAT_ID: "magic_initiate_cleric_1",
	MAGIC_INITIATE_WIZARD_FEAT_ID: "magic_initiate_wizard_1"
}


func initialize_character(character: PlayerCharacter, refill_resources: bool = false) -> void:
	if character == null or character.origin_feat_id.is_empty():
		return
	_append_unique(character.known_features, character.origin_feat_id)
	if character.origin_feat_id == SAVAGE_ATTACKER_FEAT_ID:
		character.active_effects[SAVAGE_ATTACKER_READY_KEY] = true
	var abilities: Array[String] = get_magic_initiate_abilities(character)
	for ability_id: String in abilities:
		_append_unique(character.known_features, ability_id)
	var resource_key: String = get_magic_initiate_resource_key(character)
	if resource_key.is_empty():
		return
	var had_resource: bool = character.class_resource_maximums.has(resource_key)
	var current: int = character.get_resource(resource_key)
	character.class_resource_maximums[resource_key] = 1
	character.class_resources[resource_key] = 1 if refill_resources or not had_resource else clampi(current, 0, 1)


func begin_turn(character: PlayerCharacter) -> void:
	if character != null and character.origin_feat_id == SAVAGE_ATTACKER_FEAT_ID:
		character.active_effects[SAVAGE_ATTACKER_READY_KEY] = true


func initiative_proficiency_bonus(character: PlayerCharacter) -> int:
	if character == null or character.origin_feat_id != ALERT_FEAT_ID:
		return 0
	return character.get_proficiency_bonus()


func can_apply_savage_attacker(character: PlayerCharacter, turn_based: bool) -> bool:
	if character == null or character.origin_feat_id != SAVAGE_ATTACKER_FEAT_ID:
		return false
	return not turn_based or bool(character.active_effects.get(SAVAGE_ATTACKER_READY_KEY, true))


func consume_savage_attacker(character: PlayerCharacter, turn_based: bool) -> void:
	if character == null or not turn_based:
		return
	character.active_effects[SAVAGE_ATTACKER_READY_KEY] = false


func get_magic_initiate_abilities(character: PlayerCharacter) -> Array[String]:
	var result: Array[String] = []
	if character == null:
		return result
	var value: Variant = MAGIC_INITIATE_ABILITIES.get(character.origin_feat_id, [])
	if value is Array:
		for ability_value: Variant in value:
			result.append(str(ability_value))
	return result


func get_magic_initiate_resource_key(character: PlayerCharacter) -> String:
	return "" if character == null else str(MAGIC_INITIATE_RESOURCES.get(character.origin_feat_id, ""))


func is_magic_initiate_ability(character: PlayerCharacter, ability_id: String) -> bool:
	return ability_id in get_magic_initiate_abilities(character)


static func _append_unique(values: Array[String], value: String) -> void:
	if not value.is_empty() and value not in values:
		values.append(value)
