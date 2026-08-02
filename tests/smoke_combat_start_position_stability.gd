extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const POSITION_EPSILON: float = 0.01


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	state.call("new_game")
	state.set("player_character", _make_hero())

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	var game: Node = packed.instantiate() if packed != null else null
	if game == null:
		_fail("Game scene could not be instantiated.")
		return
	root.add_child(game)
	for _frame: int in range(24):
		await process_frame

	var player: CharacterBody2D = game.get_node_or_null("Player") as CharacterBody2D
	var caretaker: Node2D = game.get_node_or_null("Caretaker") as Node2D
	var room: GuardPostTwoRoomVisibility = game.get_node_or_null("StealthTestRoom") as GuardPostTwoRoomVisibility
	var grid: BattleGrid = game.get_tree().get_first_node_in_group("battle_grid") as BattleGrid
	if player == null or caretaker == null or room == null or grid == null:
		_fail("Combat-start position fixtures are incomplete.")
		return
	var guard: Node2D = room.get_patrol_observer() as Node2D
	if guard == null:
		_fail("Service guard is missing.")
		return

	await _verify_valid_positions_remain_exact(game, grid, player, caretaker, guard, state)
	if _has_failed:
		return
	_verify_boundary_and_overlap_normalization(game, grid, player, caretaker, guard, state)
	if _has_failed:
		return

	print("Combat start preserves valid enemy positions and normalizes only invalid or conflicting placements.")
	game.queue_free()
	await process_frame
	quit(0)


var _has_failed: bool = false


func _verify_valid_positions_remain_exact(
	game: Node,
	grid: BattleGrid,
	player: CharacterBody2D,
	caretaker: Node2D,
	guard: Node2D,
	state: Node
) -> void:
	var occupied: Dictionary = {}
	var caretaker_cell: Vector2i = game.call(
		"_nearest_walkable_cell",
		grid,
		Vector2(690.0, 360.0),
		occupied
	) as Vector2i
	occupied[caretaker_cell] = caretaker
	var guard_cell: Vector2i = game.call(
		"_nearest_walkable_cell",
		grid,
		Vector2(820.0, 560.0),
		occupied
	) as Vector2i
	occupied[guard_cell] = guard
	var player_cell: Vector2i = game.call(
		"_nearest_walkable_cell",
		grid,
		Vector2(620.0, 360.0),
		occupied
	) as Vector2i

	var safe_offset := Vector2(10.0, 9.0)
	caretaker.global_position = grid.cell_to_world_center(caretaker_cell) + safe_offset
	guard.global_position = grid.cell_to_world_center(guard_cell) + Vector2(-9.0, 10.0)
	player.global_position = grid.cell_to_world_center(player_cell) + Vector2(8.0, -9.0)
	state.set("player_position", player.global_position)
	var caretaker_before: Vector2 = caretaker.global_position
	var guard_before: Vector2 = guard.global_position
	var player_before: Vector2 = player.global_position

	if caretaker.has_method("enter_combat_hostile"):
		caretaker.call("enter_combat_hostile")
	if guard.has_method("enter_combat_hostile"):
		guard.call("enter_combat_hostile")
	game.call("_start_turn_based_combat", caretaker)
	if not bool(game.call("is_turn_based_combat_active")):
		_fail("Combat did not start for the stable-position test.")
		return
	if caretaker.global_position.distance_to(caretaker_before) > POSITION_EPSILON:
		_fail("Caretaker moved despite already occupying a valid interior cell position.")
		return
	if guard.global_position.distance_to(guard_before) > POSITION_EPSILON:
		_fail("Service guard moved despite already occupying a valid interior cell position.")
		return
	if player.global_position.distance_to(player_before) > POSITION_EPSILON:
		_fail("Player moved despite already occupying a valid non-conflicting position.")
		return

	var turn_system: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	turn_system.stop_combat()
	game.set("_enemy_turn_running", false)
	game.set("_active_combat_encounter_id", "")
	if player.has_method("set_turn_based_mode"):
		player.call("set_turn_based_mode", false)


func _verify_boundary_and_overlap_normalization(
	game: Node,
	grid: BattleGrid,
	player: CharacterBody2D,
	caretaker: Node2D,
	guard: Node2D,
	state: Node
) -> void:
	var occupied: Dictionary = {}
	var enemy_origin: Vector2i = game.call(
		"_nearest_walkable_cell",
		grid,
		Vector2(690.0, 360.0),
		occupied
	) as Vector2i
	var cell_size: float = grid.get_cell_size()
	var field: Rect2 = grid.get_field_rect()
	var enemy_cell_local_origin: Vector2 = field.position + Vector2(enemy_origin) * cell_size
	var boundary_position: Vector2 = grid.to_global(
		enemy_cell_local_origin + Vector2(1.0, cell_size * 0.5)
	)
	caretaker.global_position = boundary_position
	player.global_position = grid.cell_to_world_center(enemy_origin)
	state.set("player_position", player.global_position)

	# Keep the second hostile participant in a separate valid position so the
	# normalization result is deterministic.
	occupied[enemy_origin] = caretaker
	var guard_cell: Vector2i = game.call(
		"_nearest_walkable_cell",
		grid,
		Vector2(820.0, 560.0),
		occupied
	) as Vector2i
	guard.global_position = grid.cell_to_world_center(guard_cell) + Vector2(9.0, 9.0)

	var expected_enemy_cell: Vector2i = game.call(
		"_nearest_walkable_cell",
		grid,
		boundary_position,
		{}
	) as Vector2i
	game.call("_snap_combatants_to_cells")
	var caretaker_cell_after: Vector2i = grid.world_to_cell(caretaker.global_position)
	var player_cell_after: Vector2i = grid.world_to_cell(player.global_position)
	if caretaker_cell_after != expected_enemy_cell:
		_fail("Boundary-position enemy was not moved to its nearest valid cell.")
		return
	if caretaker.global_position.distance_to(grid.cell_to_world_center(expected_enemy_cell)) > POSITION_EPSILON:
		_fail("Boundary-position enemy was not centered after required normalization.")
		return
	if player_cell_after == caretaker_cell_after:
		_fail("Player and enemy still share one cell after combat-start normalization.")
		return
	if guard.global_position.distance_to(grid.cell_to_world_center(guard_cell) + Vector2(9.0, 9.0)) > POSITION_EPSILON:
		_fail("Unrelated valid guard position changed during overlap normalization.")
		return


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.create_legacy_default()
	hero.character_name = "Проверяющий позиции"
	hero.level = 5
	hero.maximum_health = 100
	hero.current_health = 100
	return hero


func _fail(message: String) -> void:
	if _has_failed:
		return
	_has_failed = true
	push_error(message)
	quit(1)
