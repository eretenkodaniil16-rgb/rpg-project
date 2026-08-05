extends "res://scripts/game/game_guard_post_polish_runtime.gd"

const LEGACY_CATALOG_METHOD: StringName = &"_on_catalog_action_requested"
const FEEDBACK_CATALOG_METHOD: StringName = &"_on_feedback_catalog_action_requested"
const PARTY_CATALOG_METHOD: StringName = &"_on_party_catalog_action_requested"

var _last_party_action_id: String = ""
var _last_party_action_result: Dictionary = {}
var _last_test_placement: Dictionary = {}
var _last_catalog_context_diagnostics: Dictionary = {}


func _ready() -> void:
	super._ready()
	call_deferred("_bind_party_action_catalog")


func _bind_party_action_catalog() -> void:
	if _action_catalog_ui == null:
		return
	var signal_name: StringName = &"action_requested"
	var stale_connections: Array[Callable] = []
	for connection_value: Variant in _action_catalog_ui.get_signal_connection_list(signal_name):
		if not connection_value is Dictionary:
			continue
		var callable_value: Variant = (connection_value as Dictionary).get("callable")
		if not callable_value is Callable:
			continue
		var existing: Callable = callable_value as Callable
		if existing.get_object() != self:
			continue
		if existing.get_method() in [LEGACY_CATALOG_METHOD, PARTY_CATALOG_METHOD]:
			stale_connections.append(existing)
	for existing: Callable in stale_connections:
		if _action_catalog_ui.is_connected(signal_name, existing):
			_action_catalog_ui.disconnect(signal_name, existing)

	# Keep the original feedback pipeline for the main hero. It contains the full
	# inherited action chain, including combat dialogue, item use, Hide and world
	# interactions. The party handler is a second, actor-gated route used only on
	# Irna's initiative turn. Exactly one route is active for any catalogue event.
	var feedback_handler := Callable(self, FEEDBACK_CATALOG_METHOD)
	if not _action_catalog_ui.is_connected(signal_name, feedback_handler):
		_action_catalog_ui.connect(signal_name, feedback_handler)
	var party_handler := Callable(self, PARTY_CATALOG_METHOD)
	_action_catalog_ui.connect(signal_name, party_handler)


func _on_feedback_catalog_action_requested(action_id: String) -> void:
	if _is_controllable_ally_turn():
		return
	if _turn_system.active and not _turn_system.is_actor_turn(player):
		return
	super._on_feedback_catalog_action_requested(action_id)


func _remember_target_for_active_actor() -> void:
	# `_selected_target` is a shared presentation pointer. It can be cleared
	# transiently while an overlay is rebuilt, so a null value must not erase the
	# authoritative per-actor target. Explicit deselection paths clear the context
	# themselves.
	var actor: Node = _party_control_context.active_actor()
	if is_instance_valid(actor) and _target_is_valid(_selected_target):
		_party_control_context.set_target(actor, _selected_target)


func _sync_selected_target_from_party_context() -> Node:
	var actor: Node = _party_control_context.active_actor()
	if not is_instance_valid(actor):
		return null
	var target: Node = _party_control_context.target_for(actor)
	if not _target_is_valid(target):
		return null
	if _selected_target != target:
		_set_selected_target(target)
	return target


func _refresh_action_catalog() -> void:
	if _turn_system.active and _turn_system.is_player_controlled_turn():
		_sync_selected_target_from_party_context()
	super._refresh_action_catalog()


