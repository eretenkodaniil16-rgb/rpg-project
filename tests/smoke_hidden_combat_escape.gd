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
		_fail("Game scene does not use the pursuit escape runtime.")
		return

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var grid: BattleGrid = get_first_node_in_group("battle_grid") as BattleGrid
	var dummy: Node = _find_training_construct()
	if player == null or grid == null or dummy == null:
		_fail("Player, battle grid or training encounter actor is missing.")
		return

	# Route 1: a deep hiding place. One Hide roll is not enough; the enemy must lose the hero twice.
	game.call("_start_turn_based_combat", dummy)
	game.call("force_player_turn_for_testing")
	await process_frame
	if str(state.call("get_encounter_status", "training_construct")) != EncounterSystem.STATUS_ACTIVE:
		_fail("Training encounter did not become active.")
		return
	var entries_before: Dictionary = game.call("_build_catalog_entries") as Dictionary
	var escape_before: Dictionary = _find_entry(entries_before.get("action", []) as Array, "escape")
	if escape_before.is_empty() or bool(escape_before.get("enabled", false)):
		_fail("Escape should be disabled before successful hiding.")
		return

	player.global_position = grid.cell_to_world_center(Vector2i(11, 8))
	state.set("player_position", player.global_position)
	game.call("set_hide_roll_overrides_for_testing", [20])
	game.call("_on_hide_requested")
	await process_frame
	var combat_state: CombatantState = game.get("_player_combat_state") as CombatantState
	if combat_state == null or not combat_state.hidden:
		_fail("The concealed wall niche did not allow a high Stealth result to hide the player.")
		return
	if str(game.call("get_detection_state_for_testing", dummy)) != "pursuing_last_seen":
		_fail("The enemy did not begin pursuit toward the last seen position.")
		return
	game.call("_on_catalog_action_requested", "escape")
	await process_frame
	var hideout_progress: Dictionary = game.call("get_escape_progress_for_testing") as Dictionary
	if str(hideout_progress.get("route_id", "")) != "collapsed_wall_niche" or not bool(hideout_progress.get("objective_ready", false)):
		_fail("The deep hideout did not become the active escape objective.")
		return
	if bool(game.call("resolve_search_for_testing", dummy, 1)):
		_fail("A single failed search ended the encounter too early.")
		return
	if int((game.call("get_escape_progress_for_testing") as Dictionary).get("minimum_failed_searches", 0)) != 1:
		_fail("The first failed enemy search was not recorded.")
		return
	if not bool(game.call("resolve_search_for_testing", dummy, 1)):
		_fail("Two failed searches did not complete the hideout escape.")
		return
	await process_frame
	if str(state.call("get_encounter_status", "training_construct")) != EncounterSystem.STATUS_ABANDONED:
		_fail("Hideout escape did not abandon the encounter.")
		return
	if hero.experience != 0 or int(state.call("get_item_count", "straw_scrap")) != 0:
		_fail("Escaping through a hideout granted victory rewards.")
		return

	# Route 2: cross into another room, leave a trail, hide again, and survive tracking/search attempts.
	if dummy.has_method("reset_for_testing"):
		dummy.call("reset_for_testing")
	game.call("_start_turn_based_combat", dummy)
	game.call("force_player_turn_for_testing")
	await process_frame
	if str(state.call("get_encounter_status", "training_construct")) != EncounterSystem.STATUS_ACTIVE:
		_fail("Abandoned encounter could not be attempted again for the room route.")
		return
	game.call("force_hidden_escape_state_for_testing", 22, true)
	var room_path: Array[Vector2i] = [Vector2i(2, 4), Vector2i(1, 4), Vector2i(0, 4)]
	game.call("apply_hidden_path_for_testing", room_path)
	var transition_progress: Dictionary = game.call("get_escape_progress_for_testing") as Dictionary
	if str(transition_progress.get("route_id", "")) != "west_service_room" or not bool(transition_progress.get("room_entered", false)):
		_fail("Crossing the service doorway did not activate the adjacent-room route.")
		return
	if int(transition_progress.get("trace_count", 0)) < 2:
		_fail("Hidden movement did not leave a trackable path.")
		return
	player.global_position = grid.cell_to_world_center(Vector2i(0, 3))
	state.set("player_position", player.global_position)
	game.call("set_hide_roll_overrides_for_testing", [20])
	game.call("_on_hide_requested")
	await process_frame
	var room_progress: Dictionary = game.call("get_escape_progress_for_testing") as Dictionary
	if not combat_state.hidden or not bool(room_progress.get("objective_ready", false)):
		_fail("The player did not re-hide inside the adjacent room.")
		return
	if bool(game.call("resolve_search_for_testing", dummy, 20)):
		_fail("Finding one segment of the trail incorrectly completed escape.")
		return
	if str(game.call("get_detection_state_for_testing", dummy)) != "tracking":
		_fail("A successful tracking check did not switch the enemy to tracking.")
		return
	if bool(game.call("resolve_search_for_testing", dummy, 1)):
		_fail("The first failed attempt after tracking ended the encounter too early.")
		return
	if not bool(game.call("resolve_search_for_testing", dummy, 1)):
		_fail("The enemy did not finally lose the trail after two failed searches.")
		return
	await process_frame
	if str(state.call("get_encounter_status", "training_construct")) != EncounterSystem.STATUS_ABANDONED:
		_fail("Adjacent-room escape did not abandon the encounter.")
		return
	var encounter_state: Dictionary = state.call("get_encounter_state", "training_construct") as Dictionary
	if int(encounter_state.get("attempt_count", 0)) < 2:
		_fail("The second escape route did not preserve the retry attempt count.")
		return
	if bool(game.call("is_turn_based_combat_active")) or combat_state.hidden:
		_fail("Combat or hidden state leaked after the final escape.")
		return

	if not bool(state.call("save_game")):
		_fail("Abandoned encounter could not be saved.")
		return
	state.set("story_flags", {})
	state.set("quest_states", {})
	state.set("inventory", {})
	if not bool(state.call("load_game")):
		_fail("Abandoned encounter save could not be loaded.")
		return
	if str(state.call("get_encounter_status", "training_construct")) != EncounterSystem.STATUS_ABANDONED:
		_fail("Abandoned encounter state was not preserved by save/load.")
		return
	if not bool(state.call("get_flag", "training_construct_alerted", false)):
		_fail("Persistent enemy alert was not preserved after pursuit escape.")
		return

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Deep hideout, last-seen pursuit, trail tracking, room transition, re-hide and multi-sweep escape smoke test passed.")
	quit(0)


func _find_training_construct() -> Node:
	for candidate: Node in get_nodes_in_group("combat_targets"):
		if candidate.has_method("get_encounter_id") and str(candidate.call("get_encounter_id")) == "training_construct":
			return candidate
	return null


func _find_entry(entries: Array, action_id: String) -> Dictionary:
	for value: Variant in entries:
		if value is Dictionary and str((value as Dictionary).get("id", "")) == action_id:
			return (value as Dictionary).duplicate(true)
	return {}
