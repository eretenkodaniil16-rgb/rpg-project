extends "res://scripts/game/game_squad_tactical_plans_runtime.gd"

const WORLD_INTERACTION_ACTION_ID: String = "world_interact"

var _used_world_interaction_turn_token: String = ""


func _available_targets() -> Array[Node]:
	var result: Array[Node] = []
	for target: Node in get_tree().get_nodes_in_group("combat_targets"):
		if _is_player_targetable(target):
			result.append(target)
	return result


func _target_is_valid(target: Node) -> bool:
	return _is_player_targetable(target)


func _is_player_targetable(target: Node) -> bool:
	if not is_instance_valid(target) or not target is Node2D:
		return false
	if target.has_method("is_player_targetable"):
		return bool(target.call("is_player_targetable"))
	return target.has_method("is_combat_active") and bool(target.call("is_combat_active"))


func _build_catalog_entries() -> Dictionary:
	var entries: Dictionary = super._build_catalog_entries()
	if not _turn_system.active:
		return entries
	var action_value: Variant = entries.get("action", [])
	var action_entries: Array = action_value as Array if action_value is Array else []
	var interactable: Node = _current_combat_world_interactable()
	var player_turn: bool = _turn_system.is_player_turn(player) and not _enemy_turn_running
	var interaction_available: bool = player_turn and _world_interaction_available()
	var label: String = "НЕТ ОБЪЕКТА РЯДОМ"
	var description: String = "Подойдите к двери или другому доступному объекту мира."
	if interactable != null:
		label = str(interactable.call("get_combat_interaction_label")) if interactable.has_method("get_combat_interaction_label") else "ВЗАИМОДЕЙСТВОВАТЬ"
		description = str(interactable.call("get_combat_interaction_description")) if interactable.has_method("get_combat_interaction_description") else "Взаимодействовать с соседним объектом один раз за ход."
		if interactable.has_method("can_perform_world_interaction"):
			interaction_available = interaction_available and bool(interactable.call("can_perform_world_interaction"))
	action_entries.append(_entry(
		WORLD_INTERACTION_ACTION_ID,
		label,
		interaction_available and interactable != null,
		description,
		"world"
	))
	entries["action"] = action_entries
	return entries


func _on_catalog_action_requested(action_id: String) -> void:
	if action_id == WORLD_INTERACTION_ACTION_ID:
		request_world_interaction(_current_combat_world_interactable())
		_invalidate_reachable_area()
		_refresh_action_catalog()
		return
	super._on_catalog_action_requested(action_id)


func request_world_interaction(target: Node) -> bool:
	if not _turn_system.active:
		return false
	if target == null or not target.has_method("perform_world_interaction"):
		show_combat_message("Рядом нет объекта, с которым можно взаимодействовать в бою.", false)
		return true
	if not _turn_system.is_player_turn(player) or _enemy_turn_running:
		show_combat_message("Взаимодействовать с объектом можно только на своём ходу.", false)
		return true
	if target != _current_combat_world_interactable():
		show_combat_message("Объект находится вне зоны взаимодействия.", false)
		return true
	if target.has_method("can_perform_world_interaction") and not bool(target.call("can_perform_world_interaction")):
		var blocked_description: String = str(target.call("get_combat_interaction_description")) if target.has_method("get_combat_interaction_description") else "Объект сейчас недоступен."
		show_combat_message(blocked_description, false)
		return true
	if not _world_interaction_available():
		show_combat_message("Взаимодействие с объектом на этом ходу уже использовано.", false)
		return true
	_used_world_interaction_turn_token = _turn_system.current_turn_token()
	target.call("perform_world_interaction")
	_clear_movement_plan()
	_invalidate_reachable_area()
	_refresh_action_catalog()
	return true


func _current_combat_world_interactable() -> Node:
	if not is_instance_valid(player):
		return null
	var value: Variant = player.get("interactable")
	if not value is Node:
		return null
	var target: Node = value as Node
	if not is_instance_valid(target) or not target.has_method("perform_world_interaction"):
		return null
	return target


func _world_interaction_available() -> bool:
	if not _turn_system.active or not _turn_system.is_player_turn(player) or _enemy_turn_running:
		return false
	var token: String = _turn_system.current_turn_token()
	return not token.is_empty() and token != _used_world_interaction_turn_token


func is_world_interaction_available_for_testing() -> bool:
	return _world_interaction_available()


func _stop_turn_based_combat(message: String) -> void:
	_used_world_interaction_turn_token = ""
	super._stop_turn_based_combat(message)
