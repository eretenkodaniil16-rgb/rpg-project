extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const EXPECTED_RUNTIME: String = "res://scripts/game/game_guard_post_two_room_runtime.gd"
const FIRST_ROOM_ID: String = "vault_guard_post_01"
const SECOND_ROOM_ID: String = "vault_inner_watch_01"
const MUG_ID: String = "guard_post_mug_01"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	var save_path: String = ProjectSettings.globalize_path("user://savegame.json")
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	state.call("new_game")
	state.set("player_character", _make_hero())

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	var game: Node = packed.instantiate() if packed != null else null
	if game == null:
		_fail("Guard post game scene could not be instantiated.")
		return
	root.add_child(game)
	for _frame: int in range(40):
		await process_frame
	var game_script: Script = game.get_script() as Script
	if game_script == null or game_script.resource_path != EXPECTED_RUNTIME:
		_fail("Game scene does not use the two-room guard post runtime.")
		return
	game.set_process(false)

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var caretaker: Node = game.get_node_or_null("Caretaker")
	var catalog: ActionCatalogUI = game.get_node_or_null("Interface/ActionCatalogUI") as ActionCatalogUI
	var turn_system: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	if player == null or caretaker == null or catalog == null or turn_system == null:
		_fail("Guard post runtime fixtures are incomplete.")
		return
	if str(game.call("_encounter_id_for_actor", caretaker)) != FIRST_ROOM_ID:
		_fail("Caretaker was not mapped to the first-room encounter.")
		return

	player.global_position = Vector2(620.0, 360.0)
	state.set("player_position", player.global_position)
	game.call("_evaluate_guard_post_state")
	if str(state.call("get_encounter_status", FIRST_ROOM_ID)) != EncounterSystem.STATUS_ACTIVE:
		_fail("Approaching the first room did not activate its encounter.")
		return

	var mug: ThrowableWorldProp = game.call("get_throwable_prop_node_for_testing", MUG_ID) as ThrowableWorldProp
	if mug == null or not mug.is_available_for_pickup():
		_fail("Playable ceramic mug prop is missing.")
		return
	player.global_position = mug.global_position
	state.set("player_position", player.global_position)

	game.call("_start_turn_based_combat", caretaker)
	await process_frame
	if not turn_system.active:
		_fail("Combat did not start in the first room.")
		return
	if str(game.call("get_active_combat_encounter_id_for_testing")) != FIRST_ROOM_ID:
		_fail("First-room combat retained the wrong encounter id.")
		return
	if not bool(state.call("get_flag", "vault_guard_post_room1_combat_started", false)):
		_fail("Starting first-room combat did not persist the route lock.")
		return
	game.call("force_player_turn_for_testing")
	game.set("_enemy_turn_running", false)
	game.call("_refresh_action_catalog")
	await process_frame
	var pickup_entry: Dictionary = _find_action(catalog.get_entries_for_testing(), "%s%s" % ["pickup_throwable_prop__", MUG_ID], "bonus")
	if pickup_entry.is_empty() or not bool(pickup_entry.get("enabled", false)):
		_fail("Nearby interior prop is not offered as a bonus action.")
		return
	catalog.action_requested.emit(str(pickup_entry.get("id", "")))
	await process_frame
	if str(game.call("get_held_throwable_prop_id_for_testing")) != MUG_ID:
		_fail("Bonus action did not place the mug in the hero's hands.")
		return
	if turn_system.bonus_action_available or mug.is_available_for_pickup():
		_fail("Picking up the prop did not consume the bonus action and remove it from the world.")
		return

	game.call("_set_selected_target", null)
	game.call("_face_toward", player.global_position + Vector2.RIGHT * 200.0)
	game.call("_refresh_action_catalog")
	await process_frame
	var throw_entry: Dictionary = _find_action(catalog.get_entries_for_testing(), "throw_held_prop", "action")
	if throw_entry.is_empty() or not bool(throw_entry.get("enabled", false)):
		_fail("Held interior prop is not offered as an action throw.")
		return
	var noise_before: Array[Dictionary] = state.call("get_stealth_noise_events", 0) as Array[Dictionary]
	catalog.action_requested.emit("throw_held_prop")
	await create_timer(0.45).timeout
	if not str(game.call("get_held_throwable_prop_id_for_testing")).is_empty():
		_fail("Hands remained occupied after throwing the prop.")
		return
	if turn_system.action_available:
		_fail("Throwing the prop did not consume the action.")
		return
	var noise_after: Array[Dictionary] = state.call("get_stealth_noise_events", 0) as Array[Dictionary]
	if noise_after.size() <= noise_before.size():
		_fail("Thrown prop did not create a stealth noise event.")
		return
	var latest_noise: Dictionary = noise_after[noise_after.size() - 1]
	if str(latest_noise.get("noise_type", "")) != "thrown_object" or int(latest_noise.get("radius_feet", 0)) < 40:
		_fail("Thrown prop noise has incorrect type or radius: %s" % JSON.stringify(latest_noise))
		return
	var registry: Dictionary = game.call("get_throwable_registry_for_testing") as Dictionary
	var mug_record: Dictionary = (registry.get("props", {}) as Dictionary).get(MUG_ID, {}) as Dictionary
	if str(mug_record.get("state", "")) != ThrowablePropSystem.STATE_BROKEN:
		_fail("Breakable mug impact was not persisted.")
		return

	var room: Node = game.get_node_or_null("StealthTestRoom")
	var door: Node = room.call("get_test_door") if room != null else null
	var environment: CombatEnvironment = get_first_node_in_group("combat_environment") as CombatEnvironment
	var grid: BattleGrid = game.call("_get_battle_grid") as BattleGrid
	if door == null or environment == null or grid == null:
		_fail("Door or grid is unavailable for throw obstruction simulation.")
		return
	door.call("set_door_state", "closed", false)
	var door_edges: Array[Dictionary] = environment.get_edge_blocker_edges_for_testing("west_service_door_blocker")
	if door_edges.is_empty():
		_fail("Door edge is missing from throw obstruction simulation.")
		return
	var edge: Dictionary = door_edges[0]
	var left_cell: Vector2i = edge.get("a", Vector2i.ZERO) as Vector2i
	var right_cell: Vector2i = edge.get("b", Vector2i.ZERO) as Vector2i
	var blocked_landing: Vector2 = game.call(
		"resolve_throw_landing_for_testing",
		grid.cell_to_world_center(left_cell),
		grid.cell_to_world_center(right_cell)
	) as Vector2
	if grid.world_to_cell(blocked_landing) != left_cell:
		_fail("Thrown prop crossed a closed door edge.")
		return

	turn_system.stop_combat()
	game.set("_active_combat_encounter_id", "")
	state.call("set_flag", "caretaker_convinced", true)
	game.call("_evaluate_guard_post_state")
	if str(state.call("get_encounter_status", FIRST_ROOM_ID)) != EncounterSystem.STATUS_ACTIVE:
		_fail("A stale dialogue flag changed a started combat back to a peaceful resolution.")
		return
	state.call("set_flag", "caretaker_convinced", false)
	game.call("resolve_first_room_for_testing", "guards_defeated")
	var first_state: Dictionary = state.call("get_encounter_state", FIRST_ROOM_ID) as Dictionary
	if str(first_state.get("resolution_id", "")) != "guards_defeated":
		_fail("First-room combat resolution did not complete.")
		return
	if bool(state.call("has_claimed_experience_reward", "encounter_vault_guard_post_01")):
		_fail("The full encounter reward was issued before the second room.")
		return

	var second_begin: Dictionary = state.call(
		"begin_encounter",
		SECOND_ROOM_ID,
		{"source_type": "test", "source_id": "delayed_reward"},
		false,
		false
	) as Dictionary
	if not bool(second_begin.get("success", false)) and not bool(second_begin.get("duplicate", false)):
		_fail("Second-room encounter could not begin for delayed reward validation.")
		return
	var second_result: Dictionary = state.call(
		"resolve_encounter",
		SECOND_ROOM_ID,
		"inner_watch_defeated",
		{"source_type": "test", "source_id": "delayed_reward"},
		false,
		false
	) as Dictionary
	if not bool(second_result.get("success", false)):
		_fail("Second-room resolution did not complete: %s" % JSON.stringify(second_result))
		return
	if not bool(state.call("has_claimed_experience_reward", "encounter_vault_guard_post_01")):
		_fail("The unique encounter reward was not issued after the second room.")
		return
	var duplicate: Dictionary = state.call("resolve_encounter", SECOND_ROOM_ID, "inner_watch_subdued", {}, false, false) as Dictionary
	if not bool(duplicate.get("duplicate", false)):
		_fail("The second-room reward could be claimed through another resolution.")
		return

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Combat route lock, throwable noise, door blocking and delayed unique reward passed.")
	quit(0)


func _find_action(catalog: Dictionary, action_id: String, category_id: String) -> Dictionary:
	var values: Variant = catalog.get(category_id, [])
	if not values is Array:
		return {}
	for value: Variant in values as Array:
		if value is Dictionary and str((value as Dictionary).get("id", "")) == action_id:
			return (value as Dictionary).duplicate(true)
	return {}


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель караульного поста"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.level = 5
	hero.maximum_health = 42
	hero.current_health = 42
	hero.hit_die_size = 10
	hero.hit_dice_maximum = 5
	hero.hit_dice_current = 5
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
