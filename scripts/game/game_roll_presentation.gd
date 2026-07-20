extends "res://scripts/game/game_feature_ui.gd"

var _reaction_roll: bool = false

func resolve_npc_attack(attacker: Node, attack_bonus: int, damage_die: int, damage_bonus: int, damage_type: String = "slashing") -> Dictionary:
	if attacker == null or not (attacker is Node2D):
		return {"hit": false}
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
	result.target_armor_class = _class_data.get_armor_class(GameState.player_character)
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
	return {"hit": result.hit, "natural": result.natural_roll, "total": result.total, "applied": result.damage, "critical": result.critical}
