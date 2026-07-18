extends Control

signal dialogue_closed
signal runtime_choice_requested(action_id: String, target: Node)
signal attack_requested(target: Node)

@onready var speaker_label: Label = $BottomPanel/MarginContainer/VBoxContainer/SpeakerLabel
@onready var text_label: Label = $BottomPanel/MarginContainer/VBoxContainer/TextLabel
@onready var choices_container: VBoxContainer = $BottomPanel/MarginContainer/VBoxContainer/Choices

var _dialogue_target: Node = null


func start_dialogue(dialogue_data: Dictionary, dialogue_target: Node = null) -> void:
	if dialogue_data.is_empty():
		return

	_dialogue_target = _resolve_dialogue_target(dialogue_data, dialogue_target)
	GameState.input_locked = true
	speaker_label.text = str(dialogue_data.get("speaker", "Неизвестный"))
	text_label.text = str(dialogue_data.get("text", "..."))
	_clear_choices()

	var regular_choice_count: int = 0
	var choices_data: Variant = dialogue_data.get("choices", [])
	if choices_data is Array:
		for choice_data: Variant in choices_data:
			if choice_data is Dictionary:
				_add_choice_button(choice_data as Dictionary)
				regular_choice_count += 1

	if _has_attack_target():
		_add_attack_button()
	if regular_choice_count == 0:
		_add_close_button()
	show()


func show_runtime_response(speaker: String, text: String) -> void:
	speaker_label.text = speaker
	text_label.text = text
	_clear_choices()
	if _has_attack_target():
		_add_attack_button()
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
	button.set_meta("runtime_action", str(choice_data.get("runtime_action", "")))
	button.pressed.connect(_on_choice_pressed.bind(choice_data))
	choices_container.add_child(button)


func _on_choice_pressed(choice_data: Dictionary) -> void:
	var runtime_action: String = str(choice_data.get("runtime_action", ""))
	if not runtime_action.is_empty():
		_set_choices_disabled(true)
		runtime_choice_requested.emit(runtime_action, _dialogue_target)
		return

	var flag_changes: Variant = choice_data.get("set_flags", {})
	if flag_changes is Dictionary:
		for flag_name: Variant in flag_changes.keys():
			GameState.set_flag(str(flag_name), flag_changes[flag_name])

	text_label.text = str(choice_data.get("response", "Разговор завершён."))
	_clear_choices()
	if _has_attack_target():
		_add_attack_button()
	_add_close_button()
	GameState.save_game()


func _add_attack_button() -> void:
	if choices_container.get_node_or_null("AttackChoiceButton") != null:
		return
	var attack_button: Button = Button.new()
	attack_button.name = "AttackChoiceButton"
	attack_button.text = "АТАКОВАТЬ"
	attack_button.custom_minimum_size = Vector2(0.0, 50.0)
	attack_button.add_theme_color_override("font_color", Color(1.0, 0.62, 0.58, 1.0))
	attack_button.pressed.connect(_on_attack_pressed)
	choices_container.add_child(attack_button)


func _add_close_button() -> void:
	if choices_container.get_node_or_null("CloseDialogueButton") != null:
		return
	var close_button: Button = Button.new()
	close_button.name = "CloseDialogueButton"
	close_button.text = "Завершить разговор"
	close_button.custom_minimum_size = Vector2(0.0, 46.0)
	close_button.pressed.connect(_close_dialogue)
	choices_container.add_child(close_button)


func _on_attack_pressed() -> void:
	var target: Node = _dialogue_target
	_close_dialogue()
	if target != null and is_instance_valid(target):
		call_deferred("_emit_attack_requested", target)


func _emit_attack_requested(target: Node) -> void:
	if target != null and is_instance_valid(target):
		attack_requested.emit(target)


func _resolve_dialogue_target(dialogue_data: Dictionary, supplied_target: Node) -> Node:
	if supplied_target != null and is_instance_valid(supplied_target):
		return supplied_target
	var speaker: String = str(dialogue_data.get("speaker", ""))
	if speaker.is_empty():
		return null
	for candidate: Node in get_tree().get_nodes_in_group("combat_targets"):
		if candidate == null or not is_instance_valid(candidate):
			continue
		var candidate_name: String = str(candidate.call("get_combat_name")) if candidate.has_method("get_combat_name") else str(candidate.name)
		if candidate_name == speaker:
			return candidate
	return null


func _has_attack_target() -> bool:
	return _dialogue_target != null and is_instance_valid(_dialogue_target)


func _set_choices_disabled(value: bool) -> void:
	for child: Node in choices_container.get_children():
		if child is Button:
			(child as Button).disabled = value


func _clear_choices() -> void:
	for child: Node in choices_container.get_children():
		child.queue_free()


func _close_dialogue() -> void:
	_dialogue_target = null
	GameState.input_locked = false
	hide()
	dialogue_closed.emit()


func get_attack_button_for_testing() -> Button:
	return choices_container.get_node_or_null("AttackChoiceButton") as Button


func get_runtime_choice_count_for_testing() -> int:
	var count: int = 0
	for child: Node in choices_container.get_children():
		if child is Button and not str(child.get_meta("runtime_action", "")).is_empty():
			count += 1
	return count
