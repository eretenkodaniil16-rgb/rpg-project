class_name GuardPostPartyVisibility
extends "res://scripts/game/guard_post_two_room_visibility.gd"

const PARTY_ROOM_FOG_SCRIPT: Script = preload("res://scripts/game/party_room_fog_overlay.gd")
const PARTY_FOLLOW_PORTAL_GROUP: StringName = &"party_follow_portals"
const INNER_GATE_APPROACH_OFFSET_PIXELS: float = 56.0
const INNER_PARTITION_SIDE_EPSILON_PIXELS: float = 2.0


func _install_room_fog() -> void:
	var player: Node2D = get_tree().get_first_node_in_group("player") as Node2D
	if player == null:
		return
	_room_fog = PARTY_ROOM_FOG_SCRIPT.new() as PartyRoomFogOverlay
	_room_fog.name = "RoomFogOverlay"
	add_child(_room_fog)
	_room_fog.configure(player, ROOM_RECTS, ROOM_ORDER)
	add_to_group(PARTY_FOLLOW_PORTAL_GROUP)


func is_inner_gate_open() -> bool:
	var gate: StealthDoor = get_inner_gate()
	return gate != null and gate.get_door_state() in ["open", "broken"]


func resolve_party_follow_portal_route(from_global: Vector2, to_global: Vector2) -> Dictionary:
	var divider_x: float = get_inner_partition_global_x()
	var source_is_left: bool = from_global.x < divider_x - INNER_PARTITION_SIDE_EPSILON_PIXELS
	var source_is_right: bool = from_global.x > divider_x + INNER_PARTITION_SIDE_EPSILON_PIXELS
	var target_is_left: bool = to_global.x < divider_x - INNER_PARTITION_SIDE_EPSILON_PIXELS
	var target_is_right: bool = to_global.x > divider_x + INNER_PARTITION_SIDE_EPSILON_PIXELS
	var crosses_partition: bool = (
		(source_is_left and target_is_right)
		or (source_is_right and target_is_left)
	)
	if not crosses_partition:
		return {
			"applies": false,
			"reachable": true,
			"waypoints": PackedVector2Array()
		}

	var gate: StealthDoor = get_inner_gate()
	if gate == null or not is_inner_gate_open():
		return {
			"applies": true,
			"reachable": false,
			"waypoints": PackedVector2Array(),
			"reason": "inner_gate_closed"
		}

	var gate_center: Vector2 = gate.global_position
	var left_approach := Vector2(
		divider_x - INNER_GATE_APPROACH_OFFSET_PIXELS,
		gate_center.y
	)
	var right_approach := Vector2(
		divider_x + INNER_GATE_APPROACH_OFFSET_PIXELS,
		gate_center.y
	)
	var waypoints := PackedVector2Array()
	if source_is_left:
		waypoints.append(left_approach)
		waypoints.append(right_approach)
	else:
		waypoints.append(right_approach)
		waypoints.append(left_approach)
	return {
		"applies": true,
		"reachable": true,
		"waypoints": waypoints,
		"reason": "inner_gate_open"
	}
