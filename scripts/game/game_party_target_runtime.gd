extends "res://scripts/game/game_party_exploration_runtime.gd"

const TARGET_HANDLER_METHODS: Array[StringName] = [
	&"_on_feedback_target_requested",
	&"_on_party_target_requested",
	&"_on_active_party_target_requested"
]

var _last_target_request_diagnostics: Dictionary = {}


func _ready() -> void:
	super._ready()
	call_deferred("_bind_active_party_target_button")


func _bind_active_party_target_button() -> void:
	if _target_button == null:
		return
	var signal_name: StringName = &"pressed"
	var stale_handlers: Array[Callable] = []
	for connection_value: Variant in _target_button.get_signal_connection_list(signal_name):
		if not connection_value is Dictionary:
			continue
		var callable_value: Variant = (connection_value as Dictionary).get("callable")
		if not callable_value is Callable:
			continue
		var existing: Callable = callable_value as Callable
		if existing.get_object() == self and existing.get_method() in TARGET_HANDLER_METHODS:
			stale_handlers.append(existing)
	for existing: Callable in stale_handlers:
		if _target_button.is_connected(signal_name, existing):
			_target_button.disconnect(signal_name, existing)
	var handler := Callable(self, "_on_active_party_target_requested")
	if not _target_button.is_connected(signal_name, handler):
		_target_button.connect(signal_name, handler)


func _on_active_party_target_requested() -> void:
	_close_action_catalog_immediately()
	var current_actor: Node = _turn_system.current_actor() if _turn_system.active else null
	_last_target_request_diagnostics = {
		"handler_called": true,
		"handlers": get_target_button_handlers_for_testing(),
		"controllable_ally_turn": _is_controllable_ally_turn(),
		"input_locked": GameState.input_locked,
		"attack_in_progress": _attack_in_progress,
		"overlay_visible": _any_overlay_visible(),
		"button_disabled": _target_button.disabled if _target_button != null else true,
		"current_actor_id": current_actor.get_instance_id() if is_instance_valid(current_actor) else 0,
		"ally_id": _controllable_ally.get_instance_id() if is_instance_valid(_controllable_ally) else 0,
		"candidates": _target_candidate_diagnostics()
	}
	if not _is_controllable_ally_turn():
		super._on_party_target_requested()
		return
	if GameState.input_locked or _attack_in_progress or _any_overlay_visible():
		_last_target_request_diagnostics["status"] = "blocked"
		return
	_cycle_full_irina_target()
	_last_target_request_diagnostics["status"] = "resolved"
	_last_target_request_diagnostics["selected_target_id"] = get_party_target_instance_id_for_testing(_controllable_ally)
	_refresh_party_menu()


func _target_candidate_diagnostics() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for candidate_value: Variant in get_tree().get_nodes_in_group("combat_targets"):
		if not candidate_value is Node:
			continue
		var candidate: Node = candidate_value as Node
		result.append({
			"name": candidate.name,
			"id": candidate.get_instance_id(),
			"active": candidate.has_method("is_combat_active") and bool(candidate.call("is_combat_active")),
			"valid_for_irina": _full_irina_target_is_valid(candidate)
		})
	return result


func _cycle_full_irina_target() -> void:
	var targets: Array[Node] = []
	for candidate_value: Variant in get_tree().get_nodes_in_group("combat_targets"):
		if candidate_value is Node and _full_irina_target_is_valid(candidate_value as Node):
			targets.append(candidate_value as Node)
	if targets.is_empty():
		_party_control_context.clear_target(_controllable_ally)
		_set_selected_target(null)
		_update_target_label()
		show_combat_message("Для Ирины нет доступных вражеских целей.", false)
		return

	var current: Node = _party_control_context.target_for(_controllable_ally)
	var current_index: int = targets.find(current)
	var next_target: Node = (
		targets[0]
		if current_index < 0 or current_index + 1 >= targets.size()
		else targets[current_index + 1]
	)
	_party_control_context.set_target(_controllable_ally, next_target)
	_set_selected_target(next_target)
	_update_target_label()
	show_combat_message("Ирина выбирает цель: %s." % _target_name(next_target), true)


func _full_irina_target_is_valid(target: Node) -> bool:
	if (
		not is_instance_valid(target)
		or not target is Node2D
		or not target.is_in_group("combat_targets")
		or not target.has_method("is_combat_active")
		or not bool(target.call("is_combat_active"))
		or not _controllable_ally is Node2D
	):
		return false
	if _combat_environment != null:
		var cover: Dictionary = _combat_environment.get_cover(
			(_controllable_ally as Node2D).global_position,
			(target as Node2D).global_position
		)
		if bool(cover.get("total_cover", false)):
			return false
	return true


func get_target_button_handlers_for_testing() -> Array[String]:
	var result: Array[String] = []
	if _target_button == null:
		return result
	for connection_value: Variant in _target_button.get_signal_connection_list(&"pressed"):
		if not connection_value is Dictionary:
			continue
		var callable_value: Variant = (connection_value as Dictionary).get("callable")
		if callable_value is Callable:
			result.append(str((callable_value as Callable).get_method()))
	return result


func get_last_target_request_diagnostics_for_testing() -> Dictionary:
	return _last_target_request_diagnostics.duplicate(true)
