extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const MANUAL_SLOT_ID: int = 3
const MANUAL_SAVE_PATH: String = "user://save_slots/manual_03.json"


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null or not state.has_method("get_stealth_alert_record"):
		_fail("Stealth-aware GameState is missing.")
		return
	var save_path: String = ProjectSettings.globalize_path(MANUAL_SAVE_PATH)
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
	for _frame: int in range(8):
		await process_frame
	game.set_process(false)

	var caretaker: Node = game.get_node_or_null("Caretaker")
	var guard: Node = game.call("get_patrol_actor_for_testing", "service_guard") as Node
	var door: Node = get_first_node_in_group("stealth_doors")
	if caretaker == null or guard == null or door == null:
		_fail("Caretaker, service guard or test door is missing.")
		return
	if guard.is_in_group("combat_targets"):
		_fail("Technical observer incorrectly joined the combat target registry.")
		return

	(guard as Node2D).global_position = Vector2(700.0, 160.0)
	var patrol_before: Vector2 = (guard as Node2D).global_position
	game.call("force_patrol_tick_for_testing", guard, 0.5)
	var patrol_after: Vector2 = (guard as Node2D).global_position
	if patrol_after.distance_to(patrol_before) <= 0.1 or patrol_after.x > 760.0:
		_fail("Service guard did not follow the configured patrol route.")
		return

	var caretaker_record: Dictionary = state.call("get_stealth_alert_record", "caretaker") as Dictionary
	caretaker_record["state"] = StealthAlertSystem.STATE_CALM
	caretaker_record["suspicion"] = 0.0
	state.call("set_stealth_alert_record", "caretaker", caretaker_record, false, false)
	game.call("_restore_exploration_alerts")
	(guard as Node2D).global_position = Vector2(760.0, 240.0)
	(caretaker as Node2D).global_position = Vector2(900.0, 360.0)
	game.call("force_alert_broadcast_for_testing", guard, Vector2(620.0, 360.0))
	var relayed: Dictionary = game.call("get_exploration_alert_record_for_testing", caretaker) as Dictionary
	if str(relayed.get("state", "")) != StealthAlertSystem.STATE_INVESTIGATING:
		_fail("Confirmed guard alert did not start caretaker investigation.")
		return
	if str(relayed.get("last_alert_source_id", "")) != "service_guard":
		_fail("Alert relay did not preserve the source actor ID.")
		return
	if bool(game.call("is_turn_based_combat_active")):
		_fail("Relayed alert incorrectly started combat without visual confirmation.")
		return

	caretaker_record = state.call("get_stealth_alert_record", "caretaker") as Dictionary
	caretaker_record["state"] = StealthAlertSystem.STATE_CALM
	caretaker_record["suspicion"] = 0.0
	caretaker_record.erase("last_alert_source_id")
	state.call("set_stealth_alert_record", "caretaker", caretaker_record, false, false)
	game.call("_restore_exploration_alerts")
	(guard as Node2D).global_position = Vector2(100.0, 360.0)
	(caretaker as Node2D).global_position = Vector2(500.0, 360.0)
	door.call("set_door_state", "closed", false)
	game.call("force_alert_broadcast_for_testing", guard, Vector2(100.0, 360.0))
	var blocked: Dictionary = game.call("get_exploration_alert_record_for_testing", caretaker) as Dictionary
	if str(blocked.get("state", "")) != StealthAlertSystem.STATE_CALM:
		_fail("Closed door failed to block distant alert relay.")
		return

	door.call("set_door_state", "open", false)
	game.call("force_alert_broadcast_for_testing", guard, Vector2(100.0, 360.0))
	var through_open_door: Dictionary = game.call("get_exploration_alert_record_for_testing", caretaker) as Dictionary
	if str(through_open_door.get("state", "")) != StealthAlertSystem.STATE_INVESTIGATING:
		_fail("Open door did not allow an audible alert relay.")
		return
	if bool(game.call("is_turn_based_combat_active")):
		_fail("Audible alert relay incorrectly started active initiative.")
		return

	game.call("_persist_all_alert_records", false)
	state.set("input_locked", true)
	if not bool(state.call("save_manual_slot", MANUAL_SLOT_ID)):
		_fail("Patrol alert state could not be saved to a manual slot.")
		return
	state.set("input_locked", false)
	state.set("story_flags", {})
	state.set("quest_states", {})
	state.set("inventory", {})
	if not bool(state.call("load_manual_slot", MANUAL_SLOT_ID)):
		_fail("Patrol alert manual save could not be loaded.")
		return
	var restored: Dictionary = state.call("get_stealth_alert_record", "caretaker") as Dictionary
	if str(restored.get("last_alert_source_id", "")) != "service_guard":
		_fail("Relayed alert source was not preserved by save/load.")
		return

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Patrol movement, local alert relay, door audibility, non-combat investigation and manual persistence smoke test passed.")
	quit(0)


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Наблюдатель"
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
	hero.abilities["dexterity"] = 16
	hero.base_abilities["dexterity"] = 16
	return hero
