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
		_fail("Actions button is not connected to the raw-origin intent pipeline.")
		return

	game.call("_start_turn_based_combat", caretaker)
	if not bool(game.call("is_turn_based_combat_active")):
		_fail("Combat did not start.")
		return

	# Generic catalogue calls and legacy BaseButton signals must never open the
	# mobile panel. Only a complete raw touch transaction is accepted.
	catalog.toggle_catalog()
	if catalog.panel.visible:
		_fail("Generic toggle opened a catalogue that requires mobile user intent.")
		return
	game.set("_enemy_turn_running", true)
	mobile_controls.call("_process", 0.0)
	actions_button.emit_signal("button_down")
	actions_button.emit_signal("pressed")
	if catalog.panel.visible:
		_fail("Legacy BaseButton signals opened the catalogue during an enemy turn.")
		return

	game.set("_enemy_turn_running", false)
	game.call("force_player_turn_for_testing")
	mobile_controls.call("_process", 0.0)
	actions_button.emit_signal("pressed")
	if catalog.panel.visible:
		_fail("A stale pressed signal opened the catalogue on the player turn.")
		return

	# Reproduce the physical Android failure: a touch starts on Actions, movement
	# changes the gameplay state before the release, and the same touch index is
	# released after movement has completed. The release belongs to an obsolete
	# input epoch and must not open even for one frame.
	var carried_touch_index: int = 8123
	var toggles_before_carried_touch: int = int(mobile_controls.call("get_action_user_toggle_count_for_testing"))
	var epoch_before_movement: int = int(mobile_controls.call("get_action_input_epoch_for_testing"))
	mobile_controls.call("simulate_actions_press_for_testing", carried_touch_index)
	game.set("_movement_execution_running", true)
	mobile_controls.call("_process", 0.0)
	if int(mobile_controls.call("get_action_input_epoch_for_testing")) <= epoch_before_movement:
		_fail("Movement start did not invalidate the pending Actions transaction.")
		return
	game.set("_movement_execution_running", false)
	mobile_controls.call("_process", 0.0)
	mobile_controls.call("simulate_actions_release_for_testing", carried_touch_index)
	if catalog.panel.visible:
		_fail("A touch carried across completed movement opened the Actions catalogue.")
		return
	if int(mobile_controls.call("get_action_user_toggle_count_for_testing")) != toggles_before_carried_touch:
		_fail("A carried movement touch was counted as a new Actions intent.")
		return
	await process_frame
	if catalog.panel.visible:
		_fail("A carried movement touch produced a delayed one-frame catalogue flash.")
		return

	# The same rule applies to a press that begins while global input is locked
	# and is released after the lock disappears.
	var blocked_touch_index: int = 8124
	state.set("input_locked", true)
	mobile_controls.call("_process", 0.0)
	mobile_controls.call("simulate_actions_press_for_testing", blocked_touch_index)
	state.set("input_locked", false)
	mobile_controls.call("_process", 0.0)
	mobile_controls.call("simulate_actions_release_for_testing", blocked_touch_index)
	if catalog.panel.visible:
		_fail("A touch begun during input lock opened after the lock was released.")
		return

	# One real touch intent opens exactly once and remains open across multiple
	# process frames. This directly guards against the observed one-frame flash.
	mobile_controls.call("simulate_actions_touch_for_testing")
	if not catalog.panel.visible:
		_fail("A raw-origin Actions touch did not open the catalogue.")
		return
	var toggle_count_after_touch: int = int(mobile_controls.call("get_action_user_toggle_count_for_testing"))
	for _frame: int in range(8):
		mobile_controls.call("_process", 0.1)
		await process_frame
		if not catalog.panel.visible:
			_fail("The action catalogue flashed and closed without a state transition.")
			return
	if int(mobile_controls.call("get_action_user_toggle_count_for_testing")) != toggle_count_after_touch:
		_fail("Processing frames generated a second action-menu toggle.")
		return

	# Android's synthetic mouse press for the same touch must be consumed rather
	# than interpreted as a second toggle.
	mobile_controls.call("simulate_emulated_mouse_after_touch_for_testing")
	if not catalog.panel.visible:
		_fail("An emulated mouse event closed the catalogue opened by the same touch.")
		return
	if int(mobile_controls.call("get_action_user_toggle_count_for_testing")) != toggle_count_after_touch:
		_fail("The emulated mouse event was counted as another user intent.")
		return

	# A second deliberate touch closes the panel, proving normal toggle behavior
	# still works after duplicate and transition suppression.
	await create_timer(0.5).timeout
	mobile_controls.call("simulate_actions_touch_for_testing")
	if catalog.panel.visible:
		_fail("A second deliberate Actions touch did not close the catalogue.")
		return

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Actions input epochs reject movement-carried releases and preserve deliberate toggles.")
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
