class_name GuardPostTwoRoomVisibility
extends "res://scripts/game/guard_post_two_room.gd"

const ROOM_FOG_SCRIPT: Script = preload("res://scripts/game/room_fog_overlay.gd")
const DOOR_DECORATOR_SCRIPT: Script = preload("res://scripts/game/stealth_door_visual_decorator.gd")

const ROOM_WEST_SERVICE: String = "west_service_room"
const ROOM_OUTER_GUARD: String = "outer_guard_room"
const ROOM_INNER_WATCH: String = "inner_watch_room"
const ROOM_ORDER: Array[String] = [ROOM_WEST_SERVICE, ROOM_OUTER_GUARD, ROOM_INNER_WATCH]
const ROOM_RECTS: Dictionary = {
	ROOM_WEST_SERVICE: Rect2(Vector2(-200.0, -315.0), Vector2(192.0, 630.0)),
	ROOM_OUTER_GUARD: Rect2(Vector2(PARTITION_LOCAL_X, -315.0), Vector2(INNER_PARTITION_LOCAL_X - PARTITION_LOCAL_X, 630.0)),
	ROOM_INNER_WATCH: Rect2(Vector2(INNER_PARTITION_LOCAL_X, -315.0), Vector2(358.0, 630.0))
}

var _room_fog: RoomFogOverlay


func _ready() -> void:
	super._ready()
	_install_door_decorator(get_test_door(), "WestServiceDoorPresentation")
	_install_door_decorator(get_inner_gate(), "InnerWatchGatePresentation")
	_install_room_fog()


func get_room_fog_for_testing() -> RoomFogOverlay:
	return _room_fog


func get_door_decorator_for_testing(door: StealthDoor) -> StealthDoorVisualDecorator:
	if door == null:
		return null
	for child: Node in door.get_children():
		if child is StealthDoorVisualDecorator:
			return child as StealthDoorVisualDecorator
	return null


func _install_room_fog() -> void:
	var player: Node2D = get_tree().get_first_node_in_group("player") as Node2D
	if player == null:
		return
	_room_fog = ROOM_FOG_SCRIPT.new() as RoomFogOverlay
	_room_fog.name = "RoomFogOverlay"
	add_child(_room_fog)
	_room_fog.configure(player, ROOM_RECTS, ROOM_ORDER)


func _install_door_decorator(door: StealthDoor, node_name: String) -> void:
	if door == null or door.get_node_or_null(node_name) != null:
		return
	var decorator := DOOR_DECORATOR_SCRIPT.new() as StealthDoorVisualDecorator
	decorator.name = node_name
	door.add_child(decorator)
	decorator.configure(door)
