extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"


func _init() -> void:
	call_deferred("_run_test")


func _run_test() -> void:
	var game_state: Node = root.get_node_or_null("GameState")
	if game_state == null:
		_fail("GameState autoload is missing.")
		return
	game_state.call("begin_new_game", PlayerCharacter.create_legacy_default())

	var packed_scene: PackedScene = load(GAME_SCENE) as PackedScene
	if packed_scene == null:
		_fail("Game scene could not be loaded.")
		return
	var game: Node = packed_scene.instantiate()
	root.add_child(game)
	for _frame: int in range(6):
		await process_frame

	var controls: Control = game.get_node_or_null("Interface/MobileControls") as Control
	if controls == null:
		_fail("Mobile controls are missing.")
		return
	controls.call("enable_for_testing")
	await process_frame

	var move_pad: Control = controls.get_node_or_null("MovePad") as Control
	var base: Panel = move_pad.get_node_or_null("JoystickBase") as Panel if move_pad != null else null
	var knob: Panel = move_pad.get_node_or_null("JoystickKnob") as Panel if move_pad != null else null
	if not controls.visible:
		_fail("Mobile controls are not visible in the test layout.")
		return
	if move_pad == null or move_pad.size.x < 250.0 or move_pad.size.y < 250.0:
		_fail("Mobile joystick pad is smaller than the required touch target.")
		return
	if base == null or not base.visible or base.size.x < 200.0 or base.size.y < 200.0:
		_fail("Joystick base is missing or too small.")
		return
	if knob == null or not knob.visible or knob.size.x < 80.0 or knob.size.y < 80.0:
		_fail("Joystick knob is missing or too small.")
		return

	var player: CharacterBody2D = game.get_node_or_null("Player") as CharacterBody2D
	var caretaker: Node = game.get_node_or_null("Caretaker")
	if player == null or caretaker == null:
		_fail("Player or caretaker is missing.")
		return

	# Exploration: the joystick is the only continuous movement control.
	var exploration_start: Vector2 = player.global_position
	controls.call("move_joystick_for_testing", Vector2.RIGHT)
	for _frame: int in range(8):
		await physics_frame
	var exploration_direction: Vector2 = player.call("get_mobile_direction") as Vector2
	if exploration_direction.dot(Vector2.RIGHT) < 0.95:
		_fail("Exploration joystick did not write the movement vector.")
		return
	if player.global_position.distance_to(exploration_start) < 2.0:
		_fail("Exploration joystick did not move the hero.")
		return
	controls.call("release_joystick_for_testing")
	if not (player.call("get_mobile_direction") as Vector2).is_zero_approx():
		_fail("Exploration movement input was not cleared after release.")
		return

	# Combat: the same joystick changes facing only; taps remain responsible for
	# route planning through GamePlannedCombat.
	caretaker.call("enter_combat_hostile")
	game.call("_start_turn_based_combat", caretaker)
	game.call("force_player_turn_for_testing")
	await process_frame
	var combat_start: Vector2 = player.global_position
	controls.call("move_joystick_for_testing", Vector2.UP)
	for _frame: int in range(4):
		await physics_frame
	var facing: Vector2 = player.call("get_facing_direction") as Vector2
	if facing.dot(Vector2.UP) < 0.95:
		_fail("Combat joystick did not rotate the hero.")
		return
	if not (player.call("get_mobile_direction") as Vector2).is_zero_approx():
		_fail("Combat joystick still writes an exploration movement vector.")
		return
	if player.global_position.distance_to(combat_start) > 0.5:
		_fail("Combat joystick moved the hero instead of changing facing only.")
		return
	controls.call("release_joystick_for_testing")
	if not (player.call("get_mobile_facing_direction") as Vector2).is_zero_approx():
		_fail("Combat facing input was not cleared after release.")
		return

	print("Exploration movement joystick and combat facing-only joystick smoke test passed.")
	game.queue_free()
	await process_frame
	quit(0)


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
