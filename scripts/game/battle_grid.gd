class_name BattleGrid
extends Node2D

const MINOR_COLOR: Color = Color(0.55, 0.72, 0.78, 0.18)
const MAJOR_COLOR: Color = Color(0.72, 0.86, 0.9, 0.34)
const BORDER_COLOR: Color = Color(0.82, 0.92, 0.94, 0.48)
const PLAYER_CELL_COLOR: Color = Color(0.22, 0.62, 1.0, 0.14)
const TARGET_CELL_COLOR: Color = Color(1.0, 0.34, 0.24, 0.16)
const MEASURE_COLOR: Color = Color(1.0, 0.72, 0.28, 0.92)

@export var field_rect: Rect2 = Rect2(45.0, 45.0, 1190.0, 630.0)
@export var cell_size: float = DistanceSystem.PIXELS_PER_5_FEET
@export var major_line_interval: int = 5

var _grid_enabled: bool = true
var _player: Node2D = null
var _selected_target: Node2D = null
var _distance_line: Line2D
var _distance_label: Label
var _last_player_position: Vector2 = Vector2.INF
var _last_target_position: Vector2 = Vector2.INF


func _ready() -> void:
	add_to_group("battle_grid")
	_build_measurement_overlay()
	queue_redraw()


func _process(_delta: float) -> void:
	if not is_instance_valid(_player):
		_player = get_tree().get_first_node_in_group("player") as Node2D
	_selected_target = _get_selected_target()
	var player_position: Vector2 = _player.global_position if is_instance_valid(_player) else Vector2.INF
	var target_position: Vector2 = _selected_target.global_position if is_instance_valid(_selected_target) else Vector2.INF
	if player_position != _last_player_position or target_position != _last_target_position:
		_last_player_position = player_position
		_last_target_position = target_position
		_update_measurement_overlay()
		queue_redraw()


func set_grid_enabled(value: bool) -> void:
	_grid_enabled = value
	visible = value
	if value:
		_update_measurement_overlay()
		queue_redraw()


func is_grid_enabled() -> bool:
	return _grid_enabled


func get_cell_size() -> float:
	return cell_size


func _draw() -> void:
	if not _grid_enabled:
		return
	var columns: int = ceili(field_rect.size.x / cell_size)
	var rows: int = ceili(field_rect.size.y / cell_size)
	for column: int in range(columns + 1):
		var x: float = minf(field_rect.position.x + float(column) * cell_size, field_rect.end.x)
		var major: bool = column % maxi(major_line_interval, 1) == 0
		draw_line(
			Vector2(x, field_rect.position.y),
			Vector2(x, field_rect.end.y),
			MAJOR_COLOR if major else MINOR_COLOR,
			2.0 if major else 1.0,
			true
		)
	for row: int in range(rows + 1):
		var y: float = minf(field_rect.position.y + float(row) * cell_size, field_rect.end.y)
		var major: bool = row % maxi(major_line_interval, 1) == 0
		draw_line(
			Vector2(field_rect.position.x, y),
			Vector2(field_rect.end.x, y),
			MAJOR_COLOR if major else MINOR_COLOR,
			2.0 if major else 1.0,
			true
		)
	draw_rect(field_rect, BORDER_COLOR, false, 2.0)
	if is_instance_valid(_player):
		_draw_cell_highlight(_player.global_position, PLAYER_CELL_COLOR)
	if is_instance_valid(_selected_target):
		_draw_cell_highlight(_selected_target.global_position, TARGET_CELL_COLOR)


func _build_measurement_overlay() -> void:
	_distance_line = Line2D.new()
	_distance_line.name = "DistanceLine"
	_distance_line.width = 3.0
	_distance_line.default_color = MEASURE_COLOR
	_distance_line.antialiased = true
	_distance_line.z_as_relative = false
	_distance_line.z_index = 18
	_distance_line.hide()
	add_child(_distance_line)

	_distance_label = Label.new()
	_distance_label.name = "DistanceLabel"
	_distance_label.custom_minimum_size = Vector2(190.0, 34.0)
	_distance_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_distance_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_distance_label.add_theme_color_override("font_color", Color(1.0, 0.84, 0.52, 1.0))
	_distance_label.add_theme_color_override("font_shadow_color", Color(0.0, 0.0, 0.0, 0.9))
	_distance_label.add_theme_constant_override("shadow_offset_x", 2)
	_distance_label.add_theme_constant_override("shadow_offset_y", 2)
	_distance_label.add_theme_font_size_override("font_size", 18)
	_distance_label.z_as_relative = false
	_distance_label.z_index = 19
	_distance_label.hide()
	add_child(_distance_label)


func _update_measurement_overlay() -> void:
	var show_measurement: bool = _grid_enabled and is_instance_valid(_player) and is_instance_valid(_selected_target)
	_distance_line.visible = show_measurement
	_distance_label.visible = show_measurement
	if not show_measurement:
		return
	var start: Vector2 = to_local(_player.global_position)
	var finish: Vector2 = to_local(_selected_target.global_position)
	_distance_line.points = PackedVector2Array([start, finish])
	var cells: int = DistanceSystem.grid_steps(_player.global_position, _selected_target.global_position)
	var feet: int = cells * 5
	_distance_label.text = "%d %s · %d футов" % [cells, _cell_word(cells), feet]
	_distance_label.position = (start + finish) * 0.5 - Vector2(95.0, 42.0)


func _get_selected_target() -> Node2D:
	var game: Node = get_parent()
	if game == null:
		return null
	var candidate: Variant = game.get("_selected_target")
	return candidate as Node2D if candidate is Node2D and is_instance_valid(candidate) else null


func _draw_cell_highlight(global_point: Vector2, color: Color) -> void:
	var local_point: Vector2 = to_local(global_point)
	if not field_rect.has_point(local_point):
		return
	var column: int = floori((local_point.x - field_rect.position.x) / cell_size)
	var row: int = floori((local_point.y - field_rect.position.y) / cell_size)
	var cell_position := field_rect.position + Vector2(float(column), float(row)) * cell_size
	var cell_rect := Rect2(cell_position, Vector2(cell_size, cell_size)).intersection(field_rect)
	draw_rect(cell_rect, color, true)
	draw_rect(cell_rect, Color(color, minf(color.a + 0.35, 1.0)), false, 2.0)


func _cell_word(value: int) -> String:
	var last_two: int = value % 100
	var last: int = value % 10
	if last_two in range(11, 15):
		return "клеток"
	if last == 1:
		return "клетка"
	if last in range(2, 5):
		return "клетки"
	return "клеток"
