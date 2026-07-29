extends "res://scripts/game/game_exploration_stealth_runtime.gd"

const PLAYER_FEEDBACK_STATE_PRIORITY: Dictionary = {
	StealthAlertSystem.STATE_CALM: 0,
	StealthAlertSystem.STATE_SUSPICIOUS: 1,
	StealthAlertSystem.STATE_INVESTIGATING: 2,
	StealthAlertSystem.STATE_SEARCHING: 3,
	StealthAlertSystem.STATE_ALERTED: 4,
	StealthAlertSystem.STATE_COMBAT: 5
}


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


func _refresh_alert_indicator() -> void:
	if _alert_indicator == null:
		return
	var highest_state: String = _highest_player_feedback_state()
	var hidden: bool = _exploration_hidden or _player_combat_state.hidden
	if highest_state == StealthAlertSystem.STATE_CALM:
		_alert_indicator.visible = hidden
		_alert_indicator.text = "СКРЫТ" if hidden else ""
		_alert_indicator.add_theme_color_override("font_color", Color(0.62, 0.86, 0.64, 1.0))
		return
	var state_label: String = {
		StealthAlertSystem.STATE_SUSPICIOUS: "КТО-ТО НАСТОРОЖЕН",
		StealthAlertSystem.STATE_INVESTIGATING: "ПРОВЕРЯЮТ ШУМ",
		StealthAlertSystem.STATE_SEARCHING: "ВАС ИЩУТ",
		StealthAlertSystem.STATE_ALERTED: "ТРЕВОГА",
		StealthAlertSystem.STATE_COMBAT: "ОБНАРУЖЕН"
	}.get(highest_state, "ОПАСНОСТЬ")
	_alert_indicator.visible = true
	_alert_indicator.text = "СКРЫТ · %s" % state_label if hidden else state_label
	var alert_color: Color = Color(1.0, 0.78, 0.28, 1.0)
	if highest_state in [StealthAlertSystem.STATE_ALERTED, StealthAlertSystem.STATE_COMBAT]:
		alert_color = Color(1.0, 0.34, 0.28, 1.0)
	_alert_indicator.add_theme_color_override("font_color", alert_color)


func _highest_player_feedback_state() -> String:
	var highest_state: String = StealthAlertSystem.STATE_CALM
	var highest_priority: int = 0
	for value: Variant in _alert_records.values():
		if not value is Dictionary:
			continue
		var state: String = str((value as Dictionary).get("state", StealthAlertSystem.STATE_CALM))
		var priority: int = int(PLAYER_FEEDBACK_STATE_PRIORITY.get(state, 0))
		if priority > highest_priority:
			highest_priority = priority
			highest_state = state
	return highest_state
