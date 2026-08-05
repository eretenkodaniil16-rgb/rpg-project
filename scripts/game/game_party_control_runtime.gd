extends "res://scripts/game/game_guard_post_polish_runtime.gd"

const REPLACED_CATALOG_METHODS: Array[StringName] = [
	&"_on_catalog_action_requested",
	&"_on_feedback_catalog_action_requested",
	&"_on_party_catalog_action_requested"
]

var _last_party_action_id: String = ""
var _last_party_action_result: Dictionary = {}
var _last_test_placement: Dictionary = {}


func _ready() -> void:
	super._ready()
	call_deferred("_bind_party_action_catalog")


func _bind_party_action_catalog() -> void:
	if _action_catalog_ui == null:
		return
	var signal_name: StringName = &"action_requested"
	var owned_connections: Array[Callable] = []
	for connection_value: Variant in _action_catalog_ui.get_signal_connection_list(signal_name):
		if not connection_value is Dictionary:
			continue
		var callable_value: Variant = (connection_value as Dictionary).get("callable")
		if not callable_value is Callable:
			continue
		var existing: Callable = callable_value as Callable
		if existing.get_object() == self and existing.get_method() in REPLACED_CATALOG_METHODS:
			owned_connections.append(existing)
	for existing: Callable in owned_connections:
		if _action_catalog_ui.is_connected(signal_name, existing):
			_action_catalog_ui.disconnect(signal_name, existing)
	var party_handler := Callable(self, "_on_party_catalog_action_requested")
	_action_catalog_ui.connect(signal_name, party_handler)


func _on_party_catalog_action_requested(action_id: String) -> void:
	_last_party_action_id = action_id
	_last_party_action_result = {}
	if not _is_controllable_ally_turn():
		# Forward exactly once through the inherited feedback chain. Calling the
		# virtual method on self from this leaf can re-enter the party dispatcher
		# when signal bindings are rebuilt and can execute hero actions twice.
		super._on_feedback_catalog_action_requested(action_id)
		return
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
			var selected_before: Node = _selected_target
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
			_last_party_action_result = _request_controllable_ally_attack()
			_last_party_action_result["ally_position"] = [ally_position_before.x, ally_position_before.y]
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
