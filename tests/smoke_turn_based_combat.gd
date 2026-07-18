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
	if player == null or caretaker == null or grid == null:
		_fail("Required combat nodes are missing.")
		return
	game.call("_start_turn_based_combat", caretaker)
	game.call("force_player_turn_for_testing")
	await process_frame
	await process_frame
	if not bool(game.call("is_turn_based_combat_active")):
		_fail("Turn based combat did not start.")
		return

	var player_cell: Vector2i = grid.world_to_cell(player.global_position)
	var caretaker_cell: Vector2i = grid.world_to_cell(caretaker.global_position)
	if player.global_position.distance_to(grid.cell_to_world_center(player_cell)) > 0.01:
		_fail("Player was not snapped to the center of a grid cell.")
		return
	if caretaker.global_position.distance_to(grid.cell_to_world_center(caretaker_cell)) > 0.01:
		_fail("Caretaker was not snapped to the center of a grid cell.")
		return
	if player_cell == caretaker_cell:
		_fail("Player and caretaker occupied the same combat cell.")
		return

	var catalog: ActionCatalogUI = game.get_node_or_null("Interface/ActionCatalogUI") as ActionCatalogUI
	if catalog == null or catalog.catalog_button == null or not catalog.catalog_button.visible:
		_fail("Categorized action interface is missing or hidden.")
		return
	if "Раунд 1" not in catalog.resource_label.text or "Перемещение: 30 футов" not in catalog.resource_label.text:
		_fail("Action catalog does not show round and movement resources.")
		return

	var start_position: Vector2 = player.global_position
	game.call("request_combat_move", Vector2i(0, -1))
	await process_frame
	if player.global_position.distance_to(start_position) > 0.01:
		_fail("Planning a route moved the player before confirmation.")
		return
	var planned_path: Array = game.get("_planned_path") as Array
	if planned_path.size() != 2:
		_fail("One-cell route was not planned.")
		return
	game.call("_confirm_planned_movement")
	await create_timer(0.3).timeout
	if absf(player.global_position.y - (start_position.y - 64.0)) > 0.01:
		_fail("Confirmed movement did not advance exactly one grid cell.")
		return
	if "Перемещение: 25 футов" not in catalog.resource_label.text:
		_fail("Confirmed movement did not spend five feet.")
		return

	game.call("_stop_turn_based_combat", "test")
	game.call("_refresh_action_catalog")
	await process_frame
	await process_frame
	if bool(game.call("is_turn_based_combat_active")) or catalog.catalog_button.visible:
		_fail("Turn based combat did not stop cleanly.")
		return
	game.queue_free()
	await process_frame
	print("Turn based combat smoke test passed.")
	quit(0)