func _build_catalog_entries() -> Dictionary:
	# Capture the actor-specific target before the inherited catalogue builder runs.
	# Several older layers still use the shared `_selected_target` presentation
	# pointer and may clear it while rebuilding categories. That transient UI state
	# must not disable Irna's action or erase her authoritative target context.
	var ally_turn_before_super: bool = _is_controllable_ally_turn()
	var context_target_before_super: Node = (
		_party_control_context.target_for(_controllable_ally)
		if ally_turn_before_super
		else null
	)
	var context_target_valid_before_super: bool = _target_is_valid(context_target_before_super)
	var selected_before_super: Node = _selected_target
	var distance_before_super: int = -1
	if (
		context_target_valid_before_super
		and _controllable_ally is Node2D
		and context_target_before_super is Node2D
	):
		distance_before_super = DistanceSystem.distance_feet(
			(_controllable_ally as Node2D).global_position,
			(context_target_before_super as Node2D).global_position
		)

	var entries: Dictionary = super._build_catalog_entries()
	if not ally_turn_before_super:
		return entries

	if context_target_valid_before_super:
		_party_control_context.set_target(_controllable_ally, context_target_before_super)
		if _selected_target != context_target_before_super:
			_set_selected_target(context_target_before_super)

	var state: CombatantState = _active_party_state()
	var can_act: bool = (
		state != null
		and _turn_system.action_available
		and _srd_rules.can_take_action(state)
	)
	var target_melee: bool = (
		context_target_valid_before_super
		and distance_before_super >= 0
		and distance_before_super <= DistanceSystem.MELEE_REACH_FEET
	)
	_last_catalog_context_diagnostics = {
		"active_actor_id": (
			_party_control_context.active_actor().get_instance_id()
			if is_instance_valid(_party_control_context.active_actor())
			else 0
		),
		"ally_id": _controllable_ally.get_instance_id() if is_instance_valid(_controllable_ally) else 0,
		"context_target_id_before_super": (
			context_target_before_super.get_instance_id()
			if is_instance_valid(context_target_before_super)
			else 0
		),
		"context_target_valid_before_super": context_target_valid_before_super,
		"selected_target_id_before_super": (
			selected_before_super.get_instance_id()
			if is_instance_valid(selected_before_super)
			else 0
		),
		"selected_target_id_after_super": (
			_selected_target.get_instance_id()
			if is_instance_valid(_selected_target)
			else 0
		),
		"distance_feet": distance_before_super,
		"can_act": can_act,
		"target_melee": target_melee
	}

	var action_values: Variant = entries.get("action", [])
	var action_entries: Array = action_values as Array if action_values is Array else []
	for index: int in range(action_entries.size()):
		var entry_value: Variant = action_entries[index]
		if not entry_value is Dictionary:
			continue
		var entry: Dictionary = (entry_value as Dictionary).duplicate(true)
		match str(entry.get("id", "")):
			"attack":
				entry["enabled"] = can_act and target_melee
			"select_ally_target":
				entry["label"] = (
					"СМЕНИТЬ ЦЕЛЬ ИРИНЫ"
					if context_target_valid_before_super
					else "ВЫБРАТЬ ЦЕЛЬ ИРИНЫ"
				)
			_:
				pass
		action_entries[index] = entry
	entries["action"] = action_entries
	return entries


func _on_party_catalog_action_requested(action_id: String) -> void:
	if not _is_controllable_ally_turn():
		return
	_last_party_action_id = action_id
	_last_party_action_result = {}
	if action_id.begins_with(ALLY_WORLD_INTERACTION_PREFIX):
		_last_party_action_result = {"success": false, "status": "world_interaction_primary_only"}
		show_combat_message("Взаимодействия с миром выполняет основной герой на своём ходу.", false)
		return
	match action_id:
		"select_ally_target":
			_cycle_ally_target()
			_last_party_action_result = {"success": _target_is_valid(_selected_target), "status": "target_selected"}
		"confirm_move":
			_confirm_planned_movement()
			_last_party_action_result = {"success": true, "status": "movement_requested"}
		"cancel_move":
			_cancel_planned_movement()
			_last_party_action_result = {"success": true, "status": "movement_cancelled"}
		"attack":
			var context_target: Node = _party_control_context.target_for(_controllable_ally)
			if _target_is_valid(context_target):
				_set_selected_target(context_target)
			var selected_before: Node = context_target if _target_is_valid(context_target) else _selected_target
			var ally_position_before: Vector2 = (
				(_controllable_ally as Node2D).global_position
				if _controllable_ally is Node2D
				else Vector2.INF
			)
			var target_position_before: Vector2 = (
				(selected_before as Node2D).global_position
				if selected_before is Node2D
				else Vector2.INF
			)
			_last_party_action_result = _request_controllable_ally_attack(selected_before)
			_last_party_action_result["ally_position"] = [ally_position_before.x, ally_position_before.y]
			_last_party_action_result["context_target_id"] = context_target.get_instance_id() if is_instance_valid(context_target) else 0
			_last_party_action_result["selected_target_id"] = selected_before.get_instance_id() if is_instance_valid(selected_before) else 0
			_last_party_action_result["selected_target_name"] = _target_name(selected_before) if is_instance_valid(selected_before) else ""
			_last_party_action_result["target_position"] = [target_position_before.x, target_position_before.y]
			_last_party_action_result["placement_snapshot"] = _last_test_placement.duplicate(true)
		"dash":
			var dash_action_before: bool = _turn_system.action_available
			_on_dash_requested()
			_last_party_action_result = {
				"success": dash_action_before and not _turn_system.action_available,
				"status": "dash_resolved" if dash_action_before and not _turn_system.action_available else "dash_rejected"
			}
		"disengage":
			var disengage_action_before: bool = _turn_system.action_available
			_on_disengage_requested()
			_last_party_action_result = {
				"success": disengage_action_before and not _turn_system.action_available,
				"status": "disengage_resolved" if disengage_action_before and not _turn_system.action_available else "disengage_rejected"
			}
		"dodge":
			var dodge_action_before: bool = _turn_system.action_available
			_on_dodge_requested()
			_last_party_action_result = {
				"success": dodge_action_before and not _turn_system.action_available,
				"status": "dodge_resolved" if dodge_action_before and not _turn_system.action_available else "dodge_rejected"
			}
		"end_turn":
			_on_end_turn_requested()
			_last_party_action_result = {"success": true, "status": "turn_advanced"}
		_:
			_last_party_action_result = {"success": false, "status": "unsupported_action"}
			show_combat_message("Это действие недоступно Ирине.", false)
	_invalidate_reachable_area()
	_refresh_action_catalog()


