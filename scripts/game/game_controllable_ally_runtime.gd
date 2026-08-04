extends "res://scripts/game/game_item_use_runtime.gd"

const CONTROLLABLE_ALLY_SCENE: PackedScene = preload("res://scenes/game/controllable_ally.tscn")

var _controllable_ally: Node = null


func _ready() -> void:
	super._ready()
	_ensure_controllable_ally()


func _ensure_controllable_ally() -> void:
	var existing: Node = get_tree().get_first_node_in_group("controllable_allies")
	if is_instance_valid(existing):
		_controllable_ally = existing
		return
	_controllable_ally = CONTROLLABLE_ALLY_SCENE.instantiate()
	if _controllable_ally == null:
		push_error("Не удалось создать управляемого союзника.")
		return
	_controllable_ally.name = "ControllableAllyIrna"
	add_child(_controllable_ally)
	if _controllable_ally is Node2D:
		var spawn_position: Vector2 = player.global_position + Vector2(-72.0, 0.0) if is_instance_valid(player) else Vector2(360.0, 440.0)
		(_controllable_ally as Node2D).global_position = spawn_position


func _start_turn_based_combat(trigger_target: Node) -> void:
	if is_instance_valid(_controllable_ally) and _controllable_ally.has_method("is_combat_active") and bool(_controllable_ally.call("is_combat_active")):
		_turn_system.set_pending_player_controlled_actors([_controllable_ally])
	else:
		_turn_system.clear_pending_player_controlled_actors()
	super._start_turn_based_combat(trigger_target)
	_turn_system.clear_pending_player_controlled_actors()
	if _turn_system.active and is_instance_valid(_controllable_ally) and _controllable_ally.has_method("set_turn_based_mode"):
		_controllable_ally.call("set_turn_based_mode", true)


func _stop_turn_based_combat(message: String) -> void:
	super._stop_turn_based_combat(message)
	if is_instance_valid(_controllable_ally) and _controllable_ally.has_method("set_turn_based_mode"):
		_controllable_ally.call("set_turn_based_mode", false)


func get_controllable_ally_for_testing() -> Node:
	return _controllable_ally
