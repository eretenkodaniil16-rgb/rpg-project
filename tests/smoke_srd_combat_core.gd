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
	character.maximum_health = 30
	character.current_health = 30
	character.abilities["strength"] = 16
	character.abilities["dexterity"] = 14
	state.set("player_character", character)
	state.set("player_position", Vector2(320.0, 360.0))

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	var game: Node = packed.instantiate()
	root.add_child(game)
	for _frame: int in range(8):
		await process_frame

	var environment: CombatEnvironment = game.get_node_or_null("CombatEnvironment") as CombatEnvironment
	var old_panel: Control = game.find_child("SrdCombatUI", true, false) as Control
	var catalog: ActionCatalogUI = game.get_node_or_null("Interface/ActionCatalogUI") as ActionCatalogUI
	var caretaker: Node = game.get_node_or_null("Caretaker")
	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var grid: BattleGrid = game.get_node_or_null("BattleGrid") as BattleGrid
	if environment == null or old_panel == null or catalog == null or caretaker == null or player == null or grid == null:
		_fail("SRD scene components are missing.")
		return
	if not environment.is_in_group("combat_environment"):
		_fail("Environment group registration failed.")
		return
	if not environment.is_difficult_position(Vector2(400.0, 350.0)):
		_fail("Difficult terrain is missing.")
		return
	var half_cover: Dictionary = environment.get_cover(Vector2(600.0, 220.0), Vector2(700.0, 220.0))
	if int(half_cover.get("bonus", 0)) != 2:
		_fail("Half cover calculation is incorrect.")
		return
	var total_cover: Dictionary = environment.get_cover(Vector2(780.0, 550.0), Vector2(910.0, 550.0))
	if not bool(total_cover.get("total_cover", false)):
		_fail("Total cover calculation is incorrect.")
		return

	game.call("_set_selected_target", caretaker)
	game.call("_start_turn_based_combat", caretaker)
	game.call("force_player_turn_for_testing")
	await process_frame
	await process_frame
	if not bool(game.call("is_turn_based_combat_active")):
		_fail("Turn-based mode did not start.")
		return
	if player.global_position != grid.cell_to_world_center(grid.world_to_cell(player.global_position)):
		_fail("Player is not centered in a grid cell.")
		return
	if old_panel.visible:
		_fail("Legacy SRD row should be hidden.")
		return
	if not catalog.catalog_button.visible:
		_fail("Action catalog is hidden.")
		return
	var entries: Dictionary = game.call("_build_catalog_entries") as Dictionary
	var movement_entries: Array = entries.get("movement", []) as Array
	var found_prone: bool = false
	for value: Variant in movement_entries:
		if value is Dictionary and str((value as Dictionary).get("id", "")) == "prone_toggle":
			found_prone = true
	if not found_prone:
		_fail("Prone action is absent from movement category.")
		return

	var combat_state: CombatantState = game.call("get_player_combat_state") as CombatantState
	game.call("_on_prone_toggle_requested")
	await process_frame
	if combat_state == null or not combat_state.has_condition("prone"):
		_fail("Prone state was not applied.")
		return
	game.call("_on_prone_toggle_requested")
	await process_frame
	if combat_state.has_condition("prone"):
		_fail("Stand action did not clear prone state.")
		return

	game.queue_free()
	await process_frame
	print("SRD combat core smoke test passed.")
	quit(0)
