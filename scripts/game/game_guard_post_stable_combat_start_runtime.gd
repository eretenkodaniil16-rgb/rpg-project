extends "res://scripts/game/game_guard_post_polish_runtime.gd"

const COMBAT_START_BOUNDARY_MARGIN_PIXELS: float = 6.0


func _snap_combatants_to_cells() -> void:
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return
	var occupied: Dictionary = {}
	# Enemies keep priority over the player. The old implementation snapped the
	# player first and could therefore push an NPC into a distant free cell when
	# combat began at close range.
	for enemy: Node2D in _combat_start_enemies():
		_place_combatant_for_combat_start(grid, enemy, occupied)
	_place_combatant_for_combat_start(grid, player, occupied)
	GameState.player_position = player.global_position


func _combat_start_enemies() -> Array[Node2D]:
	var result: Array[Node2D] = []
	for target: Node in _available_targets():
		if not target is Node2D or not is_instance_valid(target):
			continue
		if target.has_method("is_hostile") and not bool(target.call("is_hostile")):
			continue
		if target.has_method("is_combat_active") and not bool(target.call("is_combat_active")):
			continue
		result.append(target as Node2D)
	result.sort_custom(func(left: Node2D, right: Node2D) -> bool:
		return _actor_id(left) < _actor_id(right)
	)
	return result


func _place_combatant_for_combat_start(
	grid: BattleGrid,
	actor: Node2D,
	occupied: Dictionary
) -> Vector2i:
	if not is_instance_valid(actor):
		return Vector2i(-1, -1)
	var original_position: Vector2 = actor.global_position
	var original_cell: Vector2i = grid.world_to_cell(original_position)
	if _combat_start_position_can_remain(grid, original_position, original_cell, occupied):
		occupied[original_cell] = actor
		return original_cell
	var destination_cell: Vector2i = _nearest_walkable_cell(grid, original_position, occupied)
	actor.global_position = grid.cell_to_world_center(destination_cell)
	occupied[destination_cell] = actor
	return destination_cell


func _combat_start_position_can_remain(
	grid: BattleGrid,
	world_position: Vector2,
	cell: Vector2i,
	occupied: Dictionary
) -> bool:
	if not grid.is_cell_valid(cell) or occupied.has(cell):
		return false
	if _combat_environment != null and _combat_environment.is_cell_blocked(grid, cell):
		return false
	return not _position_is_near_cell_boundary(grid, world_position, cell)


func _position_is_near_cell_boundary(
	grid: BattleGrid,
	world_position: Vector2,
	cell: Vector2i
) -> bool:
	var cell_size: float = grid.get_cell_size()
	var field: Rect2 = grid.get_field_rect()
	var local_position: Vector2 = grid.to_local(world_position)
	var cell_origin: Vector2 = field.position + Vector2(cell) * cell_size
	var offset: Vector2 = local_position - cell_origin
	var boundary_distance: float = minf(
		minf(offset.x, cell_size - offset.x),
		minf(offset.y, cell_size - offset.y)
	)
	return boundary_distance <= COMBAT_START_BOUNDARY_MARGIN_PIXELS


func combat_start_boundary_margin_for_testing() -> float:
	return COMBAT_START_BOUNDARY_MARGIN_PIXELS
