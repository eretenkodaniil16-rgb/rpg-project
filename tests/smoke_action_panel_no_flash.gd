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
		_fail("Normal BaseButton Actions signal path is not connected.")
		return

	game.call("_start_turn_based_combat", caretaker)
	if not bool(game.call("is_turn_based_combat_active")):
		_fail("Combat did not start.")
		return
	game.call("force_player_turn_for_testing")
	mobile_controls.call("_process", 0.4)

	# A generic catalogue call is still forbidden on mobile.
	catalog.toggle_catalog()
	if catalog.panel.visible:
		_fail("Generic toggle opened a catalogue that requires the Actions button.")
		return

	# A normal quick BaseButton tap must open immediately. No long press, raw
	# touch transaction or release inside the button is required.
	mobile_controls.call("simulate_actions_touch_for_testing")
	if not catalog.panel.visible:
		_fail("A normal quick Actions tap did not open the catalogue.")
		return
	var toggle_count: int = int(mobile_controls.call("get_action_user_toggle_count_for_testing"))
	if toggle_count != 1:
		_fail("One Actions tap did not produce exactly one toggle.")
		return
	mobile_controls.call("simulate_actions_touch_for_testing")
	if catalog.panel.visible:
		_fail("A second normal Actions tap did not close the catalogue.")
		return

	# Reproduce the responsiveness regression: a press begins, but the finger
	# leaves the button and no release is delivered to it. The next ordinary tap
	# must still work; there is no retained touch index to block index 0 forever.
	mobile_controls.call("simulate_actions_press_for_testing", 0)
	mobile_controls.call("simulate_actions_touch_for_testing")
	if not catalog.panel.visible:
		_fail("An incomplete previous touch blocked the next ordinary Actions tap.")
		return
	mobile_controls.call("simulate_actions_touch_for_testing")
	if catalog.panel.visible:
		_fail("Actions did not remain responsive after an incomplete touch.")
		return

	# The flash is guarded independently from button input. A foreign show(),
	# stale Tween completion or restored UI visibility must be rejected before a
	# frame can render the panel.
	var corrections_before: int = int(mobile_controls.call("get_catalog_visibility_correction_count_for_testing"))
	catalog.panel.show()
	if catalog.panel.visible:
		_fail("A foreign panel show bypassed the catalogue visibility owner.")
		return
	if int(mobile_controls.call("get_catalog_visibility_correction_count_for_testing")) <= corrections_before:
		_fail("Unexpected catalogue visibility was not recorded and corrected.")
		return

	# Movement closes an intentionally open panel. Completion of movement and a
	# simulated stale animation show cannot reopen it.
	mobile_controls.call("simulate_actions_touch_for_testing")
	if not catalog.panel.visible:
		_fail("Actions could not be deliberately opened before movement.")
		return
	game.set("_movement_execution_running", true)
	mobile_controls.call("_process", 0.0)
	if catalog.panel.visible:
		_fail("Movement start did not close the Actions catalogue.")
		return
	game.set("_movement_execution_running", false)
	mobile_controls.call("_process", 0.0)
	catalog.panel.show()
	if catalog.panel.visible:
		_fail("A stale visibility or animation event reopened Actions after movement.")
		return
	for _frame: int in range(4):
		await process_frame
		if catalog.panel.visible:
			_fail("The Actions catalogue produced a delayed one-frame flash.")
			return

	# Input lock transitions also cannot create a panel, while a later deliberate
	# quick tap remains responsive.
	state.set("input_locked", true)
	mobile_controls.call("_process", 0.0)
	state.set("input_locked", false)
	mobile_controls.call("_process", 0.0)
	catalog.panel.show()
	if catalog.panel.visible:
		_fail("Input unlock allowed unexpected catalogue visibility.")
		return
	mobile_controls.call("simulate_actions_touch_for_testing")
	if not catalog.panel.visible:
		_fail("Actions did not respond to a normal tap after transitions.")
		return

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Actions keeps normal tap responsiveness while foreign panel visibility is rejected.")
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
