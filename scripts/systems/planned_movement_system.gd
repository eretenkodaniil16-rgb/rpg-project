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
	dragging_target: bool = false
) -> Dictionary:
	if grid == null or not grid.is_cell_valid(start_cell) or not grid.is_cell_valid(destination_cell):
		return _failure("Клетка находится за пределами поля.")
	if destination_cell != start_cell and _is_blocked(grid, destination_cell, occupied_cells, environment):
		return _failure("Выбранная клетка занята или перекрыта препятствием.")
	if destination_cell == start_cell:
		return {"reachable": true, "path": [start_cell], "cost_feet": 0, "reason": ""}

	var frontier: Array[Vector2i] = [start_cell]
	var costs: Dictionary = {start_cell: 0}
	var previous: Dictionary = {}

	while not frontier.is_empty():
		var current: Vector2i = _extract_lowest_cost(frontier, costs)
		if current == destination_cell:
			break
		for direction: Vector2i in DIRECTIONS:
			var next_cell: Vector2i = current + direction
			if not grid.is_cell_valid(next_cell):
				continue
			if _is_blocked(grid, next_cell, occupied_cells, environment):
				continue
			if direction.x != 0 and direction.y != 0 and _diagonal_corner_blocked(grid, current, direction, occupied_cells, environment):
				continue
			var step_cost: int = movement_cost_for_cell(grid, next_cell, environment, state, dragging_target)
			var candidate_cost: int = int(costs.get(current, 0)) + step_cost
			if candidate_cost > available_movement_feet:
				continue
			if not costs.has(next_cell) or candidate_cost < int(costs[next_cell]):
				costs[next_cell] = candidate_cost
				previous[next_cell] = current
				if not frontier.has(next_cell):
					frontier.append(next_cell)

	if not costs.has(destination_cell):
		return _failure("До выбранной клетки нет доступного пути в пределах оставшегося перемещения.")
	var path: Array[Vector2i] = _reconstruct_path(previous, start_cell, destination_cell)
	return {
		"reachable": true,
		"path": path,
		"cost_feet": int(costs[destination_cell]),
		"reason": ""
	}


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


func _reconstruct_path(previous: Dictionary, start_cell: Vector2i, destination_cell: Vector2i) -> Array[Vector2i]:
	var reversed_path: Array[Vector2i] = [destination_cell]
	var current: Vector2i = destination_cell
	while current != start_cell:
		if not previous.has(current):
			return []
		current = previous[current] as Vector2i
		reversed_path.append(current)
	reversed_path.reverse()
	return reversed_path


func _failure(reason: String) -> Dictionary:
	return {"reachable": false, "path": [], "cost_feet": 0, "reason": reason}
