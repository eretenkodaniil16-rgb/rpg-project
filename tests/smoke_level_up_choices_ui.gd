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
	hero.character_name = "Мобильный воин"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.level = 2
	hero.experience = ProgressionSystem.total_experience_for_level(3)
	hero.maximum_health = 18
	hero.current_health = 18
	hero.hit_die_size = 10
	hero.hit_dice_maximum = 2
	hero.hit_dice_current = 2
	state.set("player_character", hero)

	var panel := LevelUpChoicesPanel.new()
	root.add_child(panel)
	await process_frame
	var open_result: Dictionary = panel.open_for(hero, state)
	if not bool(open_result.get("success", false)):
		_fail("Mobile level choice panel did not open.")
		return
	await process_frame

	var confirm := panel.find_child("LevelUpConfirmButton", true, false) as Button
	var fixed := panel.find_child("LevelUpFixedHpButton", true, false) as Button
	var subclass := panel.find_child("LevelChoice_fighter_subclass", true, false) as OptionButton
	if confirm == null or fixed == null or subclass == null:
		_fail("Required level 3 mobile controls are missing.")
		return
	if not confirm.disabled:
		_fail("Confirm button was enabled before required HP and subclass choices.")
		return

	fixed.emit_signal("pressed")
	await process_frame
	subclass = panel.find_child("LevelChoice_fighter_subclass", true, false) as OptionButton
	var subclass_index: int = _find_metadata_index(subclass, "tactical_blade")
	if subclass_index < 0:
		_fail("Tactical subclass is absent from the mobile selector.")
		return
	subclass.select(subclass_index)
	subclass.emit_signal("item_selected", subclass_index)
	await process_frame
	confirm = panel.find_child("LevelUpConfirmButton", true, false) as Button
	if confirm.disabled:
		_fail("Valid level 3 choices did not enable confirmation.")
		return

	panel.close_panel()
	panel.open_for(hero, state)
	await process_frame
	subclass = panel.find_child("LevelChoice_fighter_subclass", true, false) as OptionButton
	if subclass == null or str(subclass.get_item_metadata(subclass.selected)) != "tactical_blade":
		_fail("Deferred subclass selection was not restored in the mobile panel.")
		return
	confirm = panel.find_child("LevelUpConfirmButton", true, false) as Button
	confirm.emit_signal("pressed")
	await process_frame
	if hero.level != 3 or hero.subclass_id != "tactical_blade":
		_fail("Mobile level 3 confirmation did not apply the subclass.")
		return

	hero.experience = ProgressionSystem.total_experience_for_level(4)
	panel.open_for(hero, state)
	await process_frame
	fixed = panel.find_child("LevelUpFixedHpButton", true, false) as Button
	fixed.emit_signal("pressed")
	await process_frame
	var mode := panel.find_child("LevelChoice_level_4_advancement_Mode", true, false) as OptionButton
	if mode == null:
		_fail("Level 4 advancement mode selector is missing.")
		return
	var mode_index: int = _find_metadata_index(mode, LevelChoiceSystem.ADVANCEMENT_PLUS_TWO)
	mode.select(mode_index)
	mode.emit_signal("item_selected", mode_index)
	await process_frame
	var primary := panel.find_child("LevelChoice_level_4_advancement_PrimaryAbility", true, false) as OptionButton
	if primary == null or not primary.visible:
		_fail("Primary ability selector did not appear for +2 advancement.")
		return
	var ability_index: int = _find_metadata_index(primary, "strength")
	primary.select(ability_index)
	primary.emit_signal("item_selected", ability_index)
	await process_frame
	confirm = panel.find_child("LevelUpConfirmButton", true, false) as Button
	if confirm.disabled:
		_fail("Valid level 4 ability choice did not enable confirmation.")
		return
	confirm.emit_signal("pressed")
	await process_frame
	if hero.level != 4 or hero.get_ability_score("strength") != 12:
		_fail("Mobile level 4 advancement did not apply +2 Strength.")
		return

	var hub := CharacterHubLevelUp.new()
	root.add_child(hub)
	await process_frame
	hub.open_tab(hero, 0)
	await process_frame
	var subclass_visible: bool = false
	for node: Node in hub.find_children("*", "Label", true, false):
		if node is Label and "Тактический клинок" in (node as Label).text:
			subclass_visible = true
			break
	if not subclass_visible:
		_fail("Committed subclass is not visible in Character Hub.")
		return

	hub.queue_free()
	panel.queue_free()
	await process_frame
	print("Mobile subclass, deferred transaction and level 4 advancement UI smoke test passed.")
	quit(0)


func _find_metadata_index(option: OptionButton, value: String) -> int:
	if option == null:
		return -1
	for index: int in range(option.item_count):
		if str(option.get_item_metadata(index)) == value:
			return index
	return -1
