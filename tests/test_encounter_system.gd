extends SceneTree

const AUTOSAVE_PATH: String = "user://save_slots/autosave.json"


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null or not state.has_method("begin_encounter") or not state.has_method("resolve_encounter"):
		_fail("Encounter-aware GameState API is missing.")
		return
	var save_path: String = ProjectSettings.globalize_path(AUTOSAVE_PATH)
	if FileAccess.file_exists(AUTOSAVE_PATH):
		DirAccess.remove_absolute(save_path)

	state.call("new_game")
	state.set("player_character", _fighter())
	if str(state.call("get_encounter_status", "training_construct")) != EncounterSystem.STATUS_AVAILABLE:
		_fail("A new encounter did not begin in available state.")
		return
	var started_count: Dictionary = {"value": 0}
	state.connect("encounter_started", func(_id: String, _encounter_state: Dictionary) -> void: started_count["value"] = int(started_count["value"]) + 1)
	var begin_result: Dictionary = state.call(
		"begin_encounter",
		"training_construct",
		{"source_type": "test"}
	) as Dictionary
	if not bool(begin_result.get("success", false)) or str(state.call("get_encounter_status", "training_construct")) != EncounterSystem.STATUS_ACTIVE:
		_fail("Encounter did not transition to active state.")
		return
	var second_begin: Dictionary = state.call("begin_encounter", "training_construct") as Dictionary
	if not bool(second_begin.get("already_active", false)) or int(started_count.get("value", 0)) != 1:
		_fail("Starting an active encounter emitted a duplicate start.")
		return

	var resolved: Dictionary = state.call(
		"resolve_encounter",
		"training_construct",
		"destroyed",
		{"source_type": "combat"}
	) as Dictionary
	var character: PlayerCharacter = state.get("player_character") as PlayerCharacter
	if not bool(resolved.get("success", false)):
		_fail("Combat encounter could not be resolved.")
		return
	if str(state.call("get_encounter_status", "training_construct")) != EncounterSystem.STATUS_REWARDED:
		_fail("Resolved encounter did not reach rewarded state.")
		return
	if character.experience != 25 or int(state.call("get_item_count", "straw_scrap")) != 1:
		_fail("Encounter consequences did not grant XP and item exactly once.")
		return
	if not bool(state.call("get_flag", "training_construct_destroyed", false)):
		_fail("Encounter story flags were not applied.")
		return
	var duplicate: Dictionary = state.call(
		"resolve_encounter",
		"training_construct",
		"disabled"
	) as Dictionary
	if not bool(duplicate.get("duplicate", false)) or character.experience != 25 or int(state.call("get_item_count", "straw_scrap")) != 1:
		_fail("An alternate resolution could farm a completed encounter.")
		return

	if not bool(state.call("save_game")):
		_fail("Encounter state could not be saved.")
		return
	# new_game() intentionally discards autosave. Clear only in-memory values so
	# this test verifies loading the existing campaign rather than starting one.
	state.set("story_flags", {})
	state.set("quest_states", {})
	state.set("inventory", {})
	state.set("player_character", PlayerCharacter.new())
	if not bool(state.call("load_game")):
		_fail("Encounter state could not be loaded.")
		return
	if str(state.call("get_encounter_status", "training_construct")) != EncounterSystem.STATUS_REWARDED:
		_fail("Encounter terminal state was not preserved by save/load.")
		return
	var loaded_training: Dictionary = state.call("get_encounter_state", "training_construct") as Dictionary
	if str(loaded_training.get("resolution_id", "")) != "destroyed":
		_fail("Encounter resolution ID was not preserved.")
		return

	state.call("new_game")
	state.set("player_character", _fighter())
	state.call("begin_encounter", "training_construct")
	var failed: Dictionary = state.call("fail_encounter", "training_construct", "player_defeated") as Dictionary
	if not bool(failed.get("success", false)) or str(state.call("get_encounter_status", "training_construct")) != EncounterSystem.STATUS_FAILED:
		_fail("Encounter failure state was not recorded.")
		return
	state.call("begin_encounter", "training_construct")
	var restarted: Dictionary = state.call("get_encounter_state", "training_construct") as Dictionary
	if str(restarted.get("status", "")) != EncounterSystem.STATUS_ACTIVE or int(restarted.get("attempt_count", 0)) != 2:
		_fail("A failed encounter could not be restarted with a new attempt.")
		return
	var abandoned: Dictionary = state.call("abandon_encounter", "training_construct", "left_area") as Dictionary
	if not bool(abandoned.get("success", false)) or str(state.call("get_encounter_status", "training_construct")) != EncounterSystem.STATUS_ABANDONED:
		_fail("Encounter abandonment state was not recorded.")
		return

	state.call("new_game")
	state.set("player_character", _fighter())
	var dialogue_result: Dictionary = state.call(
		"resolve_encounter",
		"caretaker_revelation",
		"insight",
		{"source_type": "dialogue"}
	) as Dictionary
	character = state.get("player_character") as PlayerCharacter
	if not bool(dialogue_result.get("success", false)) or character.experience != 25:
		_fail("Dialogue encounter did not grant its shared reward.")
		return
	if not bool(state.call("get_flag", "caretaker_secret_noticed", false)):
		_fail("Dialogue resolution-specific flag was not applied.")
		return
	var dialogue_duplicate: Dictionary = state.call(
		"resolve_encounter",
		"caretaker_revelation",
		"persuaded"
	) as Dictionary
	if not bool(dialogue_duplicate.get("duplicate", false)) or character.experience != 25:
		_fail("Multiple dialogue solutions granted the shared encounter reward more than once.")
		return

	state.call("new_game")
	state.set("player_character", _fighter())
	state.call("set_flag", "caretaker_secret_noticed", true)
	var legacy_reward: Dictionary = state.call(
		"grant_experience_reward",
		"dialogue_caretaker_revelation",
		{},
		false,
		false
	) as Dictionary
	if not bool(legacy_reward.get("success", false)):
		_fail("Legacy dialogue reward setup failed.")
		return
	var before_migration_xp: int = (state.get("player_character") as PlayerCharacter).experience
	var migration: Dictionary = state.call("ensure_encounter_migration") as Dictionary
	if int(migration.get("encounter_count", 0)) != 1:
		_fail("Legacy dialogue result was not migrated into an encounter.")
		return
	var migrated_state: Dictionary = state.call("get_encounter_state", "caretaker_revelation") as Dictionary
	if str(migrated_state.get("resolution_id", "")) != "insight" or str(migrated_state.get("status", "")) != EncounterSystem.STATUS_REWARDED:
		_fail("Legacy dialogue resolution was inferred incorrectly.")
		return
	if (state.get("player_character") as PlayerCharacter).experience != before_migration_xp:
		_fail("Encounter migration granted legacy XP twice.")
		return
	migration = state.call("ensure_encounter_migration") as Dictionary
	if int(migration.get("encounter_count", 0)) != 0:
		_fail("Encounter migration is not idempotent.")
		return

	if FileAccess.file_exists(AUTOSAVE_PATH):
		DirAccess.remove_absolute(save_path)
	print("Encounter lifecycle, consequences, save/load and migration tests passed.")
	quit(0)


func _fighter() -> PlayerCharacter:
	var character := PlayerCharacter.new()
	character.character_name = "Испытатель столкновений"
	character.character_class_id = "fighter"
	character.character_class_name = "Воин"
	character.race_id = "human"
	character.race_name = "Человек"
	character.level = 1
	character.experience = 0
	character.maximum_health = 12
	character.current_health = 12
	character.hit_die_size = 10
	character.hit_dice_maximum = 1
	character.hit_dice_current = 1
	character.abilities["constitution"] = 14
	character.base_abilities["constitution"] = 14
	return character
