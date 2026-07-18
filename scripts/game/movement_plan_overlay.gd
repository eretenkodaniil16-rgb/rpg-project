class_name MovementPlanOverlay
extends Node2D

const PATH_COLOR: Color = Color(0.24, 0.86, 1.0, 0.95)
const JUMP_COLOR: Color = Color(1.0, 0.76, 0.22, 0.98)
const CELL_COLOR: Color = Color(0.18, 0.72, 0.96, 0.24)
const DESTINATION_COLOR: Color = Color(0.35, 1.0, 0.52, 0.38)
const INVALID_COLOR: Color = Color(1.0, 0.25, 0.2, 0.34)
const REACHABLE_COLOR: Color = Color(0.18, 0.62, 0.92, 0.13)
const REACHABLE_EDGE_COLOR: Color = Color(0.34, 0.8, 1.0, 0.24)

var _grid: BattleGrid = null
var _path: Array[Vector2i] = []
var _jump_indices: Array[int] = []
var _cost_feet: int = 0
var _reachable: bool = false
var _reachable_costs: Dictionary = {}
var _maximum_movement_feet: int = 0
var _label: Label


func _ready() -> void:
	z_index = 7
	_build_label()
	hide()


func bind_grid(grid: BattleGrid) -> void:
	_grid = grid
	_update_visibility()
	queue_redraw()


func set_reachable_cells(costs: Dictionary, maximum_movement_feet: int) -> void:
	_reachable_costs = costs.duplicate()
	_maximum_movement_feet = maxi(maximum_movement_feet, 0)
	_update_visibility()
	queue_redraw()


func clear_reachable_cells() -> void:
	_reachable_costs.clear()
	_maximum_movement_feet = 0
	_update_visibility()
	queue_redraw()


func set_plan(
	path: Array[Vector2i],
	cost_feet: int,
	reachable: bool,
	jump_indices: Array[int] = []
) -> void:
	_path = path.duplicate()
	_jump_indices = jump_indices.duplicate()
	_cost_feet = maxi(cost_feet, 0)
	_reachable = reachable
	_update_visibility()
	_update_label()
	queue_redraw()


func clear_plan() -> void:
	_path.clear()
	_jump_indices.clear()
	_cost_feet = 0
	_reachable = false
	if _label != null:
		_label.hide()
	_update_visibility()
	queue_redraw()


func has_plan() -> bool:
	return _path.size() > 1 and _reachable


func get_planned_path() -> Array[Vector2i]:
	return _path.duplicate()


func _draw() -> void:
	if _grid == null:
		return
	_draw_reachable_area()
	_draw_planned_route()


func _draw_reachable_area() -> void:
	var size: float = _grid.get_cell_size()
	for cell_value: Variant in _reachable_costs.keys():
		if not cell_value is Vector2i:
			continue
		var cell: Vector2i = cell_value as Vector2i
		if not _grid.is_cell_valid(cell):
			continue
		var center: Vector2 = to_local(_grid.cell_to_world_center(cell))
		var cell_rect := Rect2(center - Vector2(size, size) * 0.5, Vector2(size, size)).grow(-2.5)
		var cost: int = int(_reachable_costs.get(cell, 0))
		var ratio: float = 0.0 if _maximum_movement_feet <= 0 else clampf(float(cost) / float(_maximum_movement_feet), 0.0, 1.0)
		var fill: Color = Color(REACHABLE_COLOR, lerpf(REACHABLE_COLOR.a, 0.055, ratio))
		draw_rect(cell_rect, fill, true)
		draw_rect(cell_rect, REACHABLE_EDGE_COLOR, false, 1.0)


func _draw_planned_route() -> void:
	if _path.is_empty():
		return
	var size: float = _grid.get_cell_size()
	var points := PackedVector2Array()
	for index: int in range(_path.size()):
		var center: Vector2 = to_local(_grid.cell_to_world_center(_path[index]))
		points.append(center)
		var cell_rect := Rect2(center - Vector2(size, size) * 0.5, Vector2(size, size))
		var fill: Color = CELL_COLOR
		if index == _path.size() - 1:
			fill = DESTINATION_COLOR if _reachable else INVALID_COLOR
		draw_rect(cell_rect.grow(-3.0), fill, true)
		draw_rect(cell_rect.grow(-3.0), Color(fill, 0.9), false, 2.0)
	for index: int in range(1, points.size()):
		var jump: bool = index in _jump_indices
		var segment_color: Color = JUMP_COLOR if jump else (PATH_COLOR if _reachable else INVALID_COLOR)
		draw_line(points[index - 1], points[index], segment_color, 6.0 if jump else 5.0, true)
		if jump:
			var middle: Vector2 = points[index - 1].lerp(points[index], 0.5)
			draw_circle(middle, 9.0, Color(JUMP_COLOR, 0.32))
			draw_string(ThemeDB.fallback_font, middle + Vector2(-18.0, -13.0), "ПРЫЖОК", HORIZONTAL_ALIGNMENT_LEFT, 80.0, 10, JUMP_COLOR)
	for point: Vector2 in points:
		draw_circle(point, 5.0, PATH_COLOR if _reachable else INVALID_COLOR)


func _build_label() -> void:
	_label = Label.new()
	_label.name = "MovementPlanLabel"
	_label.custom_minimum_size = Vector2(240.0, 34.0)
	_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_label.add_theme_color_override("font_color", Color(0.82, 0.95, 1.0, 1.0))
	_label.add_theme_color_override("font_shadow_color", Color(0.0, 0.0, 0.0, 0.9))
	_label.add_theme_constant_override("shadow_offset_x", 2)
	_label.add_theme_constant_override("shadow_offset_y", 2)
	_label.add_theme_font_size_override("font_size", 16)
	add_child(_label)
	_label.hide()


func _update_label() -> void:
	if _label == null or _grid == null or _path.size() < 2:
		if _label != null:
			_label.hide()
		return
	var destination: Vector2 = to_local(_grid.cell_to_world_center(_path[_path.size() - 1]))
	_label.position = destination - Vector2(120.0, 58.0)
	_label.text = "%d футов · %d переходов" % [_cost_feet, maxi(_path.size() - 1, 0)] if _reachable else "Путь недоступен"
	_label.show()


func _update_visibility() -> void:
	visible = _grid != null and (not _reachable_costs.is_empty() or not _path.is_empty())
