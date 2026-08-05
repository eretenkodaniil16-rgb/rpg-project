extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const FIRST_ROOM_ID: String = "vault_guard_post_01"
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
		_fail("Guard post scene could not be instantiated.")
		return
	root.add_child(game)
	for _frame: int in range(40):
		await process_frame

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var caretaker: Node2D = game.get_node_or_null("Caretaker") as Node2D
	var room: GuardPostTwoRoomVisibility = game.get_node_or_null("StealthTestRoom") as GuardPostTwoRoomVisibility
	var dialogue: Control = game.get_node_or_null("Interface/DialogueUI") as Control
	var catalog: ActionCatalogUI = game.get_node_or_null("Interface/ActionCatalogUI") as ActionCatalogUI
	var mobile: Control = game.get_node_or_null("Interface/MobileControls") as Control
	if player == null or caretaker == null or room == null or dialogue == null or catalog == null or mobile == null:
		_fail("Parley and presentation fixtures are incomplete.")
		return
	var guard: Node = room.get_patrol_observer()
	var west_door: StealthDoor = room.get_test_door()
	var inner_gate: StealthDoor = room.get_inner_gate()
	var fog: RoomFogOverlay = room.get_room_fog_for_testing()
	if guard == null or west_door == null or inner_gate == null or fog == null:
		_fail("Guard, doors or room fog were not installed.")
		return

	var outer_position := Vector2(650.0, 360.0)
	player.global_position = outer_position
	caretaker.global_position = outer_position + Vector2(34.0, 0.0)
	state.set("player_position", player.global_position)
	if caretaker.has_method("set_facing_direction"):
		caretaker.call("set_facing_direction", player.global_position - caretaker.global_position)
	game.call("_set_selected_target", null)
	game.call("_evaluate_guard_post_state")
	for _frame: int in range(12):
		await physics_frame
		await process_frame
	if str(state.call("get_encounter_status", FIRST_ROOM_ID)) != EncounterSystem.STATUS_ACTIVE:
		_fail("First room did not become active before the caretaker conversation.")
		return
	if not player.call("has_registered_interactable", caretaker):
		_fail("Entering the caretaker trigger did not register the NPC interaction.")
		return

	mobile.call("enable_for_testing")
	game.call("_refresh_action_catalog")
	mobile.call("simulate_actions_touch_for_testing")
	await process_frame
	if not catalog.is_catalog_open():
		_fail("The completed mobile Actions gesture did not open the catalog.")
		return
	if not _visible_action_button_contains(catalog, "ПОГОВОРИТЬ: СМОТРИТЕЛЬ"):
		_fail("Entering the trigger did not open the WORLD actions containing caretaker dialogue.")
		return
	var caretaker_action_id: String = "%s%d" % [WORLD_ACTION_PREFIX, caretaker.get_instance_id()]
	var caretaker_entry: Dictionary = _find_action(catalog.get_entries_for_testing(), caretaker_action_id)
	if caretaker_entry.is_empty() or not bool(caretaker_entry.get("enabled", false)):
		_fail("Caretaker-specific interaction is unavailable without a selected target.")
		return
	catalog.call("_emit_action", caretaker_action_id, str(caretaker_entry.get("description", "")), true)
	await process_frame
	if not dialogue.visible:
		_fail("Caretaker dialogue did not open from the trigger-zone action.")
		return
	if dialogue.call("get_attack_button_for_testing") == null:
		_fail("Dialogue did not retain the caretaker as its concrete target.")
		return

	# Reproduce the stale-alert condition that previously started combat as soon
	# as the successful dialogue was closed.
	game.call("_update_exploration_actor", caretaker, 3.0)
	game.call("_update_exploration_actor", guard, 3.0)
	await process_frame
	if (game.get("_turn_system") as TurnBasedCombatSystem).active:
		_fail("Parley-neutral visual contact started combat during dialogue.")
		return

	dialogue.call("_on_choice_pressed", {
		"response": "Смотритель разрешает пройти.",
		"encounter_id": "caretaker_revelation",
		"resolution_id": "persuaded"
	})
	for _frame: int in range(4):
		await process_frame
	dialogue.call("_close_dialogue")
	for _frame: int in range(12):
		await process_frame
	var turn_system: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	if turn_system.active:
		_fail("Successful caretaker dialogue still started combat after closing.")
		return
	var first_state: Dictionary = state.call("get_encounter_state", FIRST_ROOM_ID) as Dictionary
	if str(first_state.get("resolution_id", "")) != "peaceful_passage":
		_fail("Successful persuasion did not resolve the first room peacefully.")
		return
	for actor: Node in [caretaker, guard]:
		if actor.has_method("is_hostile") and bool(actor.call("is_hostile")):
			_fail("A first-room actor remained hostile after peaceful authorization.")
			return
		var actor_id: String = str(actor.call("get_actor_id"))
		var record: Dictionary = state.call("get_stealth_alert_record", actor_id) as Dictionary
		if str(record.get("state", "")) != StealthAlertSystem.STATE_CALM:
			_fail("Peaceful authorization did not clear %s alert state: %s" % [actor_id, JSON.stringify(record)])
			return

	var west_visual: StealthDoorVisualDecorator = room.get_door_decorator_for_testing(west_door)
	var inner_visual: StealthDoorVisualDecorator = room.get_door_decorator_for_testing(inner_gate)
	if west_visual == null or inner_visual == null:
		_fail("Door presentation decorators are missing.")
		return
	if west_visual.get_visual_width_for_testing() <= 24.0 or not west_visual.has_handle_for_testing():
		_fail("The service door is still not visually distinct from the thin wall.")
		return
	west_door.set_door_state("closed", false)
	await process_frame
	if absf(west_visual.get_leaf_rotation_degrees_for_testing()) > 1.0:
		_fail("Closed door leaf has an incorrect visual rotation.")
		return
	west_door.set_door_state("open", false)
	await process_frame
	if west_visual.get_leaf_rotation_degrees_for_testing() < 70.0:
		_fail("Opened door does not have a readable open-leaf silhouette.")
		return

	if fog.get_current_room_id_for_testing() != GuardPostTwoRoomVisibility.ROOM_OUTER_GUARD:
		_fail("Outer guard room was not recognized as the current visible room.")
		return
	if not fog.is_room_concealed_for_testing(GuardPostTwoRoomVisibility.ROOM_INNER_WATCH):
		_fail("Inner watch remains visible through its closed partition.")
		return
	var inner_x: float = room.get_inner_partition_global_x()
	player.global_position = Vector2(inner_x + 96.0, 360.0)
	state.set("player_position", player.global_position)
	for _frame: int in range(5):
		await process_frame
	if fog.get_current_room_id_for_testing() != GuardPostTwoRoomVisibility.ROOM_INNER_WATCH:
		_fail("Room fog did not reveal the room entered by the player.")
		return
	if not fog.is_room_concealed_for_testing(GuardPostTwoRoomVisibility.ROOM_OUTER_GUARD):
		_fail("The room left behind remains visible through the partition.")
		return

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Target-free caretaker parley, peaceful alert cleanup, readable doors and room fog passed.")
	quit(0)


func _visible_action_button_contains(catalog: ActionCatalogUI, expected_text: String) -> bool:
	if catalog.action_grid == null:
		return false
	for child: Node in catalog.action_grid.get_children():
		if child is Button and (child as Button).text == expected_text:
			return true
	return false


func _find_action(entries: Dictionary, action_id: String) -> Dictionary:
	var values: Variant = entries.get("action", [])
	if not values is Array:
		return {}
	for value: Variant in values as Array:
		if value is Dictionary and str((value as Dictionary).get("id", "")) == action_id:
			return (value as Dictionary).duplicate(true)
	return {}


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель мирного прохода"
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
