extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var game_state: Node = get_root().get_node_or_null("GameState")
	assert(game_state != null)

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
	assert(packed != null)
	var game: Node = packed.instantiate()
	get_root().add_child(game)
	await process_frame

	var dummy: TrainingDummy = game.get_node_or_null("TrainingDummy") as TrainingDummy
	assert(dummy != null)
	assert(dummy.get_armor_class() == 10)
	assert(dummy.get_current_health() == 12)

	var popup: AttackResultPopup = game.get_node_or_null("Interface/AttackResultPopup") as AttackResultPopup
	assert(popup != null)
	assert(not popup.visible)

	var result: AttackResult = dummy.attack_for_testing(10)
	assert(result.hit)
	assert(result.total == 15)
	assert(result.damage == 4)
	assert(dummy.get_current_health() == 8)

	game.queue_free()
	await process_frame
	print("Training dummy smoke test passed.")
	quit(0)
