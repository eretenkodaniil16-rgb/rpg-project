extends "res://scripts/game/game_multi_reactor_reactions_runtime.gd"

var _last_completed_reaction_event: ReactionEvent


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
		"allow_source_reaction": false,
		"eligible_reactor_team_ids": [ReactionCandidate.TEAM_PARTY]
	}
	await _run_coordinated_reaction_event(
		"ВОЗМОЖНОСТЬ РЕАКЦИИ",
		"%s начинает сотворять «%s». Подходящие участники могут реагировать по очереди, пока заклинание не прервано или все не откажутся." % [
			attempt.caster_name,
			attempt.get_spell_name()
		],
		ReactionOpportunitySystem.TRIGGER_SPELL_CAST_STARTED,
		event_context,
		actor,
		player
	)

	if attempt.countered:
		_enemy_spell_cast_in_progress = false
		return true
	attempt.mark_proceeds()
	await get_tree().create_timer(0.18).timeout
	if not actor.has_method("consume_combat_spell_slot") or not bool(actor.call("consume_combat_spell_slot", slot_level)):
		show_combat_message("%s не смог завершить сотворение: ячейка недоступна." % attempt.caster_name, false)
		_enemy_spell_cast_in_progress = false
		return true
	attempt.mark_original_resource_expended("enemy_spell_slots_%d" % slot_level)
	await _resolve_enemy_area_spell(actor, spell, slot_level)
	_enemy_spell_cast_in_progress = false
	return true


func _run_coordinated_reaction_event(
	title: String,
	details: String,
	trigger_id: String,
	base_context: Dictionary,
	source: Node = null,
	target: Node = null,
	explicit_candidates: Array[ReactionCandidate] = []
) -> Dictionary:
	if _reaction_choice_prompt == null or _reaction_choice_prompt.is_waiting_for_decision():
		return {}
	_active_reaction_event = _reaction_coordinator.create_event(trigger_id, base_context, source, target)
	var event: ReactionEvent = _active_reaction_event
	var candidates: Array[ReactionCandidate] = explicit_candidates
	if candidates.is_empty():
		candidates = _collect_reaction_candidates(trigger_id, base_context, source, target)
	var resolutions: Array[Dictionary] = []
	var safety_limit: int = maxi(candidates.size() * 4, 8)
	var iterations: int = 0

	while _reaction_coordinator.should_continue(event) and iterations < safety_limit:
		iterations += 1
		var options: Array[Dictionary] = _reaction_coordinator.collect_options(event, candidates)
		_decorate_multi_reactor_options(options)
		if options.is_empty():
			break
		var queue: Array[Dictionary] = _reaction_coordinator.build_controller_queue(options)
		if queue.is_empty():
			break
		var controller_group: Dictionary = queue[0]
		var controller_id: String = str(controller_group.get("controller_id", ReactionCandidate.CONTROLLER_AI))
		var group_options: Array[Dictionary] = _dictionary_options(controller_group.get("options", []))
		if group_options.is_empty():
			break
		var selected_id: String = ""
		if controller_id == ReactionCandidate.CONTROLLER_PLAYER:
			_reaction_resolution_in_progress = true
			_defensive_resolution_in_progress = true
			selected_id = await _reaction_choice_prompt.request_reaction(title, details, group_options)
			_reaction_resolution_in_progress = false
			_defensive_resolution_in_progress = false
		else:
			selected_id = _reaction_coordinator.choose_ai_selection(group_options)
		if selected_id.is_empty():
			_reaction_coordinator.mark_controller_skipped(event, controller_id, group_options)
			continue
		var result: Dictionary = _reaction_coordinator.resolve_selection(event, selected_id)
		_consume_coordinated_reaction(result)
		var runtime_outcome: Dictionary = await _apply_coordinated_reaction_result(event, result)
		event.record_runtime_outcome(
			str(result.get("reactor_id", "")),
			str(result.get("option_id", "")),
			runtime_outcome
		)
		resolutions.append(result)

	if iterations >= safety_limit and _reaction_coordinator.should_continue(event):
		event.invalidate("Превышен защитный лимит последовательности реакций.")
	if event.is_open():
		event.finish()
	_last_completed_reaction_event = event
	_active_reaction_event = null
	return {
		"event": event,
		"resolutions": resolutions,
		"last_result": resolutions.back() if not resolutions.is_empty() else {},
		"stopped": event.stop_processing,
		"invalid_reason": event.invalid_reason
	}


