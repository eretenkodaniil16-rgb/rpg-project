extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const POSITION_EPSILON: float = 0.01

var _has_failed: bool = false


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
	if not bool(game.call("combat_start_preserves_world_positions_for_testing")):
		_fail("Guard-post runtime does not declare authoritative world positions.")
		return

	# Use the actual live patrol placement. Starting initiative must not normalize,
	# center or otherwise move any participant before its own turn executes.
	var caretaker_before: Vector2 = caretaker.global_position
	var guard_before: Vector2 = guard.global_position
	var player_before: Vector2 = player.global_position
	game.call("_start_turn_based_combat", caretaker)
	if not bool(game.call("is_turn_based_combat_active")):
		_fail("Combat did not start from the authored guard-post placement.")
		return
	_assert_position("Caretaker", caretaker.global_position, caretaker_before)
	_assert_position("Service guard", guard.global_position, guard_before)
	_assert_position("Player", player.global_position, player_before)
	if _has_failed:
		return
	var turn_system: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	var initiative_ids: Array[String] = []
	for entry: Dictionary in turn_system.entries:
		if bool(entry.get("is_player", false)):
			continue
		var actor: Node = entry.get("node") as Node
		if is_instance_valid(actor) and actor.has_method("get_actor_id"):
			initiative_ids.append(str(actor.call("get_actor_id")))
	if "caretaker" not in initiative_ids or "service_guard" not in initiative_ids:
		_fail("First-room initiative roster is incomplete: %s" % JSON.stringify(initiative_ids))
		return
	turn_system.stop_combat()
	game.set("_enemy_turn_running", false)
	game.set("_active_combat_encounter_id", "")
	if player.has_method("set_turn_based_mode"):
		player.call("set_turn_based_mode", false)

	# Distinct world positions may legitimately map to the same coarse grid cell.
	# The transition must preserve them rather than teleport one participant to a
	# nearest free cell, which was the source of the observed guard jump.
	var occupied: Dictionary = {}
	var shared_cell: Vector2i = game.call(
		"_nearest_walkable_cell",
		grid,
		Vector2(690.0, 360.0),
		occupied
	) as Vector2i
	var center: Vector2 = grid.cell_to_world_center(shared_cell)
	caretaker.global_position = center + Vector2(-22.0, 0.0)
	guard.global_position = center + Vector2(22.0, 0.0)
	player.global_position = center + Vector2(0.0, 34.0)
	state.set("player_position", player.global_position)
	caretaker_before = caretaker.global_position
	guard_before = guard.global_position
	player_before = player.global_position
	if grid.world_to_cell(caretaker_before) != grid.world_to_cell(guard_before):
		_fail("Overlap fixture did not place both NPCs in one logical cell.")
		return
	game.call("_snap_combatants_to_cells")
	_assert_position("Same-cell caretaker", caretaker.global_position, caretaker_before)
	_assert_position("Same-cell service guard", guard.global_position, guard_before)
	_assert_position("Same-cell player", player.global_position, player_before)
	if _has_failed:
		return

	print("Combat transition preserves authored, patrol and same-cell world positions exactly.")
	game.queue_free()
	await process_frame
	quit(0)


func _assert_position(label: String, actual: Vector2, expected: Vector2) -> void:
	if actual.distance_to(expected) > POSITION_EPSILON:
		_fail("%s moved at combat start: %s -> %s" % [label, str(expected), str(actual)])


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
