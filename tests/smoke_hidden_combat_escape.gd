extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const RUNTIME_PATH: String = "res://scripts/game/game_squad_tactical_plans_runtime.gd"
const ENCOUNTER_ID: String = "training_construct"

var _failed: bool = false


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	_failed = true
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
	var hero := _make_hero()
	state.set("player_character", hero)

	var scene: PackedScene = load(GAME_SCENE) as PackedScene
	if scene == null:
		_fail("Game scene could not be loaded.")
		return
	var game: Node = scene.instantiate()
	root.add_child(game)
	for _frame: int in range(7):
		await process_frame
	if str(game.get_script().resource_path) != RUNTIME_PATH:
		_fail("Game scene does not use the Combat AI runtime layered above pursuit escape.")
		return

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var caretaker: Node = game.get_node_or_null("Caretaker")
	var grid: BattleGrid = get_first_node_in_group("battle_grid") as BattleGrid
	if player == null or caretaker == null or grid == null:
		_fail("Player, caretaker or battle grid is missing.")
		return
	var combat_state: CombatantState = game.get("_player_combat_state") as CombatantState

	await _test_hideout_route(game, state, hero, player, grid, caretaker, combat_state)
	if _failed:
		return
	await _test_room_route(game, state, player, grid, caretaker, combat_state)
	if _failed:
		return
	_test_persistence(state, save_path)
	if _failed:
		return

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Deep hideout, last-seen pursuit, trail tracking, room transition, re-hide and multi-sweep escape smoke test passed.")
	quit(0)


func _test_hideout_route(
	game: Node,
	state: Node,
	hero: PlayerCharacter,
	player: Node2D,
	grid: BattleGrid,
	caretaker: Node,
	combat_state: CombatantState
) -> void:
	(caretaker as Node2D).global_position = Vector2(930.0, 555.0)
	player.global_position = grid.cell_to_world_center(Vector2i(11, 8))
	state.set("player_position", player.global_position)
	await _begin_pursuit_attempt(game, state, caretaker, "hideout")
	if _failed:
		return
	var escape_entry: Dictionary = _find_entry((game.call("_build_catalog_entries") as Dictionary).get("action", []) as Array, "escape")
	if escape_entry.is_empty() or bool(escape_entry.get("enabled", false)):
		_fail("Escape should be disabled before successful hiding.")
		return

	game.call("set_hide_roll_overrides_for_testing", [20])
	game.call("_on_hide_requested")
	await process_frame
	if combat_state == null or not combat_state.hidden:
		_fail("The concealed wall niche did not hide the player.")
		return
	if str(game.call("get_detection_state_for_testing", caretaker)) != "pursuing_last_seen":
		_fail("The caretaker did not pursue the last seen position.")
		return
	game.call("_on_catalog_action_requested", "escape")
	await process_frame
	var progress: Dictionary = game.call("get_escape_progress_for_testing") as Dictionary
	if str(progress.get("route_id", "")) != "collapsed_wall_niche" or not bool(progress.get("objective_ready", false)):
		_fail("The deep hideout did not become the active objective.")
		return
	if bool(game.call("resolve_search_for_testing", caretaker, 1)):
		_fail("One failed search ended the encounter too early.")
		return
	if not bool(game.call("resolve_search_for_testing", caretaker, 1)):
		_fail("Two failed searches did not complete the hideout escape.")
		return
	await process_frame
	if str(state.call("get_encounter_status", ENCOUNTER_ID)) != EncounterSystem.STATUS_ABANDONED:
		_fail("Hideout escape did not abandon the encounter.")
		return
	if hero.experience != 0 or int(state.call("get_item_count", "straw_scrap")) != 0:
		_fail("Escape granted victory rewards.")


