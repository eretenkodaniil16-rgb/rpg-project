class_name GuardPostPartyVisibility
extends "res://scripts/game/guard_post_two_room_visibility.gd"

const PARTY_ROOM_FOG_SCRIPT: Script = preload("res://scripts/game/party_room_fog_overlay.gd")


func _install_room_fog() -> void:
	var player: Node2D = get_tree().get_first_node_in_group("player") as Node2D
	if player == null:
		return
	_room_fog = PARTY_ROOM_FOG_SCRIPT.new() as PartyRoomFogOverlay
	_room_fog.name = "RoomFogOverlay"
	add_child(_room_fog)
	_room_fog.configure(player, ROOM_RECTS, ROOM_ORDER)
