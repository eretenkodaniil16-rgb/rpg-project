class_name WorldSnapshotReadinessGuard
extends Node

var _controller: WorldStateNpcNavigationController


func _ready() -> void:
	_controller = get_parent().get_node_or_null("WorldStateNpcNavigationController") as WorldStateNpcNavigationController
	add_to_group("world_state_serializers")


func can_capture_stable_world_state() -> bool:
	if not is_instance_valid(_controller):
		_controller = get_parent().get_node_or_null("WorldStateNpcNavigationController") as WorldStateNpcNavigationController
	return is_instance_valid(_controller) and bool(_controller.get("_restored")) and not bool(_controller.get("_restore_running"))
