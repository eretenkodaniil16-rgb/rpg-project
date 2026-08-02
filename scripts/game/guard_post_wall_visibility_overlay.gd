class_name GuardPostWallVisibilityOverlay
extends Node2D

const WEST_PARTITION_X: float = -8.0
const INNER_PARTITION_X: float = 632.0
const ROOM_LEFT: float = -200.0
const ROOM_RIGHT: float = 990.0
const ROOM_TOP: float = -315.0
const ROOM_BOTTOM: float = 315.0
const DOOR_GAP_TOP: float = -59.0
const DOOR_GAP_BOTTOM: float = 69.0
const WALL_VISUAL_THICKNESS: float = 12.0
const WALL_FILL: Color = Color(0.20, 0.22, 0.24, 1.0)
const WALL_EDGE: Color = Color(0.48, 0.53, 0.58, 1.0)

var _segments: Array[Rect2] = []


func _ready() -> void:
	z_as_relative = false
	z_index = 50
	_build_segments()
	queue_redraw()


func get_wall_segments_for_testing() -> Array[Rect2]:
	return _segments.duplicate()


func _build_segments() -> void:
	_segments = [
		_horizontal_segment(ROOM_LEFT, ROOM_RIGHT, ROOM_TOP),
		_horizontal_segment(ROOM_LEFT, ROOM_RIGHT, ROOM_BOTTOM),
		_vertical_segment(ROOM_LEFT, ROOM_TOP, ROOM_BOTTOM),
		_vertical_segment(ROOM_RIGHT, ROOM_TOP, ROOM_BOTTOM),
		_vertical_segment(WEST_PARTITION_X, ROOM_TOP, DOOR_GAP_TOP),
		_vertical_segment(WEST_PARTITION_X, DOOR_GAP_BOTTOM, ROOM_BOTTOM),
		_vertical_segment(INNER_PARTITION_X, ROOM_TOP, DOOR_GAP_TOP),
		_vertical_segment(INNER_PARTITION_X, DOOR_GAP_BOTTOM, ROOM_BOTTOM)
	]


func _horizontal_segment(start_x: float, end_x: float, y: float) -> Rect2:
	return Rect2(
		Vector2(start_x - WALL_VISUAL_THICKNESS * 0.5, y - WALL_VISUAL_THICKNESS * 0.5),
		Vector2(end_x - start_x + WALL_VISUAL_THICKNESS, WALL_VISUAL_THICKNESS)
	)


func _vertical_segment(x: float, start_y: float, end_y: float) -> Rect2:
	return Rect2(
		Vector2(x - WALL_VISUAL_THICKNESS * 0.5, start_y),
		Vector2(WALL_VISUAL_THICKNESS, end_y - start_y)
	)


func _draw() -> void:
	for segment: Rect2 in _segments:
		draw_rect(segment, WALL_FILL, true)
		draw_rect(segment, WALL_EDGE, false, 2.0)
