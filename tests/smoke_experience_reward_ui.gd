extends SceneTree


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
	state.call("new_game")
	var hero := PlayerCharacter.new()
	hero.character_name = "Мобильный герой"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.maximum_health = 12
	hero.current_health = 12
	hero.hit_die_size = 10
	hero.hit_dice_maximum = 1
	hero.hit_dice_current = 1
	hero.abilities["constitution"] = 14
	hero.base_abilities["constitution"] = 14
	state.set("player_character", hero)

	var packed: PackedScene = load("res://scenes/game/game.tscn") as PackedScene
	if packed == null:
		_fail("Game scene could not be loaded.")
		return
	var game: Node = packed.instantiate()
	root.add_child(game)
	await process_frame
	await process_frame

	var toast := game.find_child("ExperienceRewardToast", true, false) as ExperienceRewardToast
	var toast_panel := game.find_child("ExperienceRewardPanel", true, false) as PanelContainer
	var toast_label := game.find_child("ExperienceRewardLabel", true, false) as Label
	var hub := game.find_child("CharacterHub", true, false) as CharacterHubLevelUp
	if toast == null or toast_panel == null or toast_label == null or hub == null:
		_fail("Experience reward toast or Character Hub integration is missing.")
		return

	hub.open_tab(hero, 0)
	await process_frame
	var experience_bar := hub.find_child("CharacterExperienceBar", true, false) as ProgressBar
	if experience_bar == null or int(experience_bar.value) != 0:
		_fail("Character Hub experience bar was not initialized.")
		return

	var encounter_result: Dictionary = state.call("grant_experience_reward", "encounter_training_dummy_break") as Dictionary
	if not bool(encounter_result.get("success", false)):
		_fail("Encounter reward could not be granted in the game scene.")
		return
	await process_frame
	await process_frame
	if not toast_panel.visible or "+25 опыта" not in toast_label.text:
		_fail("Mobile experience notification was not shown.")
		return
	experience_bar = hub.find_child("CharacterExperienceBar", true, false) as ProgressBar
	if experience_bar == null or int(experience_bar.value) != 25:
		_fail("Open Character Hub did not refresh after experience gain.")
		return

	var quest_result: Dictionary = state.call("grant_experience_reward", "quest_first_steps_complete") as Dictionary
	if not bool(quest_result.get("success", false)):
		_fail("Quest reward could not be granted in the game scene.")
		return
	await process_frame
	await process_frame
	experience_bar = hub.find_child("CharacterExperienceBar", true, false) as ProgressBar
	if experience_bar == null or int(experience_bar.value) != 300:
		_fail("Character Hub did not display a full level threshold.")
		return
	var level_button := hub.find_child("LevelUpButton", true, false) as Button
	if level_button == null or level_button.text != "ПОВЫСИТЬ УРОВЕНЬ":
		_fail("Level-up button did not appear after the reward threshold.")
		return

	var experience_before_duplicate: int = hero.experience
	var duplicate: Dictionary = state.call("grant_experience_reward", "quest_first_steps_complete") as Dictionary
	await process_frame
	if not bool(duplicate.get("duplicate", false)) or hero.experience != experience_before_duplicate:
		_fail("UI flow allowed a duplicate reward to change experience.")
		return

	hub.close_sheet()
	game.queue_free()
	await process_frame
	print("Mobile experience toast and live Character Hub refresh test passed.")
	quit(0)
