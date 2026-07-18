class_name PlannedMovementSystem
extends RefCounted

const BASE_STEP_FEET: int = 5
const DIRECTIONS: Array[Vector2i] = [
	Vector2i(-1, -1), Vector2i(0, -1), Vector2i(1, -1),
	Vector2i(-1, 0), Vector2i(1, 0),
	Vector2i(-1, 1), Vector2i(0, 1), Vector2i(1, 1)
]

var _rules: SrdCombatRules = SrdCombatRules.new()


func build_path(
	grid: BattleGrid,
	start_cell: Vector2i,
	destination_cell: Vector2i,
	occupied_cells: Dictionary,
	environment: CombatEnvironment,
	state: CombatantState,
	available_movement_feet: int,
	dragging_target: bool = false,
	allow_jumps: bool = true
) -> Dictionary:
	if grid == null or not grid.is_cell_valid(start_cell) or not grid.is_cell_valid(destination_cell):
		return _failure("Клетка находится за пределами поля.")
	if destination_cell != start_cell and _is_blocked(grid, destination_cell, occupied_cells, environment):
		return _failure("Выбранная клетка занята или перекрыта препятствием.")
	if destination_cell == start_cell:
		return {"reachable": true, "path": [start_cell], "cost_feet": 0, "jump_indices": [], "reason": ""}

	var search: Dictionary = _run_search(
		grid,
		start_cell,
		occupied_cells,
		environment,
		state,
		available_movement_feet,
		dragging_target,
		allow_jumps,
		destination_cell
	)
	var costs: Dictionary = search.get("costs", {}) as Dictionary
	if not costs.has(destination_cell):
		return _failure("До выбранной клетки нет доступного пути в пределах оставшегося перемещения.")
	var reconstruction: Dictionary = _reconstruct_path(
		search.get("previous", {}) as Dictionary,
		start_cell,
		destination_cell
	)
	return {
		"reachable": true,
		"path": reconstruction.get("path", []) as Array[Vector2i],
		"cost_feet": int(costs[destination_cell]),
		"jump_indices": reconstruction.get("jump_indices", []) as Array[int],
		"reason": ""
	}


func calculate_reachable_cells(
	grid: BattleGrid,
	start_cell: Vector2i,
	occupied_cells: Dictionary,
	environment: CombatEnvironment,
	state: CombatantState,
	available_movement_feet: int,
	dragging_target: bool = false,
	allow_jumps: bool = true
) -> Dictionary:
	if grid == null or not grid.is_cell_valid(start_cell) or available_movement_feet < 0:
		return {}
	var search: Dictionary = _run_search(
		grid,
		start_cell,
		occupied_cells,
		environment,
		state,
		available_movement_feet,
		dragging_target,
		allow_jumps,
		PlannedMovementSystem.INVALID_CELL
	)
	return (search.get("costs", {}) as Dictionary).duplicate()


func evaluate_path(
	grid: BattleGrid,
	path: Array[Vector2i],
	occupied_cells: Dictionary,
	environment: CombatEnvironment,
	state: CombatantState,
	available_movement_feet: int,
	dragging_target: bool = false
) -> Dictionary:
	if grid == null or path.is_empty():
		return _failure("Маршрут пуст.")
	var total_cost: int = 0
	var jump_indices: Array[int] = []
	for index: int in range(1, path.size()):
		var from_cell: Vector2i = path[index - 1]
		var to_cell: Vector2i = path[index]
		if not grid.is_cell_valid(to_cell) or _is_blocked(grid, to_cell, occupied_cells, environment):
			return _failure("Маршрут проходит через занятую или заблокированную клетку.")
		var delta: Vector2i = to_cell - from_cell
		var distance_cells: int = maxi(absi(delta.x), absi(delta.y))
		var is_jump: bool = distance_cells > 1
		if is_jump:
			if not _jump_transition_is_valid(grid, from_cell, to_cell, occupied_cells, environment, state, dragging_target):
				return _failure("Прыжок в маршруте больше недоступен.")
			jump_indices.append(index)
		else:
			if distance_cells != 1:
				return _failure("Маршрут содержит разрыв.")
			if delta.x != 0 and delta.y != 0 and _diagonal_corner_blocked(grid, from_cell, delta, occupied_cells, environment):
				return _failure("Нельзя пройти по диагонали через закрытый угол.")
		total_cost += movement_cost_for_transition(grid, from_cell, to_cell, environment, state, dragging_target, is_jump)
		if total_cost > available_movement_feet:
			return _failure("Маршрут превышает оставшийся запас перемещения.")
	return {
		"reachable": true,
		"path": path.duplicate(),
		"cost_feet": total_cost,
		"jump_indices": jump_indices,
		"reason": ""
	}


