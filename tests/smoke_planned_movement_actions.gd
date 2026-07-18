extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState is missing.")
		return
	state.call("new_game")
	var ranger := PlayerCharacter.new()
	ranger.character_name = "Путник"
	ranger.character_class_id = "ranger"
	ranger.character_class_name = "Следопыт"
	ranger.maximum_health = 18
	ranger.current_health = 18
	ranger.abilities["dexterity"] = 16
	ranger.abilities["strength"] = 14
	state.set("player_character", ranger)
	state.set("player_position", Vector2(320.0, 360.0))
	state.set("input_locked", false)

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	var game: Node = packed.instantiate()
	root.add_child(game)
	for _frame: int in range(10):
		await process_frame

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var caretaker: Node2D = game.get_node_or_null("Caretaker") as Node2D
	var grid: BattleGrid = game.get_node_or_null("BattleGrid") as BattleGrid
	var environment: CombatEnvironment = game.get_node_or_null("CombatEnvironment") as CombatEnvironment
	var catalog: ActionCatalogUI = game.get_node_or_null("Interface/ActionCatalogUI") as ActionCatalogUI
	if player == null or caretaker == null or grid == null or environment == null or catalog == null:
		_fail("Planned combat components are missing.")
		return
	if not catalog.jump_button.visible:
		_fail("Exploration jump button is not visible outside combat.")
		return

	player.global_position = grid.cell_to_world_center(Vector2i(8, 2))
	player.call("set_facing_direction", Vector2.RIGHT)
	game.call("_on_exploration_jump_requested")
	await create_timer(0.5).timeout
	if grid.world_to_cell(player.global_position) != Vector2i(10, 2):
		_fail("Exploration jump did not land beyond the jumpable obstacle.")
		return

	game.call("_start_turn_based_combat", caretaker)
	game.call("force_player_turn_for_testing")
	await process_frame
	await process_frame
	var player_cell: Vector2i = grid.world_to_cell(player.global_position)
	var caretaker_cell: Vector2i = grid.world_to_cell(caretaker.global_position)
	if environment.is_cell_blocked(grid, player_cell) or environment.is_cell_blocked(grid, caretaker_cell):
		_fail("Combatant was snapped into a blocked obstacle cell.")
		return
	if not catalog.catalog_button.visible:
		_fail("Action catalog button is hidden during the player turn.")
		return

	var entries: Dictionary = game.call("_build_catalog_entries") as Dictionary
	for category_id: String in ["movement", "action", "bonus", "reaction"]:
		if not entries.has(category_id):
			_fail("Action catalog category is missing: %s" % category_id)
			return
	if (entries.get("action", []) as Array).is_empty():
		_fail("Action category contains no actions.")
		return
	if (entries.get("bonus", []) as Array).is_empty():
		_fail("Ranger signature ability was not separated into bonus actions.")
		return

	var turn_system: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	if turn_system == null or not turn_system.action_available or not turn_system.bonus_action_available:
		_fail("Action resources were not initialized independently.")
		return
	game.call("_on_dash_requested")
	await process_frame
	if turn_system.action_available:
		_fail("Dash did not consume the regular action.")
		return
	if not turn_system.bonus_action_available:
		_fail("Consuming a regular action also consumed the bonus action.")
		return

	game.call("_stop_turn_based_combat", "test")
	game.queue_free()
	await process_frame
	print("Planned movement and action catalog smoke test passed.")
	quit(0)
