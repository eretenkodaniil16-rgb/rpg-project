extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const DOOR_BLOCKER_ID: String = "west_service_door_blocker"
const WORLD_ACTION_PREFIX: String = "world_interact__"


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

	var game: Node = (load(GAME_SCENE) as PackedScene).instantiate()
	root.add_child(game)
	for _frame: int in range(35):
		await process_frame
	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var caretaker: Node = game.get_node_or_null("Caretaker")
	var room: GuardPostTwoRoomVisibility = game.get_node_or_null("StealthTestRoom") as GuardPostTwoRoomVisibility
	var environment: CombatEnvironment = get_first_node_in_group("combat_environment") as CombatEnvironment
	var catalog: ActionCatalogUI = game.get_node_or_null("Interface/ActionCatalogUI") as ActionCatalogUI
	var message: Label = game.get_node_or_null("Interface/CombatMessageLabel") as Label
	var grid: BattleGrid = game.call("_get_battle_grid") as BattleGrid
	if player == null or caretaker == null or room == null or environment == null or catalog == null or message == null or grid == null:
		_fail("Interactive encounter fixtures are incomplete.")
		return
	var guard: Node = room.get_patrol_observer()
	var marksman: Node = room.get_training_marksman()
	var mage: Node = room.get_training_mage()
	var door: StealthDoor = room.get_test_door()
	if guard == null or marksman == null or mage == null or door == null:
		_fail("Guard-post actors or service door are missing.")
		return

	if message.offset_top > 520.0 or message.z_index <= catalog.z_index:
		_fail("Command message is not positioned above the action catalog.")
		return
	var targets_before: Array[Node] = game.call("_available_targets") as Array[Node]
	if targets_before.has(marksman) or targets_before.has(mage):
		_fail("Inner-room guards are targetable through the sealed partition.")
		return

	game.call("_start_turn_based_combat", caretaker)
	await process_frame
	var turn_system: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	if not turn_system.active or not bool(guard.call("is_combat_participant_active")):
		_fail("First-room combat did not include the caretaker and service guard.")
		return
	if bool(marksman.call("is_combat_participant_active")) or bool(mage.call("is_combat_participant_active")):
		_fail("Inner guards joined first-room combat through the partition.")
		return
	game.call("force_player_turn_for_testing")
	game.set("_enemy_turn_running", false)

	var door_edges: Array[Dictionary] = environment.get_edge_blocker_edges_for_testing(DOOR_BLOCKER_ID)
	if door_edges.size() != 2:
		_fail("Service door edge registration is incomplete.")
		return
	var edge: Dictionary = door_edges[0]
	var left_cell: Vector2i = edge.get("a", CombatEnvironment.INVALID_CELL) as Vector2i
	var right_cell: Vector2i = edge.get("b", CombatEnvironment.INVALID_CELL) as Vector2i
	if environment.is_cell_blocked(grid, left_cell) or environment.is_cell_blocked(grid, right_cell):
		_fail("Door occupies an adjacent cell instead of its edge.")
		return

	door.set_door_state("closed", false)
	player.global_position = grid.cell_to_world_center(left_cell)
	state.set("player_position", player.global_position)
	for _frame: int in range(5):
		await physics_frame
		await process_frame
	game.call("_refresh_action_catalog")
	await process_frame
	var door_action_id: String = "%s%d" % [WORLD_ACTION_PREFIX, door.get_instance_id()]
	var door_entry: Dictionary = _find_action(catalog.get_entries_for_testing(), door_action_id)
	if door_entry.is_empty() or not bool(door_entry.get("enabled", false)) or str(door_entry.get("label", "")) != "ОТКРЫТЬ ДВЕРЬ":
		_fail("Door cannot be opened through its address-specific catalog action.")
		return
	catalog.call("_emit_action", door_action_id, str(door_entry.get("description", "")), true)
	await process_frame
	if door.get_door_state() != "open" or environment.is_transition_blocked(grid, left_cell, right_cell):
		_fail("Door action did not open the edge.")
		return
	if door.can_perform_world_interaction():
		_fail("Door interaction was not consumed for the current turn.")
		return

	var opening_round: int = turn_system.round_number
	for _step: int in range(turn_system.entries.size() + 3):
		turn_system.advance_turn()
		if turn_system.current_actor() == player and turn_system.round_number > opening_round:
			break
	if turn_system.current_actor() != player:
		_fail("Could not advance to a fresh player interaction turn.")
		return
	game.set("_enemy_turn_running", false)
	player.global_position = grid.cell_to_world_center(right_cell)
	state.set("player_position", player.global_position)
	for _frame: int in range(5):
		await physics_frame
		await process_frame
	game.call("_refresh_action_catalog")
	await process_frame
	door_entry = _find_action(catalog.get_entries_for_testing(), door_action_id)
	if door_entry.is_empty() or str(door_entry.get("label", "")) != "ЗАКРЫТЬ ДВЕРЬ":
		_fail("Door cannot be closed from the opposite adjacent cell.")
		return
	catalog.call("_emit_action", door_action_id, str(door_entry.get("description", "")), true)
	await process_frame
	if door.get_door_state() != "closed" or not environment.is_transition_blocked(grid, left_cell, right_cell):
		_fail("Reclosed door did not restore its blocked edge.")
		return

	turn_system.stop_combat()
	var initiative_overrides: Dictionary = {player.get_instance_id(): 10, marksman.get_instance_id(): 20}
	turn_system.start_combat(player, [marksman], 0, initiative_overrides)
	turn_system.force_current_actor_for_testing(marksman)
	var player_state: CombatantState = game.call("get_player_combat_state") as CombatantState
	var hero: PlayerCharacter = state.get("player_character") as PlayerCharacter
	hero.current_health = 0
	player_state.enter_dying()
	game.set("_enemy_turn_running", false)
	game.call("_queue_dying_turn_recovery_if_needed")
	await process_frame
	var resolved: bool = hero.current_health == 1 or player_state.death_save_successes > 0 or player_state.death_save_failures > 0 or player_state.stable or player_state.dead
	if not resolved:
		_fail("Initiative stalled at 0 HP instead of resolving a death save.")
		return

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("First-room isolation, address-specific door actions and dying-turn recovery passed.")
	quit(0)


func _find_action(catalog: Dictionary, action_id: String) -> Dictionary:
	var values: Variant = catalog.get("action", [])
	if not values is Array:
		return {}
	for value: Variant in values as Array:
		if value is Dictionary and str((value as Dictionary).get("id", "")) == action_id:
			return (value as Dictionary).duplicate(true)
	return {}


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель взаимодействий"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.level = 5
	hero.maximum_health = 42
	hero.current_health = 42
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
