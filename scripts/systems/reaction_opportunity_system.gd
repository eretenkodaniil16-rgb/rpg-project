class_name ReactionOpportunitySystem
extends RefCounted

const TRIGGER_SPELL_CAST_STARTED: String = "spell_cast_started"
const TRIGGER_ENEMY_LEAVES_REACH: String = "enemy_leaves_reach"
const TRIGGER_READIED_ACTION: String = "readied_action_triggered"
const TRIGGER_ATTACK_ROLL_HIT: String = DefensiveReactionSystem.TRIGGER_ATTACK_ROLL_HIT
const TRIGGER_MAGIC_MISSILE_TARGETED: String = DefensiveReactionSystem.TRIGGER_MAGIC_MISSILE_TARGETED
const TRIGGER_ELEMENTAL_DAMAGE_TAKEN: String = DefensiveReactionSystem.TRIGGER_ELEMENTAL_DAMAGE_TAKEN
const TRIGGER_CREATURE_DAMAGE_RECEIVED: String = DamageFallReactionSystem.TRIGGER_CREATURE_DAMAGE_RECEIVED
const TRIGGER_FALL_DAMAGE_PENDING: String = DamageFallReactionSystem.TRIGGER_FALL_DAMAGE_PENDING

const OPTION_COUNTERSPELL: String = "counterspell"
const OPTION_OPPORTUNITY_ATTACK: String = "opportunity_attack"
const OPTION_READIED_ATTACK: String = "readied_attack"
const OPTION_SHIELD: String = "shield_spell"
const OPTION_ABSORB_ELEMENTS: String = "absorb_elements"
const OPTION_HELLISH_REBUKE: String = "hellish_rebuke"
const OPTION_SLOW_FALL: String = "slow_fall"

var _spell_reactions: SpellReactionSystem = SpellReactionSystem.new()
var _defensive_reactions: DefensiveReactionSystem = DefensiveReactionSystem.new()
var _damage_fall_reactions: DamageFallReactionSystem = DamageFallReactionSystem.new()


func collect_options(trigger_id: String, context: Dictionary) -> Array[Dictionary]:
	match trigger_id:
		TRIGGER_SPELL_CAST_STARTED:
			return _collect_spell_cast_options(context)
		TRIGGER_ENEMY_LEAVES_REACH:
			return _collect_opportunity_attack_options(context)
		TRIGGER_READIED_ACTION:
			return _collect_readied_action_options(context)
		TRIGGER_ATTACK_ROLL_HIT:
			return _collect_shield_options(TRIGGER_ATTACK_ROLL_HIT, context)
		TRIGGER_MAGIC_MISSILE_TARGETED:
			return _collect_shield_options(TRIGGER_MAGIC_MISSILE_TARGETED, context)
		TRIGGER_ELEMENTAL_DAMAGE_TAKEN:
			return _collect_absorb_elements_options(context)
		TRIGGER_CREATURE_DAMAGE_RECEIVED:
			return _collect_hellish_rebuke_options(context)
		TRIGGER_FALL_DAMAGE_PENDING:
			return _collect_slow_fall_options(context)
		_:
			return []


func resolve_spell_cast_option(option_id: String, context: Dictionary) -> Dictionary:
	if option_id != OPTION_COUNTERSPELL:
		return _unresolved("Выбранная реакция не относится к сотворению заклинания.")
	var reactor: PlayerCharacter = context.get("reactor") as PlayerCharacter
	var attempt: SpellCastAttempt = context.get("attempt") as SpellCastAttempt
	var casting_context: Dictionary = context.get("casting_context", {}) as Dictionary
	var save_roll_overrides: Array[int] = []
	var overrides_value: Variant = context.get("save_roll_overrides", [])
	if overrides_value is Array:
		for value: Variant in overrides_value as Array:
			save_roll_overrides.append(int(value))
	return _spell_reactions.resolve_counterspell(
		reactor,
		attempt,
		bool(context.get("reaction_available", false)),
		bool(context.get("can_see_caster", false)),
		int(context.get("distance_feet", 0)),
		casting_context,
		save_roll_overrides
	)


