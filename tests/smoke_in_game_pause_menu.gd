extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var game_state: Node = root.get_node_or_null("GameState")
	if game_state == null:
		_fail("GameState autoload is missing.")
		return
	game_state.call("begin_new_game", PlayerCharacter.create_legacy_default())
	game_state.set("input_locked", false)

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	if packed == null:
		_fail("Game scene could not be loaded.")
		return
	var game: Node = packed.instantiate()
	root.add_child(game)
	for _frame: int in range(10):
		await process_frame

	var controller: InGamePauseController = game.get_node_or_null(
		"InGamePauseController"
	) as InGamePauseController
	var pause_menu: InGamePauseMenu = game.get_node_or_null(
		"Interface/PauseMenu"
	) as InGamePauseMenu
	var controls: Control = game.get_node_or_null("Interface/MobileControls") as Control
	var player: CharacterBody2D = game.get_node_or_null("Player") as CharacterBody2D
	if controller == null or pause_menu == null or controls == null or player == null:
		_fail("Pause runtime fixtures are incomplete.")
		return
	if paused or pause_menu.is_open():
		_fail("Game must start unpaused with the pause menu hidden.")
		return
	if controller.process_mode != Node.PROCESS_MODE_ALWAYS:
		_fail("Pause controller must continue processing while the tree is paused.")
		return
	if pause_menu.process_mode != Node.PROCESS_MODE_ALWAYS:
		_fail("Pause menu must continue processing while the tree is paused.")
		return

	controls.call("enable_for_testing")
	controls.call("move_joystick_for_testing", Vector2.RIGHT)
	await process_frame
	if (player.call("get_mobile_direction") as Vector2).is_zero_approx():
		_fail("Mobile input fixture did not create an active movement vector.")
		return
	if not controller.open_pause_menu():
		_fail("Controller refused to open the pause menu in normal exploration.")
		return
	await process_frame
	if not paused or not pause_menu.is_open():
		_fail("Opening the pause menu did not pause SceneTree.")
		return
	if not (player.call("get_mobile_direction") as Vector2).is_zero_approx():
		_fail("Opening pause did not release the active mobile movement vector.")
		return

	for path: String in [
		"CenterContainer/PausePanel/Margin/Content/ResumeButton",
		"CenterContainer/PausePanel/Margin/Content/SettingsButton",
		"CenterContainer/PausePanel/Margin/Content/ReturnToMenuButton",
	]:
		var button: Button = pause_menu.get_node_or_null(path) as Button
		if button == null or button.custom_minimum_size.y < 60.0:
			_fail("Pause button is missing or too small for touch: %s" % path)
			return

	pause_menu.open_settings()
	await process_frame
	var settings_panel: MainMenuSettingsPanel = pause_menu.get_settings_panel_for_testing()
	if settings_panel == null or not settings_panel.is_open():
		_fail("Shared settings panel did not open inside pause.")
		return
	if not paused:
		_fail("Opening settings unexpectedly resumed the game.")
		return
	if not pause_menu.handle_cancel():
		_fail("Back handling did not close nested settings.")
		return
	await process_frame
	if settings_panel.is_open() or not pause_menu.is_open() or not paused:
		_fail("Closing nested settings changed the pause state.")
		return
	if not pause_menu.handle_cancel():
		_fail("Back handling did not request resume from the pause screen.")
		return
	await process_frame
	if paused or pause_menu.is_open():
		_fail("Resume did not release the controller-owned SceneTree pause.")
		return

	var menu_button: Button = controls.get_node_or_null("MenuButton") as Button
	if menu_button == null:
		_fail("Mobile menu button is missing.")
		return
	menu_button.pressed.emit()
	await process_frame
	if not paused or not pause_menu.is_open():
		_fail("Mobile menu button did not open the pause menu.")
		return
	controller.close_pause_menu()
	await process_frame
	if paused or pause_menu.is_open():
		_fail("Controller did not close pause after mobile-button activation.")
		return

	_send_cancel_event(true)
	_send_cancel_event(false)
	await process_frame
	if not paused or not pause_menu.is_open():
		_fail("ui_cancel did not open the in-game pause menu.")
		return
	_send_cancel_event(true)
	_send_cancel_event(false)
	await process_frame
	if paused or pause_menu.is_open():
		_fail("ui_cancel did not resume the paused game.")
		return

	game.queue_free()
	await process_frame
	print("In-game pause menu smoke test passed")
	quit(0)


func _send_cancel_event(pressed_value: bool) -> void:
	var event: InputEventAction = InputEventAction.new()
	event.action = &"ui_cancel"
	event.pressed = pressed_value
	Input.parse_input_event(event)


func _fail(message: String) -> void:
	paused = false
	push_error(message)
	quit(1)
