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
	var options: Array[Dictionary] = _reaction_opportunities.sort_options(
		_reaction_opportunities.collect_options(
			ReactionOpportunitySystem.TRIGGER_READIED_ACTION,
			{
				"reaction_available": _turn_system.has_reaction(player),
				"readied_trigger_matches": true,
				"readied_description": "Совершить подготовленную атаку по %s, вошедшему в дистанцию оружия." % _target_name(actor)
			}
		)
	)
	if options.is_empty():
		return
	var chosen_id: String = await _reaction_choice_prompt.request_reaction(
		"СРАБОТАЛО ПОДГОТОВЛЕННОЕ ДЕЙСТВИЕ",
		"%s вошёл в дистанцию подготовленной атаки. Можно потратить реакцию сейчас или пропустить этот момент." % _target_name(actor),
		options
	)
	if chosen_id != ReactionOpportunitySystem.OPTION_READIED_ATTACK:
		show_combat_message("Подготовленная атака не использована; реакция сохранена.", true)
		return
	if not _turn_system.consume_reaction(player):
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
		or not _turn_system.has_reaction(player)
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
	var options: Array[Dictionary] = _reaction_opportunities.sort_options(
		_reaction_opportunities.collect_options(
			ReactionOpportunitySystem.TRIGGER_ENEMY_LEAVES_REACH,
			{
				"reaction_available": _turn_system.has_reaction(player),
				"target_leaves_reach": current_distance <= DistanceSystem.MELEE_REACH_FEET and future_distance > DistanceSystem.MELEE_REACH_FEET,
				"can_make_weapon_attack": melee_weapon
			}
		)
	)
	if options.is_empty():
		return false
	var chosen_id: String = await _reaction_choice_prompt.request_reaction(
		"ВОЗМОЖНОСТЬ РЕАКЦИИ",
		"%s покидает вашу досягаемость. Можно совершить атаку по возможности." % _target_name(actor),
		options
	)
	if chosen_id != ReactionOpportunitySystem.OPTION_OPPORTUNITY_ATTACK:
		show_combat_message("Атака по возможности пропущена; реакция сохранена.", true)
		return false
	if not _turn_system.consume_reaction(player):
		show_combat_message("Реакция уже недоступна.", false)
		return false
	show_combat_message("Выбрана атака по возможности.", true)
	await _perform_srd_weapon_attack(actor, weapon, str(weapon.get("ammunition_id", "")))
	return true
