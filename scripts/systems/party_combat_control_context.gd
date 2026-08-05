class_name PartyCombatControlContext
extends RefCounted

var _active_actor: Node = null
var _targets_by_actor_id: Dictionary = {}


func begin_turn(actor: Node) -> void:
	_active_actor = actor if is_instance_valid(actor) else null


func clear() -> void:
	_active_actor = null
	_targets_by_actor_id.clear()


func active_actor() -> Node:
	return _active_actor if is_instance_valid(_active_actor) else null


func owns_input(actor: Node) -> bool:
	return is_instance_valid(actor) and active_actor() == actor


func set_target(actor: Node, target: Node) -> void:
	if not is_instance_valid(actor):
		return
	var actor_id: int = actor.get_instance_id()
	if is_instance_valid(target):
		_targets_by_actor_id[actor_id] = target
	else:
		_targets_by_actor_id.erase(actor_id)


func target_for(actor: Node) -> Node:
	if not is_instance_valid(actor):
		return null
	var actor_id: int = actor.get_instance_id()
	var target: Node = _targets_by_actor_id.get(actor_id) as Node
	if not is_instance_valid(target):
		_targets_by_actor_id.erase(actor_id)
		return null
	return target


func clear_target(actor: Node) -> void:
	if is_instance_valid(actor):
		_targets_by_actor_id.erase(actor.get_instance_id())


func get_target_instance_id_for_testing(actor: Node) -> int:
	var target: Node = target_for(actor)
	return target.get_instance_id() if is_instance_valid(target) else 0
