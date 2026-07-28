extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const RUNTIME_PATH: String = "res://scripts/game/game_pursuit_escape_runtime.gd"


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
	var save_path: String = ProjectSettings.globalize_path("user://savegame.json")
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	state.call("new_game")
	var hero := _make_hero()
	state.set("player_character", hero)

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	if packed == null:
		_fail("Game scene could not be loaded.")
		return
	var game: Node = packed.instantiate()
	root.add_child(game)
	for _frame: int in range(8):
		await process_frame
	game.set_process(false)
	if str(game.get_script().resource_path) != RUNTIME_PATH:
		_fail("Game scene does not use the pursuit-compatible exploration stealth runtime.")
		return

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var caretaker: Node = game.get_node_or_null("Caretaker")
	var door: Node = get_first_node_in_group("stealth_doors")
	if player == null or caretaker == null or door == null:
		_fail("Player, alert-aware caretaker or stealth door is missing.")
		return
	if not caretaker.has_method("get_actor_id") or str(caretaker.call("get_actor_id")) != "caretaker":
		_fail("Caretaker does not expose a stable stealth actor ID.")
		return
	if str(door.call("get_door_id")) != "west_service_door":
		_fail("Persistent service door is missing its stable ID.")
		return

	player.global_position = Vector2(700.0, 360.0)
	state.set("player_position", player.global_position)
	caretaker.call("set_facing_direction", Vector2.LEFT)
	game.call("force_exploration_alert_tick_for_testing", 0.75)
	var observed: Dictionary = game.call("get_exploration_alert_record_for_testing", caretaker) as Dictionary
	if float(observed.get("suspicion", 0.0)) <= 0.0 or str(observed.get("state", "")) != StealthAlertSystem.STATE_SUSPICIOUS:
		_fail("Visible exploration movement did not raise suspicion.")
		return
	var alert_text: String = str(game.call("get_alert_indicator_text_for_testing"))
	if not alert_text.is_empty():
		_fail("Global HUD exposed enemy awareness without explicit target inspection.")
		return
	var npc_alert_label: Label = caretaker.get_node_or_null("StealthAlertLabel") as Label
	if npc_alert_label == null or npc_alert_label.visible or not npc_alert_label.text.is_empty():
		_fail("NPC alert state was exposed above the actor without inspection.")
		return

	player.global_position = Vector2(100.0, 110.0)
	state.set("player_position", player.global_position)
	door.call("set_door_state", "closed", false)
	game.call("set_exploration_hide_roll_overrides_for_testing", [20])
	game.call("_toggle_exploration_hide")
	if not bool(game.call("is_exploration_hidden_for_testing")):
		_fail("Hiding spot did not allow successful exploration hiding.")
		return
	if str(state.call("get_stealth_room_id", player.global_position)) != "west_service_room":
		_fail("Player did not enter the data-driven service room.")
		return
	game.call("_refresh_alert_indicator")
	alert_text = str(game.call("get_alert_indicator_text_for_testing"))
	if alert_text != "СКРЫТ":
		_fail("HUD did not preserve the hero's own hidden-state feedback.")
		return

	var calm_record: Dictionary = state.call("get_stealth_alert_record", "caretaker") as Dictionary
	calm_record["state"] = StealthAlertSystem.STATE_CALM
	calm_record["suspicion"] = 0.0
	state.call("set_stealth_alert_record", "caretaker", calm_record, false, false)
	game.call("_restore_exploration_alerts")
	caretaker.global_position = Vector2(500.0, 360.0)
	game.call("report_world_noise", "weapon", player.global_position, {"source_type": "closed_door_test"})
	await process_frame
	var damped: Dictionary = game.call("get_exploration_alert_record_for_testing", caretaker) as Dictionary
	if float(damped.get("suspicion", 0.0)) > 0.0:
		_fail("Closed door failed to damp a cross-room noise outside hearing range.")
		return

	door.call("set_door_state", "open", false)
	game.call("report_world_noise", "weapon", player.global_position, {"source_type": "open_door_test"})
	await process_frame
	var investigating: Dictionary = game.call("get_exploration_alert_record_for_testing", caretaker) as Dictionary
	if str(investigating.get("state", "")) != StealthAlertSystem.STATE_INVESTIGATING:
		_fail("Open-door noise did not start an investigation.")
		return
	var before_move: Vector2 = caretaker.global_position
	game.call("force_exploration_alert_tick_for_testing", 0.5)
	if caretaker.global_position.distance_to(before_move) <= 0.1:
		_fail("Investigating NPC did not move toward the last known position.")
		return

	game.call("force_post_escape_search_for_testing", caretaker, Vector2(240.0, 360.0))
	var searching: Dictionary = game.call("get_exploration_alert_record_for_testing", caretaker) as Dictionary
	if str(searching.get("state", "")) != StealthAlertSystem.STATE_SEARCHING:
		_fail("Post-combat escape did not continue as exploration search.")
		return
	game.call("_persist_all_alert_records", true)
	if not bool(state.call("save_game")):
		_fail("Stealth alert save failed.")
		return
	state.set("story_flags", {})
	state.set("quest_states", {})
	state.set("inventory", {})
	if not bool(state.call("load_game")):
		_fail("Stealth alert save could not be loaded.")
		return
	var restored: Dictionary = state.call("get_stealth_alert_record", "caretaker") as Dictionary
	if str(restored.get("state", "")) != StealthAlertSystem.STATE_SEARCHING:
		_fail("Active exploration search was not preserved by save/load.")
		return
	if str(state.call("get_stealth_door_state", "west_service_door")) != "open":
		_fail("Door state was not preserved by save/load.")
		return

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Exploration vision, concealed enemy state, hiding, door acoustics, investigation, post-escape search and persistence smoke test passed.")
	quit(0)


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Лазутчик"
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
