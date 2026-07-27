extends "res://scripts/game/game_damage_fall_reactions_runtime.gd"


func _try_enemy_spell_turn(actor: Node) -> bool:
	if _enemy_spell_cast_in_progress or actor == null or not (actor is Node2D):
		return false
	var spell: Dictionary = _enemy_spell_definition(actor)
	if spell.is_empty() or not _enemy_has_spell_slot(actor, spell):
		return false
	var distance_feet: int = DistanceSystem.distance_feet((actor as Node2D).global_position, player.global_position)
	if distance_feet > _enemy_spell_reach_feet(spell):
		return false
	var cover: Dictionary = _combat_environment.get_cover(
		(actor as Node2D).global_position,
		player.global_position
	) if _combat_environment != null else {"bonus": 0, "total_cover": false}
	if bool(cover.get("total_cover", false)):
		return false

	_enemy_spell_cast_in_progress = true
	var slot_level: int = _enemy_spell_slot_level(actor, spell)
	var attempt := SpellCastAttempt.new(spell, actor, slot_level)
	attempt.caster_constitution_modifier = (
		int(actor.call("get_saving_throw_modifier", "constitution"))
		if actor.has_method("get_saving_throw_modifier")
		else 0
	)
	attempt.caster_state = _state_for(actor)
	attempt.action_kind = "action"
	attempt.original_resource_key = "enemy_spell_slots_%d" % slot_level
	show_combat_message("%s начинает сотворять «%s»." % [attempt.caster_name, attempt.get_spell_name()], false)

	var save_overrides: Array[int] = []
	if actor.has_method("get_counterspell_save_roll_overrides"):
		var overrides_value: Variant = actor.call("get_counterspell_save_roll_overrides")
		if overrides_value is Array:
			for value: Variant in overrides_value as Array:
				save_overrides.append(int(value))
	var event_context: Dictionary = {
		"attempt": attempt,
		"save_roll_overrides": save_overrides,
		"defer_failed_counterspell_proceeds": true,
		"allow_source_reaction": false
	}
	var reaction_session: Dictionary = _create_coordinated_reaction_session(
		ReactionOpportunitySystem.TRIGGER_SPELL_CAST_STARTED,
		event_context,
		actor,
		player
	)
	while _reaction_coordinator.should_continue(reaction_session.get("event") as ReactionEvent):
		var selection: Dictionary = await _request_next_coordinated_reaction(
			"ВОЗМОЖНОСТЬ РЕАКЦИИ",
			"%s начинает сотворять «%s». Все подходящие участники проверены единым координатором реакций." % [
				attempt.caster_name,
				attempt.get_spell_name()
			],
			reaction_session
		)
		if selection.is_empty():
			break
		var event: ReactionEvent = selection.get("event") as ReactionEvent
		var selection_id: String = str(selection.get("selection_id", ""))
		var reaction_result: Dictionary = _reaction_coordinator.resolve_selection(event, selection_id)
		_consume_coordinated_reaction(reaction_result)
		show_combat_message(
			str(reaction_result.get("message", "Реакция разрешена.")),
			bool(reaction_result.get("countered", false))
		)
		GameState.save_game()
		_update_status()
		if bool(reaction_result.get("countered", false)):
			_enemy_spell_cast_in_progress = false
			_active_reaction_event = null
			return true
	attempt.mark_proceeds()
	_active_reaction_event = null

	await get_tree().create_timer(0.18).timeout
	if attempt.countered:
		_enemy_spell_cast_in_progress = false
		return true
	if not actor.has_method("consume_combat_spell_slot") or not bool(actor.call("consume_combat_spell_slot", slot_level)):
		show_combat_message("%s не смог завершить сотворение: ячейка недоступна." % attempt.caster_name, false)
		_enemy_spell_cast_in_progress = false
		return true
	attempt.mark_original_resource_expended("enemy_spell_slots_%d" % slot_level)
	await _resolve_enemy_area_spell(actor, spell, slot_level)
	_enemy_spell_cast_in_progress = false
	return true
