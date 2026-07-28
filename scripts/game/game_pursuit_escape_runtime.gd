extends "res://scripts/game/game_hidden_escape_runtime.gd"


func _active_observers() -> Array[Node]:
	var result: Array[Node] = []
	if _turn_system == null:
		return result
	for entry: Dictionary in _turn_system.entries:
		if bool(entry.get("is_player", false)):
			continue
		var actor: Node = entry.get("node") as Node
		if not is_instance_valid(actor) or not (actor is Node2D):
			continue
		if actor.has_method("can_take_combat_turn") and not bool(actor.call("can_take_combat_turn")):
			continue
		result.append(actor)
	return result


func _on_hide_requested() -> void:
	await super._on_hide_requested()
	if not _player_combat_state.hidden:
		return
	for observer: Node in _active_observers():
		_set_observer_state(observer, DETECTION_PURSUING, _last_seen_player_position)


func force_active_escape_encounter_for_testing(encounter_id: String) -> void:
	_active_combat_encounter_id = encounter_id
