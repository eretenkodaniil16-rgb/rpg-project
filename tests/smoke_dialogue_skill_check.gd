extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var state: Node = root.get_node("GameState")
	state.call("begin_new_game", PlayerCharacter.create_legacy_default())
	var game := (load(GAME_SCENE) as PackedScene).instantiate()
	root.add_child(game)
	for _frame: int in range(6):
		await process_frame

	var dialogue: Control = game.get_node("Interface/DialogueUI") as Control
	var caretaker: Node = game.get_node("Caretaker")
	var visual_controller: DialogueVisualController = dialogue.call("get_visual_controller_for_testing") as DialogueVisualController
	assert(visual_controller != null)
	var test_dialogue: Dictionary = {
		"speaker": "Смотритель",
		"text": "Проверка интеграции",
		"choices": [{
			"text": "[Сила] Проверить",
			"check": {"ability": "strength", "difficulty": 1},
			"success": {"response": "Успех", "set_flags": {"check_success": true}},
			"failure": {"response": "Неудача"}
		}]
	}
	dialogue.call("start_dialogue", test_dialogue, caretaker)
	await process_frame
	await process_frame
	var portrait: DialoguePortrait = visual_controller.get_portrait_for_testing()
	var bottom_panel: PanelContainer = visual_controller.get_bottom_panel_for_testing()
	assert(portrait != null and portrait.has_character())
	assert(bottom_panel != null and is_equal_approx(bottom_panel.offset_bottom, -10.0))
	assert(bottom_panel.offset_top <= -350.0)

	var choices: VBoxContainer = dialogue.find_child("Choices", true, false) as VBoxContainer
	assert(choices != null)
	var check_button: Button = null
	for child: Node in choices.get_children():
		if child is Button and "Проверить" in (child as Button).text:
			check_button = child as Button
			break
	assert(check_button != null)
	check_button.emit_signal("pressed")
	await process_frame
	var popup: Control = dialogue.get_node("SkillCheckPopup") as Control
	assert(popup.visible)
	popup.call("_on_continue_pressed")
	await process_frame
	assert(bool(state.call("get_flag", "check_success", false)))

	var context_button: Button = visual_controller.get_context_button_for_testing()
	assert(context_button != null)
	assert(context_button.text == "ВЗАИМ.")
	dialogue.call("_close_dialogue")
	await process_frame
	assert(context_button.visible)

	game.call("_set_selected_target", caretaker)
	game.call("_start_turn_based_combat", caretaker)
	game.call("force_player_turn_for_testing")
	await process_frame
	await process_frame
	assert(not context_button.visible)
	print("Checked dialogue, portrait and combat HUD smoke test passed.")
	quit(0)