func _apply_coordinated_reaction_result(event: ReactionEvent, result: Dictionary) -> Dictionary:
	var outcome: Dictionary = {"applied": false}
	var option_id: String = str(result.get("option_id", ""))
	var reactor_actor: Node = result.get("reactor_actor") as Node
	if not bool(result.get("resolved", false)):
		if not str(result.get("message", "")).is_empty():
			show_combat_message(str(result.get("message", "Реакция не сработала.")), false)
		GameState.save_game()
		_update_status()
		return outcome

	if reactor_actor == player:
		outcome = await _apply_player_coordinated_reaction(event, result)
	elif is_instance_valid(reactor_actor) and reactor_actor.has_method("apply_coordinated_reaction_result"):
		var hook_result: Variant = reactor_actor.call(
			"apply_coordinated_reaction_result",
			option_id,
			result.duplicate(true),
			event.context.duplicate(true),
			event.source,
			event.target
		)
		if hook_result is Dictionary:
			outcome = hook_result as Dictionary
		else:
			outcome = {"applied": true}

	if not str(result.get("message", "")).is_empty():
		show_combat_message(str(result.get("message", "Реакция разрешена.")), true)
	if is_instance_valid(event.source) and event.source.has_method("get_current_health"):
		if int(event.source.call("get_current_health")) <= 0:
			outcome["target_invalid"] = true
			event.invalidate("Источник события больше не является действующей целью.")
	GameState.save_game()
	_update_status()
	return outcome


func _apply_player_coordinated_reaction(event: ReactionEvent, result: Dictionary) -> Dictionary:
	var option_id: String = str(result.get("option_id", ""))
	match option_id:
		ReactionOpportunitySystem.OPTION_SHIELD:
			_activate_shield(int(result.get("armor_class_bonus", 5)))
			return {"applied": true, "shield_active": true}
		ReactionOpportunitySystem.OPTION_ABSORB_ELEMENTS:
			_activate_absorb_elements(
				str(result.get("damage_type", "fire")),
				int(result.get("bonus_dice_count", 1)),
				int(result.get("bonus_die_sides", 6))
			)
			return {"applied": true, "absorb_elements_active": true}
		ReactionOpportunitySystem.OPTION_OPPORTUNITY_ATTACK:
			return await _perform_player_runtime_reaction_attack(event.source, false)
		ReactionOpportunitySystem.OPTION_READIED_ATTACK:
			_player_combat_state.readied_attack = false
			return await _perform_player_runtime_reaction_attack(event.source, true)
		_:
			return {"applied": true}


func _perform_player_runtime_reaction_attack(target_actor: Node, readied: bool) -> Dictionary:
	if not _target_is_valid(target_actor):
		return {"applied": false, "target_invalid": true, "stop_reaction_chain": true}
	var weapon: Dictionary = _class_data.get_equipped_weapon(GameState.player_character)
	var health_before: int = int(target_actor.call("get_current_health")) if target_actor.has_method("get_current_health") else -1
	await _perform_srd_weapon_attack(target_actor, weapon, str(weapon.get("ammunition_id", "")))
	var health_after: int = int(target_actor.call("get_current_health")) if target_actor.has_method("get_current_health") else health_before
	return {
		"applied": true,
		"runtime_action": "readied_attack" if readied else "opportunity_attack",
		"health_before": health_before,
		"health_after": health_after,
		"target_invalid": not _target_is_valid(target_actor),
		"stop_reaction_chain": not _target_is_valid(target_actor)
	}


func _player_reaction_context_overrides(
	trigger_id: String,
	base_context: Dictionary,
	source: Node,
	target: Node
) -> Dictionary:
	var result: Dictionary = super._player_reaction_context_overrides(trigger_id, base_context, source, target)
	match trigger_id:
		ReactionOpportunitySystem.TRIGGER_ENEMY_LEAVES_REACH:
			var weapon: Dictionary = _class_data.get_equipped_weapon(GameState.player_character)
			var from_position: Vector2 = base_context.get("from_position", Vector2.ZERO) as Vector2
			var to_position: Vector2 = base_context.get("to_position", Vector2.ZERO) as Vector2
			var current_distance: int = DistanceSystem.distance_feet(player.global_position, from_position)
			var future_distance: int = DistanceSystem.distance_feet(player.global_position, to_position)
			result["target_leaves_reach"] = current_distance <= DistanceSystem.MELEE_REACH_FEET and future_distance > DistanceSystem.MELEE_REACH_FEET
			result["can_make_weapon_attack"] = not DistanceSystem.is_ranged_weapon(weapon)
		ReactionOpportunitySystem.TRIGGER_READIED_ACTION:
			var weapon: Dictionary = _class_data.get_equipped_weapon(GameState.player_character)
			var distance_feet: int = (
				DistanceSystem.distance_feet(player.global_position, (source as Node2D).global_position)
				if is_instance_valid(source) and source is Node2D
				else 999999
			)
			result["readied_trigger_matches"] = (
				_player_combat_state.readied_attack
				and _target_is_valid(source)
				and DistanceSystem.weapon_range_state(weapon, distance_feet) != "out_of_range"
			)
			result["readied_description"] = "Совершить подготовленную атаку по %s, вошедшему в дистанцию оружия." % _target_name(source)
	return result


