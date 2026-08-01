class_name WorldSnapshotReadinessGuard
extends Node

var _controller: WorldStateNpcNavigationController


func _ready() -> void:
	_controller = get_parent().get_node_or_null("WorldStateNpcNavigationController") as WorldStateNpcNavigationController
	add_to_group("world_state_serializers")


func can_capture_stable_world_state() -> bool:
	var snapshot: Dictionary = GameState.call("get_world_snapshot") as Dictionary if GameState.has_method("get_world_snapshot") else {}
	var entities_value: Variant = snapshot.get("entities", {})
	var loaded_world_exists: bool = int(snapshot.get("captured_at_unix", 0)) > 0 or (entities_value is Dictionary and not (entities_value as Dictionary).is_empty())
	if not loaded_world_exists:
		return true
	if not is_instance_valid(_controller):
		_controller = get_parent().get_node_or_null("WorldStateNpcNavigationController") as WorldStateNpcNavigationController
	return is_instance_valid(_controller) and bool(_controller.get("_restored")) and not bool(_controller.get("_restore_running"))
