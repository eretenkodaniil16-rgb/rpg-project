extends "res://scripts/core/game_state_rewards.gd"

signal encounter_started(encounter_id: String, state: Dictionary)
signal encounter_resolved(encounter_id: String, resolution_id: String, result: Dictionary)
signal encounter_failed(encounter_id: String, reason_id: String, state: Dictionary)
signal encounter_abandoned(encounter_id: String, reason_id: String, state: Dictionary)
signal encounter_state_changed(encounter_id: String, state: Dictionary)
signal encounters_migrated(encounter_count: int)

var _encounters: EncounterSystem = EncounterSystem.new()


func _ready() -> void:
	super._ready()
	_encounters.ensure_state(self)


func new_game() -> void:
	super.new_game()
	_encounters.ensure_state(self)


func load_game() -> bool:
	var loaded: bool = super.load_game()
	if not loaded:
		return false
	var migration: Dictionary = ensure_encounter_migration()
	if bool(migration.get("changed", false)):
		save_game()
	return true


func begin_encounter(
	encounter_id: String,
	context: Dictionary = {},
	save_after: bool = true,
	emit_events: bool = true
) -> Dictionary:
	var result: Dictionary = _encounters.begin_encounter(self, encounter_id, context)
	if not bool(result.get("success", false)):
		return result
	if save_after:
		save_game()
	var state: Dictionary = result.get("state", {}) as Dictionary
	if emit_events and not bool(result.get("already_active", false)):
		encounter_started.emit(encounter_id, state.duplicate(true))
		encounter_state_changed.emit(encounter_id, state.duplicate(true))
	return result


func resolve_encounter(
	encounter_id: String,
	resolution_id: String,
	context: Dictionary = {},
	save_after: bool = true,
	emit_events: bool = true
) -> Dictionary:
	var transition: Dictionary = _encounters.resolve_encounter(
		self,
		encounter_id,
		resolution_id,
		context
	)
	if not bool(transition.get("success", false)):
		return transition
	var outcome: Dictionary = transition.get("outcome", {}) as Dictionary
	var applied_flags: Array[String] = _apply_encounter_flags(outcome)
	var updated_quests: Array[String] = _apply_encounter_quest_events(outcome)
	var granted_items: Array[Dictionary] = _apply_encounter_items(outcome)
	var reward_id: String = str(transition.get("reward_id", ""))
	var reward_result: Dictionary = {}
	var reward_status: String = "no_reward"
	if not reward_id.is_empty():
		reward_result = grant_experience_reward(
			reward_id,
			{
				"source_type": "encounter",
				"source_id": encounter_id,
				"encounter_id": encounter_id,
				"resolution_id": resolution_id,
				"resolution_type": str(outcome.get("type", "unknown"))
			},
			false,
			emit_events
		)
		if bool(reward_result.get("success", false)):
			reward_status = "granted"
		elif bool(reward_result.get("duplicate", false)):
			reward_status = "already_claimed"
		else:
			reward_status = "failed"
	var completion: Dictionary = _encounters.mark_rewarded(
		self,
		encounter_id,
		reward_status,
		reward_result
	)
	var final_state: Dictionary = completion.get("state", transition.get("state", {})) as Dictionary
	var result: Dictionary = transition.duplicate(true)
	result["state"] = final_state.duplicate(true)
	result["reward_result"] = reward_result.duplicate(true)
	result["reward_status"] = reward_status
	result["applied_flags"] = applied_flags
	result["updated_quests"] = updated_quests
	result["granted_items"] = granted_items
	result["message"] = str(outcome.get("message", "Столкновение разрешено."))
	if save_after:
		save_game()
	if emit_events:
		encounter_resolved.emit(encounter_id, resolution_id, result.duplicate(true))
		encounter_state_changed.emit(encounter_id, final_state.duplicate(true))
	return result


func fail_encounter(
	encounter_id: String,
	reason_id: String = "failed",
	context: Dictionary = {},
	save_after: bool = true,
	emit_events: bool = true
) -> Dictionary:
	var result: Dictionary = _encounters.fail_encounter(self, encounter_id, reason_id, context)
	if bool(result.get("success", false)):
		if save_after:
			save_game()
		var state: Dictionary = result.get("state", {}) as Dictionary
		if emit_events:
			encounter_failed.emit(encounter_id, reason_id, state.duplicate(true))
			encounter_state_changed.emit(encounter_id, state.duplicate(true))
	return result


