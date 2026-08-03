extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const POSITION_EPSILON: float = 0.01


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	state.call("new_game")
	var character := PlayerCharacter.new()
	character.character_name = "Тактик"
	character.character_class_id = "fighter"
	character.character_class_name = "Воин"
	character.maximum_health = 20
	character.current_health = 20
	character.abilities["dexterity"] = 16
	state.set("player_character", character)
	state.set("player_position", Vector2(320.0, 360.0))
	state.set("input_locked", false)

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	if packed == null:
		_fail("Game scene failed to load.")
		return
	var game: Node = packed.instantiate()
	root.add_child(game)
	for _frame: int in range(8):
		await process_frame

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var caretaker: Node2D = game.get_node_or_null("Caretaker") as Node2D
	var grid: BattleGrid = game.get_node_or_null("BattleGrid") as BattleGrid
	var mobile_controls: Control = game.get_node_or_null("Interface/MobileControls") as Control
	if player == null or caretaker == null or grid == null or mobile_controls == null:
		_fail("Required combat nodes are missing.")
		return
	mobile_controls.call("enable_for_testing")
	var actions_button: Button = mobile_controls.call("get_actions_button_for_testing") as Button
	var player_before_combat: Vector2 = player.global_position
	var caretaker_before_combat: Vector2 = caretaker.global_position
	game.call("_start_turn_based_combat", caretaker)
	if not bool(game.call("is_turn_based_combat_active")):
		_fail("Turn based combat did not start.")
		return
	# Compare synchronously before a deferred enemy turn can move naturally.
	if player.global_position.distance_to(player_before_combat) > POSITION_EPSILON:
		_fail("Starting initiative relocated the player.")
		return
	if caretaker.global_position.distance_to(caretaker_before_combat) > POSITION_EPSILON:
		_fail("Starting initiative relocated the caretaker.")
		return
	game.call("force_player_turn_for_testing")
	await process_frame
	await process_frame

	var player_cell: Vector2i = grid.world_to_cell(player.global_position)
	var caretaker_cell: Vector2i = grid.world_to_cell(caretaker.global_position)
	if not grid.is_cell_valid(player_cell) or not grid.is_cell_valid(caretaker_cell):
		_fail("Preserved world positions do not map to valid combat cells.")
		return

	var catalog: ActionCatalogUI = game.get_node_or_null("Interface/ActionCatalogUI") as ActionCatalogUI
	if catalog == null or actions_button == null or not actions_button.visible or catalog.catalog_button.visible:
		_fail("The persistent Actions control or categorized menu is missing.")
		return
	if "Раунд 1" not in catalog.resource_label.text or "Перемещение: 30 футов" not in catalog.resource_label.text:
		_fail("Action catalog does not show round and movement resources.")
		return

	var start_position: Vector2 = player.global_position
	game.call("request_combat_move", Vector2i(0, -1))
	await process_frame
	if player.global_position.distance_to(start_position) > POSITION_EPSILON:
		_fail("Planning a route moved the player before confirmation.")
		return
	var planned_path: Array = game.get("_planned_path") as Array
	if planned_path.size() != 2:
		_fail("One-cell route was not planned.")
		return
	game.call("_confirm_planned_movement")
	await create_timer(0.3).timeout
	var expected_destination: Vector2 = grid.cell_to_world_center(player_cell + Vector2i(0, -1))
	if player.global_position.distance_to(expected_destination) > POSITION_EPSILON:
		_fail("Confirmed movement did not finish at the selected grid-cell center.")
		return
	if "Перемещение: 25 футов" not in catalog.resource_label.text:
		_fail("Confirmed movement did not spend five feet.")
		return

	game.call("_stop_turn_based_combat", "test")
	game.call("_refresh_action_catalog")
	await process_frame
	await process_frame
	if bool(game.call("is_turn_based_combat_active")):
		_fail("Turn based combat did not stop cleanly.")
		return
	if not actions_button.visible or catalog.catalog_button.visible or catalog.end_turn_button.visible or catalog.confirm_move_button.visible:
		_fail("Actions menu did not return to exploration mode after combat.")
		return
	game.queue_free()
	await process_frame
	print("Turn combat preserves initial world positions and moves only after confirmation.")
	quit(0)
