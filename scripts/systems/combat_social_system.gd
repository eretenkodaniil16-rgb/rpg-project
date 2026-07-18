class_name CombatSocialSystem
extends RefCounted

const DATA_PATH: String = "res://data/combat/social_actions.json"

var _actions: Dictionary = {}


func _init() -> void:
	_load_actions()


func get_actions() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for value: Variant in _actions.values():
		if value is Dictionary:
			result.append((value as Dictionary).duplicate(true))
	result.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return str(a.get("id", "")) < str(b.get("id", "")))
	return result


func get_action(action_id: String) -> Dictionary:
	var value: Variant = _actions.get(action_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func resolve_action(action_id: String, speaker_name: String, target: Node) -> Dictionary:
	var action: Dictionary = get_action(action_id)
	if action.is_empty() or target == null:
		return {"success": false, "message": "Для свободного общения нужно выбрать действительную цель.", "gesture": ""}
	var target_name: String = str(target.call("get_combat_name")) if target.has_method("get_combat_name") else str(target.name)
	var health_ratio: float = 1.0
	if target.has_method("get_current_health"):
		var current: int = int(target.call("get_current_health"))
		var maximum: int = int(target.get("maximum_health")) if "maximum_health" in target else maxi(current, 1)
		health_ratio = float(current) / float(maxi(maximum, 1))
	var condition_key: String = "wounded" if health_ratio <= 0.5 else "healthy"
	var response: String = _response_for(action, target_name, condition_key)
	var speaker_text: String = str(action.get("speaker_text", ""))
	var prefix: String = "%s: «%s»" % [speaker_name, speaker_text] if str(action.get("kind", "")) == "speech" else speaker_text
	var combined: String = prefix
	if not response.is_empty():
		combined += "\n%s" % response
	return {
		"success": true,
		"message": combined,
		"gesture": str(action.get("gesture", "")),
		"kind": str(action.get("kind", "speech")),
		"target_name": target_name
	}


func _response_for(action: Dictionary, target_name: String, condition_key: String) -> String:
	var responses_value: Variant = action.get("responses", {})
	if not responses_value is Dictionary:
		return ""
	var responses: Dictionary = responses_value as Dictionary
	var target_responses_value: Variant = responses.get(target_name, responses.get("default", {}))
	if not target_responses_value is Dictionary:
		return ""
	var target_responses: Dictionary = target_responses_value as Dictionary
	return str(target_responses.get(condition_key, target_responses.get("healthy", "")))


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
	var values: Variant = (parsed as Dictionary).get("actions", [])
	if not values is Array:
		return
	for value: Variant in values:
		if value is Dictionary:
			var action: Dictionary = value as Dictionary
			_actions[str(action.get("id", ""))] = action
