class_name GuardPostTwoRoomVisibility
extends "res://scripts/game/guard_post_two_room.gd"

const ROOM_FOG_SCRIPT: Script = preload("res://scripts/game/room_fog_overlay.gd")
const DOOR_DECORATOR_SCRIPT: Script = preload("res://scripts/game/stealth_door_visual_decorator.gd")
const WALL_VISIBILITY_OVERLAY_SCRIPT: Script = preload("res://scripts/game/guard_post_wall_visibility_overlay.gd")
const DOOR_REACH_EXPANDER_SCRIPT: Script = preload("res://scripts/game/door_interaction_reach_expander.gd")

const ROOM_WEST_SERVICE: String = "west_service_room"
const ROOM_OUTER_GUARD: String = "outer_guard_room"
const ROOM_INNER_WATCH: String = "inner_watch_room"
const ROOM_ORDER: Array[String] = [ROOM_WEST_SERVICE, ROOM_OUTER_GUARD, ROOM_INNER_WATCH]
const ROOM_RECTS: Dictionary = {
	ROOM_WEST_SERVICE: Rect2(Vector2(-200.0, -315.0), Vector2(192.0, 630.0)),
	ROOM_OUTER_GUARD: Rect2(Vector2(PARTITION_LOCAL_X, -315.0), Vector2(INNER_PARTITION_LOCAL_X - PARTITION_LOCAL_X, 630.0)),
	ROOM_INNER_WATCH: Rect2(Vector2(INNER_PARTITION_LOCAL_X, -315.0), Vector2(358.0, 630.0))
}

const OUTER_ROOM_LEFT: float = -200.0
const OUTER_ROOM_RIGHT: float = 990.0
const OUTER_ROOM_TOP: float = -315.0
const OUTER_ROOM_BOTTOM: float = 315.0
const OUTER_WALL_THICKNESS: float = 12.0
const OUTER_WALL_NODE_NAMES: Array[String] = [
	"OuterWallTop",
	"OuterWallBottom",
	"OuterWallLeft",
	"OuterWallRight"
]

var _room_fog: RoomFogOverlay
var _wall_visibility_overlay: GuardPostWallVisibilityOverlay
var _door_reach_expander: DoorInteractionReachExpander


func _ready() -> void:
	super._ready()
	_install_outer_boundary_collisions()
	_apply_loaded_inner_gate_snapshot()
	_install_door_reach_expander()
	_install_door_decorator(get_test_door(), "WestServiceDoorPresentation")
	_install_door_decorator(get_inner_gate(), "InnerWatchGatePresentation")
	_install_room_fog()
	_install_wall_visibility_overlay()


func get_room_fog_for_testing() -> RoomFogOverlay:
	return _room_fog


func get_wall_visibility_overlay_for_testing() -> GuardPostWallVisibilityOverlay:
	return _wall_visibility_overlay


func get_door_reach_expander_for_testing() -> DoorInteractionReachExpander:
	return _door_reach_expander


func get_outer_boundary_bodies_for_testing() -> Array[StaticBody2D]:
	var result: Array[StaticBody2D] = []
	for node_name: String in OUTER_WALL_NODE_NAMES:
		var body: StaticBody2D = get_node_or_null(node_name) as StaticBody2D
		if body != null:
			result.append(body)
	return result


func get_door_decorator_for_testing(door: StealthDoor) -> StealthDoorVisualDecorator:
	if door == null:
		return null
	for child: Node in door.get_children():
		if child is StealthDoorVisualDecorator:
			return child as StealthDoorVisualDecorator
	return null


