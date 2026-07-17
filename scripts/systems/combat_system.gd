class_name CombatSystem
extends RefCounted

var _dice_roller: DiceRoller = DiceRoller.new()


func perform_basic_attack(
	character: PlayerCharacter,
	target_armor_class: int,
	weapon: Dictionary = {},
	natural_roll_override: int = -1,
	damage_rolls_override: Array[int] = []
) -> AttackResult:
	var result: AttackResult = AttackResult.new()
	var is_unarmed: bool = weapon.is_empty()
	result.attack_name = "Безоружный удар" if is_unarmed else str(weapon.get("name", "Атака оружием"))
	result.damage_type = "дробящий" if is_unarmed else str(weapon.get("damage_type", "физический"))
	result.target_armor_class = maxi(target_armor_class, 0)

	var ability_id: String = _attack_ability(character, weapon, is_unarmed)
	result.ability_name = _ability_name(ability_id)
	result.ability_modifier = character.get_ability_modifier(ability_id)
	result.proficiency_bonus = proficiency_bonus_for_level(character.level)
	result.attack_bonus = result.ability_modifier + result.proficiency_bonus
	result.natural_roll = clampi(natural_roll_override, 1, 20) if natural_roll_override >= 1 else _dice_roller.roll_die(20)
	var inspiration_bonus: int = _consume_bardic_inspiration(character)
	result.total = result.natural_roll + result.attack_bonus + inspiration_bonus
	result.automatic_miss = result.natural_roll == 1
	result.critical = result.natural_roll == 20
	result.hit = not result.automatic_miss and (result.critical or result.total >= result.target_armor_class)
	if not result.hit:
		return result

	var damage_dice: Array = weapon.get("damage_dice", [1, 1]) as Array if not is_unarmed else [1, 1]
	if is_unarmed and character.character_class_id == "monk":
		damage_dice = [1, 6]
	var dice_count: int = maxi(int(damage_dice[0]) if damage_dice.size() > 0 else 1, 1)
	var die_sides: int = maxi(int(damage_dice[1]) if damage_dice.size() > 1 else 1, 1)
	if is_unarmed and character.character_class_id != "monk":
		result.damage = maxi(0, 1 + result.ability_modifier)
	else:
		result.damage = maxi(0, _roll_damage(dice_count * (2 if result.critical else 1), die_sides, damage_rolls_override) + result.ability_modifier)

	if ability_id == "strength" and int(character.active_effects.get("rage_attacks", 0)) > 0:
		result.bonus_damage += 2
		character.active_effects["rage_attacks"] = int(character.active_effects["rage_attacks"]) - 1
		if int(character.active_effects["rage_attacks"]) <= 0:
			character.active_effects.erase("rage_attacks")
		result.note = "Ярость: +2 урона."

	if int(character.active_effects.get("hunters_mark_hits", 0)) > 0:
		var mark_damage: int = _roll_damage(2 if result.critical else 1, 6, [])
		result.bonus_damage += mark_damage
		character.active_effects["hunters_mark_hits"] = int(character.active_effects["hunters_mark_hits"]) - 1
		if int(character.active_effects["hunters_mark_hits"]) <= 0:
			character.active_effects.erase("hunters_mark_hits")
		result.note = _append_note(result.note, "Метка охотника: +%d." % mark_damage)

	if character.character_class_id == "rogue" and bool(character.active_effects.get("sneak_attack_ready", false)):
		var sneak_damage: int = _roll_damage(2 if result.critical else 1, 6, [])
		result.bonus_damage += sneak_damage
		character.active_effects["sneak_attack_ready"] = false
		result.note = _append_note(result.note, "Скрытая атака: +%d." % sneak_damage)

	result.damage += result.bonus_damage
	return result


func perform_unarmed_strike(
	character: PlayerCharacter,
	target_armor_class: int,
	natural_roll_override: int = -1
) -> AttackResult:
	return perform_basic_attack(character, target_armor_class, {}, natural_roll_override)


func _attack_ability(character: PlayerCharacter, weapon: Dictionary, is_unarmed: bool) -> String:
	if character.character_class_id == "monk":
		var properties_value: Variant = weapon.get("properties", [])
		var properties: Array = properties_value as Array if properties_value is Array else []
		if is_unarmed or not properties.has("ranged"):
			return "dexterity"
	var rule: String = str(weapon.get("ability", "strength"))
	if rule == "finesse":
		return "dexterity" if character.get_ability_modifier("dexterity") > character.get_ability_modifier("strength") else "strength"
	return rule if rule in ["strength", "dexterity"] else "strength"


func _consume_bardic_inspiration(character: PlayerCharacter) -> int:
	var die_sides: int = int(character.active_effects.get("bardic_inspiration_die", 0))
	if die_sides <= 0:
		return 0
	character.active_effects.erase("bardic_inspiration_die")
	return _dice_roller.roll_die(die_sides)


func _roll_damage(count: int, sides: int, overrides: Array[int]) -> int:
	if sides <= 1:
		return count
	var total: int = 0
	for index: int in range(count):
		total += clampi(int(overrides[index]), 1, sides) if index < overrides.size() else _dice_roller.roll_die(sides)
	return total


func _append_note(current: String, addition: String) -> String:
	return addition if current.is_empty() else "%s %s" % [current, addition]


func _ability_name(ability_id: String) -> String:
	return {"strength":"Сила", "dexterity":"Ловкость"}.get(ability_id, ability_id)


static func proficiency_bonus_for_level(level: int) -> int:
	var safe_level: int = clampi(level, 1, 20)
	return 2 + floori(float(safe_level - 1) / 4.0)
