class_name SkillCheckSystem
extends RefCounted

const ABILITY_NAMES: Dictionary = {
	"strength": "Сила",
	"dexterity": "Ловкость",
	"constitution": "Телосложение",
	"intelligence": "Интеллект",
	"wisdom": "Мудрость",
	"charisma": "Харизма"
}
const SKILL_NAMES: Dictionary = {
	"acrobatics":"Акробатика", "animal_handling":"Уход за животными", "arcana":"Магия",
	"athletics":"Атлетика", "deception":"Обман", "history":"История",
	"insight":"Проницательность", "intimidation":"Запугивание", "investigation":"Анализ",
	"medicine":"Медицина", "nature":"Природа", "perception":"Восприятие",
	"performance":"Выступление", "persuasion":"Убеждение", "religion":"Религия",
	"sleight_of_hand":"Ловкость рук", "stealth":"Скрытность", "survival":"Выживание"
}

var _dice_roller: DiceRoller = DiceRoller.new()


func perform_check(
	character: PlayerCharacter,
	ability_id: String,
	difficulty: int,
	bonus: int = 0,
	forced_natural_roll: int = 0,
	forced_second_roll: int = 0,
	forced_lucky_reroll: int = 0,
	forced_disadvantage: bool = false
) -> SkillCheckResult:
	var normalized_ability: String = ability_id.strip_edges().to_lower()
	var result: SkillCheckResult = SkillCheckResult.new()
	result.ability_id = normalized_ability
	result.ability_name = str(ABILITY_NAMES.get(normalized_ability, normalized_ability.capitalize()))
	result.first_roll = _racial_d20(character, forced_natural_roll, forced_lucky_reroll)
	var racial_advantage: bool = bool(character.active_effects.get("racial_advantage_next_d20", false))
	if racial_advantage:
		character.active_effects.erase("racial_advantage_next_d20")
	result.advantage = racial_advantage
	result.disadvantage = forced_disadvantage
	if result.advantage and result.disadvantage:
		result.advantage = false
		result.disadvantage = false
	if result.advantage or result.disadvantage:
		result.second_roll = _racial_d20(character, forced_second_roll, 0)
		result.natural_roll = maxi(result.first_roll, result.second_roll) if result.advantage else mini(result.first_roll, result.second_roll)
	else:
		result.natural_roll = result.first_roll
	result.ability_modifier = character.get_ability_modifier(normalized_ability)
	var inspiration_bonus: int = 0
	var inspiration_die: int = int(character.active_effects.get("bardic_inspiration_die", 0))
	if inspiration_die > 0:
		inspiration_bonus = _dice_roller.roll_die(inspiration_die)
		character.active_effects.erase("bardic_inspiration_die")
	result.bonus = bonus + inspiration_bonus
	result.total = result.natural_roll + result.ability_modifier + result.bonus
	result.difficulty = clampi(difficulty, 1, 30)
	result.success = result.total >= result.difficulty
	return result


func perform_skill_check(
	character: PlayerCharacter,
	skill_id: String,
	difficulty: int,
	bonus: int = 0,
	forced_natural_roll: int = 0,
	forced_second_roll: int = 0,
	forced_lucky_reroll: int = 0,
	forced_disadvantage: bool = false,
	forced_guidance_roll: int = 0
) -> SkillCheckResult:
	var normalized_skill: String = skill_id.strip_edges().to_lower()
	var ability_id: String = character.get_skill_ability(normalized_skill)
	var skill_training_bonus: int = character.get_skill_modifier(normalized_skill) - character.get_ability_modifier(ability_id)
	var guidance_bonus: int = 0
	var has_guidance: bool = bool(character.active_effects.get(SpellcastingSystem.GUIDANCE_ACTIVE_KEY, false))
	if has_guidance:
		guidance_bonus = clampi(forced_guidance_roll, 1, 4) if forced_guidance_roll > 0 else _dice_roller.roll_die(4)
	var result: SkillCheckResult = perform_check(
		character,
		ability_id,
		difficulty,
		bonus + skill_training_bonus + guidance_bonus,
		forced_natural_roll,
		forced_second_roll,
		forced_lucky_reroll,
		forced_disadvantage
	)
	if has_guidance:
		SpellcastingSystem.new().end_concentration(character)
	result.skill_id = normalized_skill
	result.ability_name = str(SKILL_NAMES.get(normalized_skill, normalized_skill.capitalize()))
	return result


func _racial_d20(character: PlayerCharacter, override: int, lucky_reroll_override: int) -> int:
	var natural: int = clampi(override, 1, 20) if override > 0 else _dice_roller.roll_die(20)
	if natural == 1 and character.reroll_natural_one:
		natural = clampi(lucky_reroll_override, 1, 20) if lucky_reroll_override > 0 else _dice_roller.roll_die(20)
	return natural


static func difficulty_name(difficulty: int) -> String:
	if difficulty <= 8:
		return "Очень легко"
	if difficulty <= 10:
		return "Легко"
	if difficulty <= 12:
		return "Обычно"
	if difficulty <= 15:
		return "Сложно"
	if difficulty <= 18:
		return "Очень сложно"
	return "Исключительно сложно"