func movement_cost_for_transition(
	grid: BattleGrid,
	from_cell: Vector2i,
	to_cell: Vector2i,
	environment: CombatEnvironment,
	state: CombatantState,
	dragging_target: bool = false,
	is_jump: bool = false
) -> int:
	if is_jump:
		var distance_cells: int = maxi(absi(to_cell.x - from_cell.x), absi(to_cell.y - from_cell.y))
		var jump_cost: int = maxi(distance_cells, 1) * BASE_STEP_FEET
		return jump_cost * (2 if dragging_target else 1)
	return movement_cost_for_cell(grid, to_cell, environment, state, dragging_target)


func movement_cost_for_cell(
	grid: BattleGrid,
	cell: Vector2i,
	environment: CombatEnvironment,
	state: CombatantState,
	dragging_target: bool = false
) -> int:
	var destination: Vector2 = grid.cell_to_world_center(cell)
	var difficult: bool = environment != null and environment.is_difficult_position(destination)
	var crawling: bool = state != null and state.has_condition("prone")
	var cost: int = _rules.movement_cost_feet(BASE_STEP_FEET, state, difficult, crawling)
	if dragging_target:
		cost *= 2
	return cost


const INVALID_CELL: Vector2i = Vector2i(-99999, -99999)


func _run_search(
	grid: BattleGrid,
	start_cell: Vector2i,
	occupied_cells: Dictionary,
	environment: CombatEnvironment,
	state: CombatantState,
	available_movement_feet: int,
	dragging_target: bool,
	allow_jumps: bool,
	stop_cell: Vector2i
) -> Dictionary:
	var frontier: Array[Vector2i] = [start_cell]
	var costs: Dictionary = {start_cell: 0}
	var previous: Dictionary = {}
	while not frontier.is_empty():
		var current: Vector2i = _extract_lowest_cost(frontier, costs)
		if stop_cell != INVALID_CELL and current == stop_cell:
			break
		for transition: Dictionary in _transitions_from(
			grid,
			current,
			occupied_cells,
			environment,
			state,
			dragging_target,
			allow_jumps
		):
			var next_cell: Vector2i = transition.get("cell", INVALID_CELL) as Vector2i
			if next_cell == INVALID_CELL:
				continue
			var candidate_cost: int = int(costs.get(current, 0)) + int(transition.get("cost", BASE_STEP_FEET))
			if candidate_cost > available_movement_feet:
				continue
			if not costs.has(next_cell) or candidate_cost < int(costs[next_cell]):
				costs[next_cell] = candidate_cost
				previous[next_cell] = {
					"cell": current,
					"jump": bool(transition.get("jump", false))
				}
				if not frontier.has(next_cell):
					frontier.append(next_cell)
	return {"costs": costs, "previous": previous}


