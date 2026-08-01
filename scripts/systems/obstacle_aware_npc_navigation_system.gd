class_name ObstacleAwareNpcNavigationSystem
extends NpcNavigationSystem

const ACTOR_RADIUS_PIXELS: float = 22.0
const PATH_NODE_LIMIT: int = 768
const INVALID_CELL: Vector2i = Vector2i(-99999, -99999)
const DIRECTIONS: Array[Vector2i] = [
	Vector2i(1, 0),
	Vector2i(-1, 0),
	Vector2i(0, 1),
	Vector2i(0, -1),
	Vector2i(1, 1),
	Vector2i(1, -1),
	Vector2i(-1, 1),
	Vector2i(-1, -1)
]
const OCCUPANT_GROUPS: Array[String] = [
	"player",
	"combat_targets",
	"context_action_targets",
	"corpse_targets"
]


func move_actor(actor: Node2D, target_position: Vector2, speed_pixels: float, delta: float) -> Dictionary:
	if actor == null or not is_instance_valid(actor) or not actor.is_inside_tree():
		return _movement_result(false, false, true, Vector2.ZERO, actor.global_position if actor != null else Vector2.ZERO)
	var grid: BattleGrid = actor.get_tree().get_first_node_in_group("battle_grid") as BattleGrid
	var environment: CombatEnvironment = actor.get_tree().get_first_node_in_group("combat_environment") as CombatEnvironment
	if grid == null or environment == null:
		return super.move_actor(actor, target_position, speed_pixels, delta)

	if environment.is_position_blocked(actor.global_position, ACTOR_RADIUS_PIXELS):
		actor.global_position = resolve_safe_position(actor, actor.global_position)

	var occupied: Dictionary = occupied_cells(actor, grid)
	var start_cell: Vector2i = grid.world_to_cell(actor.global_position)
	var target_cell: Vector2i = nearest_safe_cell(grid, environment, grid.world_to_cell(target_position), occupied)
	if not grid.is_cell_valid(start_cell) or not grid.is_cell_valid(target_cell):
		return _movement_result(false, false, true, Vector2.ZERO, actor.global_position)
	var path: Array[Vector2i] = build_cell_path(grid, environment, start_cell, target_cell, occupied)
	if path.is_empty():
		return _movement_result(false, false, true, Vector2.ZERO, actor.global_position)

	var next_position: Vector2 = target_position if path.size() == 1 else grid.cell_to_world_center(path[1])
	if path.size() == 1 and environment.is_position_blocked(next_position, ACTOR_RADIUS_PIXELS):
		next_position = grid.cell_to_world_center(start_cell)
	var direction: Vector2 = next_position - actor.global_position
	var previous_position: Vector2 = actor.global_position
	if direction.length_squared() > 0.0001:
		var intended: Vector2 = actor.global_position.move_toward(
			next_position,
			maxf(speed_pixels, 0.0) * maxf(delta, 0.0)
		)
		var intended_cell: Vector2i = grid.world_to_cell(intended)
		if (
			grid.is_cell_valid(intended_cell)
			and not environment.is_position_blocked(intended, ACTOR_RADIUS_PIXELS)
			and not environment.is_transition_blocked(grid, start_cell, intended_cell)
		):
			actor.global_position = intended
	var moved: bool = actor.global_position.distance_squared_to(previous_position) > 0.0001
	var reached: bool = actor.global_position.distance_to(target_position) <= DEFAULT_TARGET_DISTANCE
	return _movement_result(
		moved,
		reached,
		not moved and not reached,
		direction.normalized() if direction.length_squared() > 0.0001 else Vector2.ZERO,
		next_position
	)


func resolve_safe_position(actor: Node2D, requested_position: Vector2) -> Vector2:
	if actor == null or not is_instance_valid(actor) or not actor.is_inside_tree():
		return requested_position
	var grid: BattleGrid = actor.get_tree().get_first_node_in_group("battle_grid") as BattleGrid
	var environment: CombatEnvironment = actor.get_tree().get_first_node_in_group("combat_environment") as CombatEnvironment
	if grid == null or environment == null:
		return requested_position
	var safe_cell: Vector2i = nearest_safe_cell(
		grid,
		environment,
		grid.world_to_cell(requested_position),
		occupied_cells(actor, grid)
	)
	return grid.cell_to_world_center(safe_cell) if grid.is_cell_valid(safe_cell) else actor.global_position


func build_world_path(actor: Node2D, target_position: Vector2) -> Array[Vector2]:
	var result: Array[Vector2] = []
	if actor == null or not is_instance_valid(actor) or not actor.is_inside_tree():
		return result
	var grid: BattleGrid = actor.get_tree().get_first_node_in_group("battle_grid") as BattleGrid
	var environment: CombatEnvironment = actor.get_tree().get_first_node_in_group("combat_environment") as CombatEnvironment
	if grid == null or environment == null:
		return result
	var occupied: Dictionary = occupied_cells(actor, grid)
	var start_cell: Vector2i = grid.world_to_cell(actor.global_position)
	var target_cell: Vector2i = nearest_safe_cell(grid, environment, grid.world_to_cell(target_position), occupied)
	var cells: Array[Vector2i] = build_cell_path(grid, environment, start_cell, target_cell, occupied)
	for cell: Vector2i in cells:
		result.append(grid.cell_to_world_center(cell))
	return result


