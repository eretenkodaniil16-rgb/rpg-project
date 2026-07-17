extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"


func _init() -> void:
	call_deferred("_run_test")


func _run_test() -> void:
	GameState.begin_new_game(PlayerCharacter.create_legacy_default())

	var packed_scene: PackedScene = load(GAME_SCENE) as PackedScene
	assert(packed_scene != null)
	var game: Node = packed_scene.instantiate()
	assert(game != null)
	root.add_child(game)
	await process_frame

	var player: CharacterBody2D = game.get_node("Player") as CharacterBody2D
	assert(player != null)
	player.call("set_mobile_vector", Vector2.RIGHT)
	var right_direction: Vector2 = player.call("get_mobile_direction")
	assert(right_direction.is_equal_approx(Vector2.RIGHT))

	player.call("set_mobile_direction", &"up", true)
	var diagonal_direction: Vector2 = player.call("get_mobile_direction")
	assert(diagonal_direction.x > 0.0)
	assert(diagonal_direction.y < 0.0)
	assert(diagonal_direction.length() <= 1.001)

	player.call("clear_mobile_input")
	var cleared_direction: Vector2 = player.call("get_mobile_direction")
	assert(cleared_direction.is_zero_approx())
	print("Player mobile input test passed.")
	game.queue_free()
	quit(0)
