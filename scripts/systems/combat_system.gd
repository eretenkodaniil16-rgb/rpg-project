class_name CombatSystem
extends RefCounted

var _dice_roller: DiceRoller = DiceRoller.new()


func perform_unarmed_strike(
	character: PlayerCharacter,
	target_armor_class: int,
	natural_roll_override: int = -1
) -> AttackResult:
	var result: AttackResult = AttackResult.new()
	result.natural_roll = (
		clampi(natural_roll_override, 1, 20)
		if natural_roll_override >= 1
		else _dice_roller.roll_die(20)
	)
	result.ability_modifier = character.get_ability_modifier("strength")
	result.proficiency_bonus = proficiency_bonus_for_level(character.level)
	result.attack_bonus = result.ability_modifier + result.proficiency_bonus
	result.total = result.natural_roll + result.attack_bonus
	result.target_armor_class = maxi(target_armor_class, 0)
	result.automatic_miss = result.natural_roll == 1
	result.critical = result.natural_roll == 20
	result.hit = not result.automatic_miss and (
		result.critical or result.total >= result.target_armor_class
	)
	result.damage = maxi(0, 1 + result.ability_modifier) if result.hit else 0
	return result


static func proficiency_bonus_for_level(level: int) -> int:
	var safe_level: int = clampi(level, 1, 20)
	return 2 + floori(float(safe_level - 1) / 4.0)
