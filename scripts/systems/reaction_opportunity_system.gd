class_name ReactionOpportunitySystem
extends RefCounted

const TRIGGER_SPELL_CAST_STARTED: String = "spell_cast_started"
const TRIGGER_ENEMY_LEAVES_REACH: String = "enemy_leaves_reach"
const TRIGGER_READIED_ACTION: String = "readied_action_triggered"

const OPTION_COUNTERSPELL: String = "counterspell"
const OPTION_OPPORTUNITY_ATTACK: String = "opportunity_attack"
const OPTION_READIED_ATTACK: String = "readied_attack"

var _spell_reactions: SpellReactionSystem = SpellReactionSystem.new()


func collect_options(trigger_id: String, context: Dictionary) -> Array[Dictionary]:
	match trigger_id:
		TRIGGER_SPELL_CAST_STARTED:
			return _collect_spell_cast_options(context)
		TRIGGER_ENEMY_LEAVES_REACH:
			return _collect_opportunity_attack_options(context)
		TRIGGER_READIED_ACTION:
			return _collect_readied_action_options(context)
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
