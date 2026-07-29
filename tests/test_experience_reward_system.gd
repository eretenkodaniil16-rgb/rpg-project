extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null or not state.has_method("grant_experience_reward"):
		_fail("Extended GameState experience reward API is missing.")
		return
	var save_path: String = ProjectSettings.globalize_path("user://savegame.json")
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)

	state.call("new_game")
	var fighter: PlayerCharacter = _fighter()
	state.set("player_character", fighter)
	var signal_state: Dictionary = {"xp": 0, "level": 0}
	state.connect("experience_gained", func(_id: String, amount: int, _total: int, _label: String) -> void: signal_state["xp"] = int(signal_state["xp"]) + amount)
	state.connect("level_up_available", func(_current: int, _target: int, _pending: int) -> void: signal_state["level"] = int(signal_state["level"]) + 1)

	var first: Dictionary = state.call(
		"grant_experience_reward",
		"encounter_training_dummy_break",
		{"source_type": "encounter", "encounter_id": "training_dummy"}
	) as Dictionary
	if not bool(first.get("success", false)) or fighter.experience != 25:
		_fail("The first encounter reward was not granted.")
		return
	var duplicate: Dictionary = state.call("grant_experience_reward", "encounter_training_dummy_break") as Dictionary
	if not bool(duplicate.get("duplicate", false)) or fighter.experience != 25:
		_fail("A repeated reward ID granted experience twice.")
		return
	if int(signal_state.get("xp", 0)) != 25:
		_fail("Experience signal was not emitted exactly once.")
		return

	if not bool(state.call("save_game")):
		_fail("Reward state could not be saved.")
		return
	state.call("new_game")
	if not bool(state.call("load_game")):
		_fail("Reward state could not be loaded.")
		return
	var loaded_character: PlayerCharacter = state.get("player_character") as PlayerCharacter
	if loaded_character == null or loaded_character.experience != 25:
		_fail("Experience was not preserved by save/load.")
		return
	if not bool(state.call("has_claimed_experience_reward", "encounter_training_dummy_break")):
		_fail("Claimed reward ID was not preserved by save/load.")
		return
	duplicate = state.call("grant_experience_reward", "encounter_training_dummy_break") as Dictionary
	if not bool(duplicate.get("duplicate", false)) or loaded_character.experience != 25:
		_fail("Loaded claimed reward could be farmed again.")
		return

	state.call("new_game")
	fighter = _fighter()
	state.set("player_character", fighter)
	state.call("report_quest_event", "talked_to_caretaker")
	state.call("report_quest_event", "hit_training_dummy")
	state.call("report_quest_event", "talked_to_caretaker")
	if fighter.experience != 300 or not ProgressionSystem.can_level_up(fighter):
		_fail("Completing first_steps did not grant the configured 300 XP.")
		return
	if int(state.call("get_item_count", "apprentice_token")) != 1:
		_fail("Quest item reward was lost while adding experience.")
		return
	if not bool(state.call("has_claimed_experience_reward", "quest_first_steps_complete")):
		_fail("Quest reward ID was not recorded.")
		return

	state.call("new_game")
	fighter = _fighter()
	state.set("player_character", fighter)
	state.set("quest_states", {
		"first_steps": {"status": "completed", "stage_index": 3}
	})
	state.set("story_flags", {})
	var migration: Dictionary = state.call("ensure_experience_reward_migration") as Dictionary
	if int(migration.get("reward_count", 0)) != 1 or fighter.experience != 300:
		_fail("Completed legacy quest did not receive its missing experience reward once.")
		return
	migration = state.call("ensure_experience_reward_migration") as Dictionary
	if int(migration.get("reward_count", 0)) != 0 or fighter.experience != 300:
		_fail("Experience reward migration was not idempotent.")
		return

	state.call("new_game")
	fighter = _fighter()
	state.set("player_character", fighter)
	var dialogue: Dictionary = state.call("grant_experience_reward", "dialogue_caretaker_revelation") as Dictionary
	if not bool(dialogue.get("success", false)) or fighter.experience != 25:
		_fail("Dialogue reward could not be granted from the catalog.")
		return
	dialogue = state.call("grant_experience_reward", "dialogue_caretaker_revelation") as Dictionary
	if not bool(dialogue.get("duplicate", false)) or fighter.experience != 25:
		_fail("Shared dialogue revelation reward was granted more than once.")
		return

	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Experience reward IDs, quest completion, migration and save/load tests passed.")
	quit(0)


func _fighter() -> PlayerCharacter:
	var character := PlayerCharacter.new()
	character.character_name = "Испытатель наград"
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
