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
	var planner := PlannedMovementSystem.new()
	var invalid_path: Dictionary = planner.build_path(
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

	var jump_route: Dictionary = planner.build_path(
		grid,
		Vector2i(8, 2),
		Vector2i(10, 2),
		{},
		environment,
		CombatantState.new(),
		30,
		false,
		true
	)
	if not bool(jump_route.get("reachable", false)):
		_fail("Planner failed to create an automatic jump route: %s" % jump_route)
		return
	var jump_path: Array = jump_route.get("path", []) as Array
	var jump_indices: Array = jump_route.get("jump_indices", []) as Array
	if jump_path != [Vector2i(8, 2), Vector2i(10, 2)] or jump_indices != [1]:
		_fail("Automatic jump transition is incorrect: %s" % jump_route)
		return
	if int(jump_route.get("cost_feet", 0)) != 10:
		_fail("One-cell obstacle jump must cost ten feet: %s" % jump_route)
		return

	var walking_route: Dictionary = planner.build_path(
		grid,
		Vector2i(8, 2),
		Vector2i(10, 2),
		{},
		environment,
		CombatantState.new(),
		30,
		false,
		false
	)
	if not bool(walking_route.get("reachable", false)):
		_fail("Planner failed to route around the obstacle with jumps disabled: %s" % walking_route)
		return
	var walking_path: Array = walking_route.get("path", []) as Array
	if walking_path.has(blocked_cell) or walking_path.size() < 3:
		_fail("Walking route crossed the obstacle: %s" % walking_route)
		return

	var reachable: Dictionary = planner.calculate_reachable_cells(
		grid,
		Vector2i(8, 2),
		{},
		environment,
		CombatantState.new(),
		10,
		false,
		true
	)
	if reachable.has(blocked_cell):
		_fail("Blocked obstacle cell appeared in reachable area.")
		return
	if not reachable.has(Vector2i(10, 2)) or int(reachable[Vector2i(10, 2)]) != 10:
		_fail("Jump landing is absent from reachable area: %s" % reachable)
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
