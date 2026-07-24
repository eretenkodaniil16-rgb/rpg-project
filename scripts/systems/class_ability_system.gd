class_name ClassAbilitySystem
extends RefCounted

var _dice: DiceRoller = DiceRoller.new()
var _srd_rules: SrdCombatRules = SrdCombatRules.new()
var _spellcasting: SpellcastingSystem = SpellcastingSystem.new()
var _world_time: WorldTimeSystem = WorldTimeSystem.new()


func use_self_ability(character: PlayerCharacter, ability: Dictionary) -> Dictionary:
	var effect: String = str(ability.get("effect", ""))
	if effect in ["utility_detect_magic", "utility_comprehend_languages"]:
		var state: Node = _get_game_state()
		var current_minutes: int = _world_time.get_minutes(state)
		return _spellcasting.cast_utility_spell(character, ability, current_minutes, false)
	if effect in ["rage", "bardic_inspiration", "racial_inspiration", "adrenaline_rush"] and not _consume_ability_resource(character, ability, 1):
		return _failure("Заряды способности закончились.")
	match effect:
		"rage":
			character.active_effects["rage_attacks"] = 3
			return _success("Ярость активна: следующие три атаки Силой получают +2 к урону.")
		"bardic_inspiration":
			character.active_effects["bardic_inspiration_die"] = 6
			return _success("Вдохновение добавит 1d6 к следующему броску d20.")
		"racial_inspiration":
			character.active_effects["racial_advantage_next_d20"] = true
			return _success("Находчивость даст преимущество на следующую атаку или проверку характеристики.")
		"adrenaline_rush":
			var temporary_hit_points: int = CombatSystem.proficiency_bonus_for_level(character.level)
			return {
				"success": true,
				"message": "Прилив адреналина: добавлено перемещение Рывка и %d временных HP." % temporary_hit_points,
				"healing": 0,
				"movement_bonus_feet": character.base_speed_feet,
				"temporary_hit_points": temporary_hit_points
			}
		"heal_2d8_wisdom":
			return _heal_with_dice(character, ability, 2, 8, character.get_ability_modifier("wisdom"))
		"heal_1d10_level":
			return _heal_with_dice(character, ability, 1, 10, character.level)
		"origin_heal":
			var healing_pair: Array[int] = _int_pair(ability.get("healing_dice", [1, 8]) as Array, [1, 8])
			var ability_id: String = str(ability.get("ability", "wisdom"))
			return _heal_with_dice(character, ability, healing_pair[0], healing_pair[1], character.get_ability_modifier(ability_id))
		"lay_on_hands":
			return _use_lay_on_hands(character, ability)
		_:
			return _failure("Эта особенность действует пассивно и не требует активации.")


