class_name EscapeZoneOverlay
extends Node2D

const FILL_COLOR: Color = Color(0.22, 0.78, 0.62, 0.28)
const BORDER_COLOR: Color = Color(0.45, 1.0, 0.78, 0.92)

var _grid: BattleGrid
var _cells: Array[Vector2i] = []


func bind_grid(grid: BattleGrid) -> void:
	_grid = grid
	queue_redraw()


func set_escape_cells(cells: Array[Vector2i]) -> void:
	_cells = cells.duplicate()
	visible = not _cells.is_empty()
	queue_redraw()


func clear_escape_cells() -> void:
	_cells.clear()
	hide()
	queue_redraw()


func get_escape_cells_for_testing() -> Array[Vector2i]:
	return _cells.duplicate()


func _draw() -> void:
	if _grid == null or _cells.is_empty():
		return
	var size: float = _grid.get_cell_size()
	for cell: Vector2i in _cells:
		if not _grid.is_cell_valid(cell):
			continue
		var center: Vector2 = to_local(_grid.cell_to_world_center(cell))
		var rect := Rect2(center - Vector2(size, size) * 0.5, Vector2(size, size)).grow(-3.0)
		draw_rect(rect, FILL_COLOR, true)
		draw_rect(rect, BORDER_COLOR, false, 3.0)
