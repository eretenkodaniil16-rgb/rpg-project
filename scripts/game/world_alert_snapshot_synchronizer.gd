class_name WorldAlertSnapshotSynchronizer
extends Node

var _game: Node


func _ready() -> void:
	_game = get_parent()
	add_to_group("world_state_serializers")


func prepare_world_state_for_save() -> void:
	if not is_instance_valid(_game):
		_game = get_parent()
	var state: Node = get_tree().root.get_node_or_null("GameState")
	var player: Node2D = get_tree().get_first_node_in_group("player") as Node2D
	if state != null and player != null:
		state.set("player_position", player.global_position)
	if is_instance_valid(_game) and _game.has_method("_persist_all_alert_records"):
		_game.call("_persist_all_alert_records", false)
