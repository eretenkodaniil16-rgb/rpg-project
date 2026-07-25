class_name DamageFallReactionSystem
extends RefCounted

const HELLISH_REBUKE_SPELL_ID: String = "hellish_rebuke"
const SLOW_FALL_FEATURE_ID: String = "slow_fall"

const TRIGGER_CREATURE_DAMAGE_RECEIVED: String = "creature_damage_received"
const TRIGGER_FALL_DAMAGE_PENDING: String = "fall_damage_pending"

const HELLISH_REBUKE_RANGE_FEET: int = 60
const SLOW_FALL_MINIMUM_LEVEL: int = 4

var _spellcasting: SpellcastingSystem = SpellcastingSystem.new()
var _rules: SrdCombatRules = SrdCombatRules.new()
var _dice: DiceRoller = DiceRoller.new()


func get_slow_fall_definition() -> Dictionary:
	return {
		"id": SLOW_FALL_FEATURE_ID,
		"name": "Медленное падение",
		"kind": "reaction",
		"class_id": "monk",
		"required_level": SLOW_FALL_MINIMUM_LEVEL,
		"reaction_trigger": TRIGGER_FALL_DAMAGE_PENDING,
		"description": "Монах 4 уровня или выше может реакцией уменьшить урон от падения на величину, равную пятикратному уровню монаха."
	}


func evaluate_hellish_rebuke(character: PlayerCharacter, context: Dictionary) -> Dictionary:
	if character == null:
		return _unavailable("Нет персонажа, способного использовать Адское возмездие.")
	if not bool(context.get("reaction_available", false)):
		return _unavailable("Реакция уже потрачена.")
	if not bool(context.get("reactor_can_react", true)) or character.current_health <= 0:
		return _unavailable("Персонаж не способен совершить реакцию.")
	if str(context.get("trigger_id", "")) != TRIGGER_CREATURE_DAMAGE_RECEIVED:
		return _unavailable("Триггер не позволяет использовать Адское возмездие.")
	if maxi(int(context.get("damage_applied", 0)), 0) <= 0:
		return _unavailable("Урон не был получен.")
	if not bool(context.get("source_is_creature", false)):
		return _unavailable("Источник урона не является существом.")
	if not bool(context.get("can_see_source", false)):
		return _unavailable("Нужно видеть существо, нанёсшее урон.")
	var distance_feet: int = maxi(int(context.get("distance_feet", 0)), 0)
	if distance_feet > HELLISH_REBUKE_RANGE_FEET:
		return _unavailable("Источник находится дальше 60 футов.")
	var spell: Dictionary = _spellcasting.get_spell_definition(HELLISH_REBUKE_SPELL_ID)
	if spell.is_empty():
		return _unavailable("Определение заклинания Адское возмездие отсутствует.")
	# Обычные классовые и договорные ячейки определяются профилем персонажа.
	# Поле resource_key в каталоге служит только описанием и не должно фиксировать
	# Колдуна высокого уровня на pact_slots_1.
	spell.erase("resource_key")
	spell.erase("fallback_resource_key")
	_spellcasting.ensure_character(character, false)
	var casting_context: Dictionary = context.get("casting_context", {}) as Dictionary
	var requested_slot_level: int = maxi(int(context.get("slot_level", 0)), 0)
	if not _spellcasting.can_cast_spell(character, spell, false, true, requested_slot_level, casting_context):
		return _unavailable("Адское возмездие не подготовлено, нет ячейки или недоступны компоненты.")
	var slot_level: int = _spellcasting.resolve_slot_level(character, spell, requested_slot_level)
	if slot_level <= 0:
		return _unavailable("Нет доступной ячейки для Адского возмездия.")
	return {
		"available": true,
		"spell": spell,
		"slot_level": slot_level,
		"resource_key": _spellcasting.slot_resource_key(character, slot_level),
		"distance_feet": distance_feet,
		"damage_dice_count": slot_level + 1,
		"damage_die_sides": 10
	}


