extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const EXPECTED_RUNTIME: String = "res://scripts/game/game_guard_post_two_room_runtime.gd"
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
	print("Two-room guard post peaceful authorization and violent reinforcement consequences passed.")
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
	var room: Node = fixtures.get("room") as Node
	var marksman: Node2D = fixtures.get("marksman") as Node2D
	var mage: Node2D = fixtures.get("mage") as Node2D
	var gate: Node = fixtures.get("gate") as Node
	var gate_x: float = float(room.call("get_inner_partition_global_x"))

	player.global_position = Vector2(620.0, 360.0)
	state.set("player_position", player.global_position)
	game.call("_evaluate_guard_post_state")
	if str(state.call("get_encounter_status", FIRST_ROOM_ID)) != EncounterSystem.STATUS_ACTIVE:
		_fail("Entering the first room did not activate its encounter.")
		game.queue_free()
		return
	state.call("set_flag", "caretaker_convinced", true)
	game.call("_evaluate_guard_post_state")
	var first_state: Dictionary = state.call("get_encounter_state", FIRST_ROOM_ID) as Dictionary
	if str(first_state.get("resolution_id", "")) != "peaceful_passage":
		_fail("Negotiation did not resolve the first room peacefully.")
		game.queue_free()
		return
	if str(game.call("get_first_room_outcome_for_testing")) != "peaceful":
		_fail("Peaceful first-room consequence was not persisted.")
		game.queue_free()
		return
	if str(gate.call("get_door_state")) != "open":
		_fail("The inner gate did not open after the caretaker authorized passage.")
		game.queue_free()
		return
	if bool(marksman.call("is_combat_participant_active")) or bool(mage.call("is_combat_participant_active")):
		_fail("Inner guards became combatants after a peaceful agreement.")
		game.queue_free()
		return
	if marksman.is_in_group("combat_targets") or mage.is_in_group("combat_targets"):
		_fail("Authorized inner guards remained selectable as hostile targets.")
		game.queue_free()
		return

	player.global_position = Vector2(gate_x + 96.0, 360.0)
	state.set("player_position", player.global_position)
	game.call("_evaluate_guard_post_state")
	var second_state: Dictionary = state.call("get_encounter_state", SECOND_ROOM_ID) as Dictionary
	if str(second_state.get("resolution_id", "")) != "authorized_passage":
		_fail("Marksman and mage did not peacefully honor the caretaker's authorization.")
		game.queue_free()
		return
	var turn_system: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	if turn_system != null and turn_system.active:
		_fail("Peaceful entry into the second room started combat.")
		game.queue_free()
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
	var marksman: Node2D = fixtures.get("marksman") as Node2D
	var mage: Node2D = fixtures.get("mage") as Node2D
	var room: Node = fixtures.get("room") as Node
	var gate: Node = fixtures.get("gate") as Node
	var environment: CombatEnvironment = fixtures.get("environment") as CombatEnvironment
	var grid: BattleGrid = fixtures.get("grid") as BattleGrid
	var gate_x: float = float(room.call("get_inner_partition_global_x"))

	if caretaker.global_position.x >= gate_x or guard.global_position.x >= gate_x:
		_fail("Caretaker or patrol guard is not located in the first room.")
		game.queue_free()
		return
	if marksman.global_position.x <= gate_x or mage.global_position.x <= gate_x:
		_fail("Marksman or mage is not located in the second room.")
		game.queue_free()
		return
	if str(gate.call("get_door_state")) != "locked":
		_fail("The inner gate is not locked before the first room is resolved.")
		game.queue_free()
		return
	var gate_edges: Array[Dictionary] = environment.get_edge_blocker_edges_for_testing(INNER_GATE_BLOCKER_ID)
	if gate_edges.is_empty():
		_fail("The inner gate edge blocker is missing.")
		game.queue_free()
		return
	var edge: Dictionary = gate_edges[0]
	var left_cell: Vector2i = edge.get("a", CombatEnvironment.INVALID_CELL) as Vector2i
	var right_cell: Vector2i = edge.get("b", CombatEnvironment.INVALID_CELL) as Vector2i
	if not environment.is_transition_blocked(grid, left_cell, right_cell):
		_fail("The locked inner gate does not block transition between rooms.")
		game.queue_free()
		return

	player.global_position = Vector2(620.0, 360.0)
	state.set("player_position", player.global_position)
	game.call("_evaluate_guard_post_state")
	game.call("_start_turn_based_combat", caretaker)
	await process_frame
	var turn_system: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	if turn_system == null or not turn_system.active:
		_fail("Combat did not start in the first room.")
		game.queue_free()
		return
	if not bool(guard.call("is_combat_participant_active")):
		_fail("The patrol guard did not join the caretaker in first-room combat.")
		game.queue_free()
		return
	if bool(marksman.call("is_combat_participant_active")) or bool(mage.call("is_combat_participant_active")):
		_fail("Marksman or mage incorrectly joined combat through the sealed inner gate.")
		game.queue_free()
		return
	if _turn_contains_actor(turn_system, marksman) or _turn_contains_actor(turn_system, mage):
		_fail("Second-room actors were inserted into first-room initiative.")
		game.queue_free()
		return

	turn_system.stop_combat()
	game.set("_active_combat_encounter_id", "")
	game.call("resolve_first_room_for_testing", "guards_defeated")
	if str(game.call("get_first_room_outcome_for_testing")) != "combat":
		_fail("Violent first-room outcome was not persisted as combat.")
		game.queue_free()
		return
	if str(gate.call("get_door_state")) != "open":
		_fail("The inner gate did not open after the outer guards were defeated.")
		game.queue_free()
		return
	if environment.is_transition_blocked(grid, left_cell, right_cell):
		_fail("The opened inner gate still blocks movement into the second room.")
		game.queue_free()
		return

	player.global_position = Vector2(gate_x + 96.0, 360.0)
	state.set("player_position", player.global_position)
	game.call("_evaluate_guard_post_state")
	await process_frame
	if not turn_system.active:
		_fail("Entering the second room after first-room combat did not start combat immediately.")
		game.queue_free()
		return
	if str(game.call("get_active_combat_encounter_id_for_testing")) != SECOND_ROOM_ID:
		_fail("Immediate second-room combat uses the wrong encounter id.")
		game.queue_free()
		return
	if not bool(marksman.call("is_combat_participant_active")) or not bool(mage.call("is_combat_participant_active")):
		_fail("Marksman and mage did not both activate in the second room.")
		game.queue_free()
		return
	if not _turn_contains_actor(turn_system, marksman) or not _turn_contains_actor(turn_system, mage):
		_fail("Marksman and mage are missing from second-room initiative.")
		game.queue_free()
		return
	game.queue_free()
	await process_frame


