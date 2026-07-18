class_name MovementPlanOverlay
extends Node2D

const PATH_COLOR: Color = Color(0.24, 0.86, 1.0, 0.9)
const CELL_COLOR: Color = Color(0.18, 0.72, 0.96, 0.22)
const DESTINATION_COLOR: Color = Color(0.35, 1.0, 0.52, 0.34)
const INVALID_COLOR: Color = Color(1.0, 0.25, 0.2, 0.34)

var _grid: BattleGrid = null
var _path: Array[Vector2i] = []
var _cost_feet: int = 0
var _reachable: bool = false
var _label: Label


func _ready() -> void:
	z_index = 7
	_build_label()
	hide()


func bind_grid(grid: BattleGrid) -> void:
	_grid = grid
	queue_redraw()


func set_plan(path: Array[Vector2i], cost_feet: int, reachable: bool) -> void:
	_path = path.duplicate()
	_cost_feet = maxi(cost_feet, 0)
	_reachable = reachable
	visible = _grid != null and not _path.is_empty()
	_update_label()
	queue_redraw()


func clear_plan() -> void:
	_path.clear()
	_cost_feet = 0
	_reachable = false
	hide()
	queue_redraw()


func has_plan() -> bool:
	return _path.size() > 1 and _reachable


func get_planned_path() -> Array[Vector2i]:
	return _path.duplicate()


func _draw() -> void:
	if _grid == null or _path.is_empty():
		return
	var points := PackedVector2Array()
	for index: int in range(_path.size()):
		var center: Vector2 = to_local(_grid.cell_to_world_center(_path[index]))
		points.append(center)
		var size: float = _grid.get_cell_size()
		var cell_rect := Rect2(center - Vector2(size, size) * 0.5, Vector2(size, size))
		var fill: Color = CELL_COLOR
		if index == _path.size() - 1:
			fill = DESTINATION_COLOR if _reachable else INVALID_COLOR
		draw_rect(cell_rect.grow(-3.0), fill, true)
		draw_rect(cell_rect.grow(-3.0), Color(fill, 0.9), false, 2.0)
	if points.size() >= 2:
		draw_polyline(points, PATH_COLOR if _reachable else INVALID_COLOR, 5.0, true)
	for point: Vector2 in points:
		draw_circle(point, 5.0, PATH_COLOR if _reachable else INVALID_COLOR)


func _build_label() -> void:
	_label = Label.new()
	_label.name = "MovementPlanLabel"
	_label.custom_minimum_size = Vector2(220.0, 32.0)
	_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_label.add_theme_color_override("font_color", Color(0.82, 0.95, 1.0, 1.0))
	_label.add_theme_color_override("font_shadow_color", Color(0.0, 0.0, 0.0, 0.9))
	_label.add_theme_constant_override("shadow_offset_x", 2)
	_label.add_theme_constant_override("shadow_offset_y", 2)
	_label.add_theme_font_size_override("font_size", 16)
	add_child(_label)


func _update_label() -> void:
	if _label == null or _grid == null or _path.is_empty():
		return
	var destination: Vector2 = to_local(_grid.cell_to_world_center(_path[_path.size() - 1]))
	_label.position = destination - Vector2(110.0, 58.0)
	_label.text = "%d футов · %d шагов" % [_cost_feet, maxi(_path.size() - 1, 0)] if _reachable else "Путь недоступен"
