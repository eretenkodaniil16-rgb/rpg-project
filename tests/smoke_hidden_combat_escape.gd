extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null or not state.has_method("abandon_encounter"):
		_fail("Encounter-aware GameState is missing.")
		return
	var save_path: String = ProjectSettings.globalize_path("user://savegame.json")
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	state.call("new_game")
	var hero := PlayerCharacter.new()
	hero.character_name = "Тень"
	hero.character_class_id = "rogue"
	hero.character_class_name = "Плут"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.level = 1
	hero.maximum_health = 10
	hero.current_health = 10
	hero.hit_die_size = 8
	hero.hit_dice_maximum = 1
	hero.hit_dice_current = 1
	hero.abilities["dexterity"] = 18
	hero.base_abilities["dexterity"] = 18
	hero.skill_proficiencies.append("stealth")
	state.set("player_character", hero)

	var scene: PackedScene = load(GAME_SCENE) as PackedScene
	if scene == null:
		_fail("Game scene could not be loaded.")
		return
	var game: Node = scene.instantiate()
	root.add_child(game)
	for _frame: int in range(7):
		await process_frame
	if str(game.get_script().resource_path) != "res://scripts/game/game_hidden_escape_runtime.gd":
		_fail("Game scene does not use the hidden combat escape runtime.")
		return

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var caretaker: Node = game.get_node_or_null("Caretaker")
	if player == null or caretaker == null:
		_fail("Player or caretaker is missing from the game scene.")
		return
	(caretaker as Node2D).global_position = Vector2(930.0, 555.0)
	player.global_position = Vector2(750.0, 555.0)
	game.call("_start_turn_based_combat", caretaker)
	game.call("force_player_turn_for_testing")
	await process_frame
	game.call("set_hide_roll_overrides_for_testing", [20])
	game.call("_on_hide_requested")
	await process_frame
	var combat_state: CombatantState = game.get("_player_combat_state") as CombatantState
	if combat_state == null or not combat_state.hidden:
		_fail("A high Stealth roll behind the solid wall did not hide the player.")
		return
	if str(game.call("get_detection_state_for_testing", caretaker)) != "searching":
		_fail("The observer did not switch to searching after losing the player.")
		return
	game.call("_stop_turn_based_combat", "Завершение проверки скрытности")
	if caretaker.has_method("reset_combat_state"):
		caretaker.call("reset_combat_state", true)
	await process_frame

	var dummy: Node = null
	for candidate: Node in get_nodes_in_group("combat_targets"):
		if candidate.has_method("get_encounter_id") and str(candidate.call("get_encounter_id")) == "training_construct":
			dummy = candidate
			break
	if dummy == null:
		_fail("Training encounter actor is missing.")
		return
	game.call("_start_turn_based_combat", dummy)
	game.call("force_player_turn_for_testing")
	await process_frame
	if str(state.call("get_encounter_status", "training_construct")) != EncounterSystem.STATUS_ACTIVE:
		_fail("Training encounter did not become active.")
		return

	var entries_before: Dictionary = game.call("_build_catalog_entries") as Dictionary
	var escape_before: Dictionary = _find_entry(entries_before.get("action", []) as Array, "escape")
	if escape_before.is_empty() or bool(escape_before.get("enabled", false)):
		_fail("Escape should be present but disabled before the player hides.")
		return

	game.call("force_hidden_escape_state_for_testing", 24, true)
	var entries_after: Dictionary = game.call("_build_catalog_entries") as Dictionary
	var escape_after: Dictionary = _find_entry(entries_after.get("action", []) as Array, "escape")
	if escape_after.is_empty() or not bool(escape_after.get("enabled", false)):
		_fail("Escape did not become available after successful hiding.")
		return
	var escape_cells: Array[Vector2i] = game.call("get_escape_cells_for_testing") as Array[Vector2i]
	if escape_cells.is_empty():
		_fail("Encounter escape zones were not calculated.")
		return
	var grid: BattleGrid = get_first_node_in_group("battle_grid") as BattleGrid
	if grid == null:
		_fail("Battle grid is missing.")
		return
	player.global_position = grid.cell_to_world_center(escape_cells[0])
	state.set("player_position", player.global_position)
	var escaped: bool = bool(game.call("try_complete_escape_for_testing"))
	await process_frame
	if not escaped:
		_fail("Hidden player standing in an escape zone did not leave combat.")
		return
	if str(state.call("get_encounter_status", "training_construct")) != EncounterSystem.STATUS_ABANDONED:
		_fail("Successful hidden escape did not mark the encounter abandoned.")
		return
	if hero.experience != 0 or int(state.call("get_item_count", "straw_scrap")) != 0:
		_fail("Escaping granted victory experience or loot.")
		return
	if not bool(state.call("get_flag", "training_construct_alerted", false)):
		_fail("Escape did not preserve the alerted-world consequence.")
		return
	if bool(game.call("is_turn_based_combat_active")):
		_fail("Turn-based combat remained active after successful escape.")
		return
	if combat_state.hidden:
		_fail("Hidden combat state leaked out of the abandoned encounter.")
		return

	if not bool(state.call("save_game")):
		_fail("Abandoned encounter could not be saved.")
		return
	state.call("new_game")
	if not bool(state.call("load_game")):
		_fail("Abandoned encounter save could not be loaded.")
		return
	if str(state.call("get_encounter_status", "training_construct")) != EncounterSystem.STATUS_ABANDONED:
		_fail("Abandoned encounter state was not preserved by save/load.")
		return
	var retry: Dictionary = state.call("begin_encounter", "training_construct", {"source_type": "retry"}, false, false) as Dictionary
	if not bool(retry.get("success", false)) or int((retry.get("state", {}) as Dictionary).get("attempt_count", 0)) < 2:
		_fail("An abandoned encounter could not be attempted again.")
		return

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Hide check, search state, escape zone, abandonment and retry smoke test passed.")
	quit(0)


func _find_entry(entries: Array, action_id: String) -> Dictionary:
	for value: Variant in entries:
		if value is Dictionary and str((value as Dictionary).get("id", "")) == action_id:
			return (value as Dictionary).duplicate(true)
	return {}
