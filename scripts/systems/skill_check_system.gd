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
	forced_natural_roll: int = 0
) -> SkillCheckResult:
	var normalized_ability: String = ability_id.strip_edges().to_lower()
	var result: SkillCheckResult = SkillCheckResult.new()
	result.ability_id = normalized_ability
	result.ability_name = str(ABILITY_NAMES.get(normalized_ability, normalized_ability.capitalize()))
	result.natural_roll = clampi(forced_natural_roll, 1, 20) if forced_natural_roll > 0 else _dice_roller.roll_die(20)
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
