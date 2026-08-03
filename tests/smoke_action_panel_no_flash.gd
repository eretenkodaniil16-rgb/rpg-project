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
	catalog.require_explicit_open_for_testing(true)
	await process_frame
	var actions_button: Button = mobile_controls.call("get_actions_button_for_testing") as Button
	if actions_button == null:
		_fail("Mobile Actions button is missing.")
		return
	if not bool(mobile_controls.call("is_action_gui_pipeline_connected_for_testing")):
		_fail("Actions button is not connected to its control-owned GUI stream.")
		return

	game.call("_start_turn_based_combat", caretaker)
	if not bool(game.call("is_turn_based_combat_active")):
		_fail("Combat did not start.")
		return
	game.call("force_player_turn_for_testing")
	mobile_controls.call("_process", 0.0)

	# Generic calls and legacy BaseButton signals cannot open the mobile menu.
	catalog.toggle_catalog()
	if catalog.panel.visible:
		_fail("Generic toggle opened a catalogue that requires mobile user intent.")
		return
	actions_button.emit_signal("button_down")
	actions_button.emit_signal("pressed")
	if catalog.panel.visible:
		_fail("Legacy BaseButton signals opened the catalogue.")
		return

	# Reproduce the physical failure at its actual ownership boundary. Movement
	# happens on the battlefield, then an unrelated release ends over the Actions
	# rect. Since no press was routed to the Actions Control, it must do nothing.
	var toggles_before_movement: int = int(mobile_controls.call("get_action_user_toggle_count_for_testing"))
	game.set("_movement_execution_running", true)
	mobile_controls.call("_process", 0.0)
	game.set("_movement_execution_running", false)
	mobile_controls.call("_process", 0.0)
	mobile_controls.call("simulate_unowned_action_release_for_testing", 8123)
	if catalog.panel.visible:
		_fail("A battlefield release after movement opened the Actions catalogue.")
		return
	if int(mobile_controls.call("get_action_user_toggle_count_for_testing")) != toggles_before_movement:
		_fail("An unowned movement release was counted as an Actions intent.")
		return
	for _frame: int in range(4):
		await process_frame
		if catalog.panel.visible:
			_fail("An unowned movement release produced a delayed catalogue flash.")
			return

	# A release after input lock is equally invalid without a control-owned press.
	state.set("input_locked", true)
	mobile_controls.call("_process", 0.0)
	state.set("input_locked", false)
	mobile_controls.call("_process", 0.0)
	mobile_controls.call("simulate_unowned_action_release_for_testing", 8124)
	if catalog.panel.visible:
		_fail("An unowned release opened the catalogue after input unlock.")
		return

	# A real press routed to the Actions Control opens immediately and stays open.
	mobile_controls.call("simulate_actions_touch_for_testing")
	if not catalog.panel.visible:
		_fail("A control-owned Actions press did not open the catalogue.")
		return
	var toggle_count_after_touch: int = int(mobile_controls.call("get_action_user_toggle_count_for_testing"))
	for _frame: int in range(8):
		mobile_controls.call("_process", 0.1)
		await process_frame
		if not catalog.panel.visible:
			_fail("The action catalogue closed without a state transition.")
			return
	if int(mobile_controls.call("get_action_user_toggle_count_for_testing")) != toggle_count_after_touch:
		_fail("Processing frames generated a second action-menu toggle.")
		return

	mobile_controls.call("simulate_emulated_mouse_after_touch_for_testing")
	if not catalog.panel.visible:
		_fail("An emulated mouse press closed the catalogue opened by touch.")
		return
	if int(mobile_controls.call("get_action_user_toggle_count_for_testing")) != toggle_count_after_touch:
		_fail("The emulated mouse press was counted as another user intent.")
		return

	# Starting movement closes the catalogue; ending movement cannot reopen it.
	game.set("_movement_execution_running", true)
	mobile_controls.call("_process", 0.0)
	if catalog.panel.visible:
		_fail("Movement start did not close the Actions catalogue.")
		return
	game.set("_movement_execution_running", false)
	mobile_controls.call("_process", 0.0)
	mobile_controls.call("simulate_unowned_action_release_for_testing", 8125)
	await process_frame
	if catalog.panel.visible:
		_fail("Movement completion reopened the Actions catalogue.")
		return

	# A later deliberate control-owned press still opens normally.
	mobile_controls.call("simulate_actions_touch_for_testing")
	if not catalog.panel.visible:
		_fail("Actions could not be opened deliberately after movement.")
		return
	mobile_controls.call("simulate_actions_touch_for_testing")
	if catalog.panel.visible:
		_fail("A second deliberate Actions press did not close the catalogue.")
		return

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Actions opens only from its Control-owned press; movement releases cannot flash it.")
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
