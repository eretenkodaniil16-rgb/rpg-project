extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const EXPECTED_RUNTIME: String = "res://scripts/game/game_guard_post_polish_runtime.gd"
const INNER_GATE_BLOCKER_ID: String = "inner_watch_gate_blocker"


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
	for _frame: int in range(40):
		await process_frame
	var game_script: Script = game.get_script() as Script
	if game_script == null or game_script.resource_path != EXPECTED_RUNTIME:
		_fail("Game scene does not use the polished two-room runtime.")
		return
	game.set_process(false)

	var grid: BattleGrid = game.call("_get_battle_grid") as BattleGrid
	var environment: CombatEnvironment = get_first_node_in_group("combat_environment") as CombatEnvironment
	var room: Node = game.get_node_or_null("StealthTestRoom")
	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var message_label: Label = game.get_node_or_null("Interface/CombatMessageLabel") as Label
	if grid == null or environment == null or room == null or player == null or message_label == null:
		_fail("Line-of-sight simulation fixtures are incomplete.")
		return
	var gate: Node = room.call("get_inner_gate") if room.has_method("get_inner_gate") else null
	var marksman: Node2D = room.call("get_training_marksman") as Node2D
	var mage: Node2D = room.call("get_training_mage") as Node2D
	if gate == null or marksman == null or mage == null:
		_fail("Inner gate, marksman or mage is missing.")
		return

	var gate_edges: Array[Dictionary] = environment.get_edge_blocker_edges_for_testing(INNER_GATE_BLOCKER_ID)
	if gate_edges.is_empty():
		_fail("Inner gate edge blocker was not registered.")
		return
	var doorway_edge: Dictionary = gate_edges[0]
	var doorway_left: Vector2i = doorway_edge.get("a", CombatEnvironment.INVALID_CELL) as Vector2i
	var doorway_right: Vector2i = doorway_edge.get("b", CombatEnvironment.INVALID_CELL) as Vector2i
	gate.call("set_door_state", "locked", false)
	room.call("set_inner_watch_mode", "watching")
	player.global_position = grid.cell_to_world_center(doorway_left)
	marksman.global_position = grid.cell_to_world_center(doorway_right + Vector2i(2, -2))
	mage.global_position = grid.cell_to_world_center(doorway_right + Vector2i(2, 2))
	await process_frame

	if not environment.is_transition_blocked(grid, doorway_left, doorway_right):
		_fail("Locked inner gate does not block the edge between rooms.")
		return
	for observer: Node2D in [marksman, mage]:
		if bool(game.call("_observer_can_see_position", observer, player.global_position)):
			_fail("Locked inner partition still gives line of sight to %s." % str(game.call("_target_name", observer)))
			return

	gate.call("set_door_state", "open", false)
	player.global_position = grid.cell_to_world_center(doorway_left)
	marksman.global_position = grid.cell_to_world_center(doorway_right)
	mage.global_position = grid.cell_to_world_center(doorway_right + Vector2i(1, 1))
	await process_frame
	if environment.is_transition_blocked(grid, doorway_left, doorway_right):
		_fail("Opened inner gate still blocks the edge between rooms.")
		return
	var visible_observers: Array[Node] = []
	for observer: Node2D in [marksman, mage]:
		if bool(game.call("_observer_can_see_position", observer, player.global_position)):
			visible_observers.append(observer)
	if visible_observers.is_empty():
		_fail("Opening the inner gate did not restore line of sight for the inner watch.")
		return

	room.call("activate_inner_watch_combat")
	game.call("_start_turn_based_combat", marksman)
	game.call("force_player_turn_for_testing")
	game.set("_enemy_turn_running", false)
	await process_frame
	var combat_state: CombatantState = game.get("_player_combat_state") as CombatantState
	if combat_state == null:
		_fail("Player combat state is unavailable for hide checks.")
		return
	combat_state.hidden = false
	game.call("_on_hide_requested")
	await process_frame
	if combat_state.hidden:
		_fail("The player hid while the inner watch had direct line of sight through the open gate.")
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
	print("Inner-room edge line of sight and named observers passed.")
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
