class_name DefensiveReactionSystem
extends RefCounted

const SHIELD_SPELL_ID: String = "shield_spell"
const ABSORB_ELEMENTS_SPELL_ID: String = "absorb_elements"

const TRIGGER_ATTACK_ROLL_HIT: String = "attack_roll_hit"
const TRIGGER_MAGIC_MISSILE_TARGETED: String = "magic_missile_targeted"
const TRIGGER_ELEMENTAL_DAMAGE_TAKEN: String = "elemental_damage_taken"

const ELEMENTAL_DAMAGE_TYPES: Array[String] = ["acid", "cold", "fire", "lightning", "thunder"]

var _spellcasting: SpellcastingSystem = SpellcastingSystem.new()


func evaluate_shield(character: PlayerCharacter, context: Dictionary) -> Dictionary:
	if character == null:
		return _unavailable("Нет персонажа, способного использовать Щит.")
	if not bool(context.get("reaction_available", false)):
		return _unavailable("Реакция уже потрачена.")
	if bool(context.get("shield_already_active", false)):
		return _unavailable("Щит уже действует.")
	var trigger_id: String = str(context.get("trigger_id", ""))
	if trigger_id not in [TRIGGER_ATTACK_ROLL_HIT, TRIGGER_MAGIC_MISSILE_TARGETED]:
		return _unavailable("Триггер не позволяет использовать Щит.")
	if trigger_id == TRIGGER_ATTACK_ROLL_HIT and not bool(context.get("attack_hit", false)):
		return _unavailable("Щит применяется только после попадания броском атаки.")
	var spell: Dictionary = _spellcasting.get_spell_definition(SHIELD_SPELL_ID)
	if spell.is_empty():
		return _unavailable("Определение заклинания Щит отсутствует.")
	_spellcasting.ensure_character(character, false)
	var casting_context: Dictionary = context.get("casting_context", {}) as Dictionary
	var requested_slot_level: int = maxi(int(context.get("slot_level", 0)), 0)
	if not _spellcasting.can_cast_spell(character, spell, false, true, requested_slot_level, casting_context):
		return _unavailable("Щит не подготовлен, нет ячейки или недоступны компоненты.")
	var active_resource_key: String = _spellcasting.active_resource_key(character, spell, casting_context)
	var special_resource: bool = _is_special_resource_key(active_resource_key)
	var slot_level: int = (
		maxi(int(spell.get("spell_level", 1)), 1)
		if special_resource
		else _spellcasting.resolve_slot_level(character, spell, requested_slot_level)
	)
	if slot_level <= 0:
		return _unavailable("Нет доступной ячейки для Щита.")
	var current_ac: int = maxi(int(context.get("current_ac", 0)), 0)
	var attack_total: int = maxi(int(context.get("attack_total", 0)), 0)
	var natural_roll: int = clampi(int(context.get("natural_roll", 0)), 0, 20)
	var prevents_hit: bool = (
		trigger_id == TRIGGER_MAGIC_MISSILE_TARGETED
		or (natural_roll != 20 and attack_total < current_ac + int(spell.get("armor_class_bonus", 5)))
	)
	return {
		"available": true,
		"spell": spell,
		"slot_level": slot_level,
		"resource_key": active_resource_key,
		"prevents_triggering_hit": prevents_hit,
		"blocks_magic_missile": trigger_id == TRIGGER_MAGIC_MISSILE_TARGETED,
		"armor_class_bonus": int(spell.get("armor_class_bonus", 5))
	}


func resolve_shield(character: PlayerCharacter, context: Dictionary) -> Dictionary:
	var offer: Dictionary = evaluate_shield(character, context)
	if not bool(offer.get("available", false)):
		return _failed(str(offer.get("reason", "Щит недоступен.")))
	var spell: Dictionary = offer.get("spell", {}) as Dictionary
	var payment: Dictionary = _spellcasting.consume_spell_cost_detailed(
		character,
		spell,
		int(offer.get("slot_level", 1)),
		context.get("casting_context", {}) as Dictionary
	)
	if not bool(payment.get("success", false)):
		return _failed(str(payment.get("message", "Не удалось израсходовать ячейку Щита.")))
	var blocked_magic_missile: bool = bool(offer.get("blocks_magic_missile", false))
	var prevented_hit: bool = bool(offer.get("prevents_triggering_hit", false))
	var message: String
	if blocked_magic_missile:
		message = "Щит полностью блокирует Магическую стрелу и повышает КД на 5 до начала следующего хода."
	elif prevented_hit:
		message = "Щит повышает КД на 5 и превращает вызвавшее реакцию попадание в промах."
	else:
		message = "Щит повышает КД на 5, но вызвавшая реакцию атака всё ещё попадает."
	return {
		"available": true,
		"resolved": true,
		"consume_reaction": true,
		"slot_level": int(payment.get("slot_level", offer.get("slot_level", 1))),
		"resource_key": str(payment.get("resource_key", offer.get("resource_key", ""))),
		"armor_class_bonus": int(offer.get("armor_class_bonus", 5)),
		"prevents_triggering_hit": prevented_hit,
		"blocks_magic_missile": blocked_magic_missile,
		"message": message
	}


