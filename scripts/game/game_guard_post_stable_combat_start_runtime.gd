extends "res://scripts/game/game_guard_post_polish_runtime_core.gd"

const INVALID_COMBAT_CELL: Vector2i = Vector2i(-99999, -99999)


func _capture_exploration_combat_candidates(trigger_target: Node) -> Array[Node]:
	var result: Array[Node] = super._capture_exploration_combat_candidates(trigger_target)
	var trigger_actor_id: String = _actor_id(trigger_target)
	var roster: Array[String] = []
	if trigger_actor_id in FIRST_ROOM_PARLEY_ACTOR_IDS:
		roster = FIRST_ROOM_PARLEY_ACTOR_IDS
	elif trigger_actor_id in SECOND_ROOM_ACTOR_IDS:
		roster = SECOND_ROOM_ACTOR_IDS
	for actor_id: String in roster:
		var actor: Node = _find_guard_post_actor(actor_id)
		if not _actor_can_join_encounter_roster(actor) or result.has(actor):
			continue
		result.append(actor)
	return result


func _snap_combatants_to_cells() -> void:
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return
	var occupied: Dictionary = {}
	if is_instance_valid(player):
		_place_actor_in_stable_combat_cell(player, grid, occupied)
		GameState.player_position = player.global_position
	for target: Node in _available_targets():
		if target is Node2D and is_instance_valid(target):
			_place_actor_in_stable_combat_cell(target as Node2D, grid, occupied)


func _place_actor_in_stable_combat_cell(actor: Node2D, grid: BattleGrid, occupied: Dictionary) -> Vector2i:
	var destination_cell: Vector2i = _nearest_available_combat_cell(grid, actor.global_position, occupied)
	if destination_cell == INVALID_COMBAT_CELL:
		return INVALID_COMBAT_CELL
	# Preserve the actor's current logical cell whenever possible and only align
	# the world position to its centre. This resolves line/intersection placement
	# without reassigning a distant patrol actor to an unrelated cell.
	actor.global_position = grid.cell_to_world_center(destination_cell)
	occupied[destination_cell] = actor
	return destination_cell


func _nearest_available_combat_cell(grid: BattleGrid, world_position: Vector2, occupied: Dictionary) -> Vector2i:
	var field_rect: Rect2 = grid.get_field_rect()
	var cell_size: float = maxf(grid.get_cell_size(), 1.0)
	var columns: int = maxi(floori(field_rect.size.x / cell_size), 1)
	var rows: int = maxi(floori(field_rect.size.y / cell_size), 1)
	var origin: Vector2i = grid.world_to_cell(world_position)
	origin.x = clampi(origin.x, 0, columns - 1)
	origin.y = clampi(origin.y, 0, rows - 1)
	if _combat_cell_is_available(grid, origin, occupied):
		return origin

	var maximum_radius: int = maxi(columns, rows)
	for radius: int in range(1, maximum_radius + 1):
		var best_cell: Vector2i = INVALID_COMBAT_CELL
		var best_distance: float = INF
		for x_offset: int in range(-radius, radius + 1):
			for y_offset: int in range(-radius, radius + 1):
				if maxi(absi(x_offset), absi(y_offset)) != radius:
					continue
				var candidate: Vector2i = origin + Vector2i(x_offset, y_offset)
				if not _combat_cell_is_available(grid, candidate, occupied):
					continue
				var distance: float = grid.cell_to_world_center(candidate).distance_squared_to(world_position)
				if distance < best_distance:
					best_distance = distance
					best_cell = candidate
		if best_cell != INVALID_COMBAT_CELL:
			return best_cell
	return INVALID_COMBAT_CELL


func _combat_cell_is_available(grid: BattleGrid, cell: Vector2i, occupied: Dictionary) -> bool:
	if not grid.is_cell_valid(cell) or occupied.has(cell):
		return false
	if _combat_environment != null and _combat_environment.is_cell_blocked(grid, cell):
		return false
	return true


func combat_start_uses_stable_cell_normalization_for_testing() -> bool:
	return true


func combat_start_preserves_world_positions_for_testing() -> bool:
	# Compatibility probe for obsolete tests. Exact sub-cell coordinates are no
	# longer preserved because every combatant must occupy one concrete cell.
	return false
