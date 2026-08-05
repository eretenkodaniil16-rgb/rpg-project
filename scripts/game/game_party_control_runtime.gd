extends "res://scripts/game/game_guard_post_polish_runtime.gd"

const REPLACED_CATALOG_METHODS: Array[StringName] = [
	&"_on_catalog_action_requested",
	&"_on_feedback_catalog_action_requested",
	&"_on_party_catalog_action_requested"
]

var _last_party_action_id: String = ""
var _last_party_action_result: Dictionary = {}


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
			_last_party_action_result = _request_controllable_ally_attack()
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
