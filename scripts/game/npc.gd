extends Area2D

@export_file("*.json") var dialogue_path: String = "res://data/dialogues/caretaker_intro.json"

var player_in_range: Node = null


func interact() -> void:
	var dialogue_data: Dictionary = _load_dialogue()
	if dialogue_data.is_empty():
		return
	var quest_event: String = str(dialogue_data.get("quest_event", ""))
	if not quest_event.is_empty():
		GameState.report_quest_event(quest_event)
	get_tree().call_group("dialogue_ui", "start_dialogue", dialogue_data)
	get_tree().call_group("game_world", "set_interaction_hint", false)


func _load_dialogue() -> Dictionary:
	if not FileAccess.file_exists(dialogue_path):
		push_error("Файл диалога не найден: %s" % dialogue_path)
		return {}

	var file: FileAccess = FileAccess.open(dialogue_path, FileAccess.READ)
	if file == null:
		push_error("Не удалось открыть файл диалога: %s" % dialogue_path)
		return {}

	var parsed_data: Variant = JSON.parse_string(file.get_as_text())
	if not parsed_data is Dictionary:
		push_error("Некорректный JSON диалога: %s" % dialogue_path)
		return {}
	return parsed_data as Dictionary


func _on_body_entered(body: Node2D) -> void:
	if not body.is_in_group("player"):
		return
	player_in_range = body
	if body.has_method("set_interactable"):
		body.call("set_interactable", self)
	get_tree().call_group("game_world", "set_interaction_hint", true)


func _on_body_exited(body: Node2D) -> void:
	if body != player_in_range:
		return
	if body.has_method("clear_interactable"):
		body.call("clear_interactable", self)
	player_in_range = null
	get_tree().call_group("game_world", "set_interaction_hint", false)