func resolve_defensive_option(option_id: String, context: Dictionary) -> Dictionary:
	match option_id:
		OPTION_SHIELD:
			return _defensive_reactions.resolve_shield(context.get("reactor") as PlayerCharacter, context)
		OPTION_ABSORB_ELEMENTS:
			return _defensive_reactions.resolve_absorb_elements(context.get("reactor") as PlayerCharacter, context)
		_:
			return _unresolved("Выбранная реакция не относится к защите от атаки или урона.")


func resolve_damage_fall_option(option_id: String, context: Dictionary) -> Dictionary:
	match option_id:
		OPTION_HELLISH_REBUKE:
			return _damage_fall_reactions.resolve_hellish_rebuke(context.get("reactor") as PlayerCharacter, context)
		OPTION_SLOW_FALL:
			return _damage_fall_reactions.resolve_slow_fall(context.get("reactor") as PlayerCharacter, context)
		_:
			return _unresolved("Выбранная реакция не относится к полученному урону или падению.")


func _collect_spell_cast_options(context: Dictionary) -> Array[Dictionary]:
	var reactor: PlayerCharacter = context.get("reactor") as PlayerCharacter
	var attempt: SpellCastAttempt = context.get("attempt") as SpellCastAttempt
	if reactor == null or attempt == null:
		return []
	var offer: Dictionary = _spell_reactions.evaluate_counterspell(
		reactor,
		attempt,
		bool(context.get("reaction_available", false)),
		bool(context.get("can_see_caster", false)),
		int(context.get("distance_feet", 0)),
		context.get("casting_context", {}) as Dictionary
	)
	if not bool(offer.get("available", false)):
		return []
	return [{
		"id": OPTION_COUNTERSPELL,
		"label": "КОНТРЗАКЛИНАНИЕ",
		"name": "Контрзаклинание",
		"description": "Попытаться прервать «%s». Будут потрачены реакция и ячейка %d уровня." % [
			attempt.get_spell_name(),
			int(offer.get("slot_level", 3))
		],
		"resource_text": "Реакция · ячейка %d уровня" % int(offer.get("slot_level", 3)),
		"priority": 100,
		"offer": offer
	}]


func _collect_shield_options(trigger_id: String, context: Dictionary) -> Array[Dictionary]:
	var evaluation_context: Dictionary = context.duplicate(true)
	evaluation_context["trigger_id"] = trigger_id
	var reactor: PlayerCharacter = evaluation_context.get("reactor") as PlayerCharacter
	var offer: Dictionary = _defensive_reactions.evaluate_shield(reactor, evaluation_context)
	if not bool(offer.get("available", false)):
		return []
	var prevents_text: String
	if bool(offer.get("blocks_magic_missile", false)):
		prevents_text = "Полностью блокирует урон Магической стрелы."
	elif bool(offer.get("prevents_triggering_hit", false)):
		prevents_text = "Повышение КД превратит это попадание в промах."
	else:
		prevents_text = "Эта атака всё ещё попадёт, но КД останется повышенным до начала следующего хода."
	return [{
		"id": OPTION_SHIELD,
		"label": "ЩИТ",
		"name": "Щит",
		"description": "%s КД +5 до начала следующего хода." % prevents_text,
		"resource_text": "Реакция · ячейка %d уровня" % int(offer.get("slot_level", 1)),
		"priority": 95,
		"offer": offer
	}]


func _collect_absorb_elements_options(context: Dictionary) -> Array[Dictionary]:
	var evaluation_context: Dictionary = context.duplicate(true)
	evaluation_context["trigger_id"] = TRIGGER_ELEMENTAL_DAMAGE_TAKEN
	var reactor: PlayerCharacter = evaluation_context.get("reactor") as PlayerCharacter
	var offer: Dictionary = _defensive_reactions.evaluate_absorb_elements(reactor, evaluation_context)
	if not bool(offer.get("available", false)):
		return []
	return [{
		"id": OPTION_ABSORB_ELEMENTS,
		"label": "ПОГЛОЩЕНИЕ СТИХИЙ",
		"name": "Поглощение стихий",
		"description": "Получить сопротивление урону «%s» и зарядить %dк6 этого типа для следующего рукопашного попадания." % [
			str(offer.get("damage_type", "стихийный")),
			int(offer.get("bonus_dice_count", 1))
		],
		"resource_text": "Реакция · ячейка %d уровня" % int(offer.get("slot_level", 1)),
		"priority": 85,
		"offer": offer
	}]


