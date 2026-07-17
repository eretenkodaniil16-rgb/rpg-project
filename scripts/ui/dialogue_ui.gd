extends Control

signal dialogue_closed

@onready var speaker_label: Label = $BottomPanel/MarginContainer/VBoxContainer/SpeakerLabel
@onready var text_label: Label = $BottomPanel/MarginContainer/VBoxContainer/TextLabel
@onready var choices_container: VBoxContainer = $BottomPanel/MarginContainer/VBoxContainer/Choices


func start_dialogue(dialogue_data: Dictionary) -> void:
	if dialogue_data.is_empty():
		return

	GameState.input_locked = true
	speaker_label.text = str(dialogue_data.get("speaker", "Неизвестный"))
	text_label.text = str(dialogue_data.get("text", "..."))
	_clear_choices()

	var choices_data: Variant = dialogue_data.get("choices", [])
	if choices_data is Array:
		for choice_data: Variant in choices_data:
			if choice_data is Dictionary:
				_add_choice_button(choice_data as Dictionary)

	if choices_container.get_child_count() == 0:
		_add_close_button()
	show()


func _unhandled_input(event: InputEvent) -> void:
	if visible and event.is_action_pressed("ui_cancel"):
		_close_dialogue()
		get_viewport().set_input_as_handled()


func _add_choice_button(choice_data: Dictionary) -> void:
	var button: Button = Button.new()
	button.text = str(choice_data.get("text", "Продолжить"))
	button.custom_minimum_size = Vector2(0.0, 46.0)
	button.pressed.connect(_on_choice_pressed.bind(choice_data))
	choices_container.add_child(button)


func _on_choice_pressed(choice_data: Dictionary) -> void:
	var flag_changes: Variant = choice_data.get("set_flags", {})
	if flag_changes is Dictionary:
		for flag_name: Variant in flag_changes.keys():
			GameState.set_flag(str(flag_name), flag_changes[flag_name])

	text_label.text = str(choice_data.get("response", "Разговор завершён."))
	_clear_choices()
	_add_close_button()
	GameState.save_game()


func _add_close_button() -> void:
	var close_button: Button = Button.new()
	close_button.text = "Завершить разговор"
	close_button.custom_minimum_size = Vector2(0.0, 46.0)
	close_button.pressed.connect(_close_dialogue)
	choices_container.add_child(close_button)


func _clear_choices() -> void:
	for child: Node in choices_container.get_children():
		child.queue_free()


func _close_dialogue() -> void:
	GameState.input_locked = false
	hide()
	dialogue_closed.emit()
