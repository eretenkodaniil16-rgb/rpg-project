extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const EXPECTED_GAME_STATE_SCRIPT: String = "res://scripts/core/game_state_world_snapshot.gd"
const EXPECTED_GAME_RUNTIME: String = "res://scripts/game/game_directional_touch_runtime.gd"
const SAVE_PATH: String = "user://save_slots/autosave.json"
const EXPECTED_SAVE_VERSION: int = 7


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	_cleanup_save()
	quit(1)


func _cleanup_save() -> void:
	var absolute_path: String = ProjectSettings.globalize_path(SAVE_PATH)
	if FileAccess.file_exists(SAVE_PATH):
		DirAccess.remove_absolute(absolute_path)


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	var state_script: Script = state.get_script() as Script
	if state_script == null or state_script.resource_path != EXPECTED_GAME_STATE_SCRIPT:
		_fail("GameState does not use the final world-snapshot integration layer.")
		return
	var required_methods: Array[String] = [
		"grant_experience_reward",
		"has_claimed_experience_reward",
		"begin_encounter",
		"abandon_encounter",
		"get_encounter_status",
		"set_stealth_alert_record",
		"get_stealth_alert_record",
		"set_stealth_door_state",
		"get_stealth_door_state",
		"load_autosave",
		"save_manual_slot",
		"list_manual_save_slots",
		"get_world_snapshot",
		"get_world_entity_state"
	]
	for method_name: String in required_methods:
		if not state.has_method(method_name):
			_fail("Integrated GameState is missing method: %s" % method_name)
			return
	var autoload_value: String = str(ProjectSettings.get_setting("autoload/GameState", ""))
	if EXPECTED_GAME_STATE_SCRIPT not in autoload_value:
		_fail("project.godot points GameState at an obsolete layer: %s" % autoload_value)
		return

	_cleanup_save()
	var hero := PlayerCharacter.new()
	hero.character_name = "Интеграционный герой"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.level = 1
	hero.maximum_health = 12
	hero.current_health = 12
	hero.hit_die_size = 10
	hero.hit_dice_maximum = 1
	hero.hit_dice_current = 1
	state.call("begin_new_game", hero)

	var reward: Dictionary = state.call(
		"grant_experience_reward",
		"dialogue_caretaker_revelation",
		{"source_type": "integration_test"},
		false,
		false
	) as Dictionary
	if not bool(reward.get("success", false)) or hero.experience <= 0:
		_fail("Experience reward layer did not apply through the final GameState.")
		return
	var expected_experience: int = hero.experience

	var started: Dictionary = state.call(
		"begin_encounter",
		"training_construct",
		{"source_type": "integration_test"},
		false,
		false
	) as Dictionary
	if not bool(started.get("success", false)):
		_fail("Encounter layer could not start the integration encounter.")
		return
	var abandoned: Dictionary = state.call(
		"abandon_encounter",
		"training_construct",
		"integration_test",
		{"enemies_alerted": false},
		false,
		false
	) as Dictionary
	if not bool(abandoned.get("success", false)):
		_fail("Encounter layer could not persist an abandoned result.")
		return

	var alert_record: Dictionary = state.call("get_stealth_alert_record", "caretaker") as Dictionary
	alert_record["state"] = StealthAlertSystem.STATE_SEARCHING
	alert_record["suspicion"] = 73.0
	alert_record["last_known_position"] = [448.0, 320.0]
	var stored_alert: Dictionary = state.call(
		"set_stealth_alert_record",
		"caretaker",
		alert_record,
		false,
		false
	) as Dictionary
	if str(stored_alert.get("state", "")) != StealthAlertSystem.STATE_SEARCHING:
		_fail("Stealth-alert layer did not store the NPC search state.")
		return
	if not bool(state.call("set_stealth_door_state", "west_service_door", "open", false)):
		_fail("Stealth-alert layer did not store the door state.")
		return

	if not bool(state.call("save_game")):
		_fail("Integrated state could not be saved.")
		return
	var save_file: FileAccess = FileAccess.open(SAVE_PATH, FileAccess.READ)
	if save_file == null:
		_fail("Integration autosave file was not created.")
		return
	var save_value: Variant = JSON.parse_string(save_file.get_as_text())
	if not save_value is Dictionary:
		_fail("Integration autosave file is not valid JSON.")
		return
	var save_data: Dictionary = save_value as Dictionary
	if int(save_data.get("version", 0)) != EXPECTED_SAVE_VERSION:
		_fail("Unexpected save version in the integration candidate.")
		return
	if not save_data.has("world_snapshot"):
		_fail("Save format v7 is missing the world snapshot payload.")
		return
	var flags: Dictionary = save_data.get("story_flags", {}) as Dictionary
	for registry_id: String in ["_claimed_experience_rewards_v1", "encounter_registry_v1", "stealth_alert_registry_v1"]:
		if not flags.has(registry_id):
			_fail("Save file is missing integrated registry: %s" % registry_id)
			return

	state.set("story_flags", {})
	state.set("player_character", PlayerCharacter.new())
	if not bool(state.call("load_autosave")):
		_fail("Integrated autosave could not be loaded.")
		return
	var loaded_hero: PlayerCharacter = state.get("player_character") as PlayerCharacter
	if loaded_hero == null or loaded_hero.experience != expected_experience:
		_fail("Experience was lost during integrated save/load.")
		return
	if not bool(state.call("has_claimed_experience_reward", "dialogue_caretaker_revelation")):
		_fail("Claimed reward registry was lost during save/load.")
		return
	if str(state.call("get_encounter_status", "training_construct")) != EncounterSystem.STATUS_ABANDONED:
		_fail("Encounter status was lost during save/load.")
		return
	var loaded_alert: Dictionary = state.call("get_stealth_alert_record", "caretaker") as Dictionary
	if str(loaded_alert.get("state", "")) != StealthAlertSystem.STATE_SEARCHING:
		_fail("NPC alert state was lost during save/load.")
		return
	if str(state.call("get_stealth_door_state", "west_service_door")) != "open":
		_fail("Door state was lost during save/load.")
		return

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	if packed == null:
		_fail("Final game scene could not be loaded.")
		return
	var game: Node = packed.instantiate()
	root.add_child(game)
	for _frame: int in range(12):
		await process_frame
	var game_script: Script = game.get_script() as Script
	if game_script == null or game_script.resource_path != EXPECTED_GAME_RUNTIME:
		_fail("Game scene does not use the final directional-touch world runtime.")
		return
	var level_up_panel: Control = game.find_child("LevelUpPanel", true, false) as Control
	if level_up_panel == null:
		_fail("Level-up panel is missing from the integrated game scene.")
		return
	if level_up_panel.z_index != 4095 or level_up_panel.z_index > 4096:
		_fail("Level-up panel uses an invalid or unstable z-index: %d" % level_up_panel.z_index)
		return
	var actions_button: Button = game.find_child("InteractButton", true, false) as Button
	var duplicate_button: Button = game.find_child("ActionCatalogButton", true, false) as Button
	var target_button: Button = game.find_child("TargetButton", true, false) as Button
	if actions_button == null or actions_button.text != "ДЕЙСТВИЯ" or target_button == null:
		_fail("Integrated mobile target/actions controls are incomplete.")
		return
	if duplicate_button != null and duplicate_button.visible:
		_fail("Obsolete duplicate Actions button is visible in the integrated HUD.")
		return

	game.queue_free()
	await process_frame
	_cleanup_save()
	print("v0.18 integration stack, world snapshot save format v7 and directional touch runtime passed.")
	quit(0)
