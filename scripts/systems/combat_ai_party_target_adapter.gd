class_name CombatAiPartyTargetAdapter
extends RefCounted


func is_supported(target: Node, primary_player: Node) -> bool:
	if not is_instance_valid(target):
		return false
	if target == primary_player:
		return true
	return (
		target is Node2D
		and target.has_method("get_actor_id")
		and target.has_method("get_current_health")
		and target.has_method("get_maximum_health")
		and target.has_method("get_armor_class")
		and target.has_method("get_saving_throw_modifier")
		and target.has_method("get_combatant_state")
	)


func get_actor_id(target: Node, primary_player: Node) -> String:
	if not is_instance_valid(target):
		return ""
	if target == primary_player:
		return "player"
	return str(target.call("get_actor_id")) if target.has_method("get_actor_id") else ""


func get_display_name(target: Node, primary_player: Node) -> String:
	if not is_instance_valid(target):
		return "цель"
	if target == primary_player:
		return "герой"
	if target.has_method("get_combat_name"):
		return str(target.call("get_combat_name"))
	return str(target.name)


func get_current_health(
	target: Node,
	primary_player: Node,
	player_character: PlayerCharacter
) -> int:
	if not is_instance_valid(target):
		return 0
	if target == primary_player:
		return player_character.current_health if player_character != null else 0
	return int(target.call("get_current_health")) if target.has_method("get_current_health") else 0


func get_maximum_health(
	target: Node,
	primary_player: Node,
	player_character: PlayerCharacter
) -> int:
	if not is_instance_valid(target):
		return 1
	if target == primary_player:
		return maxi(player_character.maximum_health, 1) if player_character != null else 1
	return maxi(int(target.call("get_maximum_health")), 1) if target.has_method("get_maximum_health") else 1


func get_health_ratio(
	target: Node,
	primary_player: Node,
	player_character: PlayerCharacter
) -> float:
	return float(get_current_health(target, primary_player, player_character)) / float(
		get_maximum_health(target, primary_player, player_character)
	)


func get_armor_class(
	target: Node,
	primary_player: Node,
	player_armor_class: int
) -> int:
	if not is_instance_valid(target):
		return 10
	if target == primary_player:
		return maxi(player_armor_class, 1)
	return maxi(int(target.call("get_armor_class")), 1) if target.has_method("get_armor_class") else 10


func get_saving_throw_modifier(
	target: Node,
	ability_id: String,
	primary_player: Node,
	player_character: PlayerCharacter
) -> int:
	if not is_instance_valid(target):
		return 0
	if target == primary_player:
		return player_character.get_saving_throw_modifier(ability_id) if player_character != null else 0
	return int(target.call("get_saving_throw_modifier", ability_id)) if target.has_method("get_saving_throw_modifier") else 0


func get_combatant_state(
	target: Node,
	primary_player: Node,
	player_state: CombatantState
) -> CombatantState:
	if not is_instance_valid(target):
		return null
	if target == primary_player:
		return player_state
	if target.has_method("get_combatant_state"):
		return target.call("get_combatant_state") as CombatantState
	return null


func is_available(
	target: Node,
	primary_player: Node,
	player_character: PlayerCharacter,
	player_state: CombatantState
) -> bool:
	if not is_supported(target, primary_player):
		return false
	if get_current_health(target, primary_player, player_character) <= 0:
		return false
	var state: CombatantState = get_combatant_state(target, primary_player, player_state)
	if state != null and state.dead:
		return false
	if target != primary_player and target.has_method("can_receive_enemy_attack"):
		return bool(target.call("can_receive_enemy_attack"))
	return true


func is_hidden(
	target: Node,
	primary_player: Node,
	player_state: CombatantState
) -> bool:
	var state: CombatantState = get_combatant_state(target, primary_player, player_state)
	return state != null and state.hidden


func set_current_health(
	target: Node,
	value: int,
	primary_player: Node,
	player_character: PlayerCharacter
) -> bool:
	if not is_instance_valid(target):
		return false
	if target == primary_player:
		if player_character == null:
			return false
		player_character.current_health = clampi(value, 0, maxi(player_character.maximum_health, 1))
		return true
	if target.has_method("set_current_health"):
		target.call("set_current_health", value)
		return true
	return false
