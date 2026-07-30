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
		_fail("Game scene does not use the squad tactical runtime.")
		return
	game.set_process(false)

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var caretaker: Node2D = game.get_node_or_null("Caretaker") as Node2D
	var room: Node = game.get_node_or_null("StealthTestRoom")
	var environment: CombatEnvironment = game.get_tree().get_first_node_in_group("combat_environment") as CombatEnvironment
	var catalog_ui: ActionCatalogUI = game.get_node_or_null("Interface/ActionCatalogUI") as ActionCatalogUI
	var grid: BattleGrid = game.call("_get_battle_grid") as BattleGrid
	if player == null or caretaker == null or room == null or environment == null or catalog_ui == null or grid == null:
		_fail("Interactive encounter fixtures are incomplete.")
		return
	var guard: Node2D = room.call("get_patrol_observer") as Node2D
	var marksman: Node2D = room.call("get_training_marksman") as Node2D
	var mage: Node2D = room.call("get_training_mage") as Node2D
	var door: Node = room.call("get_test_door") as Node
	if guard == null or marksman == null or mage == null or door == null:
		_fail("Guard, marksman, mage or door is missing from the playable scene.")
		return

	if bool(marksman.call("is_combat_participant_active")) or bool(mage.call("is_combat_participant_active")):
		_fail("Dormant tactical roles joined combat before provocation.")
		return
	var targets: Array[Node] = game.call("_available_targets") as Array[Node]
	if not targets.has(marksman) or not targets.has(mage):
		_fail("Visible tactical roles are absent from player target cycling.")
		return
	if not bool(game.call("_target_is_valid", marksman)) or not bool(game.call("_target_is_valid", mage)):
		_fail("Visible tactical roles are rejected by target validation.")
		return
	game.call("_set_selected_target", marksman)
	if game.get("_selected_target") != marksman:
		_fail("Marksman could not be selected as the current target.")
		return

	game.call("_start_turn_based_combat", caretaker)
	await process_frame
	var turn_system: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	if turn_system == null or not turn_system.active:
		_fail("Combat did not start through the caretaker.")
		return
	if not bool(marksman.call("is_combat_participant_active")) or not bool(mage.call("is_combat_participant_active")):
		_fail("Caretaker provocation did not activate the complete tactical squad.")
		return
	if not bool(marksman.call("is_hostile")) or not bool(mage.call("is_hostile")):
		_fail("Activated tactical squad is not hostile.")
		return
	if not _turn_contains_actor(turn_system, caretaker) or not _turn_contains_actor(turn_system, marksman) or not _turn_contains_actor(turn_system, mage):
		_fail("Caretaker, marksman and mage were not all added to initiative.")
		return

	game.call("force_player_turn_for_testing")
	if not turn_system.is_player_turn(player):
		_fail("Player turn could not be forced for interaction checks.")
		return

	door.call("set_door_state", "closed", false)
	door.call("_on_body_entered", player)
	await process_frame
	var door_cell: Vector2i = grid.world_to_cell((door as Node2D).global_position)
	if not environment.is_cell_blocked(grid, door_cell):
		_fail("Closed door is not registered as a combat blocker.")
		return
	game.call("_refresh_action_catalog")
	await process_frame
	var world_entry: Dictionary = _find_action(catalog_ui.get_entries_for_testing(), "world_interact")
	if world_entry.is_empty() or not bool(world_entry.get("enabled", false)):
		_fail("Door interaction is missing or disabled in the combat world group.")
		return
	if str(world_entry.get("label", "")) != "ОТКРЫТЬ ДВЕРЬ":
		_fail("Combat door action has an unexpected label: %s" % JSON.stringify(world_entry))
		return

	catalog_ui.action_requested.emit("world_interact")
	await process_frame
	if str(door.call("get_door_state")) != "open":
		_fail("Catalog world action did not open the door during the player turn.")
		return
	if environment.is_cell_blocked(grid, door_cell):
		_fail("Opened combat door remains blocked in the movement grid.")
		return
	if bool(door.call("can_perform_world_interaction")):
		_fail("Object interaction was not consumed for the current turn.")
		return

	catalog_ui.action_requested.emit("world_interact")
	await process_frame
	if str(door.call("get_door_state")) != "open":
		_fail("The same combat turn allowed a second door interaction.")
		return
	game.call("_refresh_action_catalog")
	await process_frame
	world_entry = _find_action(catalog_ui.get_entries_for_testing(), "world_interact")
	if world_entry.is_empty() or bool(world_entry.get("enabled", true)):
		_fail("Consumed combat door interaction remains enabled in the catalog.")
		return

	door.call("_on_body_exited", player)
	turn_system.stop_combat()
	var initiative_overrides: Dictionary = {
		player.get_instance_id(): 10,
		marksman.get_instance_id(): 20
	}
	turn_system.start_combat(player, [marksman], 0, initiative_overrides)
	turn_system.force_current_actor_for_testing(marksman)
	var player_state: CombatantState = game.call("get_player_combat_state") as CombatantState
	if player_state == null:
		_fail("Player combat state is unavailable for death-save flow.")
		return
	state.get("player_character").current_health = 0
	player_state.enter_dying()
	game.set("_enemy_turn_running", false)
	game.call("_queue_dying_turn_recovery_if_needed")
	await process_frame
	var death_save_resolved: bool = (
		state.get("player_character").current_health == 1
		or player_state.death_save_successes > 0
		or player_state.death_save_failures > 0
		or player_state.stable
		or player_state.dead
	)
	if not death_save_resolved:
		_fail("Initiative stalled at 0 HP instead of resolving a death saving throw.")
		return

	turn_system.stop_combat()
	state.get("player_character").current_health = state.get("player_character").maximum_health
	player_state.recover_from_zero_hit_points()
	door.call("_on_body_entered", player)
	door.call("interact")
	await process_frame
	if str(door.call("get_door_state")) != "closed":
		_fail("Exploration door interaction no longer works outside combat.")
		return
	door.call("_on_body_exited", player)

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Caretaker-linked tactical squad, catalog-routed combat door interaction and dying turn recovery passed.")
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
