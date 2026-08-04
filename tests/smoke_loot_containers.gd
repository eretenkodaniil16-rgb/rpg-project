extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const CHEST_ID: String = "guard_post_supply_chest_01"
const BAG_ID: String = "guard_post_abandoned_satchel_01"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	state.call("new_game")
	state.set("player_character", _make_hero())
	state.set("player_position", Vector2(320.0, 360.0))
	state.set("inventory", {})

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	var game: Node = packed.instantiate() if packed != null else null
	if game == null:
		_fail("Game scene could not be loaded.")
		return
	root.add_child(game)
	for _frame: int in range(14):
		await process_frame

	var player: Node = game.get_node_or_null("Player")
	var manager: WorldLootContainerManager = game.call("get_loot_container_manager_for_testing") as WorldLootContainerManager
	var panel: LootContainerPanel = game.call("get_loot_container_panel_for_testing") as LootContainerPanel
	if player == null or manager == null or panel == null:
		_fail("Loot runtime fixtures are incomplete.")
		return

	var chest: WorldLootContainer = manager.get_container_node(CHEST_ID)
	if chest == null:
		_fail("Supply chest was not restored from structured data.")
		return
	(player as Node2D).global_position = chest.global_position
	player.call("register_interactable", chest)
	var entries: Dictionary = game.call("get_action_catalog_entries_for_testing") as Dictionary
	if not _has_action_label(entries, "ОТКРЫТЬ: СУНДУК СНАБЖЕНИЯ"):
		_fail("Nearby closed chest has no explicit Russian open action.")
		return

	game.call("open_loot_container_for_testing", CHEST_ID)
	if not panel.is_open() or panel.get_source_id() != CHEST_ID:
		_fail("Opening the chest did not show the mobile loot panel.")
		return
	var labels: Array[String] = panel.get_item_action_labels_for_testing()
	if "ПОДОБРАТЬ: СТРЕЛА ×12" not in labels:
		_fail("Arrow stack does not use the required Russian pickup label: %s" % labels)
		return
	for label: String in labels:
		if "arrow" in label.to_lower() or "javelin" in label.to_lower() or "gold_coin" in label.to_lower():
			_fail("System item id leaked into the loot panel: %s" % label)
			return

	game.call("take_active_loot_item_for_testing", "arrow")
	if int(state.call("get_item_count", "arrow")) != 12:
		_fail("Picking the arrow stack did not transfer exactly 12 arrows.")
		return
	var chest_after: Dictionary = manager.get_record(CHEST_ID)
	if _item_quantity(chest_after, "arrow") != 0:
		_fail("Transferred arrows remained in the chest record.")
		return
	game.call("take_active_loot_item_for_testing", "arrow")
	if int(state.call("get_item_count", "arrow")) != 12:
		_fail("Repeated same-frame pickup duplicated the arrow stack.")
		return
	panel.close_panel()
	await process_frame
	if bool(state.get("input_locked")):
		_fail("Closing the loot panel did not restore world input.")
		return

	var snapshot: Dictionary = state.call("get_world_snapshot") as Dictionary
	var environment: Dictionary = snapshot.get("environment", {}) as Dictionary
	var saved_registry: Dictionary = environment.get(WorldLootContainerManager.SNAPSHOT_KEY, {}) as Dictionary
	var saved_chest: Dictionary = saved_registry.get(CHEST_ID, {}) as Dictionary
	if saved_chest.is_empty() or _item_quantity(saved_chest, "arrow") != 0 or not bool(saved_chest.get("is_open", false)):
		_fail("Opened and partially looted chest was not captured in world_snapshot.")
		return
	manager.reload_from_snapshot_for_testing()
	await process_frame
	if _item_quantity(manager.get_record(CHEST_ID), "arrow") != 0:
		_fail("Reloading the world snapshot restored already collected arrows.")
		return

	state.call("add_item", "thieves_tools", 1, false)
	var bag: WorldLootContainer = manager.get_container_node(BAG_ID)
	if bag == null:
		_fail("Abandoned bag was not restored from structured data.")
		return
	(player as Node2D).global_position = bag.global_position
	player.call("register_interactable", bag)
	game.call("open_loot_container_for_testing", BAG_ID)
	if not panel.is_open():
		_fail("Opening the bag did not show the loot panel.")
		return
	game.call("take_all_active_loot_for_testing")
	if int(state.call("get_item_count", "healers_kit")) != 1 or int(state.call("get_item_count", "parchment")) != 3:
		_fail("Take All did not transfer items that fit the inventory.")
		return
	if int(state.call("get_item_count", "thieves_tools")) != 1:
		_fail("Take All changed the already-full non-stackable item count.")
		return
	if _item_quantity(manager.get_record(BAG_ID), "thieves_tools") != 1:
		_fail("Take All removed an item that did not fit the inventory.")
		return
	panel.close_panel()

	game.queue_free()
	await process_frame
	print("Persistent loot containers, Russian pickup labels and capacity-safe transfers passed.")
	quit(0)


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель добычи"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.maximum_health = 12
	hero.current_health = 12
	hero.starter_loadout_granted = true
	return hero


func _has_action_label(entries: Dictionary, expected: String) -> bool:
	for category_id: String in ["action", "bonus", "reaction"]:
		var values: Variant = entries.get(category_id, [])
		if not values is Array:
			continue
		for value: Variant in values as Array:
			if value is Dictionary and str((value as Dictionary).get("label", "")) == expected:
				return true
	return false


func _item_quantity(record: Dictionary, item_id: String) -> int:
	var items_value: Variant = record.get("items", [])
	if not items_value is Array:
		return 0
	for value: Variant in items_value as Array:
		if value is Dictionary and str((value as Dictionary).get("item_id", "")) == item_id:
			return maxi(int((value as Dictionary).get("quantity", 0)), 0)
	return 0


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
