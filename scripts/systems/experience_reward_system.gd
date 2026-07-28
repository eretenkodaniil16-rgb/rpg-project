class_name ExperienceRewardSystem
extends RefCounted

const DATA_PATH: String = "res://data/rewards/experience_rewards.json"
const CLAIMED_REWARDS_FLAG: String = "_claimed_experience_rewards_v1"

var _definitions: Dictionary = {}


func _init() -> void:
	_load_definitions()


func ensure_state(state: Node) -> bool:
	if state == null:
		return false
	var stored: Variant = state.call("get_flag", CLAIMED_REWARDS_FLAG, {})
	if stored is Dictionary:
		return false
	state.call("set_flag", CLAIMED_REWARDS_FLAG, {})
	return true


func get_definition(reward_id: String) -> Dictionary:
	var value: Variant = _definitions.get(reward_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func get_claimed_rewards(state: Node) -> Dictionary:
	if state == null:
		return {}
	var value: Variant = state.call("get_flag", CLAIMED_REWARDS_FLAG, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func has_claimed(state: Node, reward_id: String) -> bool:
	return not reward_id.is_empty() and get_claimed_rewards(state).has(reward_id)


func claim_reward(
	character: PlayerCharacter,
	state: Node,
	reward_id: String,
	context: Dictionary = {},
	save_after: bool = true
) -> Dictionary:
	if character == null or state == null:
		return _failure(reward_id, "Персонаж или состояние игры недоступны.")
	if reward_id.is_empty():
		return _failure(reward_id, "Не указан идентификатор награды.")
	var definition: Dictionary = get_definition(reward_id)
	if definition.is_empty():
		return _failure(reward_id, "Награда опыта не найдена: %s" % reward_id)
	var claimed: Dictionary = get_claimed_rewards(state)
	if claimed.has(reward_id):
		var duplicate: Dictionary = _failure(reward_id, "Эта награда опыта уже получена.")
		duplicate["duplicate"] = true
		duplicate["claimed_record"] = (claimed.get(reward_id, {}) as Dictionary).duplicate(true) if claimed.get(reward_id, {}) is Dictionary else {}
		return duplicate
	var amount: int = maxi(int(definition.get("experience", 0)), 0)
	if amount <= 0:
		return _failure(reward_id, "Награда не содержит положительного количества опыта.")

	var before_available: bool = ProgressionSystem.can_level_up(character)
	var progression: Dictionary = ProgressionSystem.grant_experience(character, amount)
	var record: Dictionary = {
		"experience": amount,
		"label": str(definition.get("label", reward_id)),
		"source_type": str(definition.get("source_type", context.get("source_type", "unknown"))),
		"source_id": str(definition.get("source_id", context.get("source_id", ""))),
		"context": _sanitize_context(context)
	}
	claimed[reward_id] = record
	state.call("set_flag", CLAIMED_REWARDS_FLAG, claimed)
	if save_after:
		state.call("save_game")

	var result: Dictionary = progression.duplicate(true)
	result["success"] = true
	result["duplicate"] = false
	result["reward_id"] = reward_id
	result["label"] = str(definition.get("label", reward_id))
	result["source_type"] = str(definition.get("source_type", "unknown"))
	result["source_id"] = str(definition.get("source_id", ""))
	result["level_up_became_available"] = not before_available and bool(progression.get("level_up_available", false))
	return result


func _load_definitions() -> void:
	_definitions.clear()
	if not FileAccess.file_exists(DATA_PATH):
		push_error("Каталог наград опыта не найден: %s" % DATA_PATH)
		return
	var file: FileAccess = FileAccess.open(DATA_PATH, FileAccess.READ)
	if file == null:
		push_error("Не удалось открыть каталог наград опыта: %s" % DATA_PATH)
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		push_error("Каталог наград опыта содержит некорректный JSON.")
		return
	var rewards_value: Variant = (parsed as Dictionary).get("rewards", {})
	if not rewards_value is Dictionary:
		return
	for reward_id_value: Variant in (rewards_value as Dictionary).keys():
		var reward_id: String = str(reward_id_value)
		var definition_value: Variant = (rewards_value as Dictionary).get(reward_id_value, {})
		if reward_id.is_empty() or not definition_value is Dictionary:
			continue
		_definitions[reward_id] = (definition_value as Dictionary).duplicate(true)


func _failure(reward_id: String, message: String) -> Dictionary:
	return {
		"success": false,
		"duplicate": false,
		"reward_id": reward_id,
		"experience_gained": 0,
		"message": message
	}


static func _sanitize_context(context: Dictionary) -> Dictionary:
	var result: Dictionary = {}
	for key: String in ["source_type", "source_id", "quest_id", "dialogue_id", "encounter_id"]:
		if context.has(key):
			result[key] = str(context.get(key, ""))
	return result
