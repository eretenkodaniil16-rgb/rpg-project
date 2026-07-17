class_name ClassAbilitySystem
extends RefCounted

var _dice: DiceRoller = DiceRoller.new()
var _srd_rules: SrdCombatRules = SrdCombatRules.new()


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
		"heal_2d8_wisdom": return _heal_with_dice(character, ability, 2, 8, character.get_ability_modifier("wisdom"))
		"heal_1d10_level": return _heal_with_dice(character, ability, 1, 10, character.level)
		"lay_on_hands": return _use_lay_on_hands(character, ability)
		_: return _failure("Эта особенность действует пассивно и не требует активации.")


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
	damage_rolls_override: Array[int] = [],
	attack_context: Dictionary = {}
) -> AttackResult:
	var result: AttackResult = AttackResult.new()
	result.attack_name = str(ability.get("name", "Магическая атака"))
	result.target_name = str(attack_context.get("target_name", "Цель"))
	result.damage_type = _srd_rules.normalize_damage_type(str(ability.get("damage_type", "force")))
	result.is_spell = true
	result.cover_bonus = maxi(int(attack_context.get("cover_bonus", 0)), 0)
	result.target_armor_class = maxi(target_armor_class + result.cover_bonus, 0)
	result.distance_feet = maxi(int(attack_context.get("distance_feet", 0)), 0)
	var maximum_range: int = int(ability.get("range_ft", 5))
	result.range_state = "normal" if result.distance_feet <= maximum_range else "out_of_range"
	result.out_of_range = result.range_state == "out_of_range"
	if result.out_of_range:
		result.note = "Цель находится дальше %d футов." % maximum_range
		return result
	if bool(attack_context.get("total_cover", false)):
		result.automatic_miss = true
		result.note = "Цель находится за полным укрытием."
		return result

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
		result.damage_before_mitigation = result.damage
		return result
	if effect == "saving_throw_spell":
		var ability_id_for_spell: String = str(ability.get("ability", "charisma"))
		var save_ability: String = str(ability.get("save_ability", "dexterity"))
		var spell_dc: int = int(ability.get("save_dc", 8 + CombatSystem.proficiency_bonus_for_level(character.level) + character.get_ability_modifier(ability_id_for_spell)))
		var defender_state: CombatantState = attack_context.get("defender_state") as CombatantState
		var save_modifier: int = int(attack_context.get("target_save_modifier", 0))
		var save_result: Dictionary = _srd_rules.resolve_saving_throw(save_ability, save_modifier, spell_dc, defender_state)
		var rolled_damage: int = _roll_damage(dice_count, die_sides, damage_rolls_override) + int(ability.get("damage_bonus", 0))
		result.automatic_hit = true
		result.hit = not bool(save_result.get("success", false)) or bool(ability.get("save_for_half", false))
		result.natural_roll = int(save_result.get("natural", 0))
		result.total = int(save_result.get("total", 0))
		result.damage = floori(float(rolled_damage) / 2.0) if bool(save_result.get("success", false)) and bool(ability.get("save_for_half", false)) else (0 if bool(save_result.get("success", false)) else rolled_damage)
		result.damage_before_mitigation = result.damage
		result.note = "%s спасбросок: %d против Сл %d — %s." % [save_ability, result.total, spell_dc, "успех" if bool(save_result.get("success", false)) else "провал"]
		return result

	var ability_id: String = str(ability.get("ability", "charisma"))
	result.ability_name = _ability_name(ability_id)
	result.ability_modifier = character.get_ability_modifier(ability_id)
	result.proficiency_bonus = CombatSystem.proficiency_bonus_for_level(character.level)
	result.attack_bonus = result.ability_modifier + result.proficiency_bonus + int(ability.get("attack_bonus", 0))
	var attacker_state: CombatantState = attack_context.get("attacker_state") as CombatantState
	var defender_state: CombatantState = attack_context.get("defender_state") as CombatantState
	var adjustments: Dictionary = _srd_rules.attack_roll_adjustments(
		attacker_state,
		defender_state,
		result.distance_feet,
		bool(attack_context.get("attacker_can_see_defender", true)),
		bool(attack_context.get("defender_can_see_attacker", true))
	)
	if bool(adjustments.get("blocked", false)):
		result.automatic_miss = true
		result.note = "Текущее состояние не позволяет сотворить атакующее заклинание."
		return result
	result.advantage = bool(attack_context.get("advantage", false)) or bool(adjustments.get("advantage", false))
	result.disadvantage = bool(attack_context.get("disadvantage", false)) or bool(adjustments.get("disadvantage", false))
	if result.advantage and result.disadvantage:
		result.advantage = false
		result.disadvantage = false
	result.first_roll = clampi(natural_roll_override, 1, 20) if natural_roll_override >= 1 else _dice.roll_die(20)
	if result.advantage or result.disadvantage:
		var second_override: int = int(attack_context.get("second_roll_override", -1))
		result.second_roll = clampi(second_override, 1, 20) if second_override >= 1 else _dice.roll_die(20)
		result.natural_roll = maxi(result.first_roll, result.second_roll) if result.advantage else mini(result.first_roll, result.second_roll)
	else:
		result.natural_roll = result.first_roll
	result.total = result.natural_roll + result.attack_bonus + consume_bardic_inspiration(character)
	result.automatic_miss = result.natural_roll == 1
	result.critical = result.natural_roll == 20 or bool(adjustments.get("automatic_critical", false))
	result.hit = not result.automatic_miss and (result.critical or result.total >= result.target_armor_class)
	if result.cover_bonus > 0:
		result.note = "Укрытие цели повышает КД на +%d." % result.cover_bonus
	if result.hit:
		result.damage = _roll_damage(dice_count * (2 if result.critical else 1), die_sides, damage_rolls_override)
		result.damage_before_mitigation = result.damage
	if attacker_state != null:
		attacker_state.hidden = false
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
		total += clampi(int(overrides[index]), 1, sides) if index < overrides.size() else _dice.roll_die(sides)
	return total


func _success(message: String) -> Dictionary:
	return {"success": true, "message": message, "healing": 0}


func _failure(message: String) -> Dictionary:
	return {"success": false, "message": message, "healing": 0}


func _ability_name(ability_id: String) -> String:
	return {"strength":"Сила", "dexterity":"Ловкость", "wisdom":"Мудрость", "intelligence":"Интеллект", "charisma":"Харизма"}.get(ability_id, ability_id)
