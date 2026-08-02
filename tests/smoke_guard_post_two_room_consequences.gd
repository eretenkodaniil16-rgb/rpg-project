extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const EXPECTED_RUNTIME: String = "res://scripts/game/game_guard_post_player_feedback_runtime.gd"
const FIRST_ROOM_ID: String = "vault_guard_post_01"
const SECOND_ROOM_ID: String = "vault_inner_watch_01"
const INNER_GATE_BLOCKER_ID: String = "inner_watch_gate_blocker"

var _save_path: String = ""


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	_save_path = ProjectSettings.globalize_path("user://savegame.json")
	await _run_peaceful_route(state)
	await _run_violent_route(state)
	if FileAccess.file_exists(_save_path):
		DirAccess.remove_absolute(_save_path)
	print("Two-room peaceful authorization and violent reinforcement consequences passed.")
	quit(0)


func _run_peaceful_route(state: Node) -> void:
	_reset_state(state)
	var game: Node = await _spawn_game()
	if game == null:
		return
	var fixtures: Dictionary = _fixtures(game)
	if fixtures.is_empty():
		game.queue_free()
		return
	var player: Node2D = fixtures.get("player") as Node2D
	var room: GuardPostTwoRoomVisibility = fixtures.get("room") as GuardPostTwoRoomVisibility
	var marksman: Node = fixtures.get("marksman") as Node
	var mage: Node = fixtures.get("mage") as Node
	var gate: StealthDoor = fixtures.get("gate") as StealthDoor

	player.global_position = Vector2(620.0, 360.0)
	state.set("player_position", player.global_position)
	game.call("_evaluate_guard_post_state")
	state.call("set_flag", "caretaker_convinced", true)
	for _frame: int in range(4):
		await process_frame
	var first_state: Dictionary = state.call("get_encounter_state", FIRST_ROOM_ID) as Dictionary
	if str(first_state.get("resolution_id", "")) != "peaceful_passage":
		_fail("Negotiation did not resolve the first room peacefully.")
		return
	if str(game.call("get_first_room_outcome_for_testing")) != "peaceful" or gate.get_door_state() != "open":
		_fail("Peaceful outcome did not persist or open the inner gate.")
		return
	if bool(marksman.call("is_combat_participant_active")) or bool(mage.call("is_combat_participant_active")):
		_fail("Inner guards became combatants after peaceful authorization.")
		return
	if marksman.is_in_group("combat_targets") or mage.is_in_group("combat_targets"):
		_fail("Authorized inner guards remained hostile targets.")
		return

	player.global_position = Vector2(room.get_inner_partition_global_x() + 96.0, 360.0)
	state.set("player_position", player.global_position)
	game.call("_evaluate_guard_post_state")
	await process_frame
	var second_state: Dictionary = state.call("get_encounter_state", SECOND_ROOM_ID) as Dictionary
	if str(second_state.get("resolution_id", "")) != "authorized_passage":
		_fail("Inner guards did not honor the caretaker authorization.")
		return
	var turn_system: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	if turn_system.active:
		_fail("Peaceful entry into the inner room started combat.")
		return
	game.queue_free()
	await process_frame


