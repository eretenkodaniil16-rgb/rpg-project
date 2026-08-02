extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const AUTOSAVE_PATH: String = "user://save_slots/autosave.json"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	var save_path: String = ProjectSettings.globalize_path(AUTOSAVE_PATH)
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	state.call("new_game")
	state.set("player_character", _make_hero())

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	var game: Node = packed.instantiate() if packed != null else null
	if game == null:
		_fail("Game scene could not be loaded.")
		return
	root.add_child(game)
	for _frame: int in range(14):
		await process_frame

	var caretaker: Node = game.get_node_or_null("Caretaker")
	var catalog: ActionCatalogUI = game.get_node_or_null("Interface/ActionCatalogUI") as ActionCatalogUI
	var mobile_controls: Control = game.get_node_or_null("Interface/MobileControls") as Control
	if caretaker == null or catalog == null or mobile_controls == null:
		_fail("Caretaker, action catalog or mobile controls are missing.")
		return
	mobile_controls.call("enable_for_testing")
	await process_frame
	var actions_button: Button = mobile_controls.call("get_actions_button_for_testing") as Button
	var move_pad: Control = mobile_controls.get_node_or_null("MovePad") as Control
	if actions_button == null or move_pad == null:
		_fail("Mobile Actions button or joystick pad is missing.")
		return
	if actions_button.action_mode != BaseButton.ACTION_MODE_BUTTON_PRESS:
		_fail("Actions still triggers on release instead of the physical press.")
		return

	game.call("_start_turn_based_combat", caretaker)
	await process_frame
	if not bool(game.call("is_turn_based_combat_active")):
		_fail("Combat did not start.")
		return

	# A finger that begins over the disabled Actions button during an enemy turn
	# remains invalid even if the player turn begins before release.
	game.set("_enemy_turn_running", true)
	mobile_controls.call("_process", 0.0)
	catalog.close_catalog()
	var blocked_press := InputEventScreenTouch.new()
	blocked_press.index = 17
	blocked_press.position = actions_button.get_global_rect().get_center()
	blocked_press.pressed = true
	mobile_controls.call("_input", blocked_press)
	if not bool(mobile_controls.call("action_press_started_blocked_for_testing")):
		_fail("Raw touch origin during the enemy turn was not latched as blocked.")
		return

	game.set("_enemy_turn_running", false)
	game.call("force_player_turn_for_testing")
	mobile_controls.call("_process", 1.0)
	var blocked_release := InputEventScreenTouch.new()
	blocked_release.index = blocked_press.index
	blocked_release.position = blocked_press.position
	blocked_release.pressed = false
	mobile_controls.call("_input", blocked_release)
	if catalog.panel.visible:
		_fail("Carried touch opened the Actions panel on release.")
		return

	# Reproduce the uploaded Android video: the only real touch begins on the
	# joystick, is released there, and a delayed/stale Button.pressed signal is
	# delivered after the next player turn becomes available. Such a signal has
	# no valid Actions-button origin and must be discarded immediately.
	game.set("_enemy_turn_running", true)
	mobile_controls.call("_process", 0.0)
	var joystick_press := InputEventScreenTouch.new()
	joystick_press.index = 31
	joystick_press.position = move_pad.get_global_rect().get_center() + Vector2(-48.0, 0.0)
	joystick_press.pressed = true
	mobile_controls.call("_input", joystick_press)
	var joystick_release := InputEventScreenTouch.new()
	joystick_release.index = joystick_press.index
	joystick_release.position = joystick_press.position
	joystick_release.pressed = false
	mobile_controls.call("_input", joystick_release)
	game.set("_enemy_turn_running", false)
	game.call("force_player_turn_for_testing")
	mobile_controls.call("_process", 1.0)
	actions_button.emit_signal("pressed")
	if catalog.panel.visible:
		_fail("A delayed signal with joystick origin opened the Actions panel.")
		return
	await process_frame
	if catalog.panel.visible:
		_fail("The joystick-origin Actions panel appeared on the rendered frame.")
		return

	# A new intentional press that actually begins inside the enabled Actions
	# button remains the only valid way to open the catalogue.
	var fresh_press := InputEventScreenTouch.new()
	fresh_press.index = 18
	fresh_press.position = actions_button.get_global_rect().get_center()
	fresh_press.pressed = true
	mobile_controls.call("_input", fresh_press)
	actions_button.emit_signal("button_down")
	if bool(mobile_controls.call("action_press_started_blocked_for_testing")):
		_fail("A fresh player-turn press remained blocked after the guard expired.")
		return
	actions_button.emit_signal("pressed")
	if not catalog.panel.visible:
		_fail("A fresh intentional press did not open the Actions panel.")
		return
	if not bool(mobile_controls.call("is_actions_catalog_open_authorized_for_testing")):
		_fail("The catalogue opened without retaining its explicit-input authorization.")
		return

	var fresh_release := InputEventScreenTouch.new()
	fresh_release.index = fresh_press.index
	fresh_release.position = fresh_press.position
	fresh_release.pressed = false
	mobile_controls.call("_input", fresh_release)
	catalog.close_catalog()
	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Only a fresh Actions-button touch can open the catalogue; joystick and carried touches are rejected.")
	quit(0)


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Проверяющий"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.level = 1
	hero.maximum_health = 12
	hero.current_health = 12
	hero.hit_die_size = 10
	hero.hit_dice_maximum = 1
	hero.hit_dice_current = 1
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
