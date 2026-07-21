extends Node


func _ready() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	get_tree().quit(1)


func _run() -> void:
	GameState.new_game()
	var hero := PlayerCharacter.new()
	hero.character_name = "Тестовый воин"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.abilities["constitution"] = 14
	hero.maximum_health = 12
	hero.current_health = 12
	hero.hit_die_size = 10
	hero.hit_dice_maximum = 1
	hero.hit_dice_current = 1
	GameState.player_character = hero
	ClassDataSystem.new().ensure_starting_loadout(hero)

	var progression: Dictionary = ProgressionSystem.grant_experience(hero, 100)
	if hero.level != 2 or hero.experience != 100:
		_fail("Experience did not advance the fighter to level 2.")
		return
	if int(progression.get("health_gained", 0)) <= 0 or hero.maximum_health <= 12:
		_fail("Level advancement did not increase maximum health.")
		return

	var game_scene: PackedScene = load("res://scenes/game/game.tscn") as PackedScene
	var game: Node = game_scene.instantiate()
	add_child(game)
	await get_tree().process_frame
	await get_tree().process_frame

	var attack_button := game.find_child("AttackButton", true, false) as Button
	var catalog_button := game.find_child("ActionCatalogButton", true, false) as Button
	var end_turn_button := game.find_child("EndTurnFixedButton", true, false) as Button
	var confirm_move_button := game.find_child("ConfirmMovementFloatingButton", true, false) as Button
	if attack_button == null or catalog_button == null or end_turn_button == null or confirm_move_button == null:
		_fail("Combat buttons are missing from the game HUD.")
		return
	if attack_button.get_global_rect().intersects(catalog_button.get_global_rect()):
		_fail("Attack button still overlaps the mobile action catalog button.")
		return
	var route_safe_zone := Rect2(900.0, 340.0, 380.0, 380.0)
	for control: Button in [attack_button, catalog_button, end_turn_button, confirm_move_button]:
		if control.get_global_rect().intersects(route_safe_zone):
			_fail("A fixed combat button still blocks the lower-right route area: %s" % control.name)
			return
	if game.find_child("InventoryButton", true, false) != null:
		_fail("Duplicate top inventory button is still present.")
		return

	var status_hud := game.find_child("PlayerStatusHud", true, false) as PlayerStatusHud
	if status_hud == null or status_hud.find_child("GameplayHealthBar", true, false) == null:
		_fail("Compact gameplay health bar is missing.")
		return
	if status_hud.find_child("GameplayExperienceBar", true, false) != null:
		_fail("Gameplay HUD still contains the large experience panel.")
		return
	var status_panel := status_hud.find_child("PlayerStatusPanel", true, false) as Control
	if status_panel == null or status_panel.size.y > 60.0:
		_fail("Gameplay character HUD is still too large.")
		return

	var action_catalog := game.find_child("ActionCatalogUI", true, false) as ActionCatalogUI
	if action_catalog == null:
		_fail("Action catalog UI is missing.")
		return
	var action_state: Dictionary = {"id": ""}
	action_catalog.action_requested.connect(func(action_id: String) -> void: action_state["id"] = action_id)
	action_catalog.panel.show()
	action_catalog.call("_emit_action", "test_action", "Проверка", true)
	if str(action_state.get("id", "")) != "test_action" or action_catalog.panel.visible:
		_fail("Available catalog action did not emit or close the catalog.")
		return
	action_catalog.panel.show()
	action_catalog.call("_emit_action", "blocked_action", "Нужна соседняя цель.", false)
	if not action_catalog.panel.visible or "недоступно" not in action_catalog.description_label.text.to_lower():
		_fail("Unavailable catalog action did not provide visible feedback.")
		return
	action_catalog.close_catalog()

	var hub := game.find_child("CharacterHub", true, false) as CharacterHub
	if hub == null:
		_fail("Character hub is missing.")
		return
	hub.open_tab(hero, 0)
	await get_tree().process_frame
	if hub.find_child("CharacterPortrait", true, false) == null:
		_fail("Character portrait is missing from the character tab.")
		return
	if hub.find_child("CharacterHealthBar", true, false) == null or hub.find_child("CharacterExperienceBar", true, false) == null:
		_fail("Character tab health or experience bar is missing.")
		return
	hub.close_sheet()

	var selector_host := Control.new()
	selector_host.position = Vector2(500.0, 300.0)
	selector_host.size = Vector2(220.0, 120.0)
	add_child(selector_host)
	var selector := Button.new()
	selector.size = Vector2(180.0, 90.0)
	selector.set_meta("selector_id", "fighter")
	selector_host.add_child(selector)
	var selection_state: Dictionary = {"count": 0}
	selector.pressed.connect(func() -> void: selection_state["count"] = int(selection_state["count"]) + 1)
	await get_tree().process_frame

	var assist: Node = get_node_or_null("/root/CharacterSelectionTouchAssist")
	if assist == null:
		_fail("Character selection touch assistant is not registered.")
		return
	var press := InputEventScreenTouch.new()
	press.index = 41
	press.pressed = true
	press.position = Vector2(540.0, 340.0)
	assist.call("_input", press)
	var drag := InputEventScreenDrag.new()
	drag.index = 41
	drag.position = Vector2(552.0, 340.0)
	assist.call("_input", drag)
	var release := InputEventScreenTouch.new()
	release.index = 41
	release.pressed = false
	release.position = Vector2(552.0, 340.0)
	assist.call("_input", release)
	await get_tree().process_frame
	await get_tree().process_frame
	if int(selection_state.get("count", 0)) < 1:
		_fail("A small finger movement still cancels race/class selection.")
		return

	selector_host.queue_free()
	game.queue_free()
	await get_tree().process_frame
	print("Compact gameplay HUD, clear route area, responsive actions, progression and selection threshold test passed.")
	get_tree().quit(0)