func evaluate_absorb_elements(character: PlayerCharacter, context: Dictionary) -> Dictionary:
	if character == null:
		return _unavailable("Нет персонажа, способного использовать Поглощение стихий.")
	if not bool(context.get("reaction_available", false)):
		return _unavailable("Реакция уже потрачена.")
	if str(context.get("trigger_id", "")) != TRIGGER_ELEMENTAL_DAMAGE_TAKEN:
		return _unavailable("Триггер не позволяет использовать Поглощение стихий.")
	var incoming_damage: int = maxi(int(context.get("incoming_damage", 0)), 0)
	if incoming_damage <= 0:
		return _unavailable("Персонаж не получает урон.")
	var damage_type: String = _normalize_damage_type(str(context.get("damage_type", "")))
	if damage_type not in ELEMENTAL_DAMAGE_TYPES:
		return _unavailable("Этот тип урона нельзя поглотить.")
	if bool(context.get("same_absorption_active", false)):
		return _unavailable("Поглощение этой стихии уже действует.")
	var spell: Dictionary = _spellcasting.get_spell_definition(ABSORB_ELEMENTS_SPELL_ID)
	if spell.is_empty():
		return _unavailable("Определение заклинания Поглощение стихий отсутствует.")
	_spellcasting.ensure_character(character, false)
	var casting_context: Dictionary = context.get("casting_context", {}) as Dictionary
	var requested_slot_level: int = maxi(int(context.get("slot_level", 0)), 0)
	if not _spellcasting.can_cast_spell(character, spell, false, true, requested_slot_level, casting_context):
		return _unavailable("Поглощение стихий не подготовлено, нет ячейки или недоступен соматический компонент.")
	var active_resource_key: String = _spellcasting.active_resource_key(character, spell, casting_context)
	var special_resource: bool = _is_special_resource_key(active_resource_key)
	var slot_level: int = (
		maxi(int(spell.get("spell_level", 1)), 1)
		if special_resource
		else _spellcasting.resolve_slot_level(character, spell, requested_slot_level)
	)
	if slot_level <= 0:
		return _unavailable("Нет доступной ячейки для Поглощения стихий.")
	return {
		"available": true,
		"spell": spell,
		"slot_level": slot_level,
		"resource_key": active_resource_key,
		"damage_type": damage_type,
		"incoming_damage": incoming_damage,
		"bonus_dice_count": maxi(slot_level, 1),
		"bonus_die_sides": 6
	}


func resolve_absorb_elements(character: PlayerCharacter, context: Dictionary) -> Dictionary:
	var offer: Dictionary = evaluate_absorb_elements(character, context)
	if not bool(offer.get("available", false)):
		return _failed(str(offer.get("reason", "Поглощение стихий недоступно.")))
	var spell: Dictionary = offer.get("spell", {}) as Dictionary
	var payment: Dictionary = _spellcasting.consume_spell_cost_detailed(
		character,
		spell,
		int(offer.get("slot_level", 1)),
		context.get("casting_context", {}) as Dictionary
	)
	if not bool(payment.get("success", false)):
		return _failed(str(payment.get("message", "Не удалось израсходовать ячейку Поглощения стихий.")))
	var damage_type: String = str(offer.get("damage_type", "fire"))
	var dice_count: int = maxi(int(payment.get("slot_level", offer.get("slot_level", 1))), 1)
	return {
		"available": true,
		"resolved": true,
		"consume_reaction": true,
		"slot_level": int(payment.get("slot_level", offer.get("slot_level", 1))),
		"resource_key": str(payment.get("resource_key", offer.get("resource_key", ""))),
		"damage_type": damage_type,
		"bonus_dice_count": dice_count,
		"bonus_die_sides": 6,
		"message": "Поглощение стихий даёт сопротивление урону «%s» и заряжает %dк6 дополнительного урона для следующего рукопашного попадания." % [damage_type, dice_count]
	}


func _normalize_damage_type(value: String) -> String:
	var normalized: String = value.strip_edges().to_lower()
	match normalized:
		"кислотный", "кислота": return "acid"
		"холод", "холодный": return "cold"
		"огонь", "огненный": return "fire"
		"электричество", "электрический", "молния": return "lightning"
		"звук", "звуковой", "гром": return "thunder"
		_: return normalized


func _is_special_resource_key(resource_key: String) -> bool:
	return (
		not resource_key.is_empty()
		and resource_key != "unlimited"
		and not resource_key.begins_with("spell_slots_")
		and not resource_key.begins_with("pact_slots_")
	)


func _unavailable(reason: String) -> Dictionary:
	return {"available": false, "reason": reason}


func _failed(message: String) -> Dictionary:
	return {
		"available": false,
		"resolved": false,
		"consume_reaction": false,
		"message": message
	}
