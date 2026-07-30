extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const EXPECTED_RUNTIME: String = "res://scripts/game/game_interactive_tactical_runtime.gd"


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
		_fail("Game scene does not use the interactive tactical runtime.")
		return
	game.set_process(false)

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var room: Node = game.get_node_or_null("StealthTestRoom")
	var environment: CombatEnvironment = game.get_tree().get_first_node_in_group("combat_environment") as CombatEnvironment
	if player == null or room == null or environment == null:
		_fail("Interactive encounter fixtures are incomplete.")
		return
	var marksman: Node2D = room.call("get_training_marksman") as Node2D
	var mage: Node2D = room.call("get_training_mage") as Node2D
	var door: Node = room.call("get_test_door") as Node
	if marksman == null or mage == null or door == null:
		_fail("Marksman, mage or door is missing from the playable scene.")
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

	marksman.call("enter_combat_hostile")
	if not bool(marksman.call("is_combat_participant_active")) or not bool(mage.call("is_combat_participant_active")):
		_fail("Provoking one tactical role did not activate the complete squad.")
		return
	if not bool(marksman.call("is_hostile")) or not bool(mage.call("is_hostile")):
		_fail("Activated tactical squad is not hostile.")
		return

	var turn_system: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	if turn_system == null:
		_fail("Turn system is unavailable.")
		return
	var initiative_overrides: Dictionary = {
		player.get_instance_id(): 20,
		marksman.get_instance_id(): 2,
		mage.get_instance_id(): 1
	}
	turn_system.start_combat(player, [marksman, mage], 0, initiative_overrides)
	if not turn_system.is_player_turn(player):
		_fail("Deterministic player initiative was not applied.")
		return

	door.call("set_door_state", "closed", false)
	await process_frame
	var door_cell: Vector2i = (game.call("_get_battle_grid") as BattleGrid).world_to_cell((door as Node2D).global_position)
	if not environment.is_cell_blocked(game.call("_get_battle_grid") as BattleGrid, door_cell):
		_fail("Closed door is not registered as a combat blocker.")
		return
	player.call("set_interactable", door)
	var catalog: Dictionary = game.call("_build_catalog_entries") as Dictionary
	var world_entry: Dictionary = _find_action(catalog, "world_interact")
	if world_entry.is_empty() or not bool(world_entry.get("enabled", false)):
		_fail("Door interaction is missing or disabled in the combat world group.")
		return
	if str(world_entry.get("label", "")) != "ОТКРЫТЬ ДВЕРЬ":
		_fail("Combat door action has an unexpected label: %s" % JSON.stringify(world_entry))
		return

	if not bool(game.call("request_world_interaction", door)):
		_fail("Combat world interaction request was not handled.")
		return
	await process_frame
	if str(door.call("get_door_state")) != "open":
		_fail("Door did not open during the player turn.")
		return
	if environment.is_cell_blocked(game.call("_get_battle_grid") as BattleGrid, door_cell):
		_fail("Opened combat door remains blocked in the movement grid.")
		return
	if bool(game.call("is_world_interaction_available_for_testing")):
		_fail("Object interaction was not consumed for the current turn.")
		return

	door.call("interact")
	await process_frame
	if str(door.call("get_door_state")) != "open":
		_fail("The same combat turn allowed a second door interaction.")
		return
	catalog = game.call("_build_catalog_entries") as Dictionary
	world_entry = _find_action(catalog, "world_interact")
	if world_entry.is_empty() or bool(world_entry.get("enabled", true)):
		_fail("Consumed combat door interaction remains enabled in the catalog.")
		return

	turn_system.stop_combat()
	door.call("interact")
	await process_frame
	if str(door.call("get_door_state")) != "closed":
		_fail("Exploration door interaction no longer works outside combat.")
		return

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Selectable marksman/mage and one-per-turn combat door interaction passed.")
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
	hero.hit_die_size = 10
	hero.hit_dice_maximum = 5
	hero.hit_dice_current = 5
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
