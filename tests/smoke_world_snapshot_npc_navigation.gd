extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const MANUAL_SLOT_ID: int = 4
const MANUAL_SAVE_PATH: String = "user://save_slots/manual_04.json"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	_cleanup_saves(state)
	state.call("new_game")
	state.set("player_character", _make_hero())

	var game: Node = await _spawn_game()
	if game == null:
		return
	var fixtures: Dictionary = _fixtures(game)
	if fixtures.is_empty():
		return
	var controller: WorldStateNpcNavigationController = fixtures["controller"] as WorldStateNpcNavigationController
	var player: Node2D = fixtures["player"] as Node2D
	var room: GuardPostTwoRoomVisibility = fixtures["room"] as GuardPostTwoRoomVisibility
	var guard: Node2D = fixtures["guard"] as Node2D
	var caretaker: Node2D = fixtures["caretaker"] as Node2D
	var marksman: Node2D = fixtures["marksman"] as Node2D
	var environment: CombatEnvironment = fixtures["environment"] as CombatEnvironment
	var mobile: Control = fixtures["mobile"] as Control
	var inner_gate: StealthDoor = room.get_inner_gate()

	var render_order: Dictionary = controller.get_visibility_render_order_for_testing()
	if int(render_order.get("wall_z", -1)) <= int(render_order.get("fog_z", -1)):
		_fail("Wall geometry is not rendered above concealed cells.")
		return
	if int(render_order.get("door_z", -1)) <= int(render_order.get("fog_z", -1)):
		_fail("Door geometry is not rendered above concealed cells.")
		return

	var caretaker_trigger: Vector2 = controller.get_npc_trigger_extent_for_testing("caretaker")
	var guard_trigger: Vector2 = controller.get_npc_trigger_extent_for_testing("service_guard")
	if caretaker_trigger.x <= 92.0 or guard_trigger.x <= 34.0:
		_fail("NPC interaction trigger zones were not expanded.")
		return

	var player_start: Vector2 = player.global_position
	mobile.call("enable_for_testing")
	mobile.call("move_joystick_for_testing", Vector2.UP)
	for _frame: int in range(5):
		await process_frame
	var facing_after_joystick: Vector2 = player.call("get_facing_direction") as Vector2
	if facing_after_joystick.dot(Vector2.UP) < 0.95:
		_fail("Mobile joystick did not change the hero facing direction.")
		return
	if player.global_position.distance_to(player_start) > 0.5:
		_fail("Mobile joystick still moved the hero instead of changing facing only.")
		return
	mobile.call("release_joystick_for_testing")

	var click_path: Array[Vector2] = controller.plan_exploration_path_to_world_for_testing(Vector2(520.0, 600.0))
	if click_path.size() < 2:
		_fail("Tap-only exploration path could not be planned.")
		return
	player.call("set_exploration_click_path", click_path)
	for _frame: int in range(18):
		await process_frame
	if player.global_position.distance_to(player_start) < 4.0:
		_fail("Tap-selected exploration route did not move the hero.")
		return
	player.call("cancel_exploration_click_path")

	# Intended facing is retained even when CharacterBody2D is stopped by a wall.
	var partition_x: float = room.get_inner_partition_global_x()
	player.global_position = Vector2(partition_x - 28.0, 150.0)
	state.set("player_position", player.global_position)
	player.call("set_exploration_click_path", [Vector2(partition_x + 80.0, 150.0)])
	for _frame: int in range(18):
		await process_frame
	var wall_facing: Vector2 = player.call("get_facing_direction") as Vector2
	if wall_facing.x < 0.8 or absf(wall_facing.y) > 0.35:
		_fail("Wall collision changed the hero facing to the downward direction.")
		return
	player.call("cancel_exploration_click_path")

	# Directional spells use current facing without requiring a selected marker.
	player.global_position = Vector2(600.0, 360.0)
	caretaker.global_position = Vector2(690.0, 360.0)
	player.call("set_facing_direction", Vector2.RIGHT)
	var predicted: Node = game.call("predict_directional_ability_target_for_testing", "starry_wisp") as Node
	if predicted != caretaker:
		_fail("Directional spell targeting did not resolve the visible actor in front of the hero.")
		return

	# A visible suspicious guard must move and remain outside registered obstacles.
	player.global_position = Vector2(690.0, 210.0)
	guard.global_position = controller.find_safe_world_position_for_testing(guard, Vector2(790.0, 210.0))
	guard.call("set_facing_direction", player.global_position - guard.global_position)
	var guard_record: Dictionary = state.call("get_stealth_alert_record", "service_guard") as Dictionary
	guard_record["state"] = StealthAlertSystem.STATE_SUSPICIOUS
	guard_record["suspicion"] = StealthAlertSystem.SUSPICION_SUSPICIOUS
	guard_record["last_known_position"] = [player.global_position.x, player.global_position.y]
	state.call("set_stealth_alert_record", "service_guard", guard_record, false, false)
	var runtime_records: Dictionary = game.get("_alert_records") as Dictionary
	runtime_records["service_guard"] = guard_record.duplicate(true)
	game.set("_alert_records", runtime_records)
	guard.call("set_exploration_alert_state", StealthAlertSystem.STATE_SUSPICIOUS, StealthAlertSystem.SUSPICION_SUSPICIOUS, player.global_position)
	var guard_before_visible_update: Vector2 = guard.global_position
	for _step: int in range(8):
		controller.call("_update_visible_actor_movement", 0.16)
		await process_frame
	if guard.global_position.distance_to(guard_before_visible_update) < 2.0:
		_fail("Visible NPC remained permanently stationary.")
		return
	if environment.is_position_blocked(guard.global_position, 22.0):
		_fail("Visible NPC movement ended inside an obstacle.")
		return

	var invalid_position := Vector2(845.0, 557.0)
	var repaired: Vector2 = controller.find_safe_world_position_for_testing(guard, invalid_position)
	if repaired.distance_to(invalid_position) < 1.0 or environment.is_position_blocked(repaired, 22.0):
		_fail("NPC obstacle repair did not move an invalid saved position to a safe cell.")
		return

	# Freeze exploration while taking an exact manual snapshot.
	state.set("input_locked", true)
	var saved_guard_position: Vector2 = controller.find_safe_world_position_for_testing(guard, Vector2(742.0, 178.0))
	var saved_marksman_position: Vector2 = controller.find_safe_world_position_for_testing(marksman, Vector2(1080.0, 230.0))
	guard.global_position = saved_guard_position
	guard.call("set_facing_direction", Vector2.UP)
	guard.set("current_health", 7)
	marksman.global_position = saved_marksman_position
	marksman.call("set_facing_direction", Vector2.LEFT)
	marksman.set("current_health", 4)
	player.global_position = Vector2(350.0, 610.0)
	state.set("player_position", player.global_position)
	player.call("set_facing_direction", Vector2.LEFT)
	inner_gate.set_door_state("closed", false)
	guard_record["state"] = StealthAlertSystem.STATE_SEARCHING
	guard_record["suspicion"] = 67.0
	guard_record["last_known_position"] = [515.0, 420.0]
	state.call("set_stealth_alert_record", "service_guard", guard_record, false, false)
	runtime_records = game.get("_alert_records") as Dictionary
	runtime_records["service_guard"] = guard_record.duplicate(true)
	game.set("_alert_records", runtime_records)
	if not bool(state.call("save_manual_slot", MANUAL_SLOT_ID)):
		_fail("Manual world snapshot could not be written.")
		return
	state.set("input_locked", false)

	var save_file: FileAccess = FileAccess.open(MANUAL_SAVE_PATH, FileAccess.READ)
	if save_file == null:
		_fail("Manual world snapshot file is missing.")
		return
	var parsed: Variant = JSON.parse_string(save_file.get_as_text())
	if not parsed is Dictionary:
		_fail("Manual world snapshot is not valid JSON.")
		return
	var save_data: Dictionary = parsed as Dictionary
	if int(save_data.get("version", 0)) != 7:
		_fail("World snapshot did not use save format version 7.")
		return
	var snapshot: Dictionary = save_data.get("world_snapshot", {}) as Dictionary
	var entities: Dictionary = snapshot.get("entities", {}) as Dictionary
	for actor_id: String in ["caretaker", "service_guard", "training_marksman", "training_mage"]:
		if not entities.has(actor_id):
			_fail("World snapshot is missing actor: %s" % actor_id)
			return

	guard.global_position = Vector2(1000.0, 600.0)
	guard.set("current_health", 1)
	guard.call("set_facing_direction", Vector2.DOWN)
	marksman.global_position = Vector2(940.0, 620.0)
	inner_gate.set_door_state("open", false)
	if not bool(state.call("load_manual_slot", MANUAL_SLOT_ID)):
		_fail("Manual world snapshot could not be loaded.")
		return
	# Keep the restored scene static until exact positions are asserted.
	state.set("input_locked", true)
	game.queue_free()
	await process_frame

	var restored_game: Node = await _spawn_game()
	if restored_game == null:
		return
	var restored_fixtures: Dictionary = _fixtures(restored_game)
	if restored_fixtures.is_empty():
		return
	var restored_guard: Node2D = restored_fixtures["guard"] as Node2D
	var restored_marksman: Node2D = restored_fixtures["marksman"] as Node2D
	var restored_room: GuardPostTwoRoomVisibility = restored_fixtures["room"] as GuardPostTwoRoomVisibility
	if restored_guard.global_position.distance_to(saved_guard_position) > 0.5:
		_fail("NPC position was not restored exactly from the manual save.")
		return
	if int(restored_guard.get("current_health")) != 7:
		_fail("NPC health was not restored from the manual save.")
		return
	var restored_guard_facing: Vector2 = restored_guard.call("get_facing_direction") as Vector2
	if restored_guard_facing.dot(Vector2.UP) < 0.95:
		_fail("NPC facing direction was not restored from the manual save.")
		return
	if str(restored_guard.call("get_detection_state")) != StealthAlertSystem.STATE_SEARCHING:
		_fail("NPC alert/search state was not restored from the manual save.")
		return
	if restored_marksman.global_position.distance_to(saved_marksman_position) > 0.5 or int(restored_marksman.get("current_health")) != 4:
		_fail("Second-room NPC state was not restored exactly.")
		return
	if restored_room.get_inner_gate().get_door_state() != "closed":
		_fail("Door state was not restored from the world snapshot.")
		return
	var restored_player: Node2D = restored_fixtures["player"] as Node2D
	var restored_player_facing: Vector2 = restored_player.call("get_facing_direction") as Vector2
	if restored_player_facing.dot(Vector2.LEFT) < 0.95:
		_fail("Hero facing direction was not restored from the manual save.")
		return

	# Active initiative remains intentionally non-serializable.
	state.set("input_locked", false)
	var stable_snapshot_before_combat: Dictionary = state.call("get_world_snapshot") as Dictionary
	restored_game.call("_start_turn_based_combat", restored_guard)
	await process_frame
	if bool(state.call("save_game")):
		_fail("Autosave accepted an unstable active-combat world snapshot.")
		return
	if (state.call("get_world_snapshot") as Dictionary) != stable_snapshot_before_combat:
		_fail("Rejected combat autosave still changed the stable world snapshot.")
		return

	restored_game.queue_free()
	await process_frame
	_cleanup_saves(state)
	print("Exact world snapshot, safe visible NPC movement, expanded triggers, wall occlusion and directional touch controls passed.")
	quit(0)


