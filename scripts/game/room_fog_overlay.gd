class_name RoomFogOverlay
extends Node2D

const FOG_COLOR: Color = Color(0.008, 0.012, 0.020, 0.985)
const FOG_BORDER_COLOR: Color = Color(0.10, 0.14, 0.19, 0.78)
const FOG_PATTERN_COLOR: Color = Color(0.20, 0.27, 0.34, 0.08)
const VISION_RADIUS_PIXELS: float = 640.0
const REFRESH_INTERVAL_SECONDS: float = 0.08

var _player: Node2D
var _room_rects: Dictionary = {}
var _room_order: Array[String] = []
var _current_room_id: String = ""
var _grid: BattleGrid
var _environment: CombatEnvironment
var _visible_cells: Dictionary = {}
var _refresh_accumulator: float = 0.0
var _last_player_position: Vector2 = Vector2.INF
var _last_visibility_signature: int = 0


func configure(player: Node2D, room_rects: Dictionary, room_order: Array[String]) -> void:
	_player = player
	_room_rects = room_rects.duplicate(true)
	_room_order = room_order.duplicate()
	_resolve_visibility_dependencies()
	_refresh_visibility(true)


func _ready() -> void:
	add_to_group("player_visibility")
	z_as_relative = false
	z_index = 60
	process_mode = Node.PROCESS_MODE_ALWAYS
	_resolve_visibility_dependencies()
	_refresh_visibility(true)


func _process(delta: float) -> void:
	if not is_instance_valid(_player):
		_player = get_tree().get_first_node_in_group("player") as Node2D
	_resolve_visibility_dependencies()
	_refresh_accumulator += delta
	var player_moved: bool = is_instance_valid(_player) and not _player.global_position.is_equal_approx(_last_player_position)
	if player_moved or _refresh_accumulator >= REFRESH_INTERVAL_SECONDS:
		_refresh_accumulator = 0.0
		_refresh_visibility(player_moved)


func is_world_position_visible(world_position: Vector2) -> bool:
	if not is_instance_valid(_player):
		return false
	if _player.global_position.distance_to(world_position) > VISION_RADIUS_PIXELS:
		return false
	if is_instance_valid(_environment):
		return _environment.has_line_of_sight(_player.global_position, world_position)
	return _room_at(to_local(world_position)) == _current_room_id


func get_current_room_id_for_testing() -> String:
	_refresh_current_room()
	return _current_room_id


func is_room_concealed_for_testing(room_id: String) -> bool:
	_refresh_current_room()
	return _room_rects.has(room_id) and room_id != _current_room_id


func get_room_rect_for_testing(room_id: String) -> Rect2:
	var value: Variant = _room_rects.get(room_id, Rect2())
	return value as Rect2 if value is Rect2 else Rect2()


func get_visible_cells_for_testing() -> Array[Vector2i]:
	var result: Array[Vector2i] = []
	for cell_value: Variant in _visible_cells.keys():
		if cell_value is Vector2i:
			result.append(cell_value as Vector2i)
	return result


func get_vision_radius_for_testing() -> float:
	return VISION_RADIUS_PIXELS


func force_refresh_for_testing() -> void:
	_resolve_visibility_dependencies()
	_refresh_visibility(true)


func _resolve_visibility_dependencies() -> void:
	if not is_instance_valid(_grid):
		_grid = get_tree().get_first_node_in_group("battle_grid") as BattleGrid
	if not is_instance_valid(_environment):
		_environment = get_tree().get_first_node_in_group("combat_environment") as CombatEnvironment


func _refresh_visibility(force_redraw: bool) -> void:
	if not is_instance_valid(_player):
		return
	_refresh_current_room()
	_last_player_position = _player.global_position
	if not is_instance_valid(_grid):
		if force_redraw:
			queue_redraw()
		return

	var next_visible: Dictionary = {}
	var field_rect: Rect2 = _grid.get_field_rect()
	var cell_size: float = _grid.get_cell_size()
	var columns: int = ceili(field_rect.size.x / cell_size)
	var rows: int = ceili(field_rect.size.y / cell_size)
	for y: int in range(rows):
		for x: int in range(columns):
			var cell := Vector2i(x, y)
			var center := field_rect.position + Vector2((float(x) + 0.5) * cell_size, (float(y) + 0.5) * cell_size)
			if is_world_position_visible(center):
				next_visible[cell] = true

	var player_cell: Vector2i = _grid.world_to_cell(_player.global_position)
	if _grid.is_cell_valid(player_cell):
		next_visible[player_cell] = true
	var next_signature: int = hash(next_visible.keys())
	if force_redraw or next_signature != _last_visibility_signature:
		_visible_cells = next_visible
		_last_visibility_signature = next_signature
		queue_redraw()


func _refresh_current_room() -> void:
	if not is_instance_valid(_player) or _room_rects.is_empty():
		return
	var local_position: Vector2 = to_local(_player.global_position)
	var next_room_id: String = _room_at(local_position)
	if next_room_id.is_empty():
		next_room_id = _nearest_room(local_position)
	_current_room_id = next_room_id


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
	if is_instance_valid(_grid):
		_draw_cell_visibility()
	else:
		_draw_room_fallback()


func _draw_cell_visibility() -> void:
	var field_rect: Rect2 = _grid.get_field_rect()
	var cell_size: float = _grid.get_cell_size()
	var columns: int = ceili(field_rect.size.x / cell_size)
	var rows: int = ceili(field_rect.size.y / cell_size)
	for y: int in range(rows):
		for x: int in range(columns):
			var cell := Vector2i(x, y)
			if _visible_cells.has(cell):
				continue
			var world_rect := Rect2(
				field_rect.position + Vector2(float(x) * cell_size, float(y) * cell_size),
				Vector2(cell_size + 1.0, cell_size + 1.0)
			)
			var local_rect := Rect2(to_local(world_rect.position), world_rect.size)
			draw_rect(local_rect, FOG_COLOR, true)
			draw_rect(local_rect, FOG_BORDER_COLOR, false, 1.0)
	_draw_outer_darkness(field_rect)


func _draw_outer_darkness(field_rect: Rect2) -> void:
	var local_field := Rect2(to_local(field_rect.position), field_rect.size)
	for room_id: String in _room_order:
		var value: Variant = _room_rects.get(room_id, Rect2())
		if not value is Rect2:
			continue
		var room_rect: Rect2 = value as Rect2
		if room_rect.intersects(local_field):
			continue
		draw_rect(room_rect, FOG_COLOR, true)


func _draw_room_fallback() -> void:
	for room_id: String in _room_order:
		if room_id == _current_room_id:
			continue
		var value: Variant = _room_rects.get(room_id, Rect2())
		if not value is Rect2:
			continue
		var room_rect: Rect2 = value as Rect2
		draw_rect(room_rect, FOG_COLOR, true)
		draw_rect(room_rect, FOG_BORDER_COLOR, false, 2.0)
		var stripe_y: float = room_rect.position.y - room_rect.size.x
		while stripe_y < room_rect.end.y:
			draw_line(
				Vector2(room_rect.position.x, stripe_y),
				Vector2(room_rect.end.x, stripe_y + room_rect.size.x),
				FOG_PATTERN_COLOR,
				2.0
			)
			stripe_y += 52.0
