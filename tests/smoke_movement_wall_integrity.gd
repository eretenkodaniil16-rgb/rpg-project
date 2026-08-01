extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const EXPECTED_RUNTIME: String = "res://scripts/game/game_guard_post_two_room_runtime.gd"
const TOP_WALL_ID: String = "west_partition_top"
const BOTTOM_WALL_ID: String = "west_partition_bottom"
const DOOR_BLOCKER_ID: String = "west_service_door_blocker"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	var save_path: String = ProjectSettings.globalize_path("user://savegame.json")
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	state.call("new_game")
	state.set("player_character", _make_hero())

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	if packed == null:
		_fail("Game scene could not be loaded.")
		return
	var game: Node = packed.instantiate()
	root.add_child(game)
	for _frame: int in range(35):
		await process_frame
	var game_script: Script = game.get_script() as Script
	if game_script == null or game_script.resource_path != EXPECTED_RUNTIME:
		_fail("Game scene does not use the two-room tactical runtime.")
		return
	game.set_process(false)

	var grid: BattleGrid = game.call("_get_battle_grid") as BattleGrid
	var environment: CombatEnvironment = get_first_node_in_group("combat_environment") as CombatEnvironment
	var room: Node = game.get_node_or_null("StealthTestRoom")
	var player: Node2D = game.get_node_or_null("Player") as Node2D
	if grid == null or environment == null or room == null or player == null:
		_fail("Movement integrity fixtures are incomplete.")
		return
	var top_wall: Node2D = room.get_node_or_null("WestPartitionTop") as Node2D
	var bottom_wall: Node2D = room.get_node_or_null("WestPartitionBottom") as Node2D
	var door: Node2D = room.call("get_test_door") as Node2D
	var guard: Node2D = room.call("get_patrol_observer") as Node2D
	var marksman: Node2D = room.call("get_training_marksman") as Node2D
	var mage: Node2D = room.call("get_training_mage") as Node2D
	if top_wall == null or bottom_wall == null or door == null or guard == null or marksman == null or mage == null:
		_fail("Walls, door or tactical actors are missing.")
		return

	for actor: Node2D in [marksman, mage]:
		if not actor.visible:
			_fail("Second-room role is not visible: %s" % actor.name)
			return
		if actor.is_in_group("combat_targets"):
			_fail("Second-room role is targetable through the sealed room: %s" % actor.name)
			return
		if actor.has_method("is_hostile") and bool(actor.call("is_hostile")):
			_fail("Second-room role became hostile before entry: %s" % actor.name)
			return
		if actor.is_in_group("stealth_alert_actors"):
			_fail("Sealed second-room role affects first-room stealth: %s" % actor.name)
			return

	if not _is_on_vertical_grid_edge(grid, top_wall.global_position.x):
		_fail("Top wall is not aligned with a vertical cell edge.")
		return
	if not _is_on_vertical_grid_edge(grid, bottom_wall.global_position.x):
		_fail("Bottom wall is not aligned with a vertical cell edge.")
		return
	if not _is_on_vertical_grid_edge(grid, door.global_position.x):
		_fail("Door is not aligned with a vertical cell edge.")
		return

	var top_edges: Array[Dictionary] = environment.get_edge_blocker_edges_for_testing(TOP_WALL_ID)
	var door_edges: Array[Dictionary] = environment.get_edge_blocker_edges_for_testing(DOOR_BLOCKER_ID)
	var bottom_edges: Array[Dictionary] = environment.get_edge_blocker_edges_for_testing(BOTTOM_WALL_ID)
	if top_edges.size() != 4 or door_edges.size() != 2 or bottom_edges.size() != 3:
		_fail("Partition edge coverage is incorrect: top=%d door=%d bottom=%d" % [top_edges.size(), door_edges.size(), bottom_edges.size()])
		return

	door.call("set_door_state", "closed", false)
	await process_frame
	var all_edges: Array[Dictionary] = []
	all_edges.append_array(top_edges)
	all_edges.append_array(door_edges)
	all_edges.append_array(bottom_edges)
	for edge: Dictionary in all_edges:
		var left_cell: Vector2i = edge.get("a", CombatEnvironment.INVALID_CELL) as Vector2i
		var right_cell: Vector2i = edge.get("b", CombatEnvironment.INVALID_CELL) as Vector2i
		if environment.is_cell_blocked(grid, left_cell) or environment.is_cell_blocked(grid, right_cell):
			_fail("A wall edge incorrectly occupies an adjacent cell: %s" % JSON.stringify(edge))
			return
		if not environment.is_transition_blocked(grid, left_cell, right_cell):
			_fail("Closed partition edge does not block movement: %s" % JSON.stringify(edge))
			return

	var wall_los_edge: Dictionary = top_edges[0]
	var wall_los_left: Vector2i = wall_los_edge.get("a", CombatEnvironment.INVALID_CELL) as Vector2i
	var wall_los_right: Vector2i = wall_los_edge.get("b", CombatEnvironment.INVALID_CELL) as Vector2i
	if environment.has_line_of_sight(grid.cell_to_world_center(wall_los_left), grid.cell_to_world_center(wall_los_right)):
		_fail("A solid wall edge does not block line of sight.")
		return
	var door_los_edge: Dictionary = door_edges[0]
	var door_los_left: Vector2i = door_los_edge.get("a", CombatEnvironment.INVALID_CELL) as Vector2i
	var door_los_right: Vector2i = door_los_edge.get("b", CombatEnvironment.INVALID_CELL) as Vector2i
	if environment.has_line_of_sight(grid.cell_to_world_center(door_los_left), grid.cell_to_world_center(door_los_right)):
		_fail("A closed door edge does not block line of sight.")
		return

	var planner := PlannedMovementSystem.new()
	var combatant_state := CombatantState.new()
	var doorway_edge: Dictionary = door_edges[0]
	var doorway_left: Vector2i = doorway_edge.get("a", CombatEnvironment.INVALID_CELL) as Vector2i
	var doorway_right: Vector2i = doorway_edge.get("b", CombatEnvironment.INVALID_CELL) as Vector2i
	var sealed_result: Dictionary = planner.build_path(grid, doorway_left, doorway_right, {}, environment, combatant_state, 200, false, true)
	if bool(sealed_result.get("reachable", false)):
		_fail("Planner crossed the fully sealed edge partition: %s" % JSON.stringify(sealed_result))
		return
	var direct_closed: Dictionary = planner.evaluate_path(grid, [doorway_left, doorway_right], {}, environment, combatant_state, 5, false)
	if bool(direct_closed.get("reachable", false)):
		_fail("Direct transition crossed the closed door edge.")
		return
	if environment.get_jump_landing_cell(grid, doorway_left, Vector2i.RIGHT, {}) != CombatEnvironment.INVALID_CELL:
		_fail("Jump crossed the closed door edge.")
		return
	var wall_edge: Dictionary = top_edges[0]
	var wall_left: Vector2i = wall_edge.get("a", CombatEnvironment.INVALID_CELL) as Vector2i
	if environment.get_jump_landing_cell(grid, wall_left, Vector2i.RIGHT, {}) != CombatEnvironment.INVALID_CELL:
		_fail("Jump crossed a solid wall edge.")
		return

	guard.call("activate_combat_participant")
	guard.global_position = grid.cell_to_world_center(doorway_left)
	var closed_candidates: Array = game.call("_build_combat_ai_reachable_candidates", guard, 60) as Array
	if closed_candidates.size() < 3:
		_fail("AI route simulation produced too few closed-side candidates.")
		return
	for candidate_value: Variant in closed_candidates:
		if not candidate_value is Dictionary:
			continue
		var candidate: Dictionary = candidate_value as Dictionary
		var candidate_cell: Vector2i = candidate.get("cell", Vector2i(-1, -1)) as Vector2i
		if candidate_cell.x >= doorway_right.x:
			_fail("AI planned through the closed edge partition: %s" % JSON.stringify(candidate))
			return

	door.call("set_door_state", "open", false)
	for _frame: int in range(3):
		await process_frame
	for edge: Dictionary in door_edges:
		var left_cell: Vector2i = edge.get("a", CombatEnvironment.INVALID_CELL) as Vector2i
		var right_cell: Vector2i = edge.get("b", CombatEnvironment.INVALID_CELL) as Vector2i
		if environment.is_transition_blocked(grid, left_cell, right_cell):
			_fail("Opened door still blocks its cell edge: %s" % JSON.stringify(edge))
			return
	if not environment.has_line_of_sight(grid.cell_to_world_center(door_los_left), grid.cell_to_world_center(door_los_right)):
		_fail("An opened door edge still blocks line of sight.")
		return
	var open_result: Dictionary = planner.build_path(grid, doorway_left, doorway_right, {}, environment, combatant_state, 10, false, true)
	if not bool(open_result.get("reachable", false)):
		_fail("Planner cannot cross the opened edge doorway: %s" % JSON.stringify(open_result))
		return
	var open_candidates: Array = game.call("_build_combat_ai_reachable_candidates", guard, 10) as Array
	var ai_crossed_open_door: bool = false
	for candidate_value: Variant in open_candidates:
		if candidate_value is Dictionary and (candidate_value as Dictionary).get("cell", CombatEnvironment.INVALID_CELL) == doorway_right:
			ai_crossed_open_door = true
			break
	if not ai_crossed_open_door:
		_fail("AI cannot use the opened edge doorway.")
		return

	var low_barricade_position: Vector2 = environment.get_environment_object_position("low_barricade")
	var low_barricade_cell: Vector2i = grid.world_to_cell(low_barricade_position)
	var low_origin := low_barricade_cell + Vector2i.LEFT
	var legal_landing: Vector2i = environment.get_jump_landing_cell(grid, low_origin, Vector2i.RIGHT, {})
	if legal_landing == CombatEnvironment.INVALID_CELL:
		_fail("Explicitly jumpable low barricade lost its legal jump.")
		return

	room.call("activate_inner_watch_combat")
	await process_frame
	for actor: Node2D in [marksman, mage]:
		if actor.has_method("is_hostile") and not bool(actor.call("is_hostile")):
			_fail("Inner-room activation did not make the tactical role hostile: %s" % actor.name)
			return
		if not actor.is_in_group("stealth_alert_actors") or not actor.is_in_group("combat_targets"):
			_fail("Active inner-room role did not join perception and targeting: %s" % actor.name)
			return

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Cell-edge walls, two-sided door traversal, jump restrictions, AI path parity and sealed inner roles passed.")
	quit(0)


func _is_on_vertical_grid_edge(grid: BattleGrid, world_x: float) -> bool:
	var local_x: float = grid.to_local(Vector2(world_x, 0.0)).x
	var edge_index: float = (local_x - grid.get_field_rect().position.x) / grid.get_cell_size()
	return is_equal_approx(edge_index, roundf(edge_index))


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель стен"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.level = 5
	hero.maximum_health = 42
	hero.current_health = 42
	hero.hit_die_size = 10
	hero.hit_dice_maximum = 5
	hero.hit_dice_current = 5
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