func occupied_cells(excluded_actor: Node, grid: BattleGrid) -> Dictionary:
	var result: Dictionary = {}
	if grid == null or excluded_actor == null or not excluded_actor.is_inside_tree():
		return result
	var seen: Dictionary = {}
	for group_id: String in OCCUPANT_GROUPS:
		for candidate: Node in excluded_actor.get_tree().get_nodes_in_group(group_id):
			if not is_instance_valid(candidate) or candidate == excluded_actor or not candidate is Node2D:
				continue
			if candidate.has_method("is_combat_active") and not bool(candidate.call("is_combat_active")):
				continue
			var instance_id: int = candidate.get_instance_id()
			if seen.has(instance_id):
				continue
			seen[instance_id] = true
			var cell: Vector2i = grid.world_to_cell((candidate as Node2D).global_position)
			if grid.is_cell_valid(cell):
				result[cell] = candidate
	return result


func nearest_safe_cell(
	grid: BattleGrid,
	environment: CombatEnvironment,
	requested: Vector2i,
	occupied: Dictionary
) -> Vector2i:
	if _cell_is_safe(grid, environment, requested, occupied):
		return requested
	for radius: int in range(1, 12):
		for y: int in range(-radius, radius + 1):
			for x: int in range(-radius, radius + 1):
				if maxi(absi(x), absi(y)) != radius:
					continue
				var candidate: Vector2i = requested + Vector2i(x, y)
				if _cell_is_safe(grid, environment, candidate, occupied):
					return candidate
	return INVALID_CELL


func build_cell_path(
	grid: BattleGrid,
	environment: CombatEnvironment,
	start: Vector2i,
	target: Vector2i,
	occupied: Dictionary
) -> Array[Vector2i]:
	if grid == null or environment == null or not grid.is_cell_valid(start) or not grid.is_cell_valid(target):
		return []
	if start == target:
		return [start]
	var frontier: Array[Vector2i] = [start]
	var came_from: Dictionary = {start: start}
	var visited_count: int = 0
	while not frontier.is_empty() and visited_count < PATH_NODE_LIMIT:
		var current: Vector2i = frontier.pop_front()
		visited_count += 1
		for step: Vector2i in DIRECTIONS:
			var next: Vector2i = current + step
			if came_from.has(next) or not _cell_is_safe(grid, environment, next, occupied):
				continue
			if environment.is_transition_blocked(grid, current, next):
				continue
			if step.x != 0 and step.y != 0 and not _diagonal_is_safe(grid, environment, current, step, occupied):
				continue
			came_from[next] = current
			if next == target:
				return _reconstruct_path(came_from, start, target)
			frontier.append(next)
	return []


func _cell_is_safe(
	grid: BattleGrid,
	environment: CombatEnvironment,
	cell: Vector2i,
	occupied: Dictionary
) -> bool:
	if not grid.is_cell_valid(cell) or occupied.has(cell) or environment.is_cell_blocked(grid, cell):
		return false
	return not environment.is_position_blocked(grid.cell_to_world_center(cell), ACTOR_RADIUS_PIXELS)


func _diagonal_is_safe(
	grid: BattleGrid,
	environment: CombatEnvironment,
	origin: Vector2i,
	step: Vector2i,
	occupied: Dictionary
) -> bool:
	var horizontal: Vector2i = origin + Vector2i(step.x, 0)
	var vertical: Vector2i = origin + Vector2i(0, step.y)
	return (
		_cell_is_safe(grid, environment, horizontal, occupied)
		and _cell_is_safe(grid, environment, vertical, occupied)
		and not environment.is_transition_blocked(grid, origin, horizontal)
		and not environment.is_transition_blocked(grid, origin, vertical)
	)


func _reconstruct_path(came_from: Dictionary, start: Vector2i, target: Vector2i) -> Array[Vector2i]:
	var reversed: Array[Vector2i] = [target]
	var current: Vector2i = target
	while current != start and came_from.has(current):
		current = came_from[current] as Vector2i
		reversed.append(current)
	if reversed[reversed.size() - 1] != start:
		return []
	reversed.reverse()
	return reversed


func _movement_result(
	moved: bool,
	reached: bool,
	blocked: bool,
	direction: Vector2,
	next_position: Vector2
) -> Dictionary:
	return {
		"moved": moved,
		"reached": reached,
		"used_navigation": true,
		"blocked": blocked,
		"direction": direction,
		"next_position": next_position
	}