func abandon_encounter(
	encounter_id: String,
	reason_id: String = "abandoned",
	context: Dictionary = {},
	save_after: bool = true,
	emit_events: bool = true
) -> Dictionary:
	var result: Dictionary = _encounters.abandon_encounter(self, encounter_id, reason_id, context)
	if bool(result.get("success", false)):
		if save_after:
			save_game()
		var state: Dictionary = result.get("state", {}) as Dictionary
		if emit_events:
			encounter_abandoned.emit(encounter_id, reason_id, state.duplicate(true))
			encounter_state_changed.emit(encounter_id, state.duplicate(true))
	return result


func get_encounter_definition(encounter_id: String) -> Dictionary:
	return _encounters.get_definition(encounter_id)


func get_encounter_state(encounter_id: String) -> Dictionary:
	return _encounters.get_encounter_state(self, encounter_id)


func get_encounter_status(encounter_id: String) -> String:
	return _encounters.get_status(self, encounter_id)


func is_encounter_resolved(encounter_id: String) -> bool:
	return _encounters.is_terminal(self, encounter_id)


func get_active_encounter_ids() -> Array[String]:
	return _encounters.get_active_encounter_ids(self)


func get_encounter_combat_resolution_id(encounter_id: String) -> String:
	return _encounters.get_combat_resolution_id(encounter_id)


func ensure_encounter_migration() -> Dictionary:
	var changed: bool = _encounters.ensure_state(self)
	var migrated_count: int = 0
	if not _encounters.is_terminal(self, "training_construct") and has_claimed_experience_reward("encounter_training_dummy_break"):
		var training_result: Dictionary = resolve_encounter(
			"training_construct",
			"destroyed",
			{"source_type": "migration", "legacy_reward_id": "encounter_training_dummy_break"},
			false,
			false
		)
		if bool(training_result.get("success", false)):
			migrated_count += 1
			changed = true
	if not _encounters.is_terminal(self, "caretaker_revelation"):
		var caretaker_resolution: String = _legacy_caretaker_resolution()
		var caretaker_reward_claimed: bool = has_claimed_experience_reward("dialogue_caretaker_revelation")
		if not caretaker_resolution.is_empty() or caretaker_reward_claimed:
			if caretaker_resolution.is_empty():
				caretaker_resolution = "legacy_revelation"
			var caretaker_result: Dictionary = resolve_encounter(
				"caretaker_revelation",
				caretaker_resolution,
				{"source_type": "migration", "legacy_reward_id": "dialogue_caretaker_revelation"},
				false,
				false
			)
			if bool(caretaker_result.get("success", false)):
				migrated_count += 1
				changed = true
	if migrated_count > 0:
		encounters_migrated.emit(migrated_count)
	return {"changed": changed, "encounter_count": migrated_count}


func _apply_encounter_flags(outcome: Dictionary) -> Array[String]:
	var applied: Array[String] = []
	var flags_value: Variant = outcome.get("set_flags", {})
	if not flags_value is Dictionary:
		return applied
	for flag_name_value: Variant in (flags_value as Dictionary).keys():
		var flag_name: String = str(flag_name_value)
		set_flag(flag_name, (flags_value as Dictionary)[flag_name_value])
		applied.append(flag_name)
	return applied


func _apply_encounter_quest_events(outcome: Dictionary) -> Array[String]:
	var updated: Array[String] = []
	var events_value: Variant = outcome.get("quest_events", [])
	if not events_value is Array:
		return updated
	for event_value: Variant in events_value:
		for quest_id: String in report_quest_event(str(event_value)):
			if quest_id not in updated:
				updated.append(quest_id)
	return updated


func _apply_encounter_items(outcome: Dictionary) -> Array[Dictionary]:
	var granted: Array[Dictionary] = []
	var items_value: Variant = outcome.get("items", [])
	if not items_value is Array:
		return granted
	for item_value: Variant in items_value:
		if not item_value is Dictionary:
			continue
		var item: Dictionary = item_value as Dictionary
		var item_id: String = str(item.get("item_id", ""))
		var quantity: int = maxi(int(item.get("quantity", 1)), 1)
		if item_id.is_empty():
			continue
		var before: int = get_item_count(item_id)
		var after: int = add_item(item_id, quantity, false)
		granted.append({"item_id": item_id, "quantity": maxi(after - before, 0)})
	return granted


func _legacy_caretaker_resolution() -> String:
	if bool(get_flag("caretaker_convinced", false)):
		return "persuaded"
	if bool(get_flag("caretaker_secret_noticed", false)):
		return "insight"
	if bool(get_flag("keeper_symbol_known", false)):
		return "history"
	return ""
