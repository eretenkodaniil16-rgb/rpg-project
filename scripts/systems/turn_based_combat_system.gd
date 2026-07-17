class_name TurnBasedCombatSystem
extends RefCounted

const BASE_MOVEMENT_FEET: int = 30

var active: bool = false
var round_number: int = 0
var current_index: int = -1
var entries: Array[Dictionary] = []

var action_available: bool = false
var bonus_action_available: bool = false
var reaction_available: bool = false
var movement_remaining_feet: int = 0
var disengaged: bool = false
var dodging: bool = false

var _rng: RandomNumberGenerator = RandomNumberGenerator.new()


func start_combat(player: Node, opponents: Array[Node], player_dexterity_modifier: int, initiative_overrides: Dictionary = {}) -> void:
	active = true
	round_number = 1
	current_index = -1
	entries.clear()
	entries.append(_make_entry(player, true, player_dexterity_modifier, initiative_overrides))
	for opponent: Node in opponents:
		if not is_instance_valid(opponent):
			continue
		var modifier: int = int(opponent.call("get_initiative_modifier")) if opponent.has_method("get_initiative_modifier") else 0
		entries.append(_make_entry(opponent, false, modifier, initiative_overrides))
	entries.sort_custom(_sort_entries)
	current_index = _first_active_index()
	_begin_current_turn()


func stop_combat() -> void:
	active = false
	round_number = 0
	current_index = -1
	entries.clear()
	action_available = false
	bonus_action_available = false
	reaction_available = false
	movement_remaining_feet = 0
	disengaged = false
	dodging = false


func current_actor() -> Node:
	if not active or current_index < 0 or current_index >= entries.size():
		return null
	return entries[current_index].get("node") as Node


func current_entry() -> Dictionary:
	if not active or current_index < 0 or current_index >= entries.size():
		return {}
	return entries[current_index]


func is_player_turn(player: Node) -> bool:
	return active and current_actor() == player


func consume_action() -> bool:
	if not action_available:
		return false
	action_available = false
	return true


func consume_bonus_action() -> bool:
	if not bonus_action_available:
		return false
	bonus_action_available = false
	return true


func consume_reaction(actor: Node) -> bool:
	var entry_index: int = _find_entry_index(actor)
	if entry_index < 0 or not bool(entries[entry_index].get("reaction", false)):
		return false
	entries[entry_index]["reaction"] = false
	if entry_index == current_index and bool(entries[entry_index].get("is_player", false)):
		reaction_available = false
	return true


func has_reaction(actor: Node) -> bool:
	var entry_index: int = _find_entry_index(actor)
	return entry_index >= 0 and bool(entries[entry_index].get("reaction", false))


func spend_movement(feet: int) -> bool:
	var safe_cost: int = maxi(feet, 0)
	if movement_remaining_feet < safe_cost:
		return false
	movement_remaining_feet -= safe_cost
	return true


func add_movement(feet: int) -> void:
	movement_remaining_feet += maxi(feet, 0)


func use_dash() -> bool:
	if not consume_action():
		return false
	add_movement(BASE_MOVEMENT_FEET)
	return true


func use_disengage() -> bool:
	if not consume_action():
		return false
	disengaged = true
	return true


func use_dodge() -> bool:
	if not consume_action():
		return false
	dodging = true
	return true


func advance_turn() -> Node:
	if not active or entries.is_empty():
		return null
	var previous_index: int = current_index
	var candidate: int = current_index
	for _attempt: int in range(entries.size()):
		candidate += 1
		if candidate >= entries.size():
			candidate = 0
			round_number += 1
		if _entry_is_active(entries[candidate]):
			current_index = candidate
			_begin_current_turn()
			return current_actor()
	current_index = previous_index
	return current_actor()


func get_order_labels() -> Array[String]:
	var labels: Array[String] = []
	for index: int in range(entries.size()):
		var entry: Dictionary = entries[index]
		var prefix: String = "▶ " if active and index == current_index else ""
		labels.append("%s%s [%d]" % [prefix, str(entry.get("name", "Участник")), int(entry.get("initiative", 0))])
	return labels


func get_initiative(actor: Node) -> int:
	var entry_index: int = _find_entry_index(actor)
	return int(entries[entry_index].get("initiative", 0)) if entry_index >= 0 else 0


func force_current_actor_for_testing(actor: Node) -> void:
	var entry_index: int = _find_entry_index(actor)
	if entry_index >= 0:
		current_index = entry_index
		_begin_current_turn()


func _make_entry(actor: Node, is_player: bool, dexterity_modifier: int, overrides: Dictionary) -> Dictionary:
	var instance_id: int = actor.get_instance_id()
	var initiative_roll: int = int(overrides.get(instance_id, _rng.randi_range(1, 4)))
	var display_name: String = "Герой" if is_player else (str(actor.call("get_combat_name")) if actor.has_method("get_combat_name") else actor.name)
	return {
		"node": actor,
		"name": display_name,
		"is_player": is_player,
		"dexterity_modifier": dexterity_modifier,
		"initiative_roll": initiative_roll,
		"initiative": initiative_roll + dexterity_modifier,
		"reaction": true
	}


func _sort_entries(left: Dictionary, right: Dictionary) -> bool:
	var left_initiative: int = int(left.get("initiative", 0))
	var right_initiative: int = int(right.get("initiative", 0))
	if left_initiative != right_initiative:
		return left_initiative > right_initiative
	var left_dexterity: int = int(left.get("dexterity_modifier", 0))
	var right_dexterity: int = int(right.get("dexterity_modifier", 0))
	if left_dexterity != right_dexterity:
		return left_dexterity > right_dexterity
	return int((left.get("node") as Node).get_instance_id()) < int((right.get("node") as Node).get_instance_id())


func _begin_current_turn() -> void:
	if current_index < 0 or current_index >= entries.size():
		return
	entries[current_index]["reaction"] = true
	var player_turn: bool = bool(entries[current_index].get("is_player", false))
	if player_turn:
		action_available = true
		bonus_action_available = true
		reaction_available = true
		movement_remaining_feet = BASE_MOVEMENT_FEET
		disengaged = false
		dodging = false
	else:
		action_available = false
		bonus_action_available = false
		reaction_available = false
		movement_remaining_feet = 0
		disengaged = false


func _first_active_index() -> int:
	for index: int in range(entries.size()):
		if _entry_is_active(entries[index]):
			return index
	return -1


func _entry_is_active(entry: Dictionary) -> bool:
	var actor: Node = entry.get("node") as Node
	if not is_instance_valid(actor):
		return false
	return not actor.has_method("is_combat_active") or bool(actor.call("is_combat_active"))


func _find_entry_index(actor: Node) -> int:
	for index: int in range(entries.size()):
		if entries[index].get("node") == actor:
			return index
	return -1
