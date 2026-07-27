extends "res://scripts/game/game_reaction_opportunities_runtime.gd"


func _trigger_readied_attack_if_possible(actor: Node) -> void:
	if (
		not _player_combat_state.readied_attack
		or not _turn_system.has_reaction(player)
		or not _target_is_valid(actor)
		or _reaction_choice_prompt == null
		or _reaction_choice_prompt.is_waiting_for_decision()
	):
		return
	var weapon: Dictionary = _class_data.get_equipped_weapon(GameState.player_character)
	var distance_feet: int = DistanceSystem.distance_feet(
		player.global_position,
		(actor as Node2D).global_position
	)
	if DistanceSystem.weapon_range_state(weapon, distance_feet) == "out_of_range":
		return
	var session: Dictionary = _create_coordinated_reaction_session(
		ReactionOpportunitySystem.TRIGGER_READIED_ACTION,
		{
			"readied_trigger_matches": true,
			"readied_description": "Совершить подготовленную атаку по %s, вошедшему в дистанцию оружия." % _target_name(actor),
			"eligible_reactor_actor_ids": [player.get_instance_id()]
		},
		actor,
		player
	)
	var selection: Dictionary = await _request_next_coordinated_reaction(
		"СРАБОТАЛО ПОДГОТОВЛЕННОЕ ДЕЙСТВИЕ",
		"%s вошёл в дистанцию подготовленной атаки. Можно потратить реакцию сейчас или пропустить этот момент." % _target_name(actor),
		session
	)
	if selection.is_empty():
		show_combat_message("Подготовленная атака не использована; реакция сохранена.", true)
		return
	var result: Dictionary = _reaction_coordinator.resolve_selection(
		selection.get("event") as ReactionEvent,
		str(selection.get("selection_id", ""))
	)
	if str(result.get("runtime_action", "")) != ReactionOpportunitySystem.OPTION_READIED_ATTACK:
		show_combat_message(str(result.get("message", "Подготовленная атака недоступна.")), false)
		return
	var reactor_actor: Node = result.get("reactor_actor") as Node
	if reactor_actor != player or not _turn_system.consume_reaction(reactor_actor):
		show_combat_message("Реакция уже недоступна.", false)
		return
	_player_combat_state.readied_attack = false
	show_combat_message("Срабатывает выбранная подготовленная атака.", true)
	await _perform_srd_weapon_attack(actor, weapon, str(weapon.get("ammunition_id", "")))


func offer_player_opportunity_attack_if_triggered(
	actor: Node,
	from_position: Vector2,
	to_position: Vector2
) -> bool:
	if (
		not _turn_system.active
		or not _target_is_valid(actor)
		or not (actor is Node2D)
		or _reaction_choice_prompt == null
		or _reaction_choice_prompt.is_waiting_for_decision()
	):
		return false
	var current_distance: int = DistanceSystem.distance_feet(player.global_position, from_position)
	var future_distance: int = DistanceSystem.distance_feet(player.global_position, to_position)
	var weapon: Dictionary = _class_data.get_equipped_weapon(GameState.player_character)
	var melee_weapon: bool = not DistanceSystem.is_ranged_weapon(weapon)
	var session: Dictionary = _create_coordinated_reaction_session(
		ReactionOpportunitySystem.TRIGGER_ENEMY_LEAVES_REACH,
		{
			"target_leaves_reach": current_distance <= DistanceSystem.MELEE_REACH_FEET and future_distance > DistanceSystem.MELEE_REACH_FEET,
			"can_make_weapon_attack": melee_weapon,
			"from_position": from_position,
			"to_position": to_position
		},
		actor,
		null
	)
	var attack_performed: bool = false
	while _reaction_coordinator.should_continue(session.get("event") as ReactionEvent):
		var selection: Dictionary = await _request_next_coordinated_reaction(
			"ВОЗМОЖНОСТЬ РЕАКЦИИ",
			"%s покидает досягаемость реагирующих существ. Можно совершить атаку по возможности." % _target_name(actor),
			session
		)
		if selection.is_empty():
			break
		var result: Dictionary = _reaction_coordinator.resolve_selection(
			selection.get("event") as ReactionEvent,
			str(selection.get("selection_id", ""))
		)
		if str(result.get("runtime_action", "")) != ReactionOpportunitySystem.OPTION_OPPORTUNITY_ATTACK:
			continue
		var reactor_actor: Node = result.get("reactor_actor") as Node
		if not is_instance_valid(reactor_actor) or not _turn_system.consume_reaction(reactor_actor):
			show_combat_message("Реакция выбранного участника уже недоступна.", false)
			continue
		if reactor_actor == player:
			show_combat_message("Выбрана атака по возможности.", true)
			await _perform_srd_weapon_attack(actor, weapon, str(weapon.get("ammunition_id", "")))
			attack_performed = true
		elif reactor_actor.has_method("execute_reaction_runtime_action"):
			await reactor_actor.call(
				"execute_reaction_runtime_action",
				ReactionOpportunitySystem.OPTION_OPPORTUNITY_ATTACK,
				actor,
				result.duplicate(true)
			)
			attack_performed = true
		if not _target_is_valid(actor):
			var event: ReactionEvent = selection.get("event") as ReactionEvent
			event.invalidate("Цель атаки по возможности больше недоступна.")
			break
	if not attack_performed:
		show_combat_message("Атака по возможности пропущена; реакция сохранена.", true)
	return attack_performed
