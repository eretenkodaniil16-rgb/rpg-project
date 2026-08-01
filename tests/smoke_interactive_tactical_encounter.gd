extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const EXPECTED_RUNTIME: String = "res://scripts/game/game_guard_post_two_room_runtime.gd"
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

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	var game: Node = packed.instantiate() if packed != null else null
	if game == null:
		_fail("Game scene could not be loaded.")
		return
	root.add_child(game)
	for _frame: int in range(35):
		await process_frame
	var game_script: Script = game.get_script() as Script
	if game_script == null or game_script.resource_path != EXPECTED_RUNTIME:
		_fail("Game scene does not use the two-room runtime.")
		return
	game.set_process(false)

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var caretaker: Node2D = game.get_node_or_null("Caretaker") as Node2D
	var room: Node = game.get_node_or_null("StealthTestRoom")
	var environment: CombatEnvironment = get_first_node_in_group("combat_environment") as CombatEnvironment
	var catalog_ui: ActionCatalogUI = game.get_node_or_null("Interface/ActionCatalogUI") as ActionCatalogUI
	var combat_message: Label = game.get_node_or_null("Interface/CombatMessageLabel") as Label
	var grid: BattleGrid = game.call("_get_battle_grid") as BattleGrid
	if player == null or caretaker == null or room == null or environment == null or catalog_ui == null or combat_message == null or grid == null:
		_fail("Interactive encounter fixtures are incomplete.")
		return
	var guard: Node2D = room.call("get_patrol_observer") as Node2D
	var marksman: Node2D = room.call("get_training_marksman") as Node2D
	var mage: Node2D = room.call("get_training_mage") as Node2D
	var door: Node = room.call("get_test_door") as Node
	if guard == null or marksman == null or mage == null or door == null:
		_fail("Guard-post actors or west service door are missing.")
		return
	var door_action_id: String = "%s%d" % [WORLD_ACTION_PREFIX, door.get_instance_id()]

	if combat_message.offset_top > 520.0 or combat_message.z_index <= catalog_ui.z_index:
		_fail("Command message is not positioned above the action catalog.")
		return
	game.call("show_combat_message", "Прыжок выполнен.", true)
	if combat_message.text != "Прыжок выполнен.":
		_fail("Gameplay notifications no longer reach the command message label.")
		return

	var targets_before: Array[Node] = game.call("_available_targets") as Array[Node]
	if targets_before.has(marksman) or targets_before.has(mage):
		_fail("Second-room guards are targetable through the sealed inner room.")
		return
	if bool(marksman.call("is_combat_participant_active")) or bool(mage.call("is_combat_participant_active")):
		_fail("Second-room guards activated before the player entered their room.")
		return

	game.call("_start_turn_based_combat", caretaker)
	await process_frame
	var turn_system: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	if turn_system == null or not turn_system.active:
		_fail("Combat did not start through the caretaker.")
		return
	if not bool(guard.call("is_combat_participant_active")):
		_fail("Service guard did not join first-room combat.")
		return
	if bool(marksman.call("is_combat_participant_active")) or bool(mage.call("is_combat_participant_active")):
		_fail("Second-room guards joined first-room combat through the partition.")
		return
	if not _turn_contains_actor(turn_system, caretaker) or not _turn_contains_actor(turn_system, guard):
		_fail("Caretaker and service guard are not both in first-room initiative.")
		return
	if _turn_contains_actor(turn_system, marksman) or _turn_contains_actor(turn_system, mage):
		_fail("Second-room guards were inserted into first-room initiative.")
		return

	game.call("force_player_turn_for_testing")
	game.set("_enemy_turn_running", false)
	if not turn_system.is_player_turn(player):
		_fail("Player turn could not be forced for interaction checks.")
		return

	var door_edges: Array[Dictionary] = environment.get_edge_blocker_edges_for_testing(DOOR_BLOCKER_ID)
	if door_edges.size() != 2:
		_fail("West service door edge registration is incomplete.")
		return
	var tested_edge: Dictionary = door_edges[0]
	var left_cell: Vector2i = tested_edge.get("a", CombatEnvironment.INVALID_CELL) as Vector2i
	var right_cell: Vector2i = tested_edge.get("b", CombatEnvironment.INVALID_CELL) as Vector2i
	if environment.is_cell_blocked(grid, left_cell) or environment.is_cell_blocked(grid, right_cell):
		_fail("Door occupies one of its adjacent cells.")
		return

	door.call("set_door_state", "closed", false)
	player.global_position = grid.cell_to_world_center(left_cell)
	state.set("player_position", player.global_position)
	for _frame: int in range(4):
		await process_frame
	if not bool(door.call("is_player_adjacent_for_testing")):
		_fail("Real proximity detection did not recognize the left adjacent cell.")
		return
	if not environment.is_transition_blocked(grid, left_cell, right_cell):
		_fail("Closed door does not block its cell edge.")
		return
	game.call("_refresh_action_catalog")
	await process_frame
	var world_entry: Dictionary = _find_action(catalog_ui.get_entries_for_testing(), door_action_id)
	if world_entry.is_empty() or not bool(world_entry.get("enabled", false)) or str(world_entry.get("label", "")) != "ОТКРЫТЬ ДВЕРЬ":
		_fail("Door cannot be opened through its specific mobile action-catalog entry.")
		return
	catalog_ui.call("_emit_action", door_action_id, str(world_entry.get("description", "")), true)
	await process_frame
	if str(door.call("get_door_state")) != "open" or environment.is_transition_blocked(grid, left_cell, right_cell):
		_fail("Door-specific catalog action did not open the door edge.")
		return
	if bool(door.call("can_perform_world_interaction")):
		_fail("Object interaction was not consumed for the current turn.")
		return

	var opening_round: int = turn_system.round_number
	for _step: int in range(turn_system.entries.size() + 2):
		turn_system.advance_turn()
		if turn_system.current_actor() == player and turn_system.round_number > opening_round:
			break
	if turn_system.current_actor() != player or turn_system.round_number <= opening_round:
		_fail("Could not advance to a fresh player interaction turn.")
		return
	game.set("_enemy_turn_running", false)
	player.global_position = grid.cell_to_world_center(right_cell)
	state.set("player_position", player.global_position)
	for _frame: int in range(4):
		await process_frame
	game.call("_refresh_action_catalog")
	await process_frame
	world_entry = _find_action(catalog_ui.get_entries_for_testing(), door_action_id)
	if world_entry.is_empty() or not bool(world_entry.get("enabled", false)) or str(world_entry.get("label", "")) != "ЗАКРЫТЬ ДВЕРЬ":
		_fail("Door cannot be closed from the opposite adjacent cell through its own entry.")
		return
	catalog_ui.call("_emit_action", door_action_id, str(world_entry.get("description", "")), true)
	await process_frame
	if str(door.call("get_door_state")) != "closed" or not environment.is_transition_blocked(grid, left_cell, right_cell):
		_fail("Reclosed door did not restore the blocked edge.")
		return

	turn_system.stop_combat()
	var initiative_overrides: Dictionary = {
		player.get_instance_id(): 10,
		marksman.get_instance_id(): 20
	}
	turn_system.start_combat(player, [marksman], 0, initiative_overrides)
	turn_system.force_current_actor_for_testing(marksman)
	var player_state: CombatantState = game.call("get_player_combat_state") as CombatantState
	var hero: PlayerCharacter = state.get("player_character") as PlayerCharacter
	if player_state == null or hero == null:
		_fail("Player state is unavailable for death-save flow.")
		return
	hero.current_health = 0
	player_state.enter_dying()
	game.set("_enemy_turn_running", false)
	game.call("_queue_dying_turn_recovery_if_needed")
	await process_frame
	var death_save_resolved: bool = (
		hero.current_health == 1
		or player_state.death_save_successes > 0
		or player_state.death_save_failures > 0
		or player_state.stable
		or player_state.dead
	)
	if not death_save_resolved:
		_fail("Initiative stalled at 0 HP instead of resolving a death saving throw.")
		return

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("First-room isolation, addressable two-sided door interaction, layered messages and dying-turn recovery passed.")
	quit(0)


func _turn_contains_actor(turn_system: TurnBasedCombatSystem, actor: Node) -> bool:
	for entry: Dictionary in turn_system.entries:
		if entry.get("node") == actor:
			return true
	return false


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
	hero.hit_die_size = 10
	hero.hit_dice_maximum = 5
	hero.hit_dice_current = 5
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)