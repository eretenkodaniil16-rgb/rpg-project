extends "res://scripts/game/game_feature_ui.gd"

var _reaction_roll: bool = false


func resolve_npc_attack(attacker: Node, attack_bonus: int, damage_die: int, damage_bonus: int, damage_type: String = "slashing") -> Dictionary:
	if attacker == null or not (attacker is Node2D):
		_reaction_roll = false
		return {"hit": false}
	var cover: Dictionary = _combat_environment.get_cover((attacker as Node2D).global_position, player.global_position) if _combat_environment != null else {"bonus": 0, "total_cover": false}
	if bool(cover.get("total_cover", false)):
		show_combat_message("%s не видит героя за полным укрытием." % _target_name(attacker), false)
		_reaction_roll = false
		return {"hit": false, "total_cover": true}
	var adjustments: Dictionary = _srd_rules.attack_roll_adjustments(_state_for(attacker), _player_combat_state, DistanceSystem.distance_feet((attacker as Node2D).global_position, player.global_position), true, true)
	var disadvantage: bool = bool(adjustments.get("disadvantage", false)) or player_is_dodging()
	var advantage: bool = bool(adjustments.get("advantage", false))
	var roll: Dictionary = _srd_rules.roll_d20(attack_bonus, advantage, disadvantage)
	var result := AttackResult.new()
	result.attacker_name = _target_name(attacker)
	result.target_name = GameState.player_character.character_name
	result.attack_name = "Атака по возможности" if _reaction_roll else "Атака"
	result.is_reaction = _reaction_roll
	result.natural_roll = int(roll.get("natural", 1))
	result.first_roll = int(roll.get("first", result.natural_roll))
	result.second_roll = int(roll.get("second", 0))
	result.advantage = advantage
	result.disadvantage = disadvantage
	result.attack_bonus = attack_bonus
	result.total = int(roll.get("total", result.natural_roll + attack_bonus))
	result.cover_bonus = int(cover.get("bonus", 0))
	result.target_armor_class = _class_data.get_armor_class(GameState.player_character) + result.cover_bonus
	result.hit = result.natural_roll != 1 and (result.natural_roll == 20 or result.total >= result.target_armor_class)
	result.critical = result.natural_roll == 20 or bool(adjustments.get("automatic_critical", false))
	result.damage_type = damage_type
	if result.hit:
		result.damage = damage_bonus
		for _index: int in range(2 if result.critical else 1):
			result.damage += _srd_dice.roll_die(maxi(damage_die, 2))
		var applied: Dictionary = apply_damage_to_player(result.damage, damage_type, result.critical, attacker)
		result.damage = int(applied.get("applied", result.damage))
	result.target_health_after = GameState.player_character.current_health
	result.target_max_health = GameState.player_character.maximum_health
	if _combat_feed != null:
		_combat_feed.show_result(result)
	_reaction_roll = false
	return {"hit": result.hit, "natural": result.natural_roll, "total": result.total, "applied": result.damage, "critical": result.critical}


func _trigger_enemy_opportunity_attacks(from_position: Vector2, to_position: Vector2) -> void:
	for entry: Dictionary in _turn_system.entries:
		if bool(entry.get("is_player", false)):
			continue
		var actor: Node = entry.get("node") as Node
		if not is_instance_valid(actor) or not (actor is Node2D):
			continue
		if actor.has_method("is_hostile") and not bool(actor.call("is_hostile")):
			continue
		if not _turn_system.has_reaction(actor):
			continue
		var current_distance: int = DistanceSystem.distance_feet((actor as Node2D).global_position, from_position)
		var future_distance: int = DistanceSystem.distance_feet((actor as Node2D).global_position, to_position)
		if current_distance <= DistanceSystem.MELEE_REACH_FEET and future_distance > DistanceSystem.MELEE_REACH_FEET:
			_turn_system.consume_reaction(actor)
			if actor.has_method("perform_opportunity_attack"):
				_reaction_roll = true
				actor.call("perform_opportunity_attack")
				_reaction_roll = false
				if GameState.player_character.current_health <= 0:
					return
