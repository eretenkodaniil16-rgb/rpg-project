extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const CHECK_ID: String = "reward_smoke_strength"
const FAILED_CHECK_ID: String = "failed_smoke_insight"


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
	var mobile_controls: Control = game.get_node("Interface/MobileControls") as Control
	mobile_controls.call("enable_for_testing")
	var visual_controller: DialogueVisualController = dialogue.call("get_visual_controller_for_testing") as DialogueVisualController
	assert(visual_controller != null)
	var test_dialogue: Dictionary = {
		"id": "reward_dialogue_smoke",
		"speaker": "Смотритель",
		"text": "Проверка интеграции",
		"choices": [{
			"text": "[Сила] Проверить",
			"check_id": CHECK_ID,
			"check": {"ability": "strength", "difficulty": 1},
			"success": {
				"response": "Успех",
				"set_flags": {"check_success": true},
				"reward_id": "dialogue_caretaker_revelation"
			},
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
	var check_button: Button = _find_check_button(choices, "Проверить")
	assert(check_button != null)
	check_button.emit_signal("pressed")
	await process_frame
	assert(bool(dialogue.call("has_check_attempt_for_testing", "reward_dialogue_smoke", CHECK_ID)))
	var popup: Control = dialogue.get_node("SkillCheckPopup") as Control
	assert(popup.visible)
	popup.call("_on_continue_pressed")
	await process_frame
	assert(bool(state.call("get_flag", "check_success", false)))
	assert(int((state.get("player_character") as PlayerCharacter).experience) == 25)
	assert(bool(state.call("has_claimed_experience_reward", "dialogue_caretaker_revelation")))

	var actions_button: Button = visual_controller.get_context_button_for_testing()
	assert(actions_button != null)
	assert(actions_button.text == "ДЕЙСТВИЯ")
	dialogue.call("_close_dialogue")
	await process_frame
	assert(actions_button.visible)
	assert(actions_button.text == "ДЕЙСТВИЯ")

	dialogue.call("start_dialogue", test_dialogue, caretaker)
	await process_frame
	assert(int(dialogue.call("get_available_checked_choice_count_for_testing")) == 0)
	dialogue.call("_close_dialogue")
	await process_frame

	# A guaranteed failed check is also consumed permanently. This is the
	# anti-reroll contract required for caretaker conversations.
	var failed_dialogue: Dictionary = {
		"id": "failed_dialogue_smoke",
		"speaker": "Смотритель",
		"text": "Проверка неудачи",
		"choices": [{
			"text": "[Проницательность] Неудачная проверка",
			"check_id": FAILED_CHECK_ID,
			"check": {"skill": "insight", "difficulty": 99},
			"success": {"response": "Недостижимый успех"},
			"failure": {
				"response": "Проверка провалена",
				"set_flags": {"failed_check_resolved": true}
			}
		}]
	}
	dialogue.call("start_dialogue", failed_dialogue, caretaker)
	await process_frame
	check_button = _find_check_button(choices, "Неудачная проверка")
	assert(check_button != null)
	check_button.emit_signal("pressed")
	await process_frame
	assert(bool(dialogue.call("has_check_attempt_for_testing", "failed_dialogue_smoke", FAILED_CHECK_ID)))
	popup.call("_on_continue_pressed")
	await process_frame
	assert(bool(state.call("get_flag", "failed_check_resolved", false)))
	dialogue.call("_close_dialogue")
	await process_frame
	dialogue.call("start_dialogue", failed_dialogue, caretaker)
	await process_frame
	assert(int(dialogue.call("get_available_checked_choice_count_for_testing")) == 0)
	dialogue.call("_close_dialogue")
	await process_frame

	game.call("_set_selected_target", caretaker)
	game.call("_start_turn_based_combat", caretaker)
	game.call("force_player_turn_for_testing")
	await process_frame
	await process_frame
	assert(actions_button.visible)
	assert(actions_button.text == "ДЕЙСТВИЯ")
	print("Successful and failed one-shot dialogue checks, reward, portrait and persistent Actions button smoke test passed.")
	quit(0)


func _find_check_button(choices: VBoxContainer, text_fragment: String) -> Button:
	for child: Node in choices.get_children():
		if child is Button and text_fragment in (child as Button).text:
			return child as Button
	return null
