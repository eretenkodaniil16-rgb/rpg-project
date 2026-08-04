extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	state.call("new_game")
	state.set("player_character", _make_hero())
	state.set("inventory", {})
	state.call("add_item", "potion_of_healing", 2, false)
	state.call("add_item", "caretaker_field_note", 1, false)

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	var game: Node = packed.instantiate() if packed != null else null
	if game == null:
		_fail("Game scene could not be loaded.")
		return
	root.add_child(game)
	for _frame: int in range(14):
		await process_frame

	var player: Node = game.get_node_or_null("Player")
	var inventory_panel: InventoryPanel = game.get_node_or_null("Interface/InventoryPanel") as InventoryPanel
	if player == null or inventory_panel == null:
		_fail("Item-use runtime fixtures are incomplete.")
		return

	var potion_definition: Dictionary = state.call("get_item_definition", "potion_of_healing") as Dictionary
	var note_definition: Dictionary = state.call("get_item_definition", "caretaker_field_note") as Dictionary
	if potion_definition.is_empty() or note_definition.is_empty():
		_fail("Item-use extension catalog was not merged into GameState.")
		return

	var entries: Dictionary = game.call("get_action_catalog_entries_for_testing") as Dictionary
	if not _has_action_label(entries, "ВЫПИТЬ: ЗЕЛЬЕ ЛЕЧЕНИЯ"):
		_fail("Wounded hero has no explicit Russian healing-potion action.")
		return

	var potion_result: Dictionary = game.call(
		"use_item_for_testing",
		"potion_of_healing",
		null,
		{"healing_roll_override": 6}
	) as Dictionary
	if not bool(potion_result.get("success", false)):
		_fail("Healing potion use failed: %s" % potion_result)
		return
	if int(state.get("player_character").current_health) != 10:
		_fail("Healing potion did not apply the deterministic six-point heal.")
		return
	if int(state.call("get_item_count", "potion_of_healing")) != 1:
		_fail("Healing potion was not consumed exactly once.")
		return

	inventory_panel.open_inventory()
	var note_entry: Dictionary = note_definition.duplicate(true)
	note_entry["quantity"] = 1
	inventory_panel.call("_show_details", note_entry)
	var use_button: Button = inventory_panel.get("_use_button") as Button
	if use_button == null or not use_button.visible or use_button.text != "ПРОЧИТАТЬ":
		_fail("Inventory does not expose the data-driven Read button for the story note.")
		return
	inventory_panel.call("_use_selected")
	await process_frame
	if not bool(state.call("get_flag", "caretaker_field_note_read", false)):
		_fail("Reading the story note did not set its persistent flag.")
		return
	if int(state.call("get_item_count", "caretaker_field_note")) != 1:
		_fail("Non-consumable story note was removed from inventory.")
		return
	if inventory_panel.visible or bool(state.get("input_locked")):
		_fail("Using an item from inventory did not close the overlay and restore input.")
		return

	state.get("player_character").current_health = 5
	var turn_system: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	turn_system.start_combat(player, [], 0)
	var combat_result: Dictionary = game.call(
		"_execute_item_use",
		"potion_of_healing",
		null,
		{"healing_roll_override": 4}
	) as Dictionary
	if not bool(combat_result.get("success", false)):
		_fail("Combat healing-potion use failed: %s" % combat_result)
		return
	if turn_system.action_available:
		_fail("Using a healing potion in combat did not consume the main action.")
		return
	if int(state.call("get_item_count", "potion_of_healing")) != 0:
		_fail("Combat potion use did not consume the last potion exactly once.")
		return
	var note_in_combat: Dictionary = game.call("_execute_item_use", "caretaker_field_note", null, {}) as Dictionary
	if bool(note_in_combat.get("success", false)):
		_fail("Story note was allowed during combat despite its data contract.")
		return

	game.queue_free()
	await process_frame
	print("Item-use runtime, inventory button, combat action cost and story flag smoke test passed.")
	quit(0)


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель предметов"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.maximum_health = 12
	hero.current_health = 4
	hero.starter_loadout_granted = true
	return hero


func _has_action_label(entries: Dictionary, expected: String) -> bool:
	for category_id: String in ["action", "bonus", "free", "reaction"]:
		var values: Variant = entries.get(category_id, [])
		if not values is Array:
			continue
		for value: Variant in values as Array:
			if value is Dictionary and str((value as Dictionary).get("label", "")) == expected:
				return true
	return false


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
