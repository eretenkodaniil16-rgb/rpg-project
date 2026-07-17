extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"


func _init() -> void:
	call_deferred("_run_test")


func _run_test() -> void:
	var game_state: Node = root.get_node("GameState")
	game_state.call("begin_new_game", PlayerCharacter.create_legacy_default())

	var packed_scene: PackedScene = load(GAME_SCENE) as PackedScene
	assert(packed_scene != null)
	var game: Node = packed_scene.instantiate()
	root.add_child(game)
	await process_frame

	var controls: Control = game.get_node("Interface/MobileControls") as Control
	assert(controls != null)
	controls.call("enable_for_testing")
	await process_frame

	var move_pad: Control = controls.get_node("MovePad") as Control
	var base: Panel = move_pad.get_node("JoystickBase") as Panel
	var knob: Panel = move_pad.get_node("JoystickKnob") as Panel
	assert(controls.visible)
	assert(move_pad.size.x >= 250.0 and move_pad.size.y >= 250.0)
	assert(base.visible and base.size.x >= 200.0 and base.size.y >= 200.0)
	assert(knob.visible and knob.size.x >= 80.0 and knob.size.y >= 80.0)

	var player: CharacterBody2D = game.get_node("Player") as CharacterBody2D
	controls.call("move_joystick_for_testing", Vector2.RIGHT)
	var active_direction: Vector2 = player.call("get_mobile_direction") as Vector2
	assert(active_direction.x > 0.95)
	assert(absf(active_direction.y) < 0.01)

	controls.call("release_joystick_for_testing")
	var released_direction: Vector2 = player.call("get_mobile_direction") as Vector2
	assert(released_direction.is_zero_approx())

	print("Visible mobile joystick smoke test passed.")
	game.queue_free()
	quit(0)
