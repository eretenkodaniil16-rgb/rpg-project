class_name TurnBasedCombatSystem
extends RefCounted

const BASE_MOVEMENT_FEET: int = 30
const INITIATIVE_DIE_SIDES: int = 20

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
var _pending_player_controlled_actors: Array[Node] = []


func set_pending_player_controlled_actors(actors: Array[Node]) -> void:
	_pending_player_controlled_actors.clear()
	for actor: Node in actors:
		if not is_instance_valid(actor) or _pending_player_controlled_actors.has(actor):
			continue
		_pending_player_controlled_actors.append(actor)


func clear_pending_player_controlled_actors() -> void:
	_pending_player_controlled_actors.clear()


func start_combat(
	player: Node,
	opponents: Array[Node],
	player_dexterity_modifier: int,
	initiative_overrides: Dictionary = {},
	player_proficiency_bonus: int = 0,
	player_initiative_proficient: bool = false
) -> void:
	active = true
	round_number = 1
	current_index = -1
	entries.clear()
	var player_initiative_proficiency: int = maxi(player_proficiency_bonus, 0) if player_initiative_proficient else 0
	if player.has_method("get_initiative_proficiency_bonus"):
		player_initiative_proficiency = maxi(player_initiative_proficiency, int(player.call("get_initiative_proficiency_bonus")))
	entries.append(_make_entry(
		player,
		true,
		player_dexterity_modifier,
		player_initiative_proficiency,
		initiative_overrides,
		true
	))
	for controlled_actor: Node in _pending_player_controlled_actors:
		if not is_instance_valid(controlled_actor) or controlled_actor == player:
			continue
		if controlled_actor.has_method("is_combat_active") and not bool(controlled_actor.call("is_combat_active")):
			continue
		var modifier: int = int(controlled_actor.call("get_initiative_modifier")) if controlled_actor.has_method("get_initiative_modifier") else 0
		var proficiency: int = int(controlled_actor.call("get_initiative_proficiency_bonus")) if controlled_actor.has_method("get_initiative_proficiency_bonus") else 0
		entries.append(_make_entry(
			controlled_actor,
			true,
			modifier,
			maxi(proficiency, 0),
			initiative_overrides,
			false
		))
	_pending_player_controlled_actors.clear()
	for opponent: Node in opponents:
		if not is_instance_valid(opponent) or _find_entry_index(opponent) >= 0:
			continue
		var modifier: int = int(opponent.call("get_initiative_modifier")) if opponent.has_method("get_initiative_modifier") else 0
		var proficiency: int = int(opponent.call("get_initiative_proficiency_bonus")) if opponent.has_method("get_initiative_proficiency_bonus") else 0
		entries.append(_make_entry(opponent, false, modifier, maxi(proficiency, 0), initiative_overrides, false))
	entries.sort_custom(_sort_entries)
	current_index = _first_active_index()
	_begin_current_turn()


func stop_combat() -> void:
	active = false
	round_number = 0
	current_index = -1
	entries.clear()
	_pending_player_controlled_actors.clear()
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


func current_turn_token() -> String:
	var actor: Node = current_actor()
	if not active or not is_instance_valid(actor):
		return ""
	return "%d:%d:%d" % [round_number, current_index, actor.get_instance_id()]


func is_player_turn(player: Node) -> bool:
	return active and current_actor() == player


func is_actor_turn(actor: Node) -> bool:
	return active and is_instance_valid(actor) and current_actor() == actor


func is_player_controlled_turn() -> bool:
	return active and bool(current_entry().get("is_player", false))


func is_player_controlled_actor(actor: Node) -> bool:
	var entry_index: int = _find_entry_index(actor)
	return entry_index >= 0 and bool(entries[entry_index].get("is_player", false))


func is_primary_player_actor(actor: Node) -> bool:
	var entry_index: int = _find_entry_index(actor)
	return entry_index >= 0 and bool(entries[entry_index].get("is_primary_player", false))


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


