class_name WorldAlertSnapshotSynchronizer
extends Node

var _game: Node


func _ready() -> void:
	_game = get_parent()
	add_to_group("world_state_serializers")


func capture_world_state_for_save() -> Dictionary:
	if not is_instance_valid(_game):
		_game = get_parent()
	if is_instance_valid(_game) and _game.has_method("_persist_all_alert_records"):
		_game.call("_persist_all_alert_records", false)
	return {}
