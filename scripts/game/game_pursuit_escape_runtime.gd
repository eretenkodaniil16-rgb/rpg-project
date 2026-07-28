extends "res://scripts/game/game_exploration_stealth_runtime.gd"


func _update_exploration_alerts(delta: float) -> void:
	if _any_overlay_visible():
		return
	super._update_exploration_alerts(delta)


func _update_exploration_step_noise(delta: float) -> void:
	if _any_overlay_visible():
		_last_exploration_player_position = player.global_position
		_step_noise_elapsed = 0.0
		return
	super._update_exploration_step_noise(delta)


func _update_exploration_actor(actor: Node, delta: float) -> void:
	if actor == null or not is_instance_valid(actor) or not (actor is Node2D):
		return
	var actor_id: String = str(actor.call("get_actor_id"))
	var profile: Dictionary = _stealth_alerts.get_profile(actor_id)
	if profile.is_empty():
		return
	var record: Dictionary = _record_for_actor(actor_id)
	var previous_state: String = str(record.get("state", StealthAlertSystem.STATE_CALM))
	var visible: bool = _exploration_actor_can_see_player(actor, profile)
	var hiding_spot: Dictionary = _stealth_alerts.get_hiding_spot_at(player.global_position)
	var target_hidden: bool = _exploration_hidden and not hiding_spot.is_empty()
	record = _stealth_alerts.apply_visual_observation(record, visible, target_hidden, player.global_position, delta, profile)
	if visible:
		if _exploration_hidden and hiding_spot.is_empty():
			_break_exploration_hidden("NPC заметил героя вне укромного места.")
		if actor.has_method("set_facing_direction"):
			actor.call("set_facing_direction", player.global_position - (actor as Node2D).global_position)
	else:
		if previous_state in [
			StealthAlertSystem.STATE_INVESTIGATING,
			StealthAlertSystem.STATE_SEARCHING,
			StealthAlertSystem.STATE_ALERTED
		]:
			record["state"] = previous_state
		record = _advance_actor_investigation(actor, record, profile, delta)
	_alert_records[actor_id] = record
	_apply_record_to_actor(actor, record)
	if str(record.get("state", "")) == StealthAlertSystem.STATE_ALERTED and visible:
		_begin_combat_from_alert(actor, record)
