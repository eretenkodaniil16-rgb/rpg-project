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
	var action_catalog := game.find_child("ActionCatalogUI", true, false) as ActionCatalogUI
	var interaction_button := game.find_child("InteractButton", true, false) as Button
	if attack_button == null or catalog_button == null or end_turn_button == null or confirm_move_button == null or action_catalog == null or interaction_button == null:
		_fail("Exploration attack button or combat action catalog is missing.")
		return
	if game.find_child("QuickAttackButton", true, false) != null:
		_fail("A separate quick attack button is still present during combat.")
		return
	if attack_button.text != "АТАКА" or attack_button.size.y < 40.0:
		_fail("Exploration attack shortcut is too small or has an unclear label.")
		return
	if attack_button.get_global_rect().end.y > interaction_button.get_global_rect().position.y:
		_fail("Exploration attack shortcut is not placed above the interaction button.")
		return

	var menu_button := game.find_child("MenuButton", true, false) as Button
	var quest_button := game.find_child("QuestButton", true, false) as Button
	var character_button := game.find_child("CharacterButton", true, false) as Button
	if menu_button == null or quest_button == null or character_button == null:
		_fail("Top navigation buttons are missing.")
		return

	var combat_entries: Dictionary = {
		"action": [{
			"id": "attack",
			"label": "АТАКА",
			"enabled": true,
			"description": "Обычная атака экипированным оружием.",
			"group": "attack"
		}],
		"bonus": [],
		"reaction": []
	}
	action_catalog.refresh(
		true,
		true,
		false,
		combat_entries,
		"Действие: готово",
		"маршрут не выбран"
	)
	var stored_entries: Dictionary = action_catalog.get("_entries") as Dictionary
	var stored_actions: Array = stored_entries.get("action", []) as Array
	var combat_attack_found: bool = false
	for entry_value: Variant in stored_actions:
		if entry_value is Dictionary and str((entry_value as Dictionary).get("id", "")) == "attack":
			combat_attack_found = true
			break
	if not combat_attack_found:
		_fail("Combat attack is missing from ДЕЙСТВИЯ → АТАКИ.")
		return
	action_catalog.close_catalog()

	var route_safe_zone := Rect2(900.0, 340.0, 380.0, 380.0)
	for control: Button in [catalog_button, end_turn_button, confirm_move_button]:
		if control.get_global_rect().intersects(route_safe_zone):
			_fail("A fixed combat button still blocks the lower-right route area: %s" % control.name)
			return
	if game.find_child("InventoryButton", true, false) != null:
		_fail("Duplicate top inventory button is still present.")
		return

	var quest_gap: float = menu_button.get_global_rect().position.x - quest_button.get_global_rect().end.x
	var character_gap: float = quest_button.get_global_rect().position.x - character_button.get_global_rect().end.x
	if quest_gap < 0.0 or quest_gap > 20.0 or character_gap < 0.0 or character_gap > 20.0:
		_fail("Character and quest buttons are not grouped beside the menu button.")
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

	var d20_overlay := game.find_child("D20RollOverlay", true, false) as D20RollOverlay
	if d20_overlay == null or d20_overlay.z_index < 4090:
		_fail("D20 result overlay is missing or not above other UI.")
		return
	d20_overlay.show_d20_roll("Герой", "Проверка силы", 12, 16, true, 12, 0, 15, 4)
	await get_tree().process_frame
	await get_tree().process_frame
	var target_label := d20_overlay.find_child("D20TargetLabel", true, false) as Label
	var modifier_label := d20_overlay.find_child("D20ModifierLabel", true, false) as Label
	if not d20_overlay.visible or target_label == null or modifier_label == null:
		_fail("Detailed D20 result presentation is missing.")
		return
	if "15" not in target_label.text or "+4" not in modifier_label.text:
		_fail("D20 result does not show required target and modifier.")
		return

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

	await get_tree().create_timer(2.3).timeout
	selector_host.queue_free()
	game.queue_free()
	await get_tree().process_frame
	print("Exploration-only attack shortcut, combat catalog attack, detailed D20 overlay and compact HUD test passed.")
	get_tree().quit(0)
