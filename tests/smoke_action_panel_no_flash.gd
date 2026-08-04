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
	for _frame: int in range(18):
		await process_frame

	var player: Node = game.get_node_or_null("Player")
	var caretaker: Node = game.get_node_or_null("Caretaker")
	var catalog: ActionCatalogUI = game.get_node_or_null("Interface/ActionCatalogUI") as ActionCatalogUI
	var mobile_controls: Control = game.get_node_or_null("Interface/MobileControls") as Control
	if player == null or caretaker == null or catalog == null or mobile_controls == null:
		_fail("Player, caretaker, action catalog or mobile controls are missing.")
		return
	mobile_controls.call("enable_for_testing")
	catalog.require_explicit_open_for_testing(true)
	await process_frame
	var actions_button: Button = mobile_controls.call("get_actions_button_for_testing") as Button
	if actions_button == null:
		_fail("Mobile Actions button is missing.")
		return
	if not bool(mobile_controls.call("is_action_gui_pipeline_connected_for_testing")):
		_fail("Normal BaseButton release/pressed path is not connected.")
		return
	if actions_button.action_mode != BaseButton.ACTION_MODE_BUTTON_RELEASE:
		_fail("Actions does not use the original short-tap release mode.")
		return

	# Remove every registered trigger for this exact frame. The button must still
	# open the catalogue; nearby objects affect its contents, not availability.
	var nearby_value: Variant = player.call("get_nearby_interactables")
	if nearby_value is Array:
		for target: Variant in nearby_value as Array:
			if target is Node:
				player.call("unregister_interactable", target as Node)
	game.call("_refresh_action_catalog")
	mobile_controls.call("simulate_actions_touch_for_testing")
	if not catalog.panel.visible:
		_fail("Actions did not open outside every interaction trigger.")
		return
	mobile_controls.call("simulate_actions_touch_for_testing")
	if catalog.panel.visible:
		_fail("Second short Actions tap did not close the catalogue.")
		return

	# In release mode touch start alone does nothing; its normal release activates
	# immediately. No hold duration or button_down authorization exists.
	mobile_controls.call("simulate_actions_press_for_testing", 0)
	if catalog.panel.visible:
		_fail("Touch start opened Actions before the normal release.")
		return
	mobile_controls.call("simulate_actions_release_for_testing", 0)
	if not catalog.panel.visible:
		_fail("Normal short release did not open Actions.")
		return
	mobile_controls.call("simulate_actions_touch_for_testing")
	if catalog.panel.visible:
		_fail("Actions did not remain responsive after a press/release pair.")
		return

	# A generic catalogue call remains forbidden on mobile. This is the narrow
	# anti-flash boundary and it does not participate in button input.
	catalog.toggle_catalog()
	if catalog.panel.visible:
		_fail("Generic toggle bypassed the explicit mobile Actions entry point.")
		return

	state.set("input_locked", true)
	mobile_controls.call("_process", 0.0)
	mobile_controls.call("simulate_actions_touch_for_testing")
	if catalog.panel.visible:
		_fail("Actions opened while global input was explicitly locked.")
		return
	state.set("input_locked", false)
	mobile_controls.call("_process", 0.0)
	mobile_controls.call("simulate_actions_touch_for_testing")
	if not catalog.panel.visible:
		_fail("Actions did not respond immediately after input unlock.")
		return
	mobile_controls.call("simulate_actions_touch_for_testing")

	game.call("_start_turn_based_combat", caretaker)
	if not bool(game.call("is_turn_based_combat_active")):
		_fail("Combat did not start.")
		return
	game.call("force_player_turn_for_testing")
	mobile_controls.call("_process", 0.0)
	mobile_controls.call("simulate_actions_touch_for_testing")
	if not catalog.panel.visible:
		_fail("Actions did not open immediately on the player's combat turn.")
		return

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Actions opens with a normal short tap both outside triggers and on the player turn.")
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
