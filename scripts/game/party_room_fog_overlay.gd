class_name PartyRoomFogOverlay
extends "res://scripts/game/room_fog_overlay.gd"


func set_vision_source(source: Node2D) -> void:
	if source == null or not is_instance_valid(source) or _player == source:
		return
	_player = source
	_last_player_position = Vector2.INF
	_last_visibility_signature = 0
	_refresh_visibility(true)


func get_vision_source_for_testing() -> Node2D:
	return _player
