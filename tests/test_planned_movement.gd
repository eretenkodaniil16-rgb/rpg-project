extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var grid := BattleGrid.new()
	grid.name = "BattleGridTest"
	root.add_child(grid)
	var environment := CombatEnvironment.new()
	environment.name = "CombatEnvironmentTest"
	root.add_child(environment)
	await process_frame
	await process_frame

	var blocked_cell := Vector2i(9, 2)
	if not environment.is_cell_blocked(grid, blocked_cell):
		_fail("Low barricade cell must be blocked.")
		return
	if not environment.is_jumpable_cell(grid, blocked_cell):
		_fail("Low barricade must be jumpable.")
		return
	var invalid_path: Dictionary = PlannedMovementSystem.new().build_path(
		grid,
		Vector2i(8, 2),
		blocked_cell,
		{},
		environment,
		CombatantState.new(),
		30
	)
	if bool(invalid_path.get("reachable", false)):
		_fail("Planner allowed a route ending inside an obstacle.")
		return

	var planner := PlannedMovementSystem.new()
	var detour: Dictionary = planner.build_path(
		grid,
		Vector2i(8, 2),
		Vector2i(10, 2),
		{},
		environment,
		CombatantState.new(),
		30
	)
	if not bool(detour.get("reachable", false)):
		_fail("Planner failed to route around a one-cell-wide obstacle: %s" % detour)
		return
	var path: Array = detour.get("path", []) as Array
	if path.has(blocked_cell):
		_fail("Planned path crosses a blocked cell: %s" % path)
		return
	if int(detour.get("cost_feet", 0)) <= 10:
		_fail("Detour cost was not greater than a direct two-step route.")
		return

	var landing: Vector2i = environment.get_jump_landing_cell(grid, Vector2i(8, 2), Vector2i.RIGHT)
	if landing != Vector2i(10, 2):
		_fail("Jump landing over the low barricade is incorrect: %s" % landing)
		return
	var wall_landing: Vector2i = environment.get_jump_landing_cell(grid, Vector2i(11, 7), Vector2i.RIGHT)
	if wall_landing != CombatEnvironment.INVALID_CELL:
		_fail("Solid wall was incorrectly considered jumpable: %s" % wall_landing)
		return

	grid.queue_free()
	environment.queue_free()
	await process_frame
	print("Planned movement tests passed.")
	quit(0)
