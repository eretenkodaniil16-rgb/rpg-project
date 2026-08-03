extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"


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
	for _frame: int in range(20):
		await process_frame

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var room: GuardPostTwoRoomVisibility = game.get_node_or_null("StealthTestRoom") as GuardPostTwoRoomVisibility
	var guard: Node = room.get_patrol_observer() if room != null else null
	var west_door: StealthDoor = room.get_test_door() if room != null else null
	var catalog: ActionCatalogUI = game.get_node_or_null("Interface/ActionCatalogUI") as ActionCatalogUI
	var mobile: Control = game.get_node_or_null("Interface/MobileControls") as Control
	if player == null or guard == null or west_door == null or catalog == null or mobile == null:
		_fail("Pursuit test fixtures are incomplete.")
		return
	mobile.call("enable_for_testing")
	catalog.require_explicit_open_for_testing(true)
	var actions_button: Button = mobile.call("get_actions_button_for_testing") as Button
	if actions_button == null:
		_fail("Mobile Actions button is missing.")
		return

	player.global_position = Vector2(620.0, 180.0)
	state.set("player_position", player.global_position)
	(guard as Node2D).global_position = Vector2(760.0, 180.0)
	guard.call("set_facing_direction", Vector2.LEFT)
	game.call("_start_turn_based_combat", guard)
	game.call("force_player_turn_for_testing")
	await process_frame
	if not bool(game.call("is_turn_based_combat_active")):
		_fail("Combat did not start for the pursuit transition test.")
		return
	var last_known: Vector2 = game.get("_last_seen_player_position") as Vector2
	if last_known == Vector2.ZERO:
		_fail("Combat did not record an initial visual contact position.")
		return

	# Legacy signals are not a valid user intent and cannot open the menu at a
	# turn boundary. A completed GUI gesture opens normally without a timer.
	actions_button.emit_signal("pressed")
	if catalog.is_catalog_open():
		_fail("A stale pressed signal opened the action catalog at turn start.")
		return
	mobile.call("simulate_actions_touch_for_testing")
	if not catalog.is_catalog_open():
		_fail("A completed Actions gesture was blocked on the player turn.")
		return
	catalog.close_catalog()

	west_door.set_door_state("closed", false)
	var hidden_position := Vector2(100.0, 110.0)
	player.global_position = hidden_position
	state.set("player_position", player.global_position)
	game.call("set_hide_roll_overrides_for_testing", [20])
	mobile.call("simulate_actions_touch_for_testing")
	if not catalog.is_catalog_open():
		_fail("Completed Actions gesture did not open before the Hide request.")
		return
	catalog.call("_emit_action", "hide", "", true)
	if catalog.is_catalog_open():
		_fail("Action catalog remained visible underneath the blocking Hide roll overlay.")
		return
	for _frame: int in range(3):
		await process_frame
	if bool(game.call("is_turn_based_combat_active")):
		_fail("Successful Hide requested through the catalog did not end initiative.")
		return
	if catalog.is_catalog_open():
		_fail("Action catalog remained visible during the combat-to-search transition.")
		return
	if not bool(game.call("is_exploration_hidden_for_testing")):
		_fail("Combat hiding was not transferred to exploration hidden state.")
		return
	if bool(guard.call("is_hostile")):
		_fail("Searching guard remained hostile outside initiative.")
		return
	var record: Dictionary = state.call("get_stealth_alert_record", "service_guard") as Dictionary
	if str(record.get("state", "")) != StealthAlertSystem.STATE_INVESTIGATING:
		_fail("Guard did not continue as an exploration investigator.")
		return
	var stored_last_known: Vector2 = StealthAlertSystem.new().vector_from_value(record.get("last_known_position", []))
	if stored_last_known.distance_to(last_known) > 0.5:
		_fail("Pursuit target differs from the actual last visual contact: expected=%s actual=%s hidden=%s" % [last_known, stored_last_known, hidden_position])
		return
	if stored_last_known.distance_to(hidden_position) <= 0.5:
		_fail("The hidden position leaked into the patrol pursuit record.")
		return

	var before_search_move: Vector2 = (guard as Node2D).global_position
	game.call("force_exploration_alert_tick_for_testing", 0.5)
	if (guard as Node2D).global_position.distance_to(before_search_move) <= 0.1:
		_fail("Guard search did not continue toward the last known position.")
		return

	west_door.set_door_state("open", false)
	game.call("_break_exploration_hidden", "")
	player.global_position = Vector2(745.0, 180.0)
	state.set("player_position", player.global_position)
	(guard as Node2D).global_position = Vector2(760.0, 180.0)
	guard.call("set_facing_direction", Vector2.LEFT)
	var profile: Dictionary = (game.get("_stealth_alerts") as StealthAlertSystem).get_profile("service_guard")
	var visible_now: bool = bool(game.call("_exploration_actor_can_see_player", guard, profile))
	if not visible_now:
		_fail("Reacquisition fixture did not establish direct visual contact.")
		return
	for _tick: int in range(4):
		game.call("force_exploration_alert_tick_for_testing", 1.0)
		await process_frame
		if bool(game.call("is_turn_based_combat_active")):
			break
	if not bool(game.call("is_turn_based_combat_active")):
		var final_record: Dictionary = game.call("get_exploration_alert_record_for_testing", guard) as Dictionary
		_fail("Sustained reacquisition did not restart initiative: record=%s visible=%s hostile=%s" % [final_record, visible_now, guard.call("is_hostile")])
		return

	print("Catalog Hide signal, immediate modal closure, GUI-origin input, pursuit and reacquisition passed.")
	game.queue_free()
	await process_frame
	quit(0)


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.create_legacy_default()
	hero.character_name = "Scout"
	hero.abilities["dexterity"] = 18
	hero.base_abilities["dexterity"] = 18
	hero.skill_proficiencies.append("stealth")
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)