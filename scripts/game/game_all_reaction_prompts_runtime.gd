extends "res://scripts/game/game_reaction_opportunities_runtime.gd"

const UNARMED_OPPORTUNITY_WEAPON: Dictionary = {
	"id": "unarmed_strike",
	"name": "Безоружный удар",
	"type": "weapon",
	"weapon_category": "simple",
	"damage_dice": [1, 1],
	"damage_type": "дробящий",
	"ability": "strength",
	"properties": [],
	"reach_ft": 5
}


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
	var weapon: Dictionary = _opportunity_attack_weapon()
	var session: Dictionary = _create_coordinated_reaction_session(
		ReactionOpportunitySystem.TRIGGER_ENEMY_LEAVES_REACH,
		{
			"target_leaves_reach": current_distance <= DistanceSystem.MELEE_REACH_FEET and future_distance > DistanceSystem.MELEE_REACH_FEET,
			"can_make_weapon_attack": not weapon.is_empty(),
			"from_position": from_position,
			"to_position": to_position,
			"eligible_reactor_actor_ids": [player.get_instance_id()]
		},
		actor,
		null
	)
	var event: ReactionEvent = session.get("event") as ReactionEvent
	var selection: Dictionary = await _request_next_coordinated_reaction(
		"ВОЗМОЖНОСТЬ РЕАКЦИИ",
		"%s покидает вашу досягаемость. Можно совершить атаку по возможности." % _target_name(actor),
		session
	)
	if selection.is_empty():
		if event != null and event.is_open():
			event.invalidate("Игрок пропустил атаку по возможности.")
		show_combat_message("Атака по возможности пропущена; реакция сохранена.", true)
		return false
	var result: Dictionary = _reaction_coordinator.resolve_selection(
		event,
		str(selection.get("selection_id", ""))
	)
	if str(result.get("runtime_action", "")) != ReactionOpportunitySystem.OPTION_OPPORTUNITY_ATTACK:
		if event != null and event.is_open():
			event.invalidate("Выбранная реакция не является атакой по возможности.")
		show_combat_message(str(result.get("message", "Атака по возможности недоступна.")), false)
		return false
	var reactor_actor: Node = result.get("reactor_actor") as Node
	if reactor_actor != player or not _turn_system.consume_reaction(player):
		if event != null and event.is_open():
			event.invalidate("Реакция игрока уже недоступна.")
		show_combat_message("Реакция уже недоступна.", false)
		return false
	show_combat_message("Выбрана атака по возможности.", true)
	await _perform_srd_weapon_attack(actor, weapon, str(weapon.get("ammunition_id", "")))
	if event != null and event.is_open():
		event.invalidate("Атака по возможности разрешена.")
	return true


func _opportunity_attack_weapon() -> Dictionary:
	var equipped: Dictionary = _class_data.get_equipped_weapon(GameState.player_character)
	if not equipped.is_empty() and DistanceSystem.weapon_range_state(equipped, DistanceSystem.MELEE_REACH_FEET) == "melee":
		return equipped
	# Rules allow an unarmed strike even while the equipped weapon is ranged.
	return UNARMED_OPPORTUNITY_WEAPON.duplicate(true)