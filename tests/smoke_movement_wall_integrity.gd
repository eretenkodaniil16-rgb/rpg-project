extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const EXPECTED_RUNTIME: String = "res://scripts/game/game_squad_tactical_plans_runtime.gd"


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
	for _frame: int in range(24):
		await process_frame
	var game_script: Script = game.get_script() as Script
	if game_script == null or game_script.resource_path != EXPECTED_RUNTIME:
		_fail("Game scene does not use squad tactical runtime.")
		return
	game.set_process(false)

	var grid: BattleGrid = game.call("_get_battle_grid") as BattleGrid
	var environment: CombatEnvironment = game.get_tree().get_first_node_in_group("combat_environment") as CombatEnvironment
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
		_fail("Walls, door or visible tactical squad are missing.")
		return

	for actor: Node2D in [marksman, mage]:
		if not actor.visible or not actor.is_in_group("combat_targets"):
			_fail("Training role is not visible or selectable: %s" % actor.name)
			return
		if actor.has_method("is_hostile") and not bool(actor.call("is_hostile")):
			_fail("Training role is not active in the encounter: %s" % actor.name)
			return

	var top_wall_cell: Vector2i = grid.world_to_cell(top_wall.global_position)
	var bottom_wall_cell: Vector2i = grid.world_to_cell(bottom_wall.global_position)
	if not environment.is_cell_blocked(grid, top_wall_cell) or not environment.is_cell_blocked(grid, bottom_wall_cell):
		_fail("Real partition walls are absent from the combat grid.")
		return
	var wall_origin: Vector2i = _nearest_open_left(grid, environment, top_wall_cell)
	if wall_origin == CombatEnvironment.INVALID_CELL:
		_fail("Could not find a valid wall jump origin.")
		return
	if environment.get_jump_landing_cell(grid, wall_origin, Vector2i.RIGHT, {}) != CombatEnvironment.INVALID_CELL:
		_fail("A solid room wall is still considered jumpable.")
		return

	var door_cell: Vector2i = grid.world_to_cell(door.global_position)
	door.call("set_door_state", "closed", false)
	await process_frame
	if not environment.is_cell_blocked(grid, door_cell):
		_fail("Closed door does not block grid movement.")
		return
	var planner := PlannedMovementSystem.new()
	var combatant_state := CombatantState.new()
	var closed_cases: int = 0
	var rows: int = floori(grid.get_field_rect().size.y / grid.get_cell_size())
	for row: int in range(rows):
		for direction_sign: int in [-1, 1]:
			var start_cell := Vector2i(2 if direction_sign > 0 else 4, row)
			var destination_cell := Vector2i(4 if direction_sign > 0 else 2, row)
			if not grid.is_cell_valid(start_cell) or not grid.is_cell_valid(destination_cell):
				continue
			if environment.is_cell_blocked(grid, start_cell) or environment.is_cell_blocked(grid, destination_cell):
				continue
			var closed_result: Dictionary = planner.build_path(grid, start_cell, destination_cell, {}, environment, combatant_state, 120, false, true)
			closed_cases += 1
			if bool(closed_result.get("reachable", false)):
				_fail("Planner crossed the sealed partition on row %d: %s" % [row, JSON.stringify(closed_result)])
				return
	if closed_cases < 10:
		_fail("Insufficient closed-wall simulation coverage: %d" % closed_cases)
		return

	door.call("set_door_state", "open", false)
	await process_frame
	if environment.is_cell_blocked(grid, door_cell):
		_fail("Open door remains blocked in the combat grid.")
		return
	var open_start := Vector2i(2, door_cell.y)
	var open_destination := Vector2i(4, door_cell.y)
	var open_result: Dictionary = planner.build_path(grid, open_start, open_destination, {}, environment, combatant_state, 60, false, true)
	if not bool(open_result.get("reachable", false)):
		_fail("Planner cannot use the opened doorway: %s" % JSON.stringify(open_result))
		return
	for path_cell: Vector2i in open_result.get("path", []) as Array[Vector2i]:
		if path_cell != open_start and environment.is_cell_blocked(grid, path_cell):
			_fail("Opened-door route contains a blocked cell: %s" % path_cell)
			return

	door.call("set_door_state", "closed", false)
	await process_frame
	player.global_position = grid.cell_to_world_center(Vector2i(2, door_cell.y))
	var player_before: Vector2 = player.global_position
	if player.has_method("set_facing_direction"):
		player.call("set_facing_direction", Vector2.RIGHT)
	game.call("_on_exploration_jump_requested")
	for _frame: int in range(12):
		await process_frame
	if not player.global_position.is_equal_approx(player_before):
		_fail("Exploration jump crossed a closed door or partition wall.")
		return

	guard.call("activate_combat_participant")
	guard.global_position = grid.cell_to_world_center(Vector2i(2, door_cell.y))
	var candidates: Array = game.call("_build_combat_ai_reachable_candidates", guard, 60) as Array
	if candidates.size() < 3:
		_fail("AI route simulation produced too few candidates.")
		return
	for candidate_value: Variant in candidates:
		if not candidate_value is Dictionary:
			continue
		var candidate: Dictionary = candidate_value as Dictionary
		var candidate_cell: Vector2i = candidate.get("cell", Vector2i(-1, -1)) as Vector2i
		if candidate_cell.x >= 4:
			_fail("AI planned through the closed partition: %s" % JSON.stringify(candidate))
			return

	var low_barricade_position: Vector2 = environment.get_environment_object_position("low_barricade")
	var low_barricade_cell: Vector2i = grid.world_to_cell(low_barricade_position)
	var low_origin := low_barricade_cell + Vector2i.LEFT
	var legal_landing: Vector2i = environment.get_jump_landing_cell(grid, low_origin, Vector2i.RIGHT, {})
	if legal_landing == CombatEnvironment.INVALID_CELL:
		_fail("Explicitly jumpable low barricade lost its legal jump.")
		return

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Real walls, doors, jump restrictions, visible mage/marksman and AI route simulations passed.")
	quit(0)


func _nearest_open_left(grid: BattleGrid, environment: CombatEnvironment, cell: Vector2i) -> Vector2i:
	for distance: int in range(1, 5):
		var candidate: Vector2i = cell + Vector2i.LEFT * distance
		if grid.is_cell_valid(candidate) and not environment.is_cell_blocked(grid, candidate):
			return candidate
	return CombatEnvironment.INVALID_CELL


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
