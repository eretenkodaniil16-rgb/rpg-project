extends Node

var _completed: bool = false


func _ready() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	if _completed:
		return
	_completed = true
	push_error(message)
	get_tree().quit(1)


func _run() -> void:
	var state: Node = get_node_or_null("/root/GameState")
	if state == null:
		_fail("GameState autoload is unavailable.")
		return
	state.call("new_game")
	var character := PlayerCharacter.new()
	character.character_name = "Мобильный герой"
	character.character_class_id = "fighter"
	character.character_class_name = "Воин"
	character.maximum_health = 20
	character.current_health = 20
	character.level = 1
	character.experience = 0
	character.abilities["strength"] = 16
	character.abilities["dexterity"] = 14
	state.set("player_character", character)
	state.set("input_locked", false)

	var packed: PackedScene = load("res://scenes/game/game.tscn") as PackedScene
	if packed == null:
		_fail("Game scene is unavailable.")
		return
	var game: Node = packed.instantiate()
	add_child(game)
	for _frame: int in range(12):
		await get_tree().process_frame

	var mobile_controls := game.find_child("MobileControls", true, false) as Control
	var action_catalog := game.find_child("ActionCatalogUI", true, false) as ActionCatalogUI
	var menu_button := game.find_child("MenuButton", true, false) as Button
	var quest_button := game.find_child("QuestButton", true, false) as Button
	var character_button := game.find_child("CharacterButton", true, false) as Button
	var player := game.find_child("Player", true, false) as CharacterBody2D
	var caretaker := game.find_child("Caretaker", true, false) as Node
	if mobile_controls == null or action_catalog == null or menu_button == null or quest_button == null or character_button == null or player == null or caretaker == null:
		_fail("Mobile combat HUD fixtures are incomplete.")
		return
	mobile_controls.call("enable_for_testing")
	await get_tree().process_frame

	var actions_button := mobile_controls.call("get_actions_button_for_testing") as Button
	if actions_button == null or actions_button.text != "ДЕЙСТВИЯ":
		_fail("Persistent lower-right Actions button is missing.")
		return
	if action_catalog.catalog_button.visible:
		_fail("Legacy ActionCatalog button is still visible.")
		return

	game.call("_start_turn_based_combat", caretaker)
	game.call("force_player_turn_for_testing")
	mobile_controls.call("_process", 0.4)
	await get_tree().process_frame
	if not bool(game.call("is_turn_based_combat_active")):
		_fail("Combat did not start for the mobile HUD test.")
		return
	if actions_button.disabled:
		_fail("Actions button stayed disabled on the player turn.")
		return

	mobile_controls.call("simulate_actions_touch_for_testing")
	await get_tree().process_frame
	if not action_catalog.panel.visible:
		_fail("The completed lower-right Actions gesture did not open the combat catalog.")
		return
	action_catalog.close_catalog()

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
	if game.find_child("LevelUpPanel", true, false) == null:
		_fail("Mobile level-up panel is missing from the game interface.")
		return

	var action_state: Dictionary = {"id": ""}
	action_catalog.action_requested.connect(func(action_id: String) -> void: action_state["id"] = action_id)

	# Catalog actions are tested through the same quick BaseButton path used on
	# Android. Direct panel.show() is intentionally forbidden because it models
	# the spontaneous visibility bug rather than a legitimate user command.
	mobile_controls.call("simulate_actions_touch_for_testing")
	if not action_catalog.panel.visible:
		_fail("Normal Actions tap did not open the catalog for an available action.")
		return
	action_catalog.call("_emit_action", "test_action", "Проверка", true)
	if str(action_state.get("id", "")) != "test_action" or action_catalog.panel.visible:
		_fail("Available catalog action did not emit or close the catalog.")
		return

	mobile_controls.call("simulate_actions_touch_for_testing")
	if not action_catalog.panel.visible:
		_fail("Normal Actions tap did not open the catalog for feedback testing.")
		return
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

	_completed = true
	game.queue_free()
	await get_tree().process_frame
	print("Mobile combat, progression and compact HUD regression test passed.")
	get_tree().quit(0)