func apply_target_ability(character: PlayerCharacter, ability: Dictionary) -> Dictionary:
	var effect: String = str(ability.get("effect", ""))
	if effect != "hunters_mark":
		return _failure("Способность не может быть применена к этой цели.")
	if not _consume_ability_resource(character, ability, 1):
		return _failure("Свободные применения Метки охотника закончились.")
	character.active_effects["hunters_mark_hits"] = 3
	if bool(ability.get("concentration", false)):
		_spellcasting.begin_concentration(character, str(ability.get("id", "hunters_mark")))
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
	result.is_spell = bool(ability.get("is_spell", true))
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
	var cast_slot_level: int = maxi(int(ability.get("spell_level", 0)), 0)
	if _spellcasting.is_spell_definition(ability):
		var payment: Dictionary = _spellcasting.consume_spell_cost_detailed(character, ability, int(attack_context.get("slot_level", 0)), attack_context)
		if not bool(payment.get("success", false)):
			result.note = str(payment.get("message", "Заклинание недоступно."))
			return result
		cast_slot_level = int(payment.get("slot_level", cast_slot_level))
	elif not _consume_ability_resource(character, ability, 1):
		result.note = "Ресурс способности закончился."
		return result
	if bool(ability.get("concentration", false)):
		_spellcasting.begin_concentration(character, str(ability.get("id", "")))
	var damage_dice: Array[int] = _damage_dice_for_level(ability, character.level)
	damage_dice = _spellcasting.scale_dice_for_slot(ability, damage_dice, cast_slot_level, "damage")
	var dice_count: int = maxi(damage_dice[0] if damage_dice.size() > 0 else 1, 1)
	var die_sides: int = maxi(damage_dice[1] if damage_dice.size() > 1 else 6, 2)
	if bool(attack_context.get("target_wounded", false)) and int(ability.get("wounded_damage_die", 0)) > 0:
		die_sides = int(ability.get("wounded_damage_die", die_sides))
	var effect: String = str(ability.get("effect", "spell_attack"))
	if effect == "auto_hit_spell":
		result.automatic_hit = true
		result.hit = true
		result.natural_roll = 0
		result.total = 0
		result.damage = _roll_damage(dice_count, die_sides, damage_rolls_override) + _spellcasting.damage_bonus_for_slot(ability, cast_slot_level)
		result.damage_before_mitigation = result.damage
		return result
	if effect == "saving_throw_spell":
		var ability_id_for_spell: String = _spellcasting.get_spellcasting_ability(character, ability)
		if ability_id_for_spell.is_empty():
			ability_id_for_spell = str(ability.get("ability", "charisma"))
		var save_ability: String = str(ability.get("save_ability", "dexterity"))
		var spell_dc: int = int(ability.get("save_dc", 8 + CombatSystem.proficiency_bonus_for_level(character.level) + character.get_ability_modifier(ability_id_for_spell)))
		var defender_state: CombatantState = attack_context.get("defender_state") as CombatantState
		var save_modifier: int = int(attack_context.get("target_save_modifier", 0))
		var save_result: Dictionary = _srd_rules.resolve_saving_throw(save_ability, save_modifier, spell_dc, defender_state, false, false, [], {"magical": result.is_spell})
		var rolled_damage: int = _roll_damage(dice_count, die_sides, damage_rolls_override) + _spellcasting.damage_bonus_for_slot(ability, cast_slot_level)
		result.automatic_hit = true
		result.hit = not bool(save_result.get("success", false)) or bool(ability.get("save_for_half", false))
		result.natural_roll = int(save_result.get("natural", 0))
		result.total = int(save_result.get("total", 0))
		result.damage = floori(float(rolled_damage) / 2.0) if bool(save_result.get("success", false)) and bool(ability.get("save_for_half", false)) else (0 if bool(save_result.get("success", false)) else rolled_damage)
		result.damage_before_mitigation = result.damage
		result.note = "%s спасбросок: %d против Сл %d — %s." % [save_ability, result.total, spell_dc, "успех" if bool(save_result.get("success", false)) else "провал"]
		return result

	var ability_id: String = _spellcasting.get_spellcasting_ability(character, ability)
	if ability_id.is_empty():
		ability_id = str(ability.get("ability", "charisma"))
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
	var racial_advantage: bool = bool(character.active_effects.get("racial_advantage_next_d20", false))
	result.advantage = bool(attack_context.get("advantage", false)) or bool(adjustments.get("advantage", false)) or racial_advantage
	result.disadvantage = bool(attack_context.get("disadvantage", false)) or bool(adjustments.get("disadvantage", false))
	if result.advantage and result.disadvantage:
		result.advantage = false
		result.disadvantage = false
	if racial_advantage:
		character.active_effects.erase("racial_advantage_next_d20")
	result.first_roll = _racial_d20(character, natural_roll_override, int(attack_context.get("lucky_first_reroll_override", -1)))
	if result.advantage or result.disadvantage:
		var second_override: int = int(attack_context.get("second_roll_override", -1))
		result.second_roll = _racial_d20(character, second_override, int(attack_context.get("lucky_second_reroll_override", -1)))
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


func can_pay_ability_cost(character: PlayerCharacter, ability: Dictionary) -> bool:
	if _spellcasting.is_spell_definition(ability):
		return _spellcasting.can_cast_spell(character, ability, false, false)
	var resource_key: String = str(ability.get("resource_key", "unlimited"))
	if resource_key.is_empty() or resource_key == "unlimited":
		return true
	if character.get_resource(resource_key) > 0:
		return true
	var fallback_key: String = str(ability.get("fallback_resource_key", ""))
	return not fallback_key.is_empty() and character.get_resource(fallback_key) > 0


func active_resource_key(character: PlayerCharacter, ability: Dictionary) -> String:
	if _spellcasting.is_spell_definition(ability):
		return _spellcasting.active_resource_key(character, ability)
	var resource_key: String = str(ability.get("resource_key", "unlimited"))
	if resource_key.is_empty() or resource_key == "unlimited":
		return "unlimited"
	if character.get_resource(resource_key) > 0:
		return resource_key
	var fallback_key: String = str(ability.get("fallback_resource_key", ""))
	return fallback_key if not fallback_key.is_empty() and character.get_resource(fallback_key) > 0 else resource_key