func _install_outer_boundary_collisions() -> void:
	if get_node_or_null(OUTER_WALL_NODE_NAMES[0]) != null:
		return
	var horizontal_center_x: float = (OUTER_ROOM_LEFT + OUTER_ROOM_RIGHT) * 0.5
	var vertical_center_y: float = (OUTER_ROOM_TOP + OUTER_ROOM_BOTTOM) * 0.5
	var horizontal_size := Vector2(
		OUTER_ROOM_RIGHT - OUTER_ROOM_LEFT + OUTER_WALL_THICKNESS,
		OUTER_WALL_THICKNESS
	)
	var vertical_size := Vector2(
		OUTER_WALL_THICKNESS,
		OUTER_ROOM_BOTTOM - OUTER_ROOM_TOP
	)
	_build_wall(
		OUTER_WALL_NODE_NAMES[0],
		Vector2(horizontal_center_x, OUTER_ROOM_TOP),
		horizontal_size
	)
	_build_wall(
		OUTER_WALL_NODE_NAMES[1],
		Vector2(horizontal_center_x, OUTER_ROOM_BOTTOM),
		horizontal_size
	)
	_build_wall(
		OUTER_WALL_NODE_NAMES[2],
		Vector2(OUTER_ROOM_LEFT, vertical_center_y),
		vertical_size
	)
	_build_wall(
		OUTER_WALL_NODE_NAMES[3],
		Vector2(OUTER_ROOM_RIGHT, vertical_center_y),
		vertical_size
	)


func _install_door_reach_expander() -> void:
	if is_instance_valid(_door_reach_expander):
		return
	_door_reach_expander = DOOR_REACH_EXPANDER_SCRIPT.new() as DoorInteractionReachExpander
	_door_reach_expander.name = "DoorInteractionReachExpander"
	add_child(_door_reach_expander)
	var doors: Array[StealthDoor] = []
	var west_door: StealthDoor = get_test_door()
	var inner_gate: StealthDoor = get_inner_gate()
	if west_door != null:
		doors.append(west_door)
	if inner_gate != null:
		doors.append(inner_gate)
	_door_reach_expander.configure(doors)


func _apply_loaded_inner_gate_snapshot() -> void:
	var gate: StealthDoor = get_inner_gate()
	var state: Node = get_tree().root.get_node_or_null("GameState")
	if gate == null or state == null or not state.has_method("get_world_snapshot"):
		return
	var snapshot: Dictionary = state.call("get_world_snapshot") as Dictionary
	var doors_value: Variant = snapshot.get("doors", {})
	if not doors_value is Dictionary:
		return
	var gate_value: Variant = (doors_value as Dictionary).get(INNER_GATE_ID, {})
	if not gate_value is Dictionary:
		return
	var desired_state: String = str((gate_value as Dictionary).get("state", ""))
	if desired_state not in ["open", "closed", "locked", "blocked", "broken"]:
		return
	# The dynamic inner gate is created during room _ready(). Apply the loaded
	# snapshot before decorators and fog begin observing it. This avoids the
	# room's new-game default (locked/open by story flag) replacing a manual
	# save's exact door state during the first frames of scene restoration.
	gate.set("_door_state", desired_state)
	gate.call("_apply_state", false)


func _install_room_fog() -> void:
	var player: Node2D = get_tree().get_first_node_in_group("player") as Node2D
	if player == null:
		return
	_room_fog = ROOM_FOG_SCRIPT.new() as RoomFogOverlay
	_room_fog.name = "RoomFogOverlay"
	add_child(_room_fog)
	_room_fog.configure(player, ROOM_RECTS, ROOM_ORDER)


func _install_wall_visibility_overlay() -> void:
	if is_instance_valid(_wall_visibility_overlay):
		return
	_wall_visibility_overlay = WALL_VISIBILITY_OVERLAY_SCRIPT.new() as GuardPostWallVisibilityOverlay
	_wall_visibility_overlay.name = "WallVisibilityOverlay"
	add_child(_wall_visibility_overlay)


func _install_door_decorator(door: StealthDoor, node_name: String) -> void:
	if door == null or door.get_node_or_null(node_name) != null:
		return
	var decorator := DOOR_DECORATOR_SCRIPT.new() as StealthDoorVisualDecorator
	decorator.name = node_name
	door.add_child(decorator)
	decorator.configure(door)
