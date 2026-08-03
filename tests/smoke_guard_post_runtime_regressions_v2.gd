extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"

var _failed: bool = false


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	state.call("new_game")
	state.set("player_character", _make_hero())
	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	var game: Node = packed.instantiate() if packed != null else null
	if game == null:
		_fail("Game scene could not be instantiated.")
		return
	root.add_child(game)
	for _frame: int in range(50):
		await process_frame

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var room: GuardPostTwoRoomVisibility = game.get_node_or_null("StealthTestRoom") as GuardPostTwoRoomVisibility
	var target_button: Button = game.get_node_or_null("Interface/TargetButton") as Button
	var catalog: ActionCatalogUI = game.get_node_or_null("Interface/ActionCatalogUI") as ActionCatalogUI
	var mobile: Control = game.get_node_or_null("Interface/MobileControls") as Control
	if player == null or room == null or target_button == null or catalog == null or mobile == null:
		_fail("Runtime regression fixtures are incomplete.")
		return
	mobile.call("enable_for_testing")
	var actions_button: Button = mobile.call("get_actions_button_for_testing") as Button
	if actions_button == null:
		_fail("Actions button is missing from the runtime regression.")
		return
	var guard: Node = room.get_patrol_observer()
	var marksman: Node = room.get_training_marksman()
	var mage: Node = room.get_training_mage()
	var west_door: StealthDoor = room.get_test_door()
	var inner_gate: StealthDoor = room.get_inner_gate()
	if guard == null or marksman == null or mage == null or west_door == null or inner_gate == null:
		_fail("Guard-post actors or doors are missing.")
		return

	inner_gate.set_door_state("open", false)
	player.global_position = Vector2(room.get_inner_partition_global_x() + 118.0, 360.0)
	state.set("player_position", player.global_position)
	for _frame: int in range(6):
		await process_frame
	var selected_ids: Dictionary = {}
	for _press: int in range(7):
		target_button.emit_signal("pressed")
		await process_frame
		var selected: Node = game.get("_selected_target") as Node
		if is_instance_valid(selected) and selected.has_method("get_actor_id"):
			selected_ids[str(selected.call("get_actor_id"))] = true
	if not bool(selected_ids.get("training_marksman", false)) or not bool(selected_ids.get("training_mage", false)):
		_fail("Marksman and Rune Tactician are not both selectable before combat: %s" % JSON.stringify(selected_ids))
		return
	if bool(game.call("is_turn_based_combat_active")):
		_fail("Pre-combat target cycling started initiative.")
		return

	west_door.set_door_state("closed", false)
	player.global_position = Vector2(100.0, 110.0)
	state.set("player_position", player.global_position)
	(guard as Node2D).global_position = Vector2(760.0, 180.0)
	guard.call("set_facing_direction", Vector2.RIGHT)
	var record: Dictionary = state.call("get_stealth_alert_record", "service_guard") as Dictionary
	record["state"] = StealthAlertSystem.STATE_CALM
	record["suspicion"] = 0.0
	record["last_known_position"] = []
	state.call("set_stealth_alert_record", "service_guard", record, false, false)
	game.call("_restore_exploration_alerts")
	for _frame: int in range(4):
		await process_frame
	if bool(game.call("_target_is_visible_to_player", guard)):
		_fail("Unseen patrol fixture exposes the guard through room fog.")
		return
	game.call("force_patrol_tick_for_testing", guard, 0.7)
	var patrol_start: Vector2 = (guard as Node2D).global_position
	catalog.require_explicit_open_for_testing(true)
	mobile.call("simulate_actions_touch_for_testing")
	if not catalog.is_catalog_open():
		_fail("A normal quick Actions tap did not open the patrol test overlay.")
		return
	for _tick: int in range(10):
		game.call("_update_exploration_alerts", 0.25)
		await process_frame
	if (guard as Node2D).global_position.distance_to(patrol_start) <= 0.5:
		_fail("Unseen service guard stopped patrolling while the non-blocking catalogue was open.")
		return
	catalog.close_catalog()

	catalog.toggle_catalog()
	if catalog.is_catalog_open():
		_fail("Unauthorized generic toggle opened the catalogue immediately.")
		return
	await process_frame
	if catalog.is_catalog_open():
		_fail("Unauthorized generic toggle produced a one-frame catalogue flash.")
		return
	var move_pad: Control = mobile.get_node_or_null("MovePad") as Control
	if move_pad == null:
		_fail("Move pad is missing from the runtime regression.")
		return
	var joystick_press := InputEventScreenTouch.new()
	joystick_press.index = 71
	joystick_press.position = move_pad.get_global_rect().get_center()
	joystick_press.pressed = true
	mobile.call("_input", joystick_press)
	var joystick_release := InputEventScreenTouch.new()
	joystick_release.index = 71
	joystick_release.position = joystick_press.position
	joystick_release.pressed = false
	mobile.call("_input", joystick_release)
	actions_button.emit_signal("pressed")
	if catalog.is_catalog_open():
		_fail("Joystick-origin delayed signal bypassed the GUI-origin catalogue gate.")
		return
	mobile.call("simulate_actions_touch_for_testing")
	if not catalog.is_catalog_open():
		_fail("A fresh normal Actions tap did not open the catalogue.")
		return
	for _frame: int in range(4):
		await process_frame
		if not catalog.is_catalog_open():
			_fail("A fresh normal Actions tap produced a transient catalogue flash.")
			return
	if catalog.has_open_authorization_for_testing():
		_fail("Action catalogue unexpectedly retained an authorization state.")
		return

	print("Pre-combat inner targets, unseen patrol continuity and GUI-origin catalogue gate passed.")
	game.queue_free()
	await process_frame
	quit(0)


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель регрессий"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.level = 5
	hero.maximum_health = 80
	hero.current_health = 80
	return hero


func _fail(message: String) -> void:
	if _failed:
		return
	_failed = true
	push_error(message)
	quit(1)
