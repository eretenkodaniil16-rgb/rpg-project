extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const EPSILON: float = 0.05


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState is missing.")
		return
	state.call("new_game")
	state.set("player_character", PlayerCharacter.create_legacy_default())
	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	var game: Node = packed.instantiate() if packed != null else null
	if game == null:
		_fail("Game scene could not be instantiated.")
		return
	root.add_child(game)
	for _frame: int in range(24):
		await process_frame

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var caretaker: Node2D = game.get_node_or_null("Caretaker") as Node2D
	var room: Node = game.get_node_or_null("StealthTestRoom")
	var grid: BattleGrid = get_first_node_in_group("battle_grid") as BattleGrid
	var guard: Node2D = room.call("get_patrol_observer") as Node2D if room != null else null
	if player == null or caretaker == null or guard == null or grid == null:
		_fail("Combat position fixtures are incomplete.")
		return
	if not bool(game.call("combat_start_uses_stable_cell_normalization_for_testing")):
		_fail("Stable combat cell normalization is not active.")
		return

	var before: Dictionary = {
		player: player.global_position,
		caretaker: caretaker.global_position,
		guard: guard.global_position
	}
	game.call("_start_turn_based_combat", caretaker)
	if not bool(game.call("is_turn_based_combat_active")):
		_fail("Combat did not start.")
		return
	_assert_combat_positions([player, caretaker, guard], before, grid, grid.get_cell_size() * 1.5)
	if caretaker.global_position.distance_to(before[caretaker] as Vector2) <= EPSILON:
		_fail("Caretaker was left between combat cell centres.")
		return

	var turn_system: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	turn_system.stop_combat()
	game.set("_enemy_turn_running", false)
	if player.has_method("set_turn_based_mode"):
		player.call("set_turn_based_mode", false)

	var shared_cell: Vector2i = grid.world_to_cell(Vector2(690.0, 360.0))
	var shared_center: Vector2 = grid.cell_to_world_center(shared_cell)
	player.global_position = shared_center + Vector2(0.0, 20.0)
	caretaker.global_position = shared_center + Vector2(-20.0, -16.0)
	guard.global_position = shared_center + Vector2(20.0, -16.0)
	before = {
		player: player.global_position,
		caretaker: caretaker.global_position,
		guard: guard.global_position
	}
	game.call("_snap_combatants_to_cells")
	_assert_combat_positions([player, caretaker, guard], before, grid, grid.get_cell_size() * 1.8)

	print("Combatants are centred in unique nearby cells without long-distance teleportation.")
	game.queue_free()
	await process_frame
	quit(0)


func _assert_combat_positions(actors: Array, before: Dictionary, grid: BattleGrid, maximum_shift: float) -> void:
	var occupied: Dictionary = {}
	for value: Variant in actors:
		var actor: Node2D = value as Node2D
		var cell: Vector2i = grid.world_to_cell(actor.global_position)
		var center: Vector2 = grid.cell_to_world_center(cell)
		if actor.global_position.distance_to(center) > EPSILON:
			_fail("Actor is not centred in cell %s." % str(cell))
			return
		if occupied.has(cell):
			_fail("Two actors occupy cell %s." % str(cell))
			return
		occupied[cell] = true
		var old_position: Vector2 = before[actor] as Vector2
		if old_position.distance_to(actor.global_position) > maximum_shift:
			_fail("Actor moved farther than a local cell correction.")
			return


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
