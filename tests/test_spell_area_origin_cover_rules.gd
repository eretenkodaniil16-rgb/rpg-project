extends SceneTree


class CenterBlockedEnvironment:
	extends Node
	var blocked_center: Vector2 = Vector2.ZERO
	var tolerance: float = 1.0

	func has_line_of_sight(_start: Vector2, finish: Vector2) -> bool:
		return finish.distance_to(blocked_center) > tolerance


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var grid := BattleGrid.new()
	grid.field_rect = Rect2(0.0, 0.0, 640.0, 640.0)
	grid.cell_size = 64.0
	root.add_child(grid)
	await process_frame

	var areas := SpellAreaSystem.new()
	var caster_cell := Vector2i(2, 4)

	var default_line: Array[Vector2i] = areas.get_area_cells(
		grid,
		caster_cell,
		Vector2i(6, 4),
		{"shape": "line", "origin": "self", "length_ft": 20, "width_ft": 5}
	)
	if caster_cell in default_line:
		_fail("Line included its point of origin without an explicit override.")
		return
	if Vector2i(3, 4) not in default_line or Vector2i(6, 4) not in default_line:
		_fail("Self-origin line lost its forward footprint.")
		return

	var remote_origin := Vector2i(4, 4)
	var remote_line: Array[Vector2i] = areas.get_area_cells(
		grid,
		caster_cell,
		remote_origin,
		{"shape": "line", "origin": "point", "length_ft": 15, "width_ft": 5},
		Vector2.UP
	)
	if remote_origin in remote_line:
		_fail("Remote line included its point of origin by default.")
		return
	if Vector2i(4, 3) not in remote_line or Vector2i(4, 1) not in remote_line:
		_fail("Remote line ignored its explicit direction hint.")
		return
	if Vector2i(5, 4) in remote_line or Vector2i(4, 5) in remote_line:
		_fail("Remote line extended sideways or behind its explicit direction.")
		return

	var point_sphere: Array[Vector2i] = areas.get_area_cells(
		grid,
		caster_cell,
		caster_cell,
		{"shape": "sphere", "origin": "point", "radius_ft": 5}
	)
	if caster_cell not in point_sphere or Vector2i(3, 4) not in point_sphere:
		_fail("A point-origin sphere centered on the caster cell was displaced.")
		return

	var environment := CenterBlockedEnvironment.new()
	var partially_visible_cell := Vector2i(6, 6)
	environment.blocked_center = grid.cell_to_world_center(partially_visible_cell)
	root.add_child(environment)
	var filtered: Array[Vector2i] = areas.filter_cells_by_total_cover(
		grid,
		[partially_visible_cell],
		grid.cell_to_world_center(caster_cell),
		environment
	)
	if partially_visible_cell not in filtered:
		_fail("A cell with blocked center but visible edges was incorrectly treated as Total Cover.")
		return

	print("Spell area origin exclusion, explicit remote direction, point origin, and all-lines Total Cover rules passed.")
	quit(0)
