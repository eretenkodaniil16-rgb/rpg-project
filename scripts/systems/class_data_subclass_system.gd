class_name ClassDataSubclassSystem
extends ClassDataSystem

var _fighter_subclasses: FighterSubclassSystem = FighterSubclassSystem.new()


func get_ability_definition(ability_id: String) -> Dictionary:
	var base_definition: Dictionary = super.get_ability_definition(ability_id)
	if not base_definition.is_empty():
		return base_definition
	return _fighter_subclasses.get_ability_definition(ability_id)


func get_armor_class(character: PlayerCharacter) -> int:
	var result: int = super.get_armor_class(character)
	if character != null and bool(character.active_effects.get(FighterSubclassSystem.GUARDIAN_ACTIVE_KEY, false)):
		result += 1
	return result


func short_rest(character: PlayerCharacter, roll_override: int = -1) -> Dictionary:
	_fighter_subclasses.ensure_character(character)
	var result: Dictionary = super.short_rest(character, roll_override)
	if bool(result.get("success", false)) and _fighter_subclasses.recharge_short_rest(character):
		_save_state()
		result["subclass_resource_recharged"] = true
	return result


func long_rest(character: PlayerCharacter) -> Dictionary:
	_fighter_subclasses.ensure_character(character)
	var result: Dictionary = super.long_rest(character)
	if bool(result.get("success", false)):
		_fighter_subclasses.clear_combat_effects(character)
		_save_state()
	return result