func _offer_shield_for_attack(attacker: Node, attack_total: int, natural_roll: int, current_ac: int) -> Dictionary:
	var context: Dictionary = {
		"attack_hit": true,
		"attack_total": attack_total,
		"natural_roll": natural_roll,
		"current_ac": current_ac,
		"shield_already_active": _shield_active,
		"eligible_reactor_actor_ids": [player.get_instance_id()]
	}
	var summary: Dictionary = await _run_coordinated_reaction_event(
		"ПО ВАМ ПОПАЛИ",
		"%s попадает с результатом %d против КД %d. Защитная реакция разрешается до броска урона." % [
			_target_name(attacker),
			attack_total,
			current_ac
		],
		ReactionOpportunitySystem.TRIGGER_ATTACK_ROLL_HIT,
		context,
		attacker,
		player
	)
	return _find_coordinated_result(summary, ReactionOpportunitySystem.OPTION_SHIELD)


func _offer_shield_for_magic_missile(attacker: Node, spell_name: String) -> Dictionary:
	var context: Dictionary = {
		"current_ac": _class_data.get_armor_class(GameState.player_character),
		"shield_already_active": _shield_active,
		"eligible_reactor_actor_ids": [player.get_instance_id()]
	}
	var summary: Dictionary = await _run_coordinated_reaction_event(
		"МАГИЧЕСКАЯ СТРЕЛА НАЦЕЛЕНА НА ВАС",
		"%s завершает «%s». Подходящая защитная реакция может полностью заблокировать снаряды." % [
			_target_name(attacker),
			spell_name
		],
		ReactionOpportunitySystem.TRIGGER_MAGIC_MISSILE_TARGETED,
		context,
		attacker,
		player
	)
	return _find_coordinated_result(summary, ReactionOpportunitySystem.OPTION_SHIELD)


func _offer_absorb_elements(incoming_damage: int, damage_type: String, source: Node) -> Dictionary:
	var normalized_type: String = _normalize_defensive_damage_type(damage_type)
	var context: Dictionary = {
		"incoming_damage": maxi(incoming_damage, 0),
		"damage_type": normalized_type,
		"same_absorption_active": _absorb_resistance_type == normalized_type and not normalized_type.is_empty(),
		"eligible_reactor_actor_ids": [player.get_instance_id()]
	}
	var summary: Dictionary = await _run_coordinated_reaction_event(
		"ВЫ ПОЛУЧАЕТЕ СТИХИЙНЫЙ УРОН",
		"Источник %s должен нанести %d урона типа «%s». Защитная реакция применяется до окончательного уменьшения HP." % [
			_target_name(source) if source != null else "неизвестен",
			incoming_damage,
			normalized_type
		],
		ReactionOpportunitySystem.TRIGGER_ELEMENTAL_DAMAGE_TAKEN,
		context,
		source,
		player
	)
	return _find_coordinated_result(summary, ReactionOpportunitySystem.OPTION_ABSORB_ELEMENTS)


func _trigger_readied_attack_if_possible(actor: Node) -> void:
	if not _target_is_valid(actor):
		return
	await _run_coordinated_reaction_event(
		"СРАБОТАЛО ПОДГОТОВЛЕННОЕ ДЕЙСТВИЕ",
		"%s вошёл в условие подготовленного действия. Все подходящие участники могут выполнить свою подготовленную реакцию." % _target_name(actor),
		ReactionOpportunitySystem.TRIGGER_READIED_ACTION,
		{
			"eligible_reactor_team_ids": [ReactionCandidate.TEAM_PARTY],
			"allow_source_reaction": false
		},
		actor,
		player
	)


func offer_player_opportunity_attack_if_triggered(
	actor: Node,
	from_position: Vector2,
	to_position: Vector2
) -> bool:
	if not _turn_system.active or not _target_is_valid(actor) or not (actor is Node2D):
		return false
	var summary: Dictionary = await _run_coordinated_reaction_event(
		"ВОЗМОЖНОСТЬ РЕАКЦИИ",
		"%s покидает досягаемость. Все подходящие участники проверяются единым событием атаки по возможности." % _target_name(actor),
		ReactionOpportunitySystem.TRIGGER_ENEMY_LEAVES_REACH,
		{
			"from_position": from_position,
			"to_position": to_position,
			"eligible_reactor_team_ids": [ReactionCandidate.TEAM_PARTY],
			"allow_source_reaction": false
		},
		actor,
		player
	)
	return _summary_has_resolved_option(summary, ReactionOpportunitySystem.OPTION_OPPORTUNITY_ATTACK)


func _find_coordinated_result(summary: Dictionary, option_id: String) -> Dictionary:
	var resolutions_value: Variant = summary.get("resolutions", [])
	if resolutions_value is Array:
		for index: int in range((resolutions_value as Array).size() - 1, -1, -1):
			var value: Variant = (resolutions_value as Array)[index]
			if value is Dictionary and str((value as Dictionary).get("option_id", "")) == option_id:
				return value as Dictionary
	return {}


func _summary_has_resolved_option(summary: Dictionary, option_id: String) -> bool:
	var result: Dictionary = _find_coordinated_result(summary, option_id)
	return bool(result.get("resolved", false))


func get_last_completed_reaction_event_for_testing() -> ReactionEvent:
	return _last_completed_reaction_event