func _run_violent_route(state: Node) -> void:
	_reset_state(state)
	var game: Node = await _spawn_game()
	if game == null:
		return
	var fixtures: Dictionary = _fixtures(game)
	if fixtures.is_empty():
		game.queue_free()
		return
	var player: Node2D = fixtures.get("player") as Node2D
	var caretaker: Node = fixtures.get("caretaker") as Node
	var guard: Node = fixtures.get("guard") as Node
	var room: GuardPostTwoRoomVisibility = fixtures.get("room") as GuardPostTwoRoomVisibility
	var marksman: Node = fixtures.get("marksman") as Node
	var mage: Node = fixtures.get("mage") as Node
	var gate: StealthDoor = fixtures.get("gate") as StealthDoor
	var environment: CombatEnvironment = fixtures.get("environment") as CombatEnvironment
	var grid: BattleGrid = fixtures.get("grid") as BattleGrid

	var gate_edges: Array[Dictionary] = environment.get_edge_blocker_edges_for_testing(INNER_GATE_BLOCKER_ID)
	if gate.get_door_state() != "locked" or gate_edges.is_empty():
		_fail("Inner gate is not locked and registered before first-room resolution.")
		return
	var edge: Dictionary = gate_edges[0]
	var left_cell: Vector2i = edge.get("a", CombatEnvironment.INVALID_CELL) as Vector2i
	var right_cell: Vector2i = edge.get("b", CombatEnvironment.INVALID_CELL) as Vector2i
	if not environment.is_transition_blocked(grid, left_cell, right_cell):
		_fail("Locked inner gate does not block the room transition.")
		return

	player.global_position = Vector2(620.0, 360.0)
	state.set("player_position", player.global_position)
	game.call("_evaluate_guard_post_state")
	game.call("_start_turn_based_combat", caretaker)
	await process_frame
	var turn_system: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	if not turn_system.active or not bool(guard.call("is_combat_participant_active")):
		_fail("Caretaker and service guard did not start first-room combat together.")
		return
	if bool(marksman.call("is_combat_participant_active")) or bool(mage.call("is_combat_participant_active")):
		_fail("Inner guards joined through the sealed partition.")
		return

	turn_system.stop_combat()
	game.set("_active_combat_encounter_id", "")
	game.call("resolve_first_room_for_testing", "guards_defeated")
	if str(game.call("get_first_room_outcome_for_testing")) != "combat" or gate.get_door_state() != "open":
		_fail("Violent first-room consequence was not persisted or did not open the gate.")
		return
	if environment.is_transition_blocked(grid, left_cell, right_cell):
		_fail("Opened inner gate still blocks movement.")
		return

	player.global_position = Vector2(room.get_inner_partition_global_x() + 96.0, 360.0)
	state.set("player_position", player.global_position)
	game.call("_evaluate_guard_post_state")
	for _frame: int in range(4):
		await process_frame
	if not turn_system.active or str(game.call("get_active_combat_encounter_id_for_testing")) != SECOND_ROOM_ID:
		_fail("Violent entry did not start the second-room encounter immediately.")
		return
	if not bool(marksman.call("is_combat_participant_active")) or not bool(mage.call("is_combat_participant_active")):
		_fail("Marksman and mage were not both activated.")
		return
	if not _turn_contains_actor(turn_system, marksman) or not _turn_contains_actor(turn_system, mage):
		_fail("Marksman or mage is missing from second-room initiative.")
		return
	game.queue_free()
	await process_frame


func _spawn_game() -> Node:
	var game: Node = (load(GAME_SCENE) as PackedScene).instantiate()
	root.add_child(game)
	for _frame: int in range(40):
		await process_frame
	var game_script: Script = game.get_script() as Script
	if game_script == null or game_script.resource_path != EXPECTED_RUNTIME:
		_fail("Game scene does not use the hide-to-pursuit guard post runtime.")
		game.queue_free()
		return null
	return game


func _fixtures(game: Node) -> Dictionary:
	var room: GuardPostTwoRoomVisibility = game.get_node_or_null("StealthTestRoom") as GuardPostTwoRoomVisibility
	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var caretaker: Node = game.get_node_or_null("Caretaker")
	var environment: CombatEnvironment = get_first_node_in_group("combat_environment") as CombatEnvironment
	var grid: BattleGrid = game.call("_get_battle_grid") as BattleGrid
	if room == null or player == null or caretaker == null or environment == null or grid == null:
		_fail("Two-room fixtures are incomplete.")
		return {}
	var guard: Node = room.get_patrol_observer()
	var marksman: Node = room.get_training_marksman()
	var mage: Node = room.get_training_mage()
	var gate: StealthDoor = room.get_inner_gate()
	if guard == null or marksman == null or mage == null or gate == null:
		_fail("Two-room actors or inner gate are missing.")
		return {}
	return {"room": room, "player": player, "caretaker": caretaker, "guard": guard, "marksman": marksman, "mage": mage, "gate": gate, "environment": environment, "grid": grid}


func _reset_state(state: Node) -> void:
	if FileAccess.file_exists(_save_path):
		DirAccess.remove_absolute(_save_path)
	state.call("new_game")
	state.set("player_character", _make_hero())


func _turn_contains_actor(turn_system: TurnBasedCombatSystem, actor: Node) -> bool:
	for entry: Dictionary in turn_system.entries:
		if entry.get("node") == actor:
			return true
	return false


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель двух комнат"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.level = 5
	hero.maximum_health = 90
	hero.current_health = 90
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)