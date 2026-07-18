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
	for _frame: int in range(14):
		await process_frame

	var environment: CombatEnvironment = game.get_node_or_null("CombatEnvironment") as CombatEnvironment
	var old_panel: Control = game.find_child("SrdCombatUI", true, false) as Control
	var catalog: ActionCatalogUI = game.get_node_or_null("Interface/ActionCatalogUI") as ActionCatalogUI
	var dialogue_ui: Control = game.get_node_or_null("Interface/DialogueUI") as Control
	var caretaker: Node = game.get_node_or_null("Caretaker")
	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var grid: BattleGrid = game.get_node_or_null("BattleGrid") as BattleGrid
	var social_controller: CombatSocialTerrainController = game.get_node_or_null("CombatSocialTerrainController") as CombatSocialTerrainController
	if environment == null or old_panel == null or catalog == null or dialogue_ui == null or caretaker == null or player == null or grid == null or social_controller == null:
		_fail("SRD, dialogue, terrain or combat social components are missing.")
		return
	if not environment.is_in_group("combat_environment") or not environment.is_difficult_position(Vector2(400.0, 350.0)):
		_fail("Difficult terrain environment is missing.")
		return

	var fighter_speed: float = float(player.call("get_effective_movement_speed_at", Vector2(400.0, 350.0)))
	if not is_equal_approx(fighter_speed, 110.0):
		_fail("Ordinary class did not slow to half speed outside combat: %f" % fighter_speed)
		return
	character.character_class_id = "ranger"
	character.character_class_name = "Следопыт"
	var ranger_speed: float = float(player.call("get_effective_movement_speed_at", Vector2(400.0, 350.0)))
	if not is_equal_approx(ranger_speed, 220.0):
		_fail("Ranger terrain trait did not preserve exploration speed: %f" % ranger_speed)
		return

	caretaker.call("interact")
	await process_frame
	if not dialogue_ui.visible:
		_fail("Ordinary NPC conversation did not open the dialogue window.")
		return
	var ordinary_attack_button: Button = dialogue_ui.call("get_attack_button_for_testing") as Button
	if ordinary_attack_button == null or ordinary_attack_button.text != "АТАКОВАТЬ":
		_fail("Ordinary NPC dialogue does not contain the persistent attack option.")
		return
	dialogue_ui.call("_close_dialogue")
	await process_frame

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
	for _frame: int in range(4):
		await process_frame
	if not bool(game.call("is_turn_based_combat_active")):
		_fail("Turn-based mode did not start.")
		return
	if player.global_position != grid.cell_to_world_center(grid.world_to_cell(player.global_position)):
		_fail("Player is not centered in a grid cell.")
		return
	if old_panel.visible or not catalog.catalog_button.visible:
		_fail("Combat catalog visibility is incorrect.")
		return
	if catalog.category_row.get_node_or_null("FreeCategoryButton") == null:
		_fail("Free-action communication tab is missing.")
		return

	var turn_system: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	var action_before: bool = turn_system.action_available
	var bonus_before: bool = turn_system.bonus_action_available
	var movement_before: int = turn_system.movement_remaining_feet
	var ui_entries: Dictionary = catalog.get("_entries") as Dictionary
	var free_entries: Array = ui_entries.get("free", []) as Array
	if free_entries.size() != 1 or str((free_entries[0] as Dictionary).get("id", "")) != "combat_dialogue":
		_fail("Free-action tab must open one dialogue command instead of listing phrases directly.")
		return
	catalog.action_requested.emit("combat_dialogue")
	await process_frame
	await process_frame
	if not dialogue_ui.visible:
		_fail("Combat communication did not open the dialogue window.")
		return
	if int(dialogue_ui.call("get_runtime_choice_count_for_testing")) < 4:
		_fail("Combat dialogue did not load speech and gesture choices from structured data.")
		return
	var combat_attack_button: Button = dialogue_ui.call("get_attack_button_for_testing") as Button
	if combat_attack_button == null or combat_attack_button.text != "АТАКОВАТЬ":
		_fail("Combat dialogue does not contain the persistent attack option.")
		return

	dialogue_ui.emit_signal("runtime_choice_requested", "combat_social:say_stop", caretaker)
	await process_frame
	await process_frame
	if not social_controller.social_action_used_for_testing():
		_fail("Combat speech was not registered as a free action.")
		return
	if turn_system.action_available != action_before or turn_system.bonus_action_available != bonus_before or turn_system.movement_remaining_feet != movement_before:
		_fail("Free communication consumed a combat resource.")
		return
	var response_attack_button: Button = dialogue_ui.call("get_attack_button_for_testing") as Button
	if response_attack_button == null:
		_fail("Attack option disappeared after a dialogue response.")
		return
	dialogue_ui.call("_close_dialogue")
	await process_frame

	var combat_state: CombatantState = game.call("get_player_combat_state") as CombatantState
	if combat_state == null or not combat_state.ignores_nonmagical_difficult_terrain:
		_fail("Ranger terrain trait was not synchronized into combat state.")
		return
	var terrain_planner: TerrainAwareMovementSystem = game.get("_movement_planner") as TerrainAwareMovementSystem
	var difficult_cell: Vector2i = grid.world_to_cell(Vector2(400.0, 350.0))
	if terrain_planner == null or terrain_planner.movement_cost_for_cell(grid, difficult_cell, environment, combat_state) != 5:
		_fail("Ranger difficult-terrain cell did not cost five feet in combat.")
		return

	var entries: Dictionary = game.call("_build_catalog_entries") as Dictionary
	var action_entries: Array = entries.get("action", []) as Array
	var found_prone: bool = false
	for value: Variant in action_entries:
		if value is Dictionary:
			var entry: Dictionary = value as Dictionary
			if str(entry.get("id", "")) == "prone_toggle" and str(entry.get("group", "")) == "movement":
				found_prone = true
	if not found_prone:
		_fail("Prone action is absent from Action > Movement.")
		return
	game.call("_on_prone_toggle_requested")
	await process_frame
	if not combat_state.has_condition("prone"):
		_fail("Prone state was not applied.")
		return
	game.call("_on_prone_toggle_requested")
	await process_frame
	if combat_state.has_condition("prone"):
		_fail("Stand action did not clear prone state.")
		return

	game.queue_free()
	await process_frame
	print("SRD combat dialogue, persistent attack option and terrain trait smoke test passed.")
	quit(0)
