extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const EXPECTED_RUNTIME: String = "res://scripts/game/game_guard_post_polish_runtime.gd"
const FIRST_ROOM_ID: String = "vault_guard_post_01"
const SECOND_ROOM_ID: String = "vault_inner_watch_01"
const MUG_ID: String = "guard_post_mug_01"
const PICKUP_ACTION_ID: String = "pickup_throwable_prop__guard_post_mug_01"


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

	var game: Node = (load(GAME_SCENE) as PackedScene).instantiate()
	root.add_child(game)
	for _frame: int in range(40):
		await process_frame
	var game_script: Script = game.get_script() as Script
	if game_script == null or game_script.resource_path != EXPECTED_RUNTIME:
		_fail("Game scene does not use the polished guard post runtime.")
		return
	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var caretaker: Node = game.get_node_or_null("Caretaker")
	var room: Node = game.get_node_or_null("StealthTestRoom")
	var catalog: ActionCatalogUI = game.get_node_or_null("Interface/ActionCatalogUI") as ActionCatalogUI
	var turn_system: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	var mug: ThrowableWorldProp = game.call("get_throwable_prop_node_for_testing", MUG_ID) as ThrowableWorldProp
	if player == null or caretaker == null or room == null or catalog == null or turn_system == null or mug == null:
		_fail("Guard post runtime fixtures are incomplete.")
		return

	player.global_position = Vector2(620.0, 360.0)
	state.set("player_position", player.global_position)
	game.call("_evaluate_guard_post_state")
	if str(state.call("get_encounter_status", FIRST_ROOM_ID)) != EncounterSystem.STATUS_ACTIVE:
		_fail("Approaching the first room did not activate its encounter.")
		return

	player.global_position = mug.global_position
	state.set("player_position", player.global_position)
	for _frame: int in range(6):
		await physics_frame
		await process_frame
	if not player.call("has_registered_interactable", mug):
		_fail("The mug trigger did not register with the player.")
		return

	game.call("_start_turn_based_combat", caretaker)
	await process_frame
	if not turn_system.active or str(game.call("get_active_combat_encounter_id_for_testing")) != FIRST_ROOM_ID:
		_fail("First-room combat did not start with the correct encounter.")
		return
	if not bool(state.call("get_flag", "vault_guard_post_room1_combat_started", false)):
		_fail("Starting combat did not persist the route lock.")
		return
	game.call("force_player_turn_for_testing")
	game.set("_enemy_turn_running", false)
	game.call("_refresh_action_catalog")
	await process_frame
	var pickup_entry: Dictionary = _find_action(catalog.get_entries_for_testing(), PICKUP_ACTION_ID, "bonus")
	if pickup_entry.is_empty() or not bool(pickup_entry.get("enabled", false)):
		_fail("Nearby mug is not offered as a bonus action.")
		return
	catalog.action_requested.emit(PICKUP_ACTION_ID)
	await process_frame
	if str(game.call("get_held_throwable_prop_id_for_testing")) != MUG_ID or turn_system.bonus_action_available:
		_fail("Picking up the mug did not occupy the hands and consume the bonus action.")
		return

	game.call("_set_selected_target", null)
	game.call("_face_toward", player.global_position + Vector2.RIGHT * 200.0)
	game.call("_refresh_action_catalog")
	await process_frame
	var throw_entry: Dictionary = _find_action(catalog.get_entries_for_testing(), "throw_held_prop", "action")
	if throw_entry.is_empty() or not bool(throw_entry.get("enabled", false)):
		_fail("Held mug is not offered as an action throw.")
		return
	var noise_before: Array[Dictionary] = state.call("get_stealth_noise_events", 0) as Array[Dictionary]
	catalog.action_requested.emit("throw_held_prop")
	await create_timer(0.5).timeout
	if not str(game.call("get_held_throwable_prop_id_for_testing")).is_empty() or turn_system.action_available:
		_fail("Throwing the mug did not clear the hands and consume the action.")
		return
	var noise_after: Array[Dictionary] = state.call("get_stealth_noise_events", 0) as Array[Dictionary]
	if noise_after.size() <= noise_before.size():
		_fail("Thrown mug did not create a noise event.")
		return
	var latest_noise: Dictionary = noise_after.back()
	if str(latest_noise.get("noise_type", "")) != "thrown_object" or int(latest_noise.get("radius_feet", 0)) < 40:
		_fail("Thrown mug noise has incorrect data: %s" % JSON.stringify(latest_noise))
		return
	var registry: Dictionary = game.call("get_throwable_registry_for_testing") as Dictionary
	var mug_record: Dictionary = (registry.get("props", {}) as Dictionary).get(MUG_ID, {}) as Dictionary
	if str(mug_record.get("state", "")) != ThrowablePropSystem.STATE_BROKEN:
		_fail("Breakable mug impact was not persisted.")
		return

	var door: Node = room.call("get_test_door")
	var environment: CombatEnvironment = get_first_node_in_group("combat_environment") as CombatEnvironment
	var grid: BattleGrid = game.call("_get_battle_grid") as BattleGrid
	door.call("set_door_state", "closed", false)
	var door_edges: Array[Dictionary] = environment.get_edge_blocker_edges_for_testing("west_service_door_blocker")
	if door_edges.is_empty():
		_fail("Door edge is missing from throw obstruction simulation.")
		return
	var edge: Dictionary = door_edges[0]
	var left_cell: Vector2i = edge.get("a", Vector2i.ZERO) as Vector2i
	var right_cell: Vector2i = edge.get("b", Vector2i.ZERO) as Vector2i
	var blocked_landing: Vector2 = game.call("resolve_throw_landing_for_testing", grid.cell_to_world_center(left_cell), grid.cell_to_world_center(right_cell)) as Vector2
	if grid.world_to_cell(blocked_landing) != left_cell:
		_fail("Thrown object crossed a closed door edge.")
		return

	turn_system.stop_combat()
	game.set("_active_combat_encounter_id", "")
	state.call("set_flag", "caretaker_convinced", true)
	game.call("_evaluate_guard_post_state")
	if str(state.call("get_encounter_status", FIRST_ROOM_ID)) != EncounterSystem.STATUS_ACTIVE:
		_fail("A stale dialogue flag replaced an already-started combat route.")
		return
	state.call("set_flag", "caretaker_convinced", false)
	game.call("resolve_first_room_for_testing", "guards_defeated")
	if bool(state.call("has_claimed_experience_reward", "encounter_vault_guard_post_01")):
		_fail("Full encounter XP was issued before the inner room.")
		return
	state.call("begin_encounter", SECOND_ROOM_ID, {"source_type": "test"}, false, false)
	var second_result: Dictionary = state.call("resolve_encounter", SECOND_ROOM_ID, "inner_watch_defeated", {"source_type": "test"}, false, false) as Dictionary
	if not bool(second_result.get("success", false)):
		_fail("Inner room could not resolve for delayed reward validation.")
		return
	if not bool(state.call("has_claimed_experience_reward", "encounter_vault_guard_post_01")):
		_fail("Unique encounter XP was not issued after the inner room.")
		return
	var duplicate: Dictionary = state.call("resolve_encounter", SECOND_ROOM_ID, "inner_watch_subdued", {}, false, false) as Dictionary
	if not bool(duplicate.get("duplicate", false)):
		_fail("Inner-room reward could be claimed twice.")
		return

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Combat route lock, throwable noise, door blocking and delayed reward passed.")
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
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
