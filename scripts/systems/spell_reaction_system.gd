class_name SpellReactionSystem
extends RefCounted

const COUNTERSPELL_ID: String = "counterspell"
const COUNTERSPELL_RANGE_FEET: int = 60
const COUNTERSPELL_MINIMUM_SLOT_LEVEL: int = 3

var _spellcasting: SpellcastingSystem = SpellcastingSystem.new()
var _rules: SrdCombatRules = SrdCombatRules.new()


func get_counterspell_definition() -> Dictionary:
	return _spellcasting.get_spell_definition(COUNTERSPELL_ID)


func evaluate_counterspell(
	reactor: PlayerCharacter,
	attempt: SpellCastAttempt,
	reaction_available: bool,
	can_see_caster: bool,
	distance_feet: int,
	casting_context: Dictionary = {}
) -> Dictionary:
	if reactor == null or attempt == null or attempt.resolved:
		return _unavailable("Нет активного сотворения, которое можно прервать.")
	if not reaction_available:
		return _unavailable("Реакция уже израсходована до начала следующего хода.")
	if not can_see_caster:
		return _unavailable("Заклинатель не виден.")
	if maxi(distance_feet, 0) > COUNTERSPELL_RANGE_FEET:
		return _unavailable("Заклинатель находится дальше 60 футов.")
	if not attempt.has_observable_components():
		return _unavailable("У сотворения нет наблюдаемого вербального, соматического или материального компонента.")
	_spellcasting.ensure_character(reactor, false)
	var counterspell: Dictionary = get_counterspell_definition()
	if counterspell.is_empty() or COUNTERSPELL_ID not in _spellcasting.get_known_spell_ids(reactor):
		return _unavailable("Контрзаклинание не изучено.")
	if not _spellcasting.is_prepared(reactor, COUNTERSPELL_ID):
		return _unavailable("Контрзаклинание не подготовлено.")
	var component_result: Dictionary = _spellcasting.check_spell_components(counterspell, casting_context)
	if not bool(component_result.get("success", false)):
		return _unavailable(str(component_result.get("message", "Недоступен соматический компонент.")))
	if not _spellcasting.can_cast_spell(
		reactor,
		counterspell,
		false,
		true,
		int(casting_context.get("slot_level", 0)),
		casting_context
	):
		return _unavailable("Нет доступной ячейки 3 уровня или выше либо на этом ходу уже потрачена ячейка.")
	var selectable_levels: Array[int] = _spellcasting.get_available_slot_levels(
		reactor,
		COUNTERSPELL_MINIMUM_SLOT_LEVEL,
		true
	)
	if selectable_levels.is_empty():
		return _unavailable("Нет доступной ячейки 3 уровня или выше.")
	var selected_level: int = _spellcasting.resolve_slot_level(
		reactor,
		counterspell,
		int(casting_context.get("slot_level", 0))
	)
	if selected_level < COUNTERSPELL_MINIMUM_SLOT_LEVEL:
		selected_level = selectable_levels[0]
	return {
		"available": true,
		"message": "Можно применить Контрзаклинание реакцией.",
		"spell_id": COUNTERSPELL_ID,
		"slot_level": selected_level,
		"range_feet": maxi(distance_feet, 0),
		"trigger_spell_id": attempt.get_spell_id(),
		"trigger_spell_name": attempt.get_spell_name()
	}


func resolve_counterspell(
	reactor: PlayerCharacter,
	attempt: SpellCastAttempt,
	reaction_available: bool,
	can_see_caster: bool,
	distance_feet: int,
	casting_context: Dictionary = {},
	save_roll_overrides: Array[int] = [],
	defer_failed_proceeds: bool = false
) -> Dictionary:
	var offer: Dictionary = evaluate_counterspell(
		reactor,
		attempt,
		reaction_available,
		can_see_caster,
		distance_feet,
		casting_context
	)
	if not bool(offer.get("available", false)):
		return offer
	var counterspell: Dictionary = get_counterspell_definition()
	var selected_level: int = int(offer.get("slot_level", COUNTERSPELL_MINIMUM_SLOT_LEVEL))
	var payment_context: Dictionary = casting_context.duplicate(true)
	payment_context["slot_level"] = selected_level
	var payment: Dictionary = _spellcasting.consume_spell_cost_detailed(
		reactor,
		counterspell,
		selected_level,
		payment_context
	)
	if not bool(payment.get("success", false)):
		return _unavailable(str(payment.get("message", "Не удалось израсходовать ячейку Контрзаклинания.")))
	var save_dc: int = _spellcasting.get_spell_save_dc(reactor, counterspell)
	var save_result: Dictionary = _rules.resolve_saving_throw(
		"constitution",
		attempt.caster_constitution_modifier,
		save_dc,
		attempt.caster_state,
		false,
		false,
		save_roll_overrides,
		{"magical": true, "reaction_spell_id": COUNTERSPELL_ID}
	)
	var countered: bool = not bool(save_result.get("success", false))
	if countered:
		attempt.mark_countered(save_result)
	elif not defer_failed_proceeds:
		attempt.mark_proceeds(save_result)
	return {
		"available": true,
		"resolved": true,
		"countered": countered,
		"consume_reaction": true,
		"message": (
			"Контрзаклинание подавило %s. Исходная ячейка не расходуется." % attempt.get_spell_name()
			if countered
			else "%s выдерживает Контрзаклинание и продолжает сотворение." % attempt.caster_name
		),
		"counterspell_slot_level": int(payment.get("slot_level", selected_level)),
		"counterspell_resource_key": str(payment.get("resource_key", "")),
		"save_dc": save_dc,
		"save": save_result,
		"original_resource_should_be_expended": attempt.should_expend_original_resource(),
		"trigger_action_wasted": attempt.action_wasted
	}


func _unavailable(message: String) -> Dictionary:
	return {
		"available": false,
		"resolved": false,
		"countered": false,
		"consume_reaction": false,
		"message": message
	}
