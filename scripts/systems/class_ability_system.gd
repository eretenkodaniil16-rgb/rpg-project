class_name ClassAbilitySystem
extends RefCounted

var _dice: DiceRoller = DiceRoller.new()


func use_self_ability(character: PlayerCharacter, ability: Dictionary) -> Dictionary:
	var effect: String = str(ability.get("effect", ""))
	var resource_key: String = str(ability.get("resource_key", "unlimited"))
	if effect in ["rage", "bardic_inspiration"] and not _consume(character, resource_key, 1):
		return _failure("Заряды способности закончились.")

	match effect:
		"rage":
			character.active_effects["rage_attacks"] = 3
			return _success("Ярость активна: следующие три атаки Силой получают +2 к урону.")
		"bardic_inspiration":
			character.active_effects["bardic_inspiration_die"] = 6
			return _success("Вдохновение добавит 1d6 к следующему броску d20.")
		"heal_2d8_wisdom":
			return _heal_with_dice(character, ability, 2, 8, character.get_ability_modifier("wisdom"))
		"heal_1d10_level":
			return _heal_with_dice(character, ability, 1, 10, character.level)
		"lay_on_hands":
			return _use_lay_on_hands(character, ability)
		_:
			return _failure("Эта особенность действует пассивно и не требует активации.")


func apply_target_ability(character: PlayerCharacter, ability: Dictionary) -> Dictionary:
	var effect: String = str(ability.get("effect", ""))
	if effect != "hunters_mark":
		return _failure("Способность не может быть применена к этой цели.")
	var resource_key: String = str(ability.get("resource_key", "hunters_mark"))
	if not _consume(character, resource_key, 1):
		return _failure("Свободные применения Метки охотника закончились.")
	character.active_effects["hunters_mark_hits"] = 3
	return _success("Цель отмечена. Три следующих попадания нанесут дополнительно 1d6 урона.")


func perform_offensive_ability(
	character: PlayerCharacter,
	ability: Dictionary,
	target_armor_class: int,
	natural_roll_override: int = -1,
	damage_rolls_override: Array[int] = []
) -> AttackResult:
	var result: AttackResult = AttackResult.new()
	result.attack_name = str(ability.get("name", "Магическая атака"))
	result.damage_type = str(ability.get("damage_type", "магический"))
	result.is_spell = true
	result.target_armor_class = maxi(target_armor_class, 0)

	var resource_key: String = str(ability.get("resource_key", "unlimited"))
	if not _consume(character, resource_key, 1):
		result.note = "Не осталось доступных применений способности."
		return result

	var dice_value: Variant = ability.get("damage_dice", [1, 6])
	var damage_dice: Array = dice_value as Array if dice_value is Array else [1, 6]
	var dice_count: int = maxi(int(damage_dice[0]) if damage_dice.size() > 0 else 1, 1)
	var die_sides: int = maxi(int(damage_dice[1]) if damage_dice.size() > 1 else 6, 2)
	var effect: String = str(ability.get("effect", "spell_attack"))

	if effect == "auto_hit_spell":
		result.automatic_hit = true
		result.hit = true
		result.natural_roll = 0
		result.total = 0
		result.damage = _roll_damage(dice_count, die_sides, damage_rolls_override) + int(ability.get("damage_bonus", 0))
		return result

	var ability_id: String = str(ability.get("ability", "charisma"))
	result.ability_name = _ability_name(ability_id)
	result.ability_modifier = character.get_ability_modifier(ability_id)
	result.proficiency_bonus = CombatSystem.proficiency_bonus_for_level(character.level)
	result.attack_bonus = result.ability_modifier + result.proficiency_bonus + int(ability.get("attack_bonus", 0))
	result.natural_roll = clampi(natural_roll_override, 1, 20) if natural_roll_override >= 1 else _dice.roll_die(20)
	result.total = result.natural_roll + result.attack_bonus + consume_bardic_inspiration(character)
	result.automatic_miss = result.natural_roll == 1
	result.critical = result.natural_roll == 20
	result.hit = not result.automatic_miss and (result.critical or result.total >= result.target_armor_class)
	if result.hit:
		result.damage = _roll_damage(dice_count * (2 if result.critical else 1), die_sides, damage_rolls_override)
	return result


func consume_bardic_inspiration(character: PlayerCharacter) -> int:
	var die_sides: int = int(character.active_effects.get("bardic_inspiration_die", 0))
	if die_sides <= 0:
		return 0
	character.active_effects.erase("bardic_inspiration_die")
	return _dice.roll_die(die_sides)


func _heal_with_dice(character: PlayerCharacter, ability: Dictionary, count: int, sides: int, bonus: int) -> Dictionary:
	if character.current_health >= character.maximum_health:
		return _failure("Здоровье уже полностью восстановлено.")
	var resource_key: String = str(ability.get("resource_key", "spell_slots_1"))
	if not _consume(character, resource_key, 1):
		return _failure("Не осталось ячеек или применений способности.")
	var amount: int = maxi(0, _roll_damage(count, sides, []) + bonus)
	var before: int = character.current_health
	character.current_health = mini(character.maximum_health, character.current_health + amount)
	var restored: int = character.current_health - before
	return {"success": true, "message": "Восстановлено %d здоровья." % restored, "healing": restored}


func _use_lay_on_hands(character: PlayerCharacter, ability: Dictionary) -> Dictionary:
	if character.current_health >= character.maximum_health:
		return _failure("Здоровье уже полностью восстановлено.")
	var resource_key: String = str(ability.get("resource_key", "lay_on_hands_pool"))
	var available: int = character.get_resource(resource_key)
	if available <= 0:
		return _failure("Запас Наложения рук исчерпан.")
	var missing: int = character.maximum_health - character.current_health
	var amount: int = mini(available, missing)
	character.consume_resource(resource_key, amount)
	character.current_health += amount
	return {"success": true, "message": "Наложение рук восстановило %d здоровья." % amount, "healing": amount}


func _consume(character: PlayerCharacter, resource_key: String, amount: int) -> bool:
	return character.consume_resource(resource_key, amount)


func _roll_damage(count: int, sides: int, overrides: Array[int]) -> int:
	var total: int = 0
	for index: int in range(count):
		if index < overrides.size():
			total += clampi(int(overrides[index]), 1, sides)
		else:
			total += _dice.roll_die(sides)
	return total


func _success(message: String) -> Dictionary:
	return {"success": true, "message": message, "healing": 0}


func _failure(message: String) -> Dictionary:
	return {"success": false, "message": message, "healing": 0}


func _ability_name(ability_id: String) -> String:
	return {
		"strength": "Сила", "dexterity": "Ловкость", "wisdom": "Мудрость",
		"intelligence": "Интеллект", "charisma": "Харизма"
	}.get(ability_id, ability_id)
