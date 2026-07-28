extends "res://scripts/game/game_hidden_escape_runtime.gd"


func _active_observers() -> Array[Node]:
	var result: Array[Node] = []
	if _turn_system == null:
		return result
	for entry: Dictionary in _turn_system.entries:
		if bool(entry.get("is_player", false)):
			continue
		var actor: Node = entry.get("node") as Node
		if not is_instance_valid(actor) or not (actor is Node2D) or not _target_is_valid(actor):
			continue
		if actor.has_method("can_take_combat_turn") and not bool(actor.call("can_take_combat_turn")):
			continue
		result.append(actor)
	return result