func _damage_dice_for_level(ability: Dictionary, level: int) -> Array[int]:
	var selected: Array[int] = [1, 6]
	var base_value: Variant = ability.get("damage_dice", selected)
	if base_value is Array:
		selected = _int_pair(base_value as Array, selected)
	var progression_value: Variant = ability.get("damage_dice_progression", {})
	if not progression_value is Dictionary:
		return selected
	var best_level: int = -1
	for threshold_value: Variant in (progression_value as Dictionary).keys():
		var threshold: int = int(str(threshold_value))
		if threshold <= level and threshold > best_level:
			var dice_value: Variant = (progression_value as Dictionary)[threshold_value]
			if dice_value is Array:
				selected = _int_pair(dice_value as Array, selected)
				best_level = threshold
	return selected


func _int_pair(value: Array, fallback: Array[int]) -> Array[int]:
	if value.size() < 2:
		return fallback
	return [maxi(int(value[0]), 1), maxi(int(value[1]), 2)]


func _heal_with_dice(character: PlayerCharacter, ability: Dictionary, count: int, sides: int, bonus: int) -> Dictionary:
	if character.current_health >= character.maximum_health:
		return _failure("Здоровье уже полностью восстановлено.")
	var slot_level: int = maxi(int(ability.get("spell_level", 0)), 0)
	if _spellcasting.is_spell_definition(ability):
		var payment: Dictionary = _spellcasting.consume_spell_cost_detailed(character, ability)
		if not bool(payment.get("success", false)):
			return _failure(str(payment.get("message", "Заклинание недоступно.")))
		slot_level = int(payment.get("slot_level", slot_level))
	elif not _consume_ability_resource(character, ability, 1):
		return _failure("Ресурс способности закончился.")
	var healing_dice: Array[int] = _spellcasting.scale_dice_for_slot(ability, [count, sides], slot_level, "healing")
	var amount: int = maxi(0, _roll_damage(healing_dice[0], healing_dice[1], []) + bonus)
	var before: int = character.current_health
	character.current_health = mini(character.maximum_health, character.current_health + amount)
	var restored: int = character.current_health - before
	return {"success": true, "message": "Восстановлено %d здоровья ячейкой %d уровня." % [restored, slot_level], "healing": restored, "slot_level": slot_level}


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


func _consume_ability_resource(character: PlayerCharacter, ability: Dictionary, amount: int) -> bool:
	if _spellcasting.is_spell_definition(ability):
		return _spellcasting.consume_spell_cost(character, ability)
	var resource_key: String = str(ability.get("resource_key", "unlimited"))
	if resource_key.is_empty() or resource_key == "unlimited":
		return true
	if character.consume_resource(resource_key, amount):
		return true
	var fallback_key: String = str(ability.get("fallback_resource_key", ""))
	return not fallback_key.is_empty() and character.consume_resource(fallback_key, amount)


func _racial_d20(character: PlayerCharacter, override: int, lucky_reroll_override: int = -1) -> int:
	var natural: int = clampi(override, 1, 20) if override >= 1 else _dice.roll_die(20)
	if natural == 1 and character.reroll_natural_one:
		natural = clampi(lucky_reroll_override, 1, 20) if lucky_reroll_override >= 1 else _dice.roll_die(20)
	return natural


func _roll_damage(count: int, sides: int, overrides: Array[int]) -> int:
	var total: int = 0
	for index: int in range(count):
		total += clampi(int(overrides[index]), 1, sides) if index < overrides.size() else _dice.roll_die(sides)
	return total


func _get_game_state() -> Node:
	var main_loop: MainLoop = Engine.get_main_loop()
	if main_loop is SceneTree:
		return (main_loop as SceneTree).root.get_node_or_null("GameState")
	return null


func _success(message: String) -> Dictionary:
	return {"success": true, "message": message, "healing": 0}


func _failure(message: String) -> Dictionary:
	return {"success": false, "message": message, "healing": 0}


func _ability_name(ability_id: String) -> String:
	return {"strength":"Сила", "dexterity":"Ловкость", "wisdom":"Мудрость", "intelligence":"Интеллект", "charisma":"Харизма", "constitution":"Телосложение"}.get(ability_id, ability_id)
