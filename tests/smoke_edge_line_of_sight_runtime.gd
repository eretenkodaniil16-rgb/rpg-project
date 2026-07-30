extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const EXPECTED_RUNTIME: String = "res://scripts/game/game_squad_tactical_plans_runtime.gd"
const DOOR_BLOCKER_ID: String = "west_service_door_blocker"


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
	for _frame: int in range(30):
		await process_frame
	if str((game.get_script() as Script).resource_path) != EXPECTED_RUNTIME:
		_fail("Game scene does not use the expected tactical runtime.")
		return

	var grid: BattleGrid = game.call("_get_battle_grid") as BattleGrid
	var environment: CombatEnvironment = get_first_node_in_group("combat_environment") as CombatEnvironment
	var room: Node = game.get_node_or_null("StealthTestRoom")
	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var caretaker: Node2D = game.get_node_or_null("Caretaker") as Node2D
	var message_label: Label = game.get_node_or_null("Interface/CombatMessageLabel") as Label
	if grid == null or environment == null or room == null or player == null or caretaker == null or message_label == null:
		_fail("Line-of-sight simulation fixtures are incomplete.")
		return

	var door: Node = room.call("get_test_door") as Node
	var guard: Node2D = room.call("get_patrol_observer") as Node2D
	var marksman: Node2D = room.call("get_training_marksman") as Node2D
	var mage: Node2D = room.call("get_training_mage") as Node2D
	if door == null or guard == null or marksman == null or mage == null:
		_fail("Door or tactical observers are missing.")
		return

	var door_edges: Array[Dictionary] = environment.get_edge_blocker_edges_for_testing(DOOR_BLOCKER_ID)
	if door_edges.is_empty():
		_fail("Door edge blocker was not registered.")
		return
	var doorway_edge: Dictionary = door_edges[0]
	var doorway_left: Vector2i = doorway_edge.get("a", CombatEnvironment.INVALID_CELL) as Vector2i
	var doorway_right: Vector2i = doorway_edge.get("b", CombatEnvironment.INVALID_CELL) as Vector2i

	door.call("set_door_state", "closed", false)
	player.global_position = grid.cell_to_world_center(doorway_left)
	caretaker.global_position = grid.cell_to_world_center(doorway_right + Vector2i(3, 0))
	guard.global_position = grid.cell_to_world_center(doorway_right + Vector2i(2, -2))
	marksman.global_position = grid.cell_to_world_center(doorway_right + Vector2i(4, -3))
	mage.global_position = grid.cell_to_world_center(doorway_right + Vector2i(4, 3))
	await process_frame

	guard.call("enter_combat_hostile")
	game.call("_start_turn_based_combat", caretaker)
	game.call("force_player_turn_for_testing")
	game.set("_enemy_turn_running", false)
	await process_frame
	var observers: Array[Node] = game.call("_active_observers") as Array[Node]
	for expected_observer: Node2D in [caretaker, guard, marksman, mage]:
		if not observers.has(expected_observer):
			_fail("Expected hostile observer did not join the visibility simulation: %s" % str(game.call("_target_name", expected_observer)))
			return
	for observer: Node in observers:
		if bool(game.call("_observer_can_see_position", observer, player.global_position)):
			_fail("Closed edge partition still gives line of sight to %s." % str(game.call("_target_name", observer)))
			return

	game.call("set_hide_roll_overrides_for_testing", [20])
	game.call("_on_hide_requested")
	await process_frame
	var combat_state: CombatantState = game.get("_player_combat_state") as CombatantState
	if combat_state == null or not combat_state.hidden:
		_fail("The player could not hide while every observer was behind the closed partition.")
		return

	combat_state.hidden = false
	door.call("set_door_state", "open", false)
	player.global_position = grid.cell_to_world_center(doorway_left)
	caretaker.global_position = grid.cell_to_world_center(doorway_right)
	game.call("force_player_turn_for_testing")
	game.set("_enemy_turn_running", false)
	await process_frame

	var visible_observers: Array[Node] = []
	for observer: Node in game.call("_active_observers") as Array[Node]:
		if bool(game.call("_observer_can_see_position", observer, player.global_position)):
			visible_observers.append(observer)
	if visible_observers.is_empty():
		_fail("Opening the doorway did not restore line of sight for any observer.")
		return
	game.call("_on_hide_requested")
	await process_frame
	if combat_state.hidden:
		_fail("The player hid successfully while an observer had direct line of sight through the open doorway.")
		return
	if message_label.text.contains("хотя бы один противник"):
		_fail("Hide failure still uses the anonymous observer message.")
		return
	for observer: Node in visible_observers:
		var observer_name: String = str(game.call("_target_name", observer))
		if not message_label.text.contains(observer_name):
			_fail("Hide failure did not name visible observer %s: %s" % [observer_name, message_label.text])
			return

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Cell-edge line of sight and named hide observers passed.")
	quit(0)


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель обзора"
	hero.character_class_id = "rogue"
	hero.character_class_name = "Плут"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.level = 5
	hero.maximum_health = 42
	hero.current_health = 42
	hero.hit_die_size = 8
	hero.hit_dice_maximum = 5
	hero.hit_dice_current = 5
	hero.abilities["dexterity"] = 18
	hero.base_abilities["dexterity"] = 18
	hero.skill_proficiencies.append("stealth")
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
