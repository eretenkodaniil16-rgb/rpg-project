extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var game_state: Node = get_root().get_node_or_null("GameState")
	if game_state == null:
		_fail("GameState autoload is missing.")
		return

	var character := PlayerCharacter.new()
	character.character_name = "Боец"
	character.character_class_id = "fighter"
	character.character_class_name = "Воин"
	character.level = 1
	character.abilities["strength"] = 16
	game_state.set("player_character", character)
	game_state.set("player_position", Vector2(320.0, 360.0))
	game_state.set("input_locked", false)

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	if packed == null:
		_fail("Game scene failed to load.")
		return
	var game: Node = packed.instantiate()
	get_root().add_child(game)
	await process_frame
	await process_frame

	var dummy: Node = game.get_node_or_null("TrainingDummy")
	if dummy == null:
		_fail("Training dummy was not created in the game scene.")
		return
	if int(dummy.call("get_armor_class")) != 10 or int(dummy.call("get_current_health")) != 12:
		_fail("Training dummy has incorrect initial combat stats.")
		return

	var popup: Node = game.get_node_or_null("Interface/AttackResultPopup")
	if popup == null or bool(popup.get("visible")):
		_fail("Attack result popup was not initialized hidden.")
		return

	var result: Variant = dummy.call("attack_for_testing", 10)
	if result == null:
		_fail("Training attack returned no result.")
		return
	if not bool(result.get("hit")) or int(result.get("total")) != 15 or int(result.get("damage")) != 4:
		_fail("Training attack result is incorrect.")
		return
	if int(dummy.call("get_current_health")) != 8:
		_fail("Training dummy did not receive damage.")
		return

	game.queue_free()
	await process_frame
	print("Training dummy smoke test passed.")
	quit(0)
