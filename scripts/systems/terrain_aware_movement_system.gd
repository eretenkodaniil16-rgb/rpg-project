class_name TerrainAwareMovementSystem
extends PlannedMovementSystem

var _terrain_rules: SrdCombatRules = SrdCombatRules.new()


func movement_cost_for_cell(
	grid: BattleGrid,
	cell: Vector2i,
	environment: CombatEnvironment,
	state: CombatantState,
	dragging_target: bool = false
) -> int:
	var destination: Vector2 = grid.cell_to_world_center(cell)
	var difficult: bool = environment != null and environment.is_difficult_position(destination)
	if state != null and state.ignores_nonmagical_difficult_terrain:
		difficult = false
	var crawling: bool = state != null and state.has_condition("prone")
	var cost: int = _terrain_rules.movement_cost_feet(BASE_STEP_FEET, state, difficult, crawling)
	if dragging_target:
		cost *= 2
	return cost
