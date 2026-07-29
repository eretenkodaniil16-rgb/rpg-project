class_name EscapeZoneOverlay
extends Node2D

const HIDEOUT_FILL: Color = Color(0.38, 0.22, 0.62, 0.34)
const HIDEOUT_BORDER: Color = Color(0.78, 0.58, 1.0, 0.96)
const TRANSITION_FILL: Color = Color(0.18, 0.48, 0.82, 0.28)
const TRANSITION_BORDER: Color = Color(0.48, 0.78, 1.0, 0.94)
const DESTINATION_FILL: Color = Color(0.22, 0.78, 0.62, 0.28)
const DESTINATION_BORDER: Color = Color(0.45, 1.0, 0.78, 0.92)

var _grid: BattleGrid
var _hideout_cells: Array[Vector2i] = []
var _transition_cells: Array[Vector2i] = []
var _destination_cells: Array[Vector2i] = []


func bind_grid(grid: BattleGrid) -> void:
	_grid = grid
	queue_redraw()


func set_escape_cells(cells: Array[Vector2i]) -> void:
	_hideout_cells = cells.duplicate()
	_transition_cells.clear()
	_destination_cells.clear()
	visible = not _hideout_cells.is_empty()
	queue_redraw()


func set_route_cells(groups: Dictionary) -> void:
	_hideout_cells = _typed_cells(groups.get("hideout", []))
	_transition_cells = _typed_cells(groups.get("transition", []))
	_destination_cells = _typed_cells(groups.get("destination", []))
	visible = not (_hideout_cells.is_empty() and _transition_cells.is_empty() and _destination_cells.is_empty())
	queue_redraw()


func clear_escape_cells() -> void:
	_hideout_cells.clear()
	_transition_cells.clear()
	_destination_cells.clear()
	hide()
	queue_redraw()


func get_escape_cells_for_testing() -> Array[Vector2i]:
	var result: Array[Vector2i] = []
	for group: Array[Vector2i] in [_hideout_cells, _transition_cells, _destination_cells]:
		for cell: Vector2i in group:
			if cell not in result:
				result.append(cell)
	return result


func _draw() -> void:
	if _grid == null:
		return
	_draw_cells(_hideout_cells, HIDEOUT_FILL, HIDEOUT_BORDER)
	_draw_cells(_transition_cells, TRANSITION_FILL, TRANSITION_BORDER)
	_draw_cells(_destination_cells, DESTINATION_FILL, DESTINATION_BORDER)


func _draw_cells(cells: Array[Vector2i], fill: Color, border: Color) -> void:
	var size: float = _grid.get_cell_size()
	for cell: Vector2i in cells:
		if not _grid.is_cell_valid(cell):
			continue
		var center: Vector2 = to_local(_grid.cell_to_world_center(cell))
		var rect := Rect2(center - Vector2(size, size) * 0.5, Vector2(size, size)).grow(-3.0)
		draw_rect(rect, fill, true)
		draw_rect(rect, border, false, 3.0)


static func _typed_cells(value: Variant) -> Array[Vector2i]:
	var result: Array[Vector2i] = []
	if value is Array:
		for item: Variant in value as Array:
			if item is Vector2i:
				result.append(item)
	return result