func set_player_movement(feet: int) -> void:
	movement_remaining_feet = maxi(feet, 0)


func use_dash(feet: int = BASE_MOVEMENT_FEET) -> bool:
	if not consume_action():
		return false
	add_movement(feet)
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


func get_initiative_roll(actor: Node) -> int:
	var entry_index: int = _find_entry_index(actor)
	return int(entries[entry_index].get("initiative_roll", 0)) if entry_index >= 0 else 0


func swap_initiative(actor: Node, ally: Node, actor_willing: bool = true, ally_willing: bool = true) -> bool:
	if not active or actor == ally or not actor_willing or not ally_willing:
		return false
	var actor_index: int = _find_entry_index(actor)
	var ally_index: int = _find_entry_index(ally)
	if actor_index < 0 or ally_index < 0:
		return false
	if not _entry_is_active(entries[actor_index]) or not _entry_is_active(entries[ally_index]):
		return false
	if _actor_is_incapacitated(actor) or _actor_is_incapacitated(ally):
		return false
	var current: Node = current_actor()
	var actor_initiative: int = int(entries[actor_index].get("initiative", 0))
	entries[actor_index]["initiative"] = int(entries[ally_index].get("initiative", 0))
	entries[ally_index]["initiative"] = actor_initiative
	entries[actor_index]["initiative_swapped"] = true
	entries[ally_index]["initiative_swapped"] = true
	entries.sort_custom(_sort_entries)
	current_index = _find_entry_index(current)
	return true


func force_current_actor_for_testing(actor: Node) -> void:
	var entry_index: int = _find_entry_index(actor)
	if entry_index >= 0:
		current_index = entry_index
		_begin_current_turn()


func _make_entry(
	actor: Node,
	is_player: bool,
	dexterity_modifier: int,
	initiative_proficiency_bonus: int,
	overrides: Dictionary,
	is_primary_player: bool = false
) -> Dictionary:
	var instance_id: int = actor.get_instance_id()
	var initiative_roll: int = clampi(int(overrides.get(instance_id, _rng.randi_range(1, INITIATIVE_DIE_SIDES))), 1, INITIATIVE_DIE_SIDES)
	var display_name: String = "Герой"
	if actor.has_method("get_combat_name"):
		display_name = str(actor.call("get_combat_name"))
	elif not is_primary_player:
		display_name = actor.name
	return {
		"node": actor,
		"name": display_name,
		"is_player": is_player,
		"is_primary_player": is_primary_player,
		"dexterity_modifier": dexterity_modifier,
		"initiative_proficiency_bonus": initiative_proficiency_bonus,
		"initiative_roll": initiative_roll,
		"initiative": initiative_roll + dexterity_modifier + initiative_proficiency_bonus,
		"reaction": true,
		"initiative_swapped": false
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
	var actor: Node = entries[current_index].get("node") as Node
	if is_instance_valid(actor) and actor.has_method("on_combat_turn_started"):
		actor.call("on_combat_turn_started")
	var player_controlled_turn: bool = bool(entries[current_index].get("is_player", false))
	if player_controlled_turn:
		action_available = true
		bonus_action_available = true
		reaction_available = true
		movement_remaining_feet = int(actor.call("get_combat_speed_feet")) if is_instance_valid(actor) and actor.has_method("get_combat_speed_feet") else BASE_MOVEMENT_FEET
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


func _actor_is_incapacitated(actor: Node) -> bool:
	if actor == null:
		return true
	if actor.has_method("is_incapacitated"):
		return bool(actor.call("is_incapacitated"))
	if actor.has_method("can_take_combat_turn"):
		return not bool(actor.call("can_take_combat_turn"))
	return false


func _find_entry_index(actor: Node) -> int:
	for index: int in range(entries.size()):
		if entries[index].get("node") == actor:
			return index
	return -1
