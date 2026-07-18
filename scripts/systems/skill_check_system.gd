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

var _dice_roller: DiceRoller = DiceRoller.new()


func perform_check(
	character: PlayerCharacter,
	ability_id: String,
	difficulty: int,
	bonus: int = 0,
	forced_natural_roll: int = 0,
	forced_second_roll: int = 0,
	forced_lucky_reroll: int = 0
) -> SkillCheckResult:
	var normalized_ability: String = ability_id.strip_edges().to_lower()
	var result: SkillCheckResult = SkillCheckResult.new()
	result.ability_id = normalized_ability
	result.ability_name = str(ABILITY_NAMES.get(normalized_ability, normalized_ability.capitalize()))
	var first: int = _racial_d20(character, forced_natural_roll, forced_lucky_reroll)
	var racial_advantage: bool = bool(character.active_effects.get("racial_advantage_next_d20", false))
	if racial_advantage:
		character.active_effects.erase("racial_advantage_next_d20")
		var second: int = _racial_d20(character, forced_second_roll, 0)
		result.natural_roll = maxi(first, second)
	else:
		result.natural_roll = first
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
