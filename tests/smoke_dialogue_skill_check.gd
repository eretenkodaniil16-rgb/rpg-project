extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var state: Node = root.get_node("GameState")
	state.call("begin_new_game", PlayerCharacter.create_legacy_default())
	var game := (load(GAME_SCENE) as PackedScene).instantiate()
	root.add_child(game)
	await process_frame

	var dialogue: Control = game.get_node("Interface/DialogueUI") as Control
	var test_dialogue: Dictionary = {
		"speaker": "Тест",
		"text": "Проверка интеграции",
		"choices": [{
			"text": "[Сила] Проверить",
			"check": {"ability": "strength", "difficulty": 1},
			"success": {"response": "Успех", "set_flags": {"check_success": true}},
			"failure": {"response": "Неудача"}
		}]
	}
	dialogue.call("start_dialogue", test_dialogue)
	await process_frame
	var choices: VBoxContainer = dialogue.get_node("BottomPanel/MarginContainer/VBoxContainer/Choices") as VBoxContainer
	assert(choices.get_child_count() == 1)
	(choices.get_child(0) as Button).emit_signal("pressed")
	await process_frame
	var popup: Control = dialogue.get_node("SkillCheckPopup") as Control
	assert(popup.visible)
	popup.call("_on_continue_pressed")
	await process_frame
	assert(bool(state.call("get_flag", "check_success", false)))
	print("Checked dialogue smoke test passed.")
	quit(0)
