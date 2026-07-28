extends "res://scripts/core/game_state.gd"

signal experience_gained(reward_id: String, amount: int, total_experience: int, label: String)
signal level_up_available(current_level: int, target_level: int, pending_level_count: int)
signal experience_rewards_migrated(reward_count: int, experience_gained: int)

var _experience_rewards: ExperienceRewardSystem = ExperienceRewardSystem.new()


func _ready() -> void:
	super._ready()
	_experience_rewards.ensure_state(self)


func load_game() -> bool:
	var loaded: bool = super.load_game()
	if not loaded:
		return false
	var migration: Dictionary = ensure_experience_reward_migration()
	if int(migration.get("reward_count", 0)) > 0:
		save_game()
	return true


func grant_experience_reward(
	reward_id: String,
	context: Dictionary = {},
	save_after: bool = true,
	emit_events: bool = true
) -> Dictionary:
	var result: Dictionary = _experience_rewards.claim_reward(
		player_character,
		self,
		reward_id,
		context,
		save_after
	)
	if not bool(result.get("success", false)):
		return result
	if emit_events:
		experience_gained.emit(
			reward_id,
			int(result.get("experience_gained", 0)),
			player_character.experience,
			str(result.get("label", reward_id))
		)
		if bool(result.get("level_up_became_available", false)):
			level_up_available.emit(
				player_character.level,
				player_character.level + 1,
				int(result.get("pending_level_count", 1))
			)
	return result


func has_claimed_experience_reward(reward_id: String) -> bool:
	return _experience_rewards.has_claimed(self, reward_id)


func get_claimed_experience_rewards() -> Dictionary:
	return _experience_rewards.get_claimed_rewards(self)


func get_experience_reward_definition(reward_id: String) -> Dictionary:
	return _experience_rewards.get_definition(reward_id)


func ensure_experience_reward_migration() -> Dictionary:
	var changed: bool = _experience_rewards.ensure_state(self)
	var reward_count: int = 0
	var experience_gained_total: int = 0
	for quest_id_value: Variant in quest_states.keys():
		var quest_id: String = str(quest_id_value)
		var state_value: Variant = quest_states.get(quest_id, {})
		if not state_value is Dictionary or str((state_value as Dictionary).get("status", "")) != "completed":
			continue
		var definition: Dictionary = get_quest_definition(quest_id)
		for reward_id: String in _experience_reward_ids(definition):
			if _experience_rewards.has_claimed(self, reward_id):
				continue
			var result: Dictionary = grant_experience_reward(
				reward_id,
				{"source_type": "quest_migration", "quest_id": quest_id},
				false,
				false
			)
			if bool(result.get("success", false)):
				reward_count += 1
				experience_gained_total += int(result.get("experience_gained", 0))
				changed = true
	if reward_count > 0:
		experience_rewards_migrated.emit(reward_count, experience_gained_total)
	return {
		"changed": changed,
		"reward_count": reward_count,
		"experience_gained": experience_gained_total
	}


func _grant_quest_rewards(definition: Dictionary) -> void:
	super._grant_quest_rewards(definition)
	var quest_id: String = str(definition.get("id", ""))
	for reward_id: String in _experience_reward_ids(definition):
		grant_experience_reward(
			reward_id,
			{"source_type": "quest", "quest_id": quest_id},
			false,
			true
		)


static func _experience_reward_ids(definition: Dictionary) -> Array[String]:
	var result: Array[String] = []
	var rewards_value: Variant = definition.get("rewards", [])
	if not rewards_value is Array:
		return result
	for reward_value: Variant in rewards_value:
		if not reward_value is Dictionary:
			continue
		var reward_id: String = str((reward_value as Dictionary).get("reward_id", ""))
		if not reward_id.is_empty() and reward_id not in result:
			result.append(reward_id)
	return result