func _collect_hellish_rebuke_options(context: Dictionary) -> Array[Dictionary]:
	var evaluation_context: Dictionary = context.duplicate(true)
	evaluation_context["trigger_id"] = TRIGGER_CREATURE_DAMAGE_RECEIVED
	var reactor: PlayerCharacter = evaluation_context.get("reactor") as PlayerCharacter
	var offer: Dictionary = _damage_fall_reactions.evaluate_hellish_rebuke(reactor, evaluation_context)
	if not bool(offer.get("available", false)):
		return []
	return [{
		"id": OPTION_HELLISH_REBUKE,
		"label": "АДСКОЕ ВОЗМЕЗДИЕ",
		"name": "Адское возмездие",
		"description": "Существо, которое только что нанесло вам урон, совершит спасбросок Ловкости и получит %dк10 огненного урона, половину при успехе." % int(offer.get("damage_dice_count", 2)),
		"resource_text": "Реакция · ячейка %d уровня" % int(offer.get("slot_level", 1)),
		"priority": 90,
		"offer": offer
	}]


func _collect_slow_fall_options(context: Dictionary) -> Array[Dictionary]:
	var evaluation_context: Dictionary = context.duplicate(true)
	evaluation_context["trigger_id"] = TRIGGER_FALL_DAMAGE_PENDING
	var reactor: PlayerCharacter = evaluation_context.get("reactor") as PlayerCharacter
	var offer: Dictionary = _damage_fall_reactions.evaluate_slow_fall(reactor, evaluation_context)
	if not bool(offer.get("available", false)):
		return []
	return [{
		"id": OPTION_SLOW_FALL,
		"label": "МЕДЛЕННОЕ ПАДЕНИЕ",
		"name": "Медленное падение",
		"description": "Уменьшить ожидаемый урон от падения с %d до %d." % [
			int(offer.get("pending_fall_damage", 0)),
			int(offer.get("final_damage", 0))
		],
		"resource_text": "Реакция",
		"priority": 92,
		"offer": offer
	}]


func _collect_opportunity_attack_options(context: Dictionary) -> Array[Dictionary]:
	if not bool(context.get("reaction_available", false)):
		return []
	if not bool(context.get("target_leaves_reach", false)):
		return []
	if not bool(context.get("can_make_weapon_attack", false)):
		return []
	return [{
		"id": OPTION_OPPORTUNITY_ATTACK,
		"label": "АТАКА ПО ВОЗМОЖНОСТИ",
		"name": "Атака по возможности",
		"description": "Совершить одну рукопашную атаку по существу, покидающему вашу досягаемость.",
		"resource_text": "Реакция",
		"priority": 80
	}]


func _collect_readied_action_options(context: Dictionary) -> Array[Dictionary]:
	if not bool(context.get("reaction_available", false)):
		return []
	if not bool(context.get("readied_trigger_matches", false)):
		return []
	return [{
		"id": OPTION_READIED_ATTACK,
		"label": "ВЫПОЛНИТЬ ПОДГОТОВЛЕННОЕ",
		"name": "Подготовленное действие",
		"description": str(context.get("readied_description", "Выполнить подготовленное действие после наступления выбранного условия.")),
		"resource_text": "Реакция",
		"priority": 90
	}]


func sort_options(options: Array[Dictionary]) -> Array[Dictionary]:
	var result: Array[Dictionary] = options.duplicate(true)
	result.sort_custom(func(left: Dictionary, right: Dictionary) -> bool:
		return int(left.get("priority", 0)) > int(right.get("priority", 0))
	)
	return result


func _unresolved(message: String) -> Dictionary:
	return {
		"available": false,
		"resolved": false,
		"countered": false,
		"consume_reaction": false,
		"message": message
	}
