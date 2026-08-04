extends "res://scripts/game/game_controllable_ally_control_runtime.gd"


func resolve_npc_attack(
	attacker: Node,
	attack_bonus: int,
	damage_die: int,
	damage_bonus: int,
	damage_type: String = "slashing"
) -> Dictionary:
	if _enemy_should_attack_ally(attacker):
		return _resolve_npc_attack_against_ally(
			attacker,
			attack_bonus,
			damage_die,
			damage_bonus,
			damage_type
		)
	return super.resolve_npc_attack(
		attacker,
		attack_bonus,
		damage_die,
		damage_bonus,
		damage_type
	)


func _enemy_should_attack_ally(attacker: Node) -> bool:
	if (
		not is_instance_valid(attacker)
		or not attacker is Node2D
		or not is_instance_valid(_controllable_ally)
		or not _controllable_ally is Node2D
		or not _controllable_ally.has_method("can_receive_enemy_attack")
		or not bool(_controllable_ally.call("can_receive_enemy_attack"))
	):
		return false
	var attacker_position: Vector2 = (attacker as Node2D).global_position
	var ally_position: Vector2 = (_controllable_ally as Node2D).global_position
	var ally_distance: int = DistanceSystem.distance_feet(attacker_position, ally_position)
	if ally_distance > DistanceSystem.MELEE_REACH_FEET:
		return false
	if not is_instance_valid(player):
		return true
	var player_distance: int = DistanceSystem.distance_feet(
		attacker_position,
		player.global_position
	)
	return (
		GameState.player_character.current_health <= 0
		or ally_distance <= player_distance
	)


func _resolve_npc_attack_against_ally(
	attacker: Node,
	attack_bonus: int,
	damage_die: int,
	damage_bonus: int,
	damage_type: String,
	natural_override: int = -1,
	damage_override: int = -1
) -> Dictionary:
	if (
		not is_instance_valid(attacker)
		or not attacker is Node2D
		or not is_instance_valid(_controllable_ally)
		or not _controllable_ally is Node2D
	):
		return {"hit": false, "status": "invalid_actor"}
	var ally_state: CombatantState = _ally_state()
	if ally_state == null or ally_state.dead:
		return {"hit": false, "status": "ally_dead"}
	var attacker_position: Vector2 = (attacker as Node2D).global_position
	var ally_position: Vector2 = (_controllable_ally as Node2D).global_position
	var cover: Dictionary = (
		_combat_environment.get_cover(attacker_position, ally_position)
		if _combat_environment != null
		else {"bonus": 0, "total_cover": false}
	)
	if bool(cover.get("total_cover", false)):
		show_combat_message(
			"%s не видит Ирну за полным укрытием." % _target_name(attacker),
			false
		)
		return {"hit": false, "total_cover": true}
	var attacker_state: CombatantState = _state_for(attacker)
	var distance: int = DistanceSystem.distance_feet(attacker_position, ally_position)
	var adjustments: Dictionary = _srd_rules.attack_roll_adjustments(
		attacker_state,
		ally_state,
		distance,
		true,
		true
	)
	if bool(adjustments.get("blocked", false)):
		return {"hit": false, "blocked": true}
	var roll: Dictionary
	if natural_override >= 1:
		var natural: int = clampi(natural_override, 1, 20)
		roll = {
			"natural": natural,
			"total": natural + attack_bonus
		}
	else:
		roll = _srd_rules.roll_d20(
			attack_bonus,
			bool(adjustments.get("advantage", false)),
			bool(adjustments.get("disadvantage", false)) or _ally_is_dodging()
		)
	var natural_roll: int = int(roll.get("natural", 1))
	var target_ac: int = _ally_armor_class() + int(cover.get("bonus", 0))
	var hit: bool = natural_roll != 1 and (
		natural_roll == 20
		or int(roll.get("total", 0)) >= target_ac
	)
	if not hit:
		show_combat_message(
			"%s промахивается по Ирне: %d против КД %d." % [
				_target_name(attacker),
				int(roll.get("total", 0)),
				target_ac
			],
			false
		)
		return {
			"hit": false,
			"natural": natural_roll,
			"total": int(roll.get("total", 0)),
			"target": "ally"
		}
	var critical: bool = (
		natural_roll == 20
		or bool(adjustments.get("automatic_critical", false))
	)
	var damage: int = damage_override
	if damage < 0:
		damage = damage_bonus
		for _index: int in range(2 if critical else 1):
			damage += _srd_dice.roll_die(maxi(damage_die, 2))
	var damage_result: Dictionary = _apply_damage_to_ally(
		maxi(damage, 0),
		damage_type,
		critical,
		attacker
	)
	damage_result["hit"] = true
	damage_result["natural"] = natural_roll
	damage_result["total"] = int(roll.get("total", 0))
	damage_result["target"] = "ally"
	return damage_result


