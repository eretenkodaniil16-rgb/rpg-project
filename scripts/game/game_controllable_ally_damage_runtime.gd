extends "res://scripts/game/game_controllable_ally_control_runtime.gd"


func resolve_npc_attack(
	attacker: Node,
	attack_bonus: int,
	damage_die: int,
	damage_bonus: int,
	damage_type: String = "slashing"
) -> Dictionary:
	return super.resolve_npc_attack(
		attacker,
		attack_bonus,
		damage_die,
		damage_bonus,
		damage_type
	)


func _enemy_should_attack_ally(attacker: Node) -> bool:
	if not is_instance_valid(attacker) or not attacker is Node2D:
		return false
	if not is_instance_valid(_controllable_ally) or not _controllable_ally is Node2D:
		return false
	if not _controllable_ally.has_method("can_receive_enemy_attack"):
		return false
	if not bool(_controllable_ally.call("can_receive_enemy_attack")):
		return false
	var attacker_position: Vector2 = (attacker as Node2D).global_position
	var ally_position: Vector2 = (_controllable_ally as Node2D).global_position
	var ally_distance: int = DistanceSystem.distance_feet(attacker_position, ally_position)
	if ally_distance > DistanceSystem.MELEE_REACH_FEET:
		return false
	if not is_instance_valid(player):
		return true
	var player_distance: int = DistanceSystem.distance_feet(attacker_position, player.global_position)
	return GameState.player_character.current_health <= 0 or ally_distance <= player_distance


func enemy_should_attack_ally_for_testing(attacker: Node) -> bool:
	return _enemy_should_attack_ally(attacker)
