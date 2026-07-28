extends "res://scripts/game/game_fighter_subclasses_runtime.gd"

var _active_combat_encounter_id: String = ""


func _start_turn_based_combat(trigger_target: Node) -> void:
	var encounter_id: String = _encounter_id_for_actor(trigger_target)
	if not encounter_id.is_empty() and GameState.has_method("begin_encounter"):
		var begin_result: Dictionary = GameState.call(
			"begin_encounter",
			encounter_id,
			{
				"source_type": "combat",
				"source_id": _target_name(trigger_target),
				"trigger_actor_id": trigger_target.get_instance_id()
			},
			true,
			true
		) as Dictionary
		if bool(begin_result.get("success", false)) or bool(begin_result.get("duplicate", false)):
			_active_combat_encounter_id = encounter_id
	super._start_turn_based_combat(trigger_target)


func _stop_turn_based_combat(message: String) -> void:
	_resolve_active_combat_encounter_if_complete()
	_active_combat_encounter_id = ""
	super._stop_turn_based_combat(message)


func handle_player_defeat(source: Node = null) -> void:
	if not _active_combat_encounter_id.is_empty() and GameState.has_method("fail_encounter"):
		GameState.call(
			"fail_encounter",
			_active_combat_encounter_id,
			"player_defeated",
			{
				"source_type": "combat",
				"source_name": _target_name(source) if source != null else "unknown"
			},
			true,
			true
		)
	_active_combat_encounter_id = ""
	await super.handle_player_defeat(source)


func get_active_combat_encounter_id_for_testing() -> String:
	return _active_combat_encounter_id


func _resolve_active_combat_encounter_if_complete() -> void:
	if _active_combat_encounter_id.is_empty() or not GameState.has_method("get_encounter_status"):
		return
	var status: String = str(GameState.call("get_encounter_status", _active_combat_encounter_id))
	if status in [EncounterSystem.STATUS_RESOLVED, EncounterSystem.STATUS_REWARDED]:
		return
	if not _combat_should_end():
		return
	var resolution_id: String = ""
	if GameState.has_method("get_encounter_combat_resolution_id"):
		resolution_id = str(GameState.call("get_encounter_combat_resolution_id", _active_combat_encounter_id))
	if resolution_id.is_empty() or not GameState.has_method("resolve_encounter"):
		return
	GameState.call(
		"resolve_encounter",
		_active_combat_encounter_id,
		resolution_id,
		{
			"source_type": "combat",
			"source_id": "combat_runtime",
			"combat_round": _turn_system.round_number
		},
		true,
		true
	)


func _encounter_id_for_actor(actor: Node) -> String:
	if actor == null or not is_instance_valid(actor):
		return ""
	if actor.has_method("get_encounter_id"):
		return str(actor.call("get_encounter_id"))
	return ""
