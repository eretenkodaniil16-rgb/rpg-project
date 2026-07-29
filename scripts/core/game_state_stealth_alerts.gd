extends "res://scripts/core/game_state_encounters.gd"

signal stealth_alert_changed(actor_id: String, record: Dictionary)
signal stealth_noise_reported(noise_event: Dictionary)
signal stealth_door_state_changed(door_id: String, door_state: String)
signal stealth_alerts_migrated(actor_count: int)

var _stealth_alerts: StealthAlertSystem = StealthAlertSystem.new()


func _ready() -> void:
	super._ready()
	_stealth_alerts.ensure_state(self)


func new_game() -> void:
	super.new_game()
	_stealth_alerts.ensure_state(self)


func load_game() -> bool:
	var loaded: bool = super.load_game()
	if not loaded:
		return false
	var migration: Dictionary = ensure_stealth_alert_migration()
	if bool(migration.get("changed", false)):
		save_game()
	return true


func get_stealth_profile(actor_id: String) -> Dictionary:
	return _stealth_alerts.get_profile(actor_id)


func get_stealth_alert_record(actor_id: String) -> Dictionary:
	return _stealth_alerts.get_actor_record(self, actor_id)


func get_all_stealth_alert_records() -> Dictionary:
	return _stealth_alerts.get_all_actor_records(self)


func set_stealth_alert_record(
	actor_id: String,
	record: Dictionary,
	save_after: bool = false,
	emit_event: bool = true
) -> Dictionary:
	if actor_id.is_empty() or not _stealth_alerts.has_profile(actor_id):
		return {}
	var stored: Dictionary = _stealth_alerts.store_actor_record(self, actor_id, record)
	if save_after:
		save_game()
	if emit_event:
		stealth_alert_changed.emit(actor_id, stored.duplicate(true))
	return stored


func clear_stealth_alert_record(actor_id: String, save_after: bool = false) -> void:
	_stealth_alerts.clear_actor_record(self, actor_id)
	if save_after:
		save_game()
	stealth_alert_changed.emit(actor_id, get_stealth_alert_record(actor_id))


func report_stealth_noise(
	noise_type: String,
	world_position: Vector2,
	overrides: Dictionary = {},
	save_after: bool = false,
	emit_event: bool = true
) -> Dictionary:
	var profile: Dictionary = _stealth_alerts.get_noise_profile(noise_type)
	if profile.is_empty():
		profile = {"radius_feet": 15, "intensity": 15}
	var event: Dictionary = {
		"noise_type": noise_type,
		"position": _stealth_alerts.vector_to_value(world_position),
		"room_id": _stealth_alerts.get_room_id_at(world_position),
		"radius_feet": int(profile.get("radius_feet", 15)),
		"intensity": int(profile.get("intensity", 15))
	}
	for key: Variant in overrides.keys():
		event[key] = overrides[key]
	var stored: Dictionary = _stealth_alerts.append_noise_event(self, event)
	if save_after:
		save_game()
	if emit_event:
		stealth_noise_reported.emit(stored.duplicate(true))
	return stored


func get_stealth_noise_events(after_sequence: int = 0) -> Array[Dictionary]:
	return _stealth_alerts.get_noise_events(self, after_sequence)


func get_stealth_door_state(door_id: String) -> String:
	return _stealth_alerts.get_door_state(self, door_id)


func set_stealth_door_state(door_id: String, door_state: String, save_after: bool = true) -> bool:
	if not _stealth_alerts.set_door_state(self, door_id, door_state):
		return false
	if save_after:
		save_game()
	stealth_door_state_changed.emit(door_id, door_state)
	return true


func get_stealth_room_id(world_position: Vector2) -> String:
	return _stealth_alerts.get_room_id_at(world_position)


func get_stealth_hiding_spot(world_position: Vector2) -> Dictionary:
	return _stealth_alerts.get_hiding_spot_at(world_position)


func ensure_stealth_alert_migration() -> Dictionary:
	var changed: bool = _stealth_alerts.ensure_state(self)
	var migrated_count: int = 0
	var legacy_alerted: bool = bool(get_flag("training_construct_alerted", false))
	var encounter_state: Dictionary = get_encounter_state("training_construct")
	var abandoned_after_escape: bool = (
		str(encounter_state.get("status", "")) == EncounterSystem.STATUS_ABANDONED
		and bool((encounter_state.get("close_context", {}) as Dictionary).get("enemies_alerted", false))
	)
	if legacy_alerted or abandoned_after_escape:
		var record: Dictionary = _stealth_alerts.get_actor_record(self, "caretaker")
		if str(record.get("state", StealthAlertSystem.STATE_CALM)) == StealthAlertSystem.STATE_CALM:
			record["state"] = StealthAlertSystem.STATE_SUSPICIOUS
			record["suspicion"] = 45.0
			record["last_known_position"] = _stealth_alerts.vector_to_value(player_position)
			record["search_seconds_remaining"] = 0.0
			record["alert_cooldown_seconds"] = 18.0
			_stealth_alerts.store_actor_record(self, "caretaker", record)
			migrated_count += 1
			changed = true
	if migrated_count > 0:
		stealth_alerts_migrated.emit(migrated_count)
	return {"changed": changed, "actor_count": migrated_count}