func _apply_damage_to_ally(
	amount: int,
	damage_type: String,
	critical_hit: bool = false,
	source: Node = null
) -> Dictionary:
	if not is_instance_valid(_controllable_ally):
		return {"applied": 0, "status": "ally_missing"}
	var state: CombatantState = _ally_state()
	if state == null:
		return {"applied": 0, "status": "state_missing"}
	if state.dead:
		return {"applied": 0, "dead": true}
	if _ally_current_health() <= 0:
		var zero_result: Dictionary = _srd_rules.damage_at_zero_hit_points(
			state,
			critical_hit
		)
		show_combat_message(
			"Урон по Ирне при 0 HP: получено %d провала спасброска смерти." % int(
				zero_result.get("failures_added", 0)
			),
			false
		)
		if bool(zero_result.get("dead", false)):
			_call_ally("mark_dead")
		_update_status()
		return zero_result
	var mitigation: Dictionary = _srd_rules.resolve_damage(
		maxi(amount, 0),
		damage_type,
		state
	)
	var applied: int = int(mitigation.get("applied", 0))
	var before: int = _ally_current_health()
	var after: int = maxi(0, before - applied)
	var remaining_damage: int = maxi(applied - before, 0)
	var source_name: String = _target_name(source) if is_instance_valid(source) else "Источник"
	show_combat_message(
		"%s наносит Ирне %d урона. HP: %d/%d." % [
			source_name,
			applied,
			after,
			_ally_maximum_health()
		],
		false
	)
	if after > 0:
		_call_ally("set_current_health", [after])
	elif remaining_damage >= _ally_maximum_health():
		_call_ally("mark_dead")
		show_combat_message("Ирна погибает от массивного урона.", false)
	else:
		_call_ally("enter_dying")
		show_combat_message(
			"Ирна теряет сознание и начинает совершать спасброски смерти.",
			false
		)
	_update_status()
	return {
		"applied": applied,
		"current_health": _ally_current_health(),
		"dead": state.dead,
		"dying": _ally_current_health() <= 0 and not state.dead,
		"critical": critical_hit
	}


func _ally_armor_class() -> int:
	return int(_controllable_ally.call("get_armor_class")) if is_instance_valid(_controllable_ally) and _controllable_ally.has_method("get_armor_class") else 10


func _ally_is_dodging() -> bool:
	return bool(_controllable_ally.call("is_dodging")) if is_instance_valid(_controllable_ally) and _controllable_ally.has_method("is_dodging") else false


func enemy_should_attack_ally_for_testing(attacker: Node) -> bool:
	return _enemy_should_attack_ally(attacker)


func resolve_npc_attack_against_ally_for_testing(
	attacker: Node,
	natural_roll: int,
	damage: int
) -> Dictionary:
	return _resolve_npc_attack_against_ally(
		attacker,
		0,
		2,
		0,
		"slashing",
		natural_roll,
		damage
	)


func apply_damage_to_controllable_ally_for_testing(
	amount: int,
	critical_hit: bool = false
) -> Dictionary:
	return _apply_damage_to_ally(
		amount,
		"slashing",
		critical_hit,
		null
	)
