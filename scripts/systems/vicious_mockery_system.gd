class_name ViciousMockerySystem
extends RefCounted

const SPELL_ID: String = "vicious_mockery"
const RANGE_FEET: int = 60

var _rules: SrdCombatRules = SrdCombatRules.new()
var _dice: DiceRoller = DiceRoller.new()
var _spellcasting: SpellcastingSystem = SpellcastingSystem.new()


func get_definition() -> Dictionary:
	return {
		"id": SPELL_ID,
		"name": "Злая насмешка",
		"kind": "active",
		"is_spell": true,
		"spell_level": 0,
		"school": "Очарование",
		"target": "enemy",
		"resource_key": "unlimited",
		"always_prepared": true,
		"effect": "vicious_mockery",
		"ability": "charisma",
		"save_ability": "wisdom",
		"damage_dice": [1, 6],
		"damage_type": "psychic",
		"range_ft": RANGE_FEET,
		"casting_time_text": "1 действие",
		"components": ["v"],
		"description": "Существо, которое вы видите или слышите в пределах 60 футов, совершает спасбросок Мудрости. При провале получает психический урон и помеху на следующий бросок атаки до конца своего следующего хода.",
		"button": "ЗЛАЯ НАСМЕШКА"
	}


func validate_cast(
	character: PlayerCharacter,
	distance_feet: int,
	can_see_or_hear_target: bool,
	casting_context: Dictionary
) -> Dictionary:
	if character == null:
		return _failure("Заклинатель не определён.")
	if character.character_class_id != "bard":
		return _failure("Злая насмешка доступна Барду.")
	if SPELL_ID not in character.known_features:
		return _failure("Злая насмешка не выбрана среди заговоров Барда.")
	if maxi(distance_feet, 0) > RANGE_FEET:
		return _failure("Цель находится дальше 60 футов.")
	if not can_see_or_hear_target:
		return _failure("Цель нельзя ни увидеть, ни услышать.")
	var components: Dictionary = _spellcasting.check_spell_components(get_definition(), casting_context)
	if not bool(components.get("success", false)):
		return _failure(str(components.get("message", "Нельзя произнести вербальный компонент.")))
	return {"success": true, "message": "Злая насмешка доступна."}


func resolve(
	character: PlayerCharacter,
	target_name: String,
	target_state: CombatantState,
	target_wisdom_save_modifier: int,
	distance_feet: int,
	can_see_or_hear_target: bool,
	casting_context: Dictionary,
	save_roll_overrides: Array[int] = [],
	damage_rolls_override: Array[int] = []
) -> Dictionary:
	var validation: Dictionary = validate_cast(character, distance_feet, can_see_or_hear_target, casting_context)
	if not bool(validation.get("success", false)):
		return validation
	var spell_dc: int = 8 + CombatSystem.proficiency_bonus_for_level(character.level) + character.get_ability_modifier("charisma")
	var save_result: Dictionary = _rules.resolve_saving_throw(
		"wisdom",
		target_wisdom_save_modifier,
		spell_dc,
		target_state,
		false,
		false,
		save_roll_overrides,
		{"magical": true, "spell_id": SPELL_ID}
	)
	var failed_save: bool = not bool(save_result.get("success", false))
	var result := AttackResult.new()
	result.attack_name = "Злая насмешка"
	result.target_name = target_name
	result.damage_type = "psychic"
	result.is_spell = true
	result.automatic_hit = true
	result.hit = failed_save
	result.natural_roll = int(save_result.get("natural", 0))
	result.first_roll = result.natural_roll
	result.total = int(save_result.get("total", 0))
	result.target_armor_class = spell_dc
	result.distance_feet = maxi(distance_feet, 0)
	result.note = "Спасбросок Мудрости: %d против Сл %d — %s." % [
		result.total,
		spell_dc,
		"провал" if failed_save else "успех"
	]
	if failed_save:
		var dice_count: int = cantrip_dice_count(character.level)
		result.damage = _roll_damage(dice_count, 6, damage_rolls_override)
		result.damage_before_mitigation = result.damage
		result.note += " Следующий бросок атаки цели совершается с помехой."
	else:
		result.damage = 0
		result.damage_before_mitigation = 0
	return {
		"success": true,
		"failed_save": failed_save,
		"spell_dc": spell_dc,
		"save": save_result,
		"result": result,
		"message": (
			"%s не выдерживает Злую насмешку." % target_name
			if failed_save
			else "%s выдерживает Злую насмешку." % target_name
		)
	}


func cantrip_dice_count(character_level: int) -> int:
	if character_level >= 17:
		return 4
	if character_level >= 11:
		return 3
	if character_level >= 5:
		return 2
	return 1


func _roll_damage(count: int, sides: int, overrides: Array[int]) -> int:
	var total: int = 0
	for index: int in range(maxi(count, 1)):
		if index < overrides.size():
			total += clampi(overrides[index], 1, sides)
		else:
			total += _dice.roll_die(sides)
	return total


func _failure(message: String) -> Dictionary:
	return {
		"success": false,
		"failed_save": false,
		"message": message
	}
