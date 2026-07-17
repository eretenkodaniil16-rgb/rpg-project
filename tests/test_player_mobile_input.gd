extends SceneTree

const PLAYER_SCRIPT: Script = preload("res://scripts/game/player.gd")


func _init() -> void:
	call_deferred("_run_test")


func _run_test() -> void:
	GameState.begin_new_game(PlayerCharacter.create_legacy_default())

	var player: CharacterBody2D = CharacterBody2D.new()
	player.name = "Player"
	var body: Polygon2D = Polygon2D.new()
	body.name = "Body"
	player.add_child(body)
	var name_label: Label = Label.new()
	name_label.name = "NameLabel"
	player.add_child(name_label)
	player.set_script(PLAYER_SCRIPT)
	root.add_child(player)
	await process_frame

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
	player.queue_free()
	quit(0)