func _test_room_route(
	game: Node,
	state: Node,
	player: Node2D,
	grid: BattleGrid,
	caretaker: Node,
	combat_state: CombatantState
) -> void:
	(caretaker as Node2D).global_position = grid.cell_to_world_center(Vector2i(4, 4))
	player.global_position = grid.cell_to_world_center(Vector2i(2, 4))
	state.set("player_position", player.global_position)
	await _begin_pursuit_attempt(game, state, caretaker, "room_transition")
	if _failed:
		return

	game.call("force_hidden_escape_state_for_testing", 18, true)
	var room_path: Array[Vector2i] = [Vector2i(2, 4), Vector2i(1, 4), Vector2i(0, 4)]
	game.call("apply_hidden_path_for_testing", room_path)
	var transition: Dictionary = game.call("get_escape_progress_for_testing") as Dictionary
	if str(transition.get("route_id", "")) != "west_service_room" or not bool(transition.get("room_entered", false)):
		_fail("The adjacent-room route was not activated.")
		return
	if int(transition.get("trace_count", 0)) < 2:
		_fail("Hidden movement did not leave a trackable path.")
		return

	player.global_position = grid.cell_to_world_center(Vector2i(0, 3))
	state.set("player_position", player.global_position)
	game.call("set_hide_roll_overrides_for_testing", [9])
	game.call("_on_hide_requested")
	await process_frame
	var hidden_room: Dictionary = game.call("get_escape_progress_for_testing") as Dictionary
	if not combat_state.hidden or not bool(hidden_room.get("objective_ready", false)):
		_fail("The player did not re-hide inside the adjacent room.")
		return
	if bool(game.call("resolve_search_for_testing", caretaker, 20)):
		_fail("Finding one trace segment incorrectly completed escape.")
		return
	if str(game.call("get_detection_state_for_testing", caretaker)) != "tracking":
		_fail("Successful tracking did not change the enemy state.")
		return
	if bool(game.call("resolve_search_for_testing", caretaker, 1)):
		_fail("One failed search after tracking ended the encounter too early.")
		return
	if not bool(game.call("resolve_search_for_testing", caretaker, 1)):
		_fail("The enemy did not lose the trail after two failed searches.")
		return
	await process_frame
	if str(state.call("get_encounter_status", ENCOUNTER_ID)) != EncounterSystem.STATUS_ABANDONED:
		_fail("Adjacent-room escape did not abandon the encounter.")
		return
	var encounter_state: Dictionary = state.call("get_encounter_state", ENCOUNTER_ID) as Dictionary
	if int(encounter_state.get("attempt_count", 0)) < 2:
		_fail("Retry attempt count was not preserved.")
		return
	if bool(game.call("is_turn_based_combat_active")) or combat_state.hidden:
		_fail("Combat or hidden state leaked after escape.")


func _begin_pursuit_attempt(game: Node, state: Node, caretaker: Node, source_id: String) -> void:
	if caretaker.has_method("reset_combat_state"):
		caretaker.call("reset_combat_state", true)
	# This smoke validates one observer. Reset the new reinforcement so a previous
	# abandoned attempt does not intentionally add a second searcher.
	var guard: Node = game.call("get_patrol_actor_for_testing", "service_guard") as Node
	if guard != null:
		if guard.has_method("reset_combat_state"):
			guard.call("reset_combat_state", true)
		var guard_record: Dictionary = state.call("get_stealth_alert_record", "service_guard") as Dictionary
		guard_record["state"] = StealthAlertSystem.STATE_CALM
		guard_record["suspicion"] = 0.0
		guard_record["last_known_position"] = [0.0, 0.0]
		state.call("set_stealth_alert_record", "service_guard", guard_record, false, false)
		game.call("_restore_exploration_alerts")
	var begin_result: Dictionary = state.call(
		"begin_encounter",
		ENCOUNTER_ID,
		{"source_type": "pursuit_smoke", "source_id": source_id},
		false,
		false
	) as Dictionary
	if not bool(begin_result.get("success", false)) and not bool(begin_result.get("duplicate", false)):
		_fail("Training encounter could not begin for pursuit smoke testing.")
		return
	game.call("_start_turn_based_combat", caretaker)
	game.call("force_active_escape_encounter_for_testing", ENCOUNTER_ID)
	game.call("force_player_turn_for_testing")
	await process_frame
	if not bool(game.call("is_turn_based_combat_active")):
		_fail("Turn-based combat did not start with the mobile enemy observer.")
		return
	if str(state.call("get_encounter_status", ENCOUNTER_ID)) != EncounterSystem.STATUS_ACTIVE:
		_fail("Encounter registry is not active during pursuit.")


func _test_persistence(state: Node, save_path: String) -> void:
	if not bool(state.call("save_game")):
		_fail("Abandoned encounter could not be saved.")
		return
	state.set("story_flags", {})
	state.set("quest_states", {})
	state.set("inventory", {})
	if not bool(state.call("load_game")):
		_fail("Abandoned encounter save could not be loaded.")
		return
	if str(state.call("get_encounter_status", ENCOUNTER_ID)) != EncounterSystem.STATUS_ABANDONED:
		_fail("Abandoned encounter state was not preserved by save/load.")
		return
	if not bool(state.call("get_flag", "training_construct_alerted", false)):
		_fail("Persistent alert flag was not preserved.")
		return
	if not FileAccess.file_exists(save_path):
		_fail("Save file disappeared during persistence test.")


func _make_hero() -> PlayerCharacter:
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
	return hero


func _find_entry(entries: Array, action_id: String) -> Dictionary:
	for value: Variant in entries:
		if value is Dictionary and str((value as Dictionary).get("id", "")) == action_id:
			return (value as Dictionary).duplicate(true)
	return {}
