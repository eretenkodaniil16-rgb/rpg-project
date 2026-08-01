class_name RoomFogOverlay
extends Node2D

const FOG_COLOR: Color = Color(0.015, 0.022, 0.032, 0.965)
const FOG_BORDER_COLOR: Color = Color(0.10, 0.14, 0.19, 0.96)
const FOG_PATTERN_COLOR: Color = Color(0.20, 0.27, 0.34, 0.10)
const EDGE_FEATHER_WIDTH: float = 24.0

var _player: Node2D
var _room_rects: Dictionary = {}
var _room_order: Array[String] = []
var _current_room_id: String = ""


func configure(player: Node2D, room_rects: Dictionary, room_order: Array[String]) -> void:
	_player = player
	_room_rects = room_rects.duplicate(true)
	_room_order = room_order.duplicate()
	_refresh_current_room(true)


func _ready() -> void:
	z_as_relative = false
	z_index = 60
	process_mode = Node.PROCESS_MODE_ALWAYS
	queue_redraw()


func _process(_delta: float) -> void:
	if not is_instance_valid(_player):
		_player = get_tree().get_first_node_in_group("player") as Node2D
	_refresh_current_room(false)


func get_current_room_id_for_testing() -> String:
	_refresh_current_room(false)
	return _current_room_id


func is_room_concealed_for_testing(room_id: String) -> bool:
	_refresh_current_room(false)
	return _room_rects.has(room_id) and room_id != _current_room_id


func get_room_rect_for_testing(room_id: String) -> Rect2:
	var value: Variant = _room_rects.get(room_id, Rect2())
	return value as Rect2 if value is Rect2 else Rect2()


func _refresh_current_room(force_redraw: bool) -> void:
	if not is_instance_valid(_player) or _room_rects.is_empty():
		return
	var local_position: Vector2 = to_local(_player.global_position)
	var next_room_id: String = _room_at(local_position)
	if next_room_id.is_empty():
		next_room_id = _nearest_room(local_position)
	if force_redraw or next_room_id != _current_room_id:
		_current_room_id = next_room_id
		queue_redraw()


func _room_at(local_position: Vector2) -> String:
	for room_id: String in _room_order:
		var value: Variant = _room_rects.get(room_id, Rect2())
		if value is Rect2 and (value as Rect2).grow(1.0).has_point(local_position):
			return room_id
	return ""


func _nearest_room(local_position: Vector2) -> String:
	var nearest_id: String = ""
	var nearest_distance: float = INF
	for room_id: String in _room_order:
		var value: Variant = _room_rects.get(room_id, Rect2())
		if not value is Rect2:
			continue
		var distance: float = local_position.distance_squared_to((value as Rect2).get_center())
		if distance < nearest_distance:
			nearest_distance = distance
			nearest_id = room_id
	return nearest_id


func _draw() -> void:
	if _room_rects.is_empty():
		return
	for room_id: String in _room_order:
		if room_id == _current_room_id:
			continue
		var value: Variant = _room_rects.get(room_id, Rect2())
		if not value is Rect2:
			continue
		_draw_concealed_room(value as Rect2, room_id)


func _draw_concealed_room(room_rect: Rect2, room_id: String) -> void:
	draw_rect(room_rect, FOG_COLOR, true)
	draw_rect(room_rect, FOG_BORDER_COLOR, false, 2.0)
	var stripe_y: float = room_rect.position.y - room_rect.size.x
	while stripe_y < room_rect.end.y:
		var from := Vector2(room_rect.position.x, stripe_y)
		var to := Vector2(room_rect.end.x, stripe_y + room_rect.size.x)
		draw_line(from, to, FOG_PATTERN_COLOR, 2.0)
		stripe_y += 52.0
	_draw_boundary_feather(room_rect, room_id)


func _draw_boundary_feather(room_rect: Rect2, room_id: String) -> void:
	var room_index: int = _room_order.find(room_id)
	var current_index: int = _room_order.find(_current_room_id)
	if room_index < 0 or current_index < 0:
		return
	var edge_on_left: bool = room_index > current_index
	for step: int in range(4):
		var ratio: float = float(step + 1) / 4.0
		var alpha: float = 0.22 * (1.0 - ratio)
		var width: float = EDGE_FEATHER_WIDTH / 4.0
		var x: float = room_rect.position.x + float(step) * width if edge_on_left else room_rect.end.x - float(step + 1) * width
		draw_rect(
			Rect2(Vector2(x, room_rect.position.y), Vector2(width, room_rect.size.y)),
			Color(0.16, 0.22, 0.30, alpha),
			true
		)