func resolve_hellish_rebuke(character: PlayerCharacter, context: Dictionary) -> Dictionary:
	var offer: Dictionary = evaluate_hellish_rebuke(character, context)
	if not bool(offer.get("available", false)):
		return _failed(str(offer.get("reason", "Адское возмездие недоступно.")))
	var spell: Dictionary = offer.get("spell", {}) as Dictionary
	var payment: Dictionary = _spellcasting.consume_spell_cost_detailed(
		character,
		spell,
		int(offer.get("slot_level", 1)),
		context.get("casting_context", {}) as Dictionary
	)
	if not bool(payment.get("success", false)):
		return _failed(str(payment.get("message", "Не удалось израсходовать ячейку Адского возмездия.")))

	var save_overrides: Array[int] = _int_array(context.get("save_roll_overrides", []))
	var damage_overrides: Array[int] = _int_array(context.get("damage_roll_overrides", []))
	var target_state: CombatantState = context.get("target_state") as CombatantState
	var target_save_modifier: int = int(context.get("target_dexterity_save_modifier", 0))
	var spell_dc: int = _spellcasting.get_spell_save_dc(character, spell)
	var save_result: Dictionary = _rules.resolve_saving_throw(
		"dexterity",
		target_save_modifier,
		spell_dc,
		target_state,
		false,
		false,
		save_overrides,
		{"magical": true, "spell_id": HELLISH_REBUKE_SPELL_ID}
	)
	var dice_count: int = maxi(int(payment.get("slot_level", offer.get("slot_level", 1))) + 1, 2)
	var raw_damage: int = _roll_damage(dice_count, 10, damage_overrides)
	var save_succeeded: bool = bool(save_result.get("success", false))
	var final_damage: int = floori(float(raw_damage) / 2.0) if save_succeeded else raw_damage
	var result := AttackResult.new()
	result.attack_name = "Адское возмездие"
	result.target_name = str(context.get("target_name", "Существо"))
	result.damage_type = "fire"
	result.is_spell = true
	result.automatic_hit = true
	result.hit = true
	result.natural_roll = int(save_result.get("natural", 0))
	result.first_roll = result.natural_roll
	result.total = int(save_result.get("total", 0))
	result.target_armor_class = spell_dc
	result.distance_feet = int(offer.get("distance_feet", 0))
	result.damage_before_mitigation = final_damage
	result.damage = final_damage
	result.note = "Спасбросок Ловкости: %d против Сл %d — %s; огненный урон %d%s." % [
		result.total,
		spell_dc,
		"успех" if save_succeeded else "провал",
		final_damage,
		" после уменьшения вдвое" if save_succeeded else ""
	]
	return {
		"available": true,
		"resolved": true,
		"consume_reaction": true,
		"slot_level": int(payment.get("slot_level", offer.get("slot_level", 1))),
		"resource_key": str(payment.get("resource_key", offer.get("resource_key", ""))),
		"save": save_result,
		"save_succeeded": save_succeeded,
		"raw_damage": raw_damage,
		"damage": final_damage,
		"result": result,
		"message": "Адское возмездие окружает %s зелёным пламенем: %d огненного урона." % [result.target_name, final_damage]
	}


func evaluate_slow_fall(character: PlayerCharacter, context: Dictionary) -> Dictionary:
	if character == null:
		return _unavailable("Нет падающего персонажа.")
	if str(context.get("trigger_id", "")) != TRIGGER_FALL_DAMAGE_PENDING:
		return _unavailable("Триггер не позволяет использовать Медленное падение.")
	if not bool(context.get("reaction_available", false)):
		return _unavailable("Реакция уже потрачена.")
	if not bool(context.get("reactor_can_react", true)) or character.current_health <= 0:
		return _unavailable("Персонаж не способен совершить реакцию.")
	if character.character_class_id != "monk" or character.level < SLOW_FALL_MINIMUM_LEVEL:
		return _unavailable("Медленное падение доступно монаху с 4 уровня.")
	var pending_damage: int = maxi(int(context.get("pending_fall_damage", 0)), 0)
	if pending_damage <= 0:
		return _unavailable("Падение не должно нанести урон.")
	var reduction: int = 5 * maxi(character.level, 0)
	return {
		"available": true,
		"pending_fall_damage": pending_damage,
		"reduction": reduction,
		"final_damage": maxi(pending_damage - reduction, 0)
	}


func resolve_slow_fall(character: PlayerCharacter, context: Dictionary) -> Dictionary:
	var offer: Dictionary = evaluate_slow_fall(character, context)
	if not bool(offer.get("available", false)):
		return _failed(str(offer.get("reason", "Медленное падение недоступно.")))
	return {
		"available": true,
		"resolved": true,
		"consume_reaction": true,
		"reduction": int(offer.get("reduction", 0)),
		"pending_fall_damage": int(offer.get("pending_fall_damage", 0)),
		"final_damage": int(offer.get("final_damage", 0)),
		"message": "Медленное падение уменьшает урон на %d: итоговый урон %d." % [
			int(offer.get("reduction", 0)),
			int(offer.get("final_damage", 0))
		]
	}


func _roll_damage(count: int, sides: int, overrides: Array[int]) -> int:
	var total: int = 0
	for index: int in range(maxi(count, 1)):
		if index < overrides.size():
			total += clampi(overrides[index], 1, sides)
		else:
			total += _dice.roll_die(sides)
	return total


func _int_array(value: Variant) -> Array[int]:
	var result: Array[int] = []
	if value is Array:
		for item: Variant in value as Array:
			result.append(int(item))
	return result


func _unavailable(reason: String) -> Dictionary:
	return {"available": false, "reason": reason}


func _failed(message: String) -> Dictionary:
	return {
		"available": false,
		"resolved": false,
		"consume_reaction": false,
		"message": message
	}