func _spawn_game() -> Node:
	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	var game: Node = packed.instantiate() if packed != null else null
	if game == null:
		_fail("Two-room game scene could not be instantiated.")
		return null
	root.add_child(game)
	for _frame: int in range(40):
		await process_frame
	var script: Script = game.get_script() as Script
	if script == null or script.resource_path != EXPECTED_RUNTIME:
		_fail("Game scene does not use the two-room guard post runtime.")
		game.queue_free()
		return null
	game.set_process(false)
	return game


func _fixtures(game: Node) -> Dictionary:
	var room: Node = game.get_node_or_null("StealthTestRoom")
	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var caretaker: Node = game.get_node_or_null("Caretaker")
	var environment: CombatEnvironment = get_first_node_in_group("combat_environment") as CombatEnvironment
	var grid: BattleGrid = game.call("_get_battle_grid") as BattleGrid
	if room == null or player == null or caretaker == null or environment == null or grid == null:
		_fail("Two-room fixtures are incomplete.")
		return {}
	var guard: Node = room.call("get_patrol_observer")
	var marksman: Node2D = room.call("get_training_marksman") as Node2D
	var mage: Node2D = room.call("get_training_mage") as Node2D
	var gate: Node = room.call("get_inner_gate") if room.has_method("get_inner_gate") else null
	if guard == null or marksman == null or mage == null or gate == null:
		_fail("Two-room actors or inner gate are missing.")
		return {}
	return {
		"room": room,
		"player": player,
		"caretaker": caretaker,
		"guard": guard,
		"marksman": marksman,
		"mage": mage,
		"gate": gate,
		"environment": environment,
		"grid": grid
	}


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
	hero.maximum_health = 42
	hero.current_health = 42
	hero.hit_die_size = 10
	hero.hit_dice_maximum = 5
	hero.hit_dice_current = 5
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
