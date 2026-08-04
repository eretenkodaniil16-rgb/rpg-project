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
	var character := PlayerCharacter.new()
	character.character_name = "Испытатель ресурсов"
	character.character_class_id = "ranger"
	character.character_class_name = "Следопыт"
	character.maximum_health = 30
	character.current_health = 30
	character.abilities["dexterity"] = 18
	character.weapon_proficiencies = ["simple_weapons", "martial_weapons"]
	character.equipped_weapon_id = "longbow"
	character.starter_loadout_granted = true
	state.set("player_character", character)
	state.set("player_position", Vector2(320.0, 360.0))

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	if packed == null:
		_fail("Game scene failed to load.")
		return
	var game: Node = packed.instantiate()
	root.add_child(game)
	for _frame: int in range(10):
		await process_frame

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var caretaker: Node2D = game.get_node_or_null("Caretaker") as Node2D
	var manager: DroppedInventoryItemManager = game.call("get_dropped_inventory_manager_for_testing") as DroppedInventoryItemManager
	if player == null or caretaker == null or manager == null:
		_fail("Consumable inventory runtime fixtures are incomplete.")
		return

	state.set("inventory", {"arrow": 5, "javelin": 1, "longbow": 1})
	var reservation: Dictionary = state.call(
		"reserve_inventory_item",
		"arrow",
		1,
		"cancelled_test",
		{}
	) as Dictionary
	if not bool(reservation.get("success", false)):
		_fail("A valid arrow reservation was rejected.")
		return
	if int(state.call("get_item_count", "arrow")) != 5:
		_fail("Reserving an item changed the stored inventory before commit.")
		return
	state.call("rollback_inventory_transaction", str(reservation.get("transaction_id", "")))
	if int(state.call("get_item_count", "arrow")) != 5:
		_fail("Rolling back an attack reservation consumed an arrow.")
		return

	var test_bow: Dictionary = {
		"id": "test_bow",
		"name": "Проверочный лук",
		"type": "weapon",
		"weapon_category": "simple",
		"damage_dice": [1, 4],
		"damage_type": "колющий",
		"ability": "dexterity",
		"properties": ["ammunition", "ranged"],
		"range_normal_ft": 30,
		"range_long_ft": 60,
		"ammunition_id": "arrow"
	}
	caretaker.global_position = player.global_position + Vector2(64.0, 0.0)
	await game.call(
		"perform_transactional_weapon_attack_for_testing",
		caretaker,
		test_bow,
		"arrow",
		1
	)
	await _close_attack_popup(game)
	if int(state.call("get_item_count", "arrow")) != 4:
		_fail("A completed natural-one miss did not consume exactly one arrow.")
		return

	await game.call(
		"perform_transactional_weapon_attack_for_testing",
		caretaker,
		test_bow,
		"arrow",
		20
	)
	await _close_attack_popup(game)
	if int(state.call("get_item_count", "arrow")) != 3:
		_fail("A completed hit did not consume exactly one arrow.")
		return

	var short_range_bow: Dictionary = test_bow.duplicate(true)
	short_range_bow["range_normal_ft"] = 5
	short_range_bow["range_long_ft"] = 10
	caretaker.global_position = player.global_position + Vector2(192.0, 0.0)
	await game.call(
		"perform_transactional_weapon_attack_for_testing",
		caretaker,
		short_range_bow,
		"arrow",
		20
	)
	await _close_attack_popup(game)
	if int(state.call("get_item_count", "arrow")) != 3:
		_fail("An out-of-range attack committed its reserved arrow.")
		return

	var javelin: Dictionary = state.call("get_item_definition", "javelin") as Dictionary
	caretaker.global_position = player.global_position + Vector2(128.0, 0.0)
	await game.call(
		"perform_transactional_weapon_attack_for_testing",
		caretaker,
		javelin,
		"",
		1
	)
	await _close_attack_popup(game)
	if int(state.call("get_item_count", "javelin")) != 0:
		_fail("A ranged javelin throw did not remove the weapon from inventory.")
		return
	if manager.get_drop_count_for_testing() != 1:
		_fail("A thrown javelin did not create one recoverable world item.")
		return

	var snapshot: Dictionary = state.call("get_world_snapshot") as Dictionary
	var environment: Dictionary = snapshot.get("environment", {}) as Dictionary
	var dropped_records: Dictionary = environment.get(
		DroppedInventoryItemManager.SNAPSHOT_KEY,
		{}
	) as Dictionary
	if dropped_records.size() != 1:
		_fail("The thrown weapon was not captured in the world snapshot.")
		return
	var drop_id: String = str(dropped_records.keys()[0])
	var dropped_node: DroppedInventoryItem = manager.get_drop_node_for_testing(drop_id)
	if dropped_node == null or not dropped_node.is_available_for_pickup():
		_fail("The recoverable javelin has no active world node.")
		return
	if not manager.collect_drop(drop_id, false):
		_fail("The recoverable javelin could not be collected.")
		return
	if dropped_node.is_available_for_pickup() or manager.collect_drop(drop_id, false):
		_fail("A collected javelin remained available for a duplicate same-frame pickup.")
		return
	if int(state.call("get_item_count", "javelin")) != 1 or manager.get_drop_count_for_testing() != 0:
		_fail("Collecting the javelin did not restore inventory and clear the world record.")
		return

	var save_data: Dictionary = state.call("_build_save_data", "manual", 1) as Dictionary
	var saved_arrow_count: int = int(state.call("get_item_count", "arrow"))
	state.call("add_item", "arrow", 5, false)
	if not bool(state.call("_apply_save_data", save_data)):
		_fail("Current consumable inventory save data could not be reloaded.")
		return
	if int(state.call("get_item_count", "arrow")) != saved_arrow_count:
		_fail("Reloading did not restore the exact ammunition quantity.")
		return

	var legacy_save: Dictionary = save_data.duplicate(true)
	legacy_save["version"] = 6
	legacy_save.erase("world_snapshot")
	if not bool(state.call("_apply_save_data", legacy_save)):
		_fail("A version-6 save without dropped items failed backward-compatible loading.")
		return
	if int(state.call("get_item_count", "arrow")) != saved_arrow_count:
		_fail("Legacy save migration changed ammunition quantities.")
		return
	var migrated_snapshot: Dictionary = state.call("get_world_snapshot") as Dictionary
	var migrated_environment: Dictionary = migrated_snapshot.get("environment", {}) as Dictionary
	if migrated_environment.has(DroppedInventoryItemManager.SNAPSHOT_KEY):
		var migrated_drops: Variant = migrated_environment.get(DroppedInventoryItemManager.SNAPSHOT_KEY, {})
		if migrated_drops is Dictionary and not (migrated_drops as Dictionary).is_empty():
			_fail("Legacy save migration invented dropped inventory items.")
			return

	game.queue_free()
	await process_frame
	print("Ammunition transactions, misses, hits, thrown recovery and save compatibility passed.")
	quit(0)


func _close_attack_popup(game: Node) -> void:
	var popup: Control = game.find_child("AttackResultPopup", true, false) as Control
	if popup != null and popup.visible and popup.has_method("_on_continue_pressed"):
		popup.call("_on_continue_pressed")
		await process_frame


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
