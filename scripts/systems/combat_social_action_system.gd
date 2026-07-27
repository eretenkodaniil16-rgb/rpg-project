class_name CombatSocialActionSystem
extends RefCounted

const DATA_PATH: String = "res://data/combat/social_actions.json"

var _actions: Dictionary = {}


func _init() -> void:
	_load_actions()


func get_actions(race_id: String = "") -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	var effective_race_id: String = _resolve_race_id(race_id)
	for action_id: Variant in _actions.keys():
		var value: Variant = _actions[action_id]
		if not value is Dictionary:
			continue
		var action: Dictionary = value as Dictionary
		var required_race_id: String = str(action.get("required_race_id", ""))
		if not required_race_id.is_empty() and required_race_id != effective_race_id:
			continue
		result.append(action.duplicate(true))
	result.sort_custom(_sort_actions)
	return result


func resolve_action(action_id: String, speaker_name: String, target: Node, race_id: String = "") -> Dictionary:
	var value: Variant = _actions.get(action_id, {})
	if not value is Dictionary or target == null:
		return {"success": false, "message": "Для общения нужно выбрать действительную цель.", "gesture": ""}
	var action: Dictionary = (value as Dictionary).duplicate(true)
	var required_race_id: String = str(action.get("required_race_id", ""))
	if not required_race_id.is_empty() and required_race_id != _resolve_race_id(race_id):
		return {"success": false, "message": "Эта свободная способность недоступна выбранной расе.", "gesture": ""}
	var target_name: String = str(target.call("get_combat_name")) if target.has_method("get_combat_name") else str(target.name)
	var condition_key: String = "healthy"
	if target.has_method("get_current_health"):
		var current_health: int = int(target.call("get_current_health"))
		var maximum_value: Variant = target.get("maximum_health")
		var maximum_health: int = maxi(int(maximum_value), 1) if maximum_value != null else maxi(current_health, 1)
		if float(current_health) / float(maximum_health) <= 0.5:
			condition_key = "wounded"
	var speaker_text: String = str(action.get("speaker_text", ""))
	var kind: String = str(action.get("kind", "speech"))
	var hero_line: String = "Вы: %s" % speaker_text
	var message: String = speaker_text
	if kind == "speech":
		hero_line = "Вы: «%s»" % speaker_text
		message = "%s: «%s»" % [speaker_name, speaker_text]
	var response: String = _get_response(action, target_name, condition_key)
	var dialogue_text: String = hero_line
	if not response.is_empty():
		message += "\n%s" % response
		dialogue_text += "\n\n%s" % response
	return {
		"success": true,
		"message": message,
		"dialogue_text": dialogue_text,
		"speaker_text": speaker_text,
		"response": response,
		"target_name": target_name,
		"gesture": str(action.get("gesture", "")),
		"kind": kind
	}


func _sort_actions(first: Dictionary, second: Dictionary) -> bool:
	return str(first.get("id", "")) < str(second.get("id", ""))


func _get_response(action: Dictionary, target_name: String, condition_key: String) -> String:
	var responses_value: Variant = action.get("responses", {})
	if not responses_value is Dictionary:
		return ""
	var responses: Dictionary = responses_value as Dictionary
	var target_value: Variant = responses.get(target_name, responses.get("default", {}))
	if not target_value is Dictionary:
		return ""
	var target_responses: Dictionary = target_value as Dictionary
	return str(target_responses.get(condition_key, target_responses.get("healthy", "")))


func _resolve_race_id(explicit_race_id: String) -> String:
	if not explicit_race_id.is_empty():
		return explicit_race_id
	var main_loop: MainLoop = Engine.get_main_loop()
	if not main_loop is SceneTree:
		return ""
	var state: Node = (main_loop as SceneTree).root.get_node_or_null("GameState")
	if state == null:
		return ""
	var character_value: Variant = state.get("player_character")
	return (character_value as PlayerCharacter).race_id if character_value is PlayerCharacter else ""


func _load_actions() -> void:
	if not FileAccess.file_exists(DATA_PATH):
		push_error("Файл боевых социальных действий не найден: %s" % DATA_PATH)
		return
	var file: FileAccess = FileAccess.open(DATA_PATH, FileAccess.READ)
	if file == null:
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		return
	var actions_value: Variant = (parsed as Dictionary).get("actions", [])
	if not actions_value is Array:
		return
	for value: Variant in actions_value:
		if value is Dictionary:
			var action: Dictionary = value as Dictionary
			_actions[str(action.get("id", ""))] = action
