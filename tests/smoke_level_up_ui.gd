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
	hero.abilities["constitution"] = 14
	hero.base_abilities["constitution"] = 14
	hero.maximum_health = 12
	hero.current_health = 12
	hero.hit_die_size = 10
	hero.hit_dice_maximum = 1
	hero.hit_dice_current = 1
	hero.experience = ProgressionSystem.total_experience_for_level(2)
	state.set("player_character", hero)
	ClassDataSystem.new().ensure_starting_loadout(hero)

	var packed: PackedScene = load("res://scenes/game/game.tscn") as PackedScene
	if packed == null:
		_fail("Game scene failed to load.")
		return
	var game: Node = packed.instantiate()
	root.add_child(game)
	await process_frame
	await process_frame

	var hub := game.find_child("CharacterHub", true, false) as CharacterHub
	var panel := game.find_child("LevelUpPanel", true, false) as LevelUpPanel
	if hub == null or panel == null:
		_fail("Character Hub or LevelUpPanel is missing.")
		return
	hub.open_tab(hero, 0)
	await process_frame
	var level_button := hub.find_child("LevelUpButton", true, false) as Button
	if level_button == null or level_button.custom_minimum_size.y < 54.0:
		_fail("Mobile level-up button is missing or too small.")
		return
	level_button.pressed.emit()
	await process_frame
	if not panel.visible or not bool(state.get("input_locked")):
		_fail("Level-up panel did not open as an input-locking modal.")
		return
	var fixed_button := panel.find_child("LevelUpFixedHpButton", true, false) as Button
	var roll_button := panel.find_child("LevelUpRollHpButton", true, false) as Button
	var confirm_button := panel.find_child("LevelUpConfirmButton", true, false) as Button
	if fixed_button == null or roll_button == null or confirm_button == null:
		_fail("Level-up HP or confirmation controls are missing.")
		return
	roll_button.pressed.emit()
	await process_frame
	var saved_roll: int = int(LevelUpSystem.new().get_transaction(state).get("hp_roll", 0))
	if saved_roll <= 0:
		_fail("Mobile HP roll was not saved immediately.")
		return
	panel.close_panel()
	if bool(state.get("input_locked")):
		_fail("Closing the level-up panel did not release input.")
		return
	panel.open_for(hero, state)
	await process_frame
	if int(LevelUpSystem.new().get_transaction(state).get("hp_roll", 0)) != saved_roll:
		_fail("Reopened mobile panel did not restore the saved HP roll.")
		return
	fixed_button = panel.find_child("LevelUpFixedHpButton", true, false) as Button
	confirm_button = panel.find_child("LevelUpConfirmButton", true, false) as Button
	fixed_button.pressed.emit()
	await process_frame
	if confirm_button.disabled:
		_fail("A valid fixed-HP transaction did not enable confirmation.")
		return
	confirm_button.pressed.emit()
	await process_frame
	if hero.level != 2 or panel.visible:
		_fail("Mobile confirmation did not commit and close the level-up panel.")
		return
	if not hub.visible:
		_fail("Character Hub did not reopen after successful level-up.")
		return

	print("Mobile Character Hub to saved LevelUpPanel flow passed.")
	quit(0)