func _transitions_from(
	grid: BattleGrid,
	current: Vector2i,
	occupied_cells: Dictionary,
	environment: CombatEnvironment,
	state: CombatantState,
	dragging_target: bool,
	allow_jumps: bool
) -> Array[Dictionary]:
	var transitions: Array[Dictionary] = []
	for direction: Vector2i in DIRECTIONS:
		var next_cell: Vector2i = current + direction
		if grid.is_cell_valid(next_cell) and not _is_blocked(grid, next_cell, occupied_cells, environment):
			if direction.x == 0 or direction.y == 0 or not _diagonal_corner_blocked(grid, current, direction, occupied_cells, environment):
				transitions.append({
					"cell": next_cell,
					"cost": movement_cost_for_transition(grid, current, next_cell, environment, state, dragging_target, false),
					"jump": false
				})
		if not allow_jumps or not _can_jump(state, dragging_target) or environment == null:
			continue
		var landing: Vector2i = environment.get_jump_landing_cell(grid, current, direction, occupied_cells)
		if landing == CombatEnvironment.INVALID_CELL or _is_blocked(grid, landing, occupied_cells, environment):
			continue
		transitions.append({
			"cell": landing,
			"cost": movement_cost_for_transition(grid, current, landing, environment, state, dragging_target, true),
			"jump": true
		})
	return transitions


func _can_jump(state: CombatantState, dragging_target: bool) -> bool:
	if dragging_target:
		return false
	if state == null:
		return true
	return not state.has_condition("prone") and not state.has_condition("grappled") and not state.has_condition("restrained")


func _jump_transition_is_valid(
	grid: BattleGrid,
	from_cell: Vector2i,
	to_cell: Vector2i,
	occupied_cells: Dictionary,
	environment: CombatEnvironment,
	state: CombatantState,
	dragging_target: bool
) -> bool:
	if environment == null or not _can_jump(state, dragging_target):
		return false
	var delta: Vector2i = to_cell - from_cell
	var direction := Vector2i(signi(delta.x), signi(delta.y))
	if direction == Vector2i.ZERO:
		return false
	return environment.get_jump_landing_cell(grid, from_cell, direction, occupied_cells) == to_cell


func _is_blocked(grid: BattleGrid, cell: Vector2i, occupied_cells: Dictionary, environment: CombatEnvironment) -> bool:
	if occupied_cells.has(cell):
		return true
	return environment != null and environment.is_cell_blocked(grid, cell)


func _diagonal_corner_blocked(
	grid: BattleGrid,
	current: Vector2i,
	direction: Vector2i,
	occupied_cells: Dictionary,
	environment: CombatEnvironment
) -> bool:
	var horizontal: Vector2i = current + Vector2i(direction.x, 0)
	var vertical: Vector2i = current + Vector2i(0, direction.y)
	return _is_blocked(grid, horizontal, occupied_cells, environment) and _is_blocked(grid, vertical, occupied_cells, environment)


func _extract_lowest_cost(frontier: Array[Vector2i], costs: Dictionary) -> Vector2i:
	var best_index: int = 0
	var best_cost: int = int(costs.get(frontier[0], 0))
	for index: int in range(1, frontier.size()):
		var candidate_cost: int = int(costs.get(frontier[index], 0))
		if candidate_cost < best_cost:
			best_cost = candidate_cost
			best_index = index
	var result: Vector2i = frontier[best_index]
	frontier.remove_at(best_index)
	return result


func _reconstruct_path(previous: Dictionary, start_cell: Vector2i, destination_cell: Vector2i) -> Dictionary:
	var reversed_path: Array[Vector2i] = [destination_cell]
	var reversed_jump_flags: Array[bool] = []
	var current: Vector2i = destination_cell
	while current != start_cell:
		if not previous.has(current):
			return {"path": [], "jump_indices": []}
		var link: Dictionary = previous[current] as Dictionary
		reversed_jump_flags.append(bool(link.get("jump", false)))
		current = link.get("cell", start_cell) as Vector2i
		reversed_path.append(current)
	reversed_path.reverse()
	reversed_jump_flags.reverse()
	var jump_indices: Array[int] = []
	for flag_index: int in range(reversed_jump_flags.size()):
		if reversed_jump_flags[flag_index]:
			jump_indices.append(flag_index + 1)
	return {"path": reversed_path, "jump_indices": jump_indices}


func _failure(reason: String) -> Dictionary:
	return {"reachable": false, "path": [], "cost_feet": 0, "jump_indices": [], "reason": reason}
