extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const MUG_ID: String = "guard_post_mug_01"
const CANDLESTICK_ID: String = "guard_post_candlestick_01"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	var save_path: String = ProjectSettings.globalize_path("user://savegame.json")
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	state.call("new_game")
	state.set("player_character", _make_hero())

	var first: Node = await _spawn_game()
	if first == null:
		return
	var player: Node2D = first.get_node_or_null("Player") as Node2D
	var mug: ThrowableWorldProp = first.call("get_throwable_prop_node_for_testing", MUG_ID) as ThrowableWorldProp
	var candlestick: ThrowableWorldProp = first.call("get_throwable_prop_node_for_testing", CANDLESTICK_ID) as ThrowableWorldProp
	if player == null or mug == null or candlestick == null:
		_fail("Initial throwable prop fixtures are incomplete.")
		return

	player.global_position = mug.global_position
	first.call("_pickup_throwable_prop", MUG_ID)
	first.call("_throw_held_prop")
	await create_timer(0.45).timeout
	var first_registry: Dictionary = first.call("get_throwable_registry_for_testing") as Dictionary
	var first_mug: Dictionary = (first_registry.get("props", {}) as Dictionary).get(MUG_ID, {}) as Dictionary
	if str(first_mug.get("state", "")) != ThrowablePropSystem.STATE_BROKEN:
		_fail("Mug was not broken before the save round-trip.")
		return

	player.global_position = candlestick.global_position
	first.call("_pickup_throwable_prop", CANDLESTICK_ID)
	if str(first.call("get_held_throwable_prop_id_for_testing")) != CANDLESTICK_ID:
		_fail("Candlestick was not held before saving.")
		return
	state.call("save_game")
	first.queue_free()
	await process_frame

	if not bool(state.call("load_game")):
		_fail("Save containing throwable prop state could not be loaded.")
		return
	var second: Node = await _spawn_game()
	if second == null:
		return
	var second_registry: Dictionary = second.call("get_throwable_registry_for_testing") as Dictionary
	var second_mug: Dictionary = (second_registry.get("props", {}) as Dictionary).get(MUG_ID, {}) as Dictionary
	if str(second_mug.get("state", "")) != ThrowablePropSystem.STATE_BROKEN:
		_fail("Broken mug returned after loading.")
		return
	if str(second.call("get_held_throwable_prop_id_for_testing")) != CANDLESTICK_ID:
		_fail("Held candlestick was not restored after loading.")
		return
	var second_mug_node: ThrowableWorldProp = second.call("get_throwable_prop_node_for_testing", MUG_ID) as ThrowableWorldProp
	var second_candlestick: ThrowableWorldProp = second.call("get_throwable_prop_node_for_testing", CANDLESTICK_ID) as ThrowableWorldProp
	if second_mug_node == null or second_mug_node.is_available_for_pickup():
		_fail("Broken mug became available after loading.")
		return
	if second_candlestick == null or second_candlestick.is_available_for_pickup():
		_fail("Held candlestick incorrectly appeared in the world after loading.")
		return

	var second_player: Node2D = second.get_node_or_null("Player") as Node2D
	if second_player == null:
		_fail("Player is missing after loading throwable prop state.")
		return
	second.call("_set_selected_target", null)
	second.call("_face_toward", second_player.global_position + Vector2.RIGHT * 200.0)
	second.call("_throw_held_prop")
	await create_timer(0.45).timeout
	var thrown_position: Vector2 = second_candlestick.global_position
	if str(second.call("get_held_throwable_prop_id_for_testing")) != "" or not second_candlestick.is_available_for_pickup():
		_fail("Reusable candlestick did not return to the world after loading and throwing.")
		return
	second.queue_free()
	await process_frame

	if not bool(state.call("load_game")):
		_fail("Second throwable prop save could not be loaded.")
		return
	var third: Node = await _spawn_game()
	if third == null:
		return
	var third_candlestick: ThrowableWorldProp = third.call("get_throwable_prop_node_for_testing", CANDLESTICK_ID) as ThrowableWorldProp
	if third_candlestick == null or not third_candlestick.is_available_for_pickup():
		_fail("Reusable candlestick was not restored to the world.")
		return
	if third_candlestick.global_position.distance_to(thrown_position) > 1.0:
		_fail("Reusable candlestick landing position was not restored.")
		return
	if not str(third.call("get_held_throwable_prop_id_for_testing")).is_empty():
		_fail("Hands remained occupied after the reusable prop save round-trip.")
		return

	third.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Broken, held and reusable throwable prop states survived save/load round-trips.")
	quit(0)


func _spawn_game() -> Node:
	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	var game: Node = packed.instantiate() if packed != null else null
	if game == null:
		_fail("Game scene could not be instantiated for save restoration.")
		return null
	root.add_child(game)
	for _frame: int in range(30):
		await process_frame
	game.set_process(false)
	return game


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель сохранений"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.level = 3
	hero.maximum_health = 28
	hero.current_health = 28
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
