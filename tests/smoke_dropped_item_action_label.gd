extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const PICKUP_PREFIX: String = "pickup_dropped_inventory:"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	state.call("new_game")
	var hero := PlayerCharacter.new()
	hero.character_name = "Проверяющий подписи"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.maximum_health = 12
	hero.current_health = 12
	hero.starter_loadout_granted = true
	state.set("player_character", hero)
	state.set("player_position", Vector2(320.0, 360.0))

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	var game: Node = packed.instantiate() if packed != null else null
	if game == null:
		_fail("Game scene failed to load.")
		return
	root.add_child(game)
	for _frame: int in range(10):
		await process_frame

	var player: Node = game.get_node_or_null("Player")
	var manager: DroppedInventoryItemManager = game.call("get_dropped_inventory_manager_for_testing") as DroppedInventoryItemManager
	if player == null or manager == null:
		_fail("Player or dropped-item manager is missing.")
		return
	var dropped: DroppedInventoryItem = manager.spawn_dropped_item(
		"javelin",
		1,
		(player as Node2D).global_position
	)
	if dropped == null:
		_fail("The javelin drop could not be created.")
		return
	player.call("register_interactable", dropped)
	var entries: Dictionary = game.call("get_action_catalog_entries_for_testing") as Dictionary
	var actions: Array = entries.get("action", []) as Array
	var pickup_found: bool = false
	for value: Variant in actions:
		if not value is Dictionary:
			continue
		var entry: Dictionary = value as Dictionary
		if not str(entry.get("id", "")).begins_with(PICKUP_PREFIX):
			continue
		pickup_found = true
		var label: String = str(entry.get("label", ""))
		if label != "ПОДОБРАТЬ: ДРОТИК":
			_fail("Dropped item has an incorrect pickup label: %s" % label)
			return
		if "javelin" in label.to_lower():
			_fail("System item id leaked into the player-facing action label.")
			return
		var description: String = str(entry.get("description", ""))
		if "инвентар" not in description.to_lower():
			_fail("Pickup action does not explain the inventory transfer.")
			return
	if not pickup_found:
		_fail("No explicit pickup action was added for the nearby dropped item.")
		return

	game.queue_free()
	await process_frame
	print("Dropped item action uses an explicit Russian pickup label.")
	quit(0)


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
