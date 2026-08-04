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
	character.character_name = "Стрелок по направлению"
	character.character_class_id = "ranger"
	character.character_class_name = "Следопыт"
	character.maximum_health = 20
	character.current_health = 20
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
	var manager: DroppedInventoryItemManager = game.call("get_dropped_inventory_manager_for_testing") as DroppedInventoryItemManager
	if player == null or manager == null:
		_fail("Directional consumable fixtures are incomplete.")
		return
	_move_all_targets_behind_player(player)
	player.call("set_facing_direction", Vector2.RIGHT)
	state.set("inventory", {"arrow": 2, "javelin": 1, "longbow": 1})

	var longbow: Dictionary = state.call("get_item_definition", "longbow") as Dictionary
	if longbow.is_empty():
		_fail("Longbow definition is missing.")
		return
	game.call("_request_directional_ranged_attack", longbow)
	await create_timer(1.0).timeout
	if int(state.call("get_item_count", "arrow")) != 1:
		_fail("An empty-direction bow shot did not consume exactly one arrow.")
		return
	if bool(state.call("has_active_inventory_transactions")):
		_fail("An empty-direction bow shot left an active reservation.")
		return
	if manager.get_drop_count_for_testing() != 0:
		_fail("An ordinary arrow incorrectly created a recoverable world item.")
		return

	state.set("inventory", {"arrow": 0, "javelin": 1, "longbow": 1})
	game.call("_request_directional_ranged_attack", longbow)
	await create_timer(0.2).timeout
	if int(state.call("get_item_count", "arrow")) != 0:
		_fail("A no-ammunition shot changed the inventory.")
		return
	if bool(state.call("has_active_inventory_transactions")):
		_fail("A rejected no-ammunition shot left an active reservation.")
		return

	var javelin: Dictionary = state.call("get_item_definition", "javelin") as Dictionary
	if javelin.is_empty():
		_fail("Javelin definition is missing.")
		return
	game.call("_request_directional_ranged_attack", javelin)
	await create_timer(1.0).timeout
	if int(state.call("get_item_count", "javelin")) != 0:
		_fail("An empty-direction javelin throw did not consume the weapon.")
		return
	if manager.get_drop_count_for_testing() != 1:
		_fail("An empty-direction javelin throw did not create one recoverable item.")
		return
	var snapshot: Dictionary = state.call("get_world_snapshot") as Dictionary
	var environment: Dictionary = snapshot.get("environment", {}) as Dictionary
	var records: Dictionary = environment.get(DroppedInventoryItemManager.SNAPSHOT_KEY, {}) as Dictionary
	if records.size() != 1:
		_fail("The empty-direction javelin drop was not persisted in world state.")
		return
	if bool(state.call("has_active_inventory_transactions")):
		_fail("An empty-direction javelin throw left an active reservation.")
		return

	game.queue_free()
	await process_frame
	print("Target-free bow and javelin transactions passed.")
	quit(0)


func _move_all_targets_behind_player(player: Node2D) -> void:
	var seen: Dictionary = {}
	for group_name: String in ["combat_targets", "context_action_targets"]:
		for candidate: Node in get_nodes_in_group(group_name):
			if not candidate is Node2D or candidate == player:
				continue
			var instance_id: int = candidate.get_instance_id()
			if seen.has(instance_id):
				continue
			seen[instance_id] = true
			(candidate as Node2D).global_position = player.global_position + Vector2(-512.0, 0.0)


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
