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
	hero.character_name = "Тактик"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.subclass_id = FighterSubclassSystem.TACTICAL_SUBCLASS_ID
	hero.subclass_name = "Тактический клинок"
	hero.level = 3
	hero.experience = ProgressionSystem.total_experience_for_level(3)
	hero.maximum_health = 28
	hero.current_health = 28
	hero.hit_die_size = 10
	hero.hit_dice_maximum = 3
	hero.hit_dice_current = 3
	state.set("player_character", hero)

	var scene: PackedScene = load("res://scenes/game/game.tscn") as PackedScene
	if scene == null:
		_fail("Game scene could not be loaded.")
		return
	var game: Node = scene.instantiate()
	root.add_child(game)
	await process_frame
	await process_frame

	if str(game.get_script().resource_path) != "res://scripts/game/game_guard_post_polish_runtime.gd":
		_fail("Game scene does not use the runtime layered above Combat AI, pursuit, encounters and fighter subclasses.")
		return
	if FighterSubclassSystem.TACTICAL_ABILITY_ID not in hero.known_features:
		_fail("Game startup did not synchronize the selected fighter subclass.")
		return

	var catalog_value: Variant = game.call("_build_catalog_entries")
	if not catalog_value is Dictionary:
		_fail("Action catalog entries could not be built.")
		return
	var entries: Dictionary = catalog_value as Dictionary
	var tactical_entry_found: bool = false
	var bonus_entries_value: Variant = entries.get("bonus", [])
	if bonus_entries_value is Array:
		for value: Variant in bonus_entries_value as Array:
			if value is Dictionary and str((value as Dictionary).get("id", "")) == "ability:tactical_focus":
				tactical_entry_found = true
				break
	if not tactical_entry_found:
		_fail("Tactical preparation is missing from the mobile bonus-action catalog.")
		return

	var hub := game.find_child("CharacterHub", true, false) as CharacterHubLevelUp
	if hub == null:
		_fail("Character Hub is missing.")
		return
	hub.open_tab(hero, 2)
	await process_frame
	var power_button_found: bool = false
	for node: Node in hub.find_children("*", "Button", true, false):
		var button := node as Button
		if button != null and "ТАКТИЧЕСКАЯ ПОДГОТОВКА" in button.text.to_upper():
			power_button_found = true
			break
	if not power_button_found:
		_fail("Character Hub does not show the active subclass ability.")
		return

	var ability: Dictionary = FighterSubclassSystem.new().get_ability_definition(
		FighterSubclassSystem.TACTICAL_ABILITY_ID
	)
	if bool(game.call("_ability_attempt_is_valid", ability)):
		_fail("Combat-only subclass ability is enabled outside turn-based combat.")
		return

	hub.close_sheet()
	game.queue_free()
	await process_frame
	print("Fighter subclass through final runtime, action catalog and Character Hub smoke test passed.")
	quit(0)
