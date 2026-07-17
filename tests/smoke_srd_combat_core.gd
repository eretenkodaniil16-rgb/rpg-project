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
	if packed == null:
		_fail("Game scene failed to load.")
		return
	var game: Node = packed.instantiate()
	root.add_child(game)
	for _frame: int in range(6):
		await process_frame

	var environment: Node = game.get_node_or_null("CombatEnvironment")
	var srd_ui: Control = game.find_child("SrdCombatUI", true, false) as Control
	var caretaker: Node = game.get_node_or_null("Caretaker")
	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var grid: BattleGrid = game.get_node_or_null("BattleGrid") as BattleGrid
	if environment == null or srd_ui == null or caretaker == null or player == null or grid == null:
		_fail("SRD combat scene components are missing.")
		return
	if not environment.is_in_group("combat_environment"):
		_fail("Combat environment group registration failed.")
		return
	if not bool(environment.call("is_difficult_position", Vector2(400.0, 350.0))):
		_fail("Difficult terrain was not registered in the test lobby.")
		return
	var half_cover: Dictionary = environment.call("get_cover", Vector2(600.0, 220.0), Vector2(700.0, 220.0)) as Dictionary
	if int(half_cover.get("bonus", 0)) != 2 or bool(half_cover.get("total_cover", false)):
		_fail("Half cover calculation is incorrect: %s" % half_cover)
		return
	var total_cover: Dictionary = environment.call("get_cover", Vector2(780.0, 550.0), Vector2(910.0, 550.0)) as Dictionary
	if not bool(total_cover.get("total_cover", false)):
		_fail("Total cover did not block line of sight: %s" % total_cover)
		return

	game.call("_set_selected_target", caretaker)
	game.call("_start_turn_based_combat", caretaker)
	for _frame: int in range(4):
		await process_frame
	if not bool(game.call("is_turn_based_combat_active")):
		_fail("SRD battle did not enter turn-based mode.")
		return
	game.call("force_player_turn_for_testing")
	await process_frame
	if player.global_position != grid.cell_to_world_center(grid.world_to_cell(player.global_position)):
		_fail("Player is not centered in the battle grid cell.")
		return
	if (caretaker as Node2D).global_position != grid.cell_to_world_center(grid.world_to_cell((caretaker as Node2D).global_position)):
		_fail("Caretaker is not centered in the battle grid cell.")
		return
	if not srd_ui.visible:
		_fail("SRD combat action panel is hidden during the player turn.")
		return

	var combat_state: CombatantState = game.call("get_player_combat_state") as CombatantState
	if combat_state == null:
		_fail("Player combat state is unavailable.")
		return
	game.call("_on_prone_toggle_requested")
	await process_frame
	if not combat_state.has_condition("prone"):
		_fail("Prone action did not add the condition.")
		return
	game.call("_on_prone_toggle_requested")
	await process_frame
	if combat_state.has_condition("prone"):
		_fail("Standing up did not remove the prone condition.")
		return

	combat_state.damage_resistances = ["fire"]
	var health_before: int = character.current_health
	game.call("apply_damage_to_player", 10, "fire", false, caretaker)
	if character.current_health != health_before - 5:
		_fail("Player damage resistance was not applied in the live scene: %d -> %d" % [health_before, character.current_health])
		return

	game.queue_free()
	await process_frame
	print("SRD combat core smoke test passed.")
	quit(0)