func _spawn_game() -> Node:
	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	var game: Node = packed.instantiate() if packed != null else null
	if game == null:
		_fail("Game scene could not be instantiated.")
		return null
	root.add_child(game)
	for _frame: int in range(60):
		await process_frame
	return game


func _fixtures(game: Node) -> Dictionary:
	var controller: WorldStateNpcNavigationController = game.get_node_or_null("WorldStateNpcNavigationController") as WorldStateNpcNavigationController
	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var room: GuardPostTwoRoomVisibility = game.get_node_or_null("StealthTestRoom") as GuardPostTwoRoomVisibility
	var caretaker: Node2D = game.get_node_or_null("Caretaker") as Node2D
	var guard: Node2D = room.get_patrol_observer() if room != null else null
	var marksman: Node2D = room.get_training_marksman() if room != null else null
	var mage: Node2D = room.get_training_mage() if room != null else null
	var environment: CombatEnvironment = game.get_node_or_null("CombatEnvironment") as CombatEnvironment
	var mobile: Control = game.get_node_or_null("Interface/MobileControls") as Control
	if controller == null or player == null or room == null or caretaker == null or guard == null or marksman == null or mage == null or environment == null or mobile == null:
		_fail("World snapshot test fixtures are incomplete.")
		return {}
	return {
		"controller": controller,
		"player": player,
		"room": room,
		"caretaker": caretaker,
		"guard": guard,
		"marksman": marksman,
		"mage": mage,
		"environment": environment,
		"mobile": mobile
	}


func _cleanup_saves(state: Node) -> void:
	for slot_id: int in range(1, SaveSlotSystem.MANUAL_SLOT_COUNT + 1):
		state.call("delete_manual_save_slot", slot_id)
	state.call("discard_autosave")


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель мира"
	hero.character_class_id = "wizard"
	hero.character_class_name = "Волшебник"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.level = 5
	hero.maximum_health = 34
	hero.current_health = 34
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
