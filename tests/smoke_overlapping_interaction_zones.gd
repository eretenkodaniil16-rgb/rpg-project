extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const MUG_ID: String = "guard_post_mug_01"
const PICKUP_ACTION_ID: String = "pickup_throwable_prop__guard_post_mug_01"
const WORLD_ACTION_PREFIX: String = "world_interact__"


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
		_fail("Game scene could not be instantiated.")
		return
	root.add_child(game)
	for _frame: int in range(30):
		await process_frame
	game.set_process(false)

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var caretaker: Node2D = game.get_node_or_null("Caretaker") as Node2D
	var room: Node = game.get_node_or_null("StealthTestRoom")
	var catalog: ActionCatalogUI = game.get_node_or_null("Interface/ActionCatalogUI") as ActionCatalogUI
	var dialogue: Control = game.get_node_or_null("Interface/DialogueUI") as Control
	var grid: BattleGrid = game.call("_get_battle_grid") as BattleGrid
	var mug: ThrowableWorldProp = game.call("get_throwable_prop_node_for_testing", MUG_ID) as ThrowableWorldProp
	var door: Node = room.call("get_test_door") if room != null and room.has_method("get_test_door") else null
	if player == null or caretaker == null or room == null or catalog == null or dialogue == null or grid == null or mug == null or door == null:
		_fail("Overlapping interaction fixtures are incomplete.")
		return

	var door_edges: Array[Dictionary] = (get_first_node_in_group("combat_environment") as CombatEnvironment).get_edge_blocker_edges_for_testing("west_service_door_blocker")
	if door_edges.is_empty():
		_fail("West service door edge is missing.")
		return
	var player_cell: Vector2i = door_edges[0].get("a", CombatEnvironment.INVALID_CELL) as Vector2i
	var overlap_position: Vector2 = grid.cell_to_world_center(player_cell)
	door.call("set_door_state", "closed", false)
	player.global_position = overlap_position
	caretaker.global_position = overlap_position + Vector2(20.0, -12.0)
	mug.global_position = overlap_position + Vector2(-16.0, 14.0)
	state.set("player_position", player.global_position)
	for _frame: int in range(12):
		await physics_frame
		await process_frame

	var nearby: Array[Node] = player.call("get_nearby_interactables") as Array[Node]
	if not nearby.has(door):
		_fail("Door trigger zone was overwritten by another overlapping zone.")
		return
	if not nearby.has(caretaker):
		_fail("Caretaker trigger zone was overwritten by another overlapping zone.")
		return
	if not nearby.has(mug):
		_fail("Mug trigger zone was not registered alongside door and caretaker.")
		return

	game.call("_refresh_action_catalog")
	await process_frame
	var entries: Dictionary = catalog.get_entries_for_testing()
	var door_action_id: String = "%s%d" % [WORLD_ACTION_PREFIX, door.get_instance_id()]
	var caretaker_action_id: String = "%s%d" % [WORLD_ACTION_PREFIX, caretaker.get_instance_id()]
	var door_entry: Dictionary = _find_action(entries, "action", door_action_id)
	var caretaker_entry: Dictionary = _find_action(entries, "action", caretaker_action_id)
	var mug_entry: Dictionary = _find_action(entries, "action", PICKUP_ACTION_ID)
	if door_entry.is_empty() or caretaker_entry.is_empty() or mug_entry.is_empty():
		_fail("Action catalog did not expose door, caretaker and mug as three separate entries: %s" % JSON.stringify(entries))
		return
	var unique_ids: Dictionary = {
		door_action_id: true,
		caretaker_action_id: true,
		PICKUP_ACTION_ID: true
	}
	if unique_ids.size() != 3:
		_fail("Overlapping interactions do not have stable unique action IDs.")
		return

	catalog.call("_emit_action", door_action_id, str(door_entry.get("description", "")), true)
	await process_frame
	if str(door.call("get_door_state")) != "open":
		_fail("Selecting the door-specific action did not open the door.")
		return
	if dialogue.visible:
		_fail("Door-specific action also triggered caretaker dialogue.")
		return
	if not mug.is_available_for_pickup():
		_fail("Door-specific action also consumed the mug.")
		return

	catalog.call("_emit_action", caretaker_action_id, str(caretaker_entry.get("description", "")), true)
	await process_frame
	if not dialogue.visible:
		_fail("Selecting the caretaker-specific action did not open dialogue.")
		return
	if str(door.call("get_door_state")) != "open" or not mug.is_available_for_pickup():
		_fail("Caretaker-specific action changed another overlapping object.")
		return
	dialogue.hide()
	state.set("input_locked", false)

	catalog.call("_emit_action", PICKUP_ACTION_ID, str(mug_entry.get("description", "")), true)
	await process_frame
	if str(game.call("get_held_throwable_prop_id_for_testing")) != MUG_ID:
		_fail("Selecting the mug-specific action did not pick up the mug.")
		return
	if str(door.call("get_door_state")) != "open":
		_fail("Mug-specific action changed the overlapping door.")
		return
	if caretaker.has_method("is_hostile") and bool(caretaker.call("is_hostile")):
		_fail("Mug-specific action made the overlapping caretaker hostile.")
		return

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Overlapping door, caretaker and prop trigger zones expose independent actions.")
	quit(0)


func _find_action(entries: Dictionary, category_id: String, action_id: String) -> Dictionary:
	var value: Variant = entries.get(category_id, [])
	if not value is Array:
		return {}
	for entry_value: Variant in value as Array:
		if entry_value is Dictionary and str((entry_value as Dictionary).get("id", "")) == action_id:
			return (entry_value as Dictionary).duplicate(true)
	return {}


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель зон взаимодействия"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.level = 3
	hero.maximum_health = 28
	hero.current_health = 28
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
