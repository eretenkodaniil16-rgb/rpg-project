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
	var mobile_controls: Control = game.get_node_or_null("Interface/MobileControls") as Control
	var movement_overlay: MovementPlanOverlay = game.get_node_or_null("MovementPlanOverlay") as MovementPlanOverlay
	if player == null or caretaker == null or grid == null or environment == null or catalog == null or mobile_controls == null or movement_overlay == null:
		_fail("Planned combat components are missing.")
		return

	mobile_controls.call("enable_for_testing")
	await process_frame
	var mobile_jump: Button = mobile_controls.call("get_jump_button_for_testing") as Button
	if mobile_jump == null or not mobile_jump.visible:
		_fail("Mobile jump button is not visible beside the joystick outside combat.")
		return
	if catalog.jump_button.visible:
		_fail("Legacy jump button must stay hidden after moving jump beside the joystick.")
		return

	player.global_position = grid.cell_to_world_center(Vector2i(8, 2))
	player.call("set_facing_direction", Vector2.RIGHT)
	game.call("_on_exploration_jump_requested")
	await create_timer(0.5).timeout
	if grid.world_to_cell(player.global_position) != Vector2i(10, 2):
		_fail("Exploration jump did not land beyond the jumpable obstacle.")
		return

	# Return before the barricade so the combat planner can test an automatic jump.
	player.global_position = grid.cell_to_world_center(Vector2i(8, 2))
	state.set("player_position", player.global_position)
	game.call("_start_turn_based_combat", caretaker)
	game.call("force_player_turn_for_testing")
	await process_frame
	await process_frame
	var player_cell: Vector2i = grid.world_to_cell(player.global_position)
	var caretaker_cell: Vector2i = grid.world_to_cell(caretaker.global_position)
	if environment.is_cell_blocked(grid, player_cell) or environment.is_cell_blocked(grid, caretaker_cell):
		_fail("Combatant was snapped into a blocked obstacle cell.")
		return
	if not catalog.catalog_button.visible or not catalog.end_turn_button.visible:
		_fail("Permanent combat controls are hidden during the player turn.")
		return
	if catalog.confirm_move_button.visible:
		_fail("Movement confirmation appeared before a route was selected.")
		return
	if catalog.action_group_row.get_child_count() != 4:
		_fail("Action subcategories Attack, Movement, Spells and Tactics are missing.")
		return

	var entries: Dictionary = game.call("_build_catalog_entries") as Dictionary
	for category_id: String in ["action", "bonus", "reaction"]:
		if not entries.has(category_id):
			_fail("Action catalog category is missing: %s" % category_id)
			return
	if entries.has("movement"):
		_fail("Movement should be an Action subcategory, not a separate top-level category.")
		return
	if (entries.get("action", []) as Array).is_empty():
		_fail("Action category contains no actions.")
		return
	if (entries.get("bonus", []) as Array).is_empty():
		_fail("Ranger signature ability was not separated into bonus actions.")
		return

	var reachable_costs: Dictionary = movement_overlay.get("_reachable_costs") as Dictionary
	if reachable_costs.is_empty() or reachable_costs.has(Vector2i(9, 2)) or not reachable_costs.has(Vector2i(10, 2)):
		_fail("Reachable area did not exclude the obstacle and include its jump landing: %s" % reachable_costs)
		return

	game.call("_plan_to_cell", Vector2i(10, 2))
	await process_frame
	var planned_path: Array = game.get("_planned_path") as Array
	var jump_indices: Array = game.get("_planned_jump_indices") as Array
	if planned_path != [Vector2i(8, 2), Vector2i(10, 2)] or jump_indices != [1]:
		_fail("Automatic combat jump route is incorrect: %s / %s" % [planned_path, jump_indices])
		return
	if not catalog.confirm_move_button.visible:
		_fail("Floating movement confirmation did not appear for a selected route.")
		return

	# Pressing a selected route cell removes that cell and everything after it.
	game.call("_handle_route_press", Vector2i(10, 2))
	await process_frame
	if not (game.get("_planned_path") as Array).is_empty() or catalog.confirm_move_button.visible:
		_fail("Pressing a selected cell did not remove the route tail including that cell.")
		return

	game.call("_plan_to_cell", Vector2i(10, 2))
	await process_frame
	game.call("_confirm_planned_movement")
	await create_timer(0.7).timeout
	if grid.world_to_cell(player.global_position) != Vector2i(10, 2):
		_fail("Confirmed automatic jump route did not move the player to the landing cell.")
		return
	if catalog.confirm_move_button.visible:
		_fail("Floating confirmation remained visible after movement completed.")
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
