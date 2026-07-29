extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const RUNTIME_PATH: String = "res://scripts/game/game_combat_ai_runtime.gd"


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


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
	if packed == null:
		_fail("Game scene could not be loaded.")
		return
	var game: Node = packed.instantiate()
	root.add_child(game)
	for _frame: int in range(12):
		await process_frame
	if str(game.get_script().resource_path) != RUNTIME_PATH:
		_fail("Game scene does not use the final Combat AI runtime.")
		return
	game.set_process(false)

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var caretaker: Node = game.get_node_or_null("Caretaker")
	var catalog: ActionCatalogUI = game.get_node_or_null("Interface/ActionCatalogUI") as ActionCatalogUI
	var target_button: Button = game.find_child("TargetButton", true, false) as Button
	var mobile_controls: Control = game.get_node_or_null("Interface/MobileControls") as Control
	var room: StealthTestRoom = get_first_node_in_group("stealth_world") as StealthTestRoom
	if player == null or caretaker == null or catalog == null or target_button == null or mobile_controls == null or room == null:
		_fail("Player, caretaker, target selector, mobile Actions button or stealth room is missing.")
		return
	mobile_controls.call("enable_for_testing")
	await process_frame
	var actions_button: Button = mobile_controls.call("get_actions_button_for_testing") as Button
	if actions_button == null:
		_fail("The persistent lower-right Actions button is missing.")
		return
	var guard: Node = room.get_patrol_observer()
	if guard == null:
		_fail("Patrol guard is missing.")
		return

	if not is_equal_approx(target_button.anchor_top, 0.0) or not is_equal_approx(target_button.anchor_bottom, 0.0):
		_fail("Target selector is not anchored in the upper-right HUD area.")
		return
	if not is_equal_approx(actions_button.anchor_top, 1.0) or not is_equal_approx(actions_button.anchor_bottom, 1.0):
		_fail("Actions button is not anchored in the lower-right HUD area.")
		return
	if actions_button.text != "ДЕЙСТВИЯ":
		_fail("The lower-right button does not have the permanent ДЕЙСТВИЯ label.")
		return
	if target_button.get_global_rect().intersects(actions_button.get_global_rect()):
		_fail("Target selector and Actions button overlap each other.")
		return
	if catalog.catalog_button.visible or not catalog.catalog_button.disabled:
		_fail("The duplicate ActionCatalogButton is still exposed in the player HUD.")
		return

	game.call("select_context_target_for_testing", caretaker)
	var before_inspection: String = str(game.call("get_target_label_text_for_testing"))
	if "состояние неизвестно" not in before_inspection:
		_fail("Target state was not concealed before explicit inspection.")
		return
	for forbidden: String in ["КД", "HP", "%", "СПОКОЕН", "НАСТОРОЖЕН"]:
		if forbidden in before_inspection:
			_fail("Target label exposed hidden state before inspection: %s" % forbidden)
			return
	var caretaker_alert: Label = caretaker.get_node_or_null("StealthAlertLabel") as Label
	var guard_alert: Label = guard.get_node_or_null("StealthAlertLabel") as Label
	if (caretaker_alert != null and caretaker_alert.visible) or (guard_alert != null and guard_alert.visible):
		_fail("NPC state is still displayed above the actor.")
		return

	game.call("_refresh_action_catalog")
	if not actions_button.visible or actions_button.disabled:
		_fail("The lower-right Actions button is unavailable during exploration.")
		return
	actions_button.emit_signal("pressed")
	await process_frame
	if not catalog.panel.visible:
		_fail("The lower-right Actions button did not open the menu outside combat.")
		return
	var inspect_button: Button = null
	for button: Node in catalog.action_grid.get_children():
		if button is Button and (button as Button).text == "ОСМОТРЕТЬ":
			inspect_button = button as Button
			break
	if inspect_button == null:
		_fail("Contextual Inspect action is missing from the target menu.")
		return
	inspect_button.emit_signal("pressed")
	await process_frame
	var inspected: String = str(game.call("get_target_label_text_for_testing"))
	if "Поведение:" not in inspected or "состояние неизвестно" in inspected:
		_fail("Inspect action did not reveal qualitative target state.")
		return
	for forbidden: String in ["КД", "HP", "%"]:
		if forbidden in inspected:
			_fail("Inspect action exposed exact combat values: %s" % forbidden)
			return

	var door: StealthDoor = room.get_test_door()
	var navigation_link: NavigationLink2D = room.get_navigation_link_for_testing()
	if door == null or navigation_link == null:
		_fail("Door navigation link was not created.")
		return
	door.set_door_state("closed", false)
	await physics_frame
	if navigation_link.enabled:
		_fail("Closed door left its navigation link enabled.")
		return
	door.set_door_state("open", false)
	await physics_frame
	if not navigation_link.enabled:
		_fail("Open door did not enable its navigation link.")
		return
	if guard.get_node_or_null("NpcNavigationAgent") == null:
		_fail("Patrol guard does not own a NavigationAgent2D.")
		return

	var patrol_start: Vector2 = (guard as Node2D).global_position
	for _step: int in range(5):
		game.call("force_patrol_tick_for_testing", guard, 0.7)
		await physics_frame
	if (guard as Node2D).global_position.distance_to(patrol_start) <= 1.0:
		_fail("Navigation-backed patrol did not advance to the next waypoint.")
		return

	(guard as Node2D).global_position = player.global_position + Vector2(120.0, 0.0)
	var guard_record: Dictionary = state.call("get_stealth_alert_record", "service_guard") as Dictionary
	guard_record["state"] = StealthAlertSystem.STATE_INVESTIGATING
	guard_record["suspicion"] = 72.0
	guard_record["last_known_position"] = [player.global_position.x, player.global_position.y]
	state.call("set_stealth_alert_record", "service_guard", guard_record, false, false)
	game.call("_restore_exploration_alerts")
	target_button.show()
	actions_button.show()
	game.call("_start_turn_based_combat", caretaker)
	game.call("force_player_turn_for_testing")
	game.call("_apply_catalog_visibility_rules")
	game.call("_refresh_action_catalog")
	await process_frame
	if not bool(game.call("is_turn_based_combat_active")):
		_fail("Primary combat did not start.")
		return
	if not target_button.visible:
		_fail("Target selector disappeared when combat started.")
		return
	if not actions_button.visible or actions_button.disabled:
		_fail("The lower-right Actions button is unavailable during the player combat turn.")
		return
	if catalog.catalog_button.visible:
		_fail("The duplicate ActionCatalogButton became visible during combat.")
		return
	actions_button.emit_signal("pressed")
	await process_frame
	if not catalog.panel.visible:
		_fail("The lower-right Actions button did not open the combat menu.")
		return
	catalog.close_catalog()

	game.call("force_combat_join_check_for_testing")
	if not bool(game.call("turn_system_has_actor_for_testing", guard)):
		_fail("Alerted allied guard did not join active initiative.")
		return
	if not guard.is_in_group("combat_targets"):
		_fail("Joined guard was not activated as a combat target.")
		return
	var selected_before_cycle: Node = game.get("_selected_target") as Node
	target_button.emit_signal("pressed")
	await process_frame
	var selected_after_cycle: Node = game.get("_selected_target") as Node
	if selected_after_cycle == null or selected_after_cycle == selected_before_cycle:
		_fail("Upper-right target selector did not cycle between combat targets.")
		return
	game.call("force_combat_join_check_for_testing")
	var turn_system: Variant = game.get("_turn_system")
	var joined_count: int = 0
	if turn_system is TurnBasedCombatSystemAi:
		for entry: Dictionary in (turn_system as TurnBasedCombatSystemAi).entries:
			if entry.get("node") == guard:
				joined_count += 1
	if joined_count != 1:
		_fail("Guard was added to initiative more than once.")
		return

	var intent: Dictionary = game.call("get_ai_intent_for_testing", "service_guard", {
		"distance_feet": 25,
		"actor_health_ratio": 1.0,
		"target_visible": true,
		"can_attack": false,
		"can_move": true
	}) as Dictionary
	if str(intent.get("intent", "")) != NpcAiSystem.INTENT_ADVANCE:
		_fail("NPC AI foundation did not select advance for a distant visible target.")
		return

	var alert_indicator: Label = game.get_node_or_null("Interface/ExplorationStealthAlertIndicator") as Label
	if alert_indicator != null and alert_indicator.visible and alert_indicator.text != "СКРЫТ":
		_fail("Global HUD still exposes enemy alert state.")
		return

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("NPC context actions, single mobile Actions button, concealed state, navigation, combat join and Combat AI smoke test passed.")
	quit(0)


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Наблюдатель"
	hero.character_class_id = "rogue"
	hero.character_class_name = "Плут"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.level = 1
	hero.maximum_health = 12
	hero.current_health = 12
	hero.hit_die_size = 8
	hero.hit_dice_maximum = 1
	hero.hit_dice_current = 1
	hero.abilities["dexterity"] = 18
	hero.base_abilities["dexterity"] = 18
	hero.skill_proficiencies.append("stealth")
	return hero