func start_party_combat_for_testing(
	opponents: Array[Node],
	initiative_overrides: Dictionary
) -> void:
	# Reproduce the production combat-entry contract while retaining deterministic
	# initiative for the end-to-end party-control test. Starting TurnBasedCombatSystem
	# directly leaves exploration movement enabled on the ally and produces a false
	# out-of-range failure while the Actions catalogue is open.
	if _turn_system.active or not is_instance_valid(player) or not is_instance_valid(_controllable_ally):
		return
	_turn_system.set_pending_player_controlled_actors([_controllable_ally])
	_snap_combatants_to_cells()
	_turn_system.start_combat(player, opponents, 0, initiative_overrides)
	_turn_system.clear_pending_player_controlled_actors()
	if player.has_method("set_turn_based_mode"):
		player.call("set_turn_based_mode", true)
	_call_ally("set_turn_based_mode", [true])
	for opponent: Node in opponents:
		if is_instance_valid(opponent) and opponent.has_method("set_turn_based_mode"):
			opponent.call("set_turn_based_mode", true)
	_begin_current_turn()


func force_controllable_ally_turn_for_testing() -> void:
	# Some focused tests start the domain turn system directly. Preserve the same
	# invariant as production combat: exploration following must be disabled before
	# the ally receives input or opens her Actions catalogue.
	_call_ally("set_turn_based_mode", [true])
	super.force_controllable_ally_turn_for_testing()


func place_controllable_ally_adjacent_for_testing(target: Node) -> bool:
	var placed: bool = super.place_controllable_ally_adjacent_for_testing(target)
	var ally_position: Vector2 = (
		(_controllable_ally as Node2D).global_position
		if _controllable_ally is Node2D
		else Vector2.INF
	)
	var target_position: Vector2 = (
		(target as Node2D).global_position
		if target is Node2D
		else Vector2.INF
	)
	_last_test_placement = {
		"placed": placed,
		"ally_position": [ally_position.x, ally_position.y],
		"target_id": target.get_instance_id() if is_instance_valid(target) else 0,
		"target_name": _target_name(target) if is_instance_valid(target) else "",
		"target_position": [target_position.x, target_position.y],
		"distance_feet": DistanceSystem.distance_feet(ally_position, target_position) if placed else -1
	}
	return placed


func get_catalog_action_handler_methods_for_testing() -> Array[String]:
	var result: Array[String] = []
	if _action_catalog_ui == null:
		return result
	for connection_value: Variant in _action_catalog_ui.get_signal_connection_list(&"action_requested"):
		if not connection_value is Dictionary:
			continue
		var callable_value: Variant = (connection_value as Dictionary).get("callable")
		if callable_value is Callable:
			var callable: Callable = callable_value as Callable
			if callable.get_object() == self:
				result.append(str(callable.get_method()))
	return result


func get_last_party_action_for_testing() -> Dictionary:
	return {
		"action_id": _last_party_action_id,
		"result": _last_party_action_result.duplicate(true)
	}


func get_catalog_context_diagnostics_for_testing() -> Dictionary:
	return _last_catalog_context_diagnostics.duplicate(true)
