extends "res://scripts/game/game_exploration_stealth_runtime.gd"

const PATROL_ALERT_GROUP_SYSTEM_SCRIPT: Script = preload("res://scripts/systems/patrol_alert_group_system.gd")
const PLAYER_FEEDBACK_STATE_PRIORITY: Dictionary = {
	StealthAlertSystem.STATE_CALM: 0,
	StealthAlertSystem.STATE_SUSPICIOUS: 1,
	StealthAlertSystem.STATE_INVESTIGATING: 2,
	StealthAlertSystem.STATE_SEARCHING: 3,
	StealthAlertSystem.STATE_ALERTED: 4,
	StealthAlertSystem.STATE_COMBAT: 5
}

var _patrol_alert_groups: PatrolAlertGroupSystem = PATROL_ALERT_GROUP_SYSTEM_SCRIPT.new() as PatrolAlertGroupSystem
var _alert_broadcasted: Dictionary = {}


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


func _exploration_alert_actors() -> Array[Node]:
	var result: Array[Node] = super._exploration_alert_actors()
	var seen_ids: Dictionary = {}
	for actor: Node in result:
		if is_instance_valid(actor):
			seen_ids[actor.get_instance_id()] = true
	for actor: Node in get_tree().get_nodes_in_group("stealth_alert_actors"):
		if not is_instance_valid(actor) or not (actor is Node2D) or not actor.has_method("get_actor_id"):
			continue
		if seen_ids.has(actor.get_instance_id()):
			continue
		var actor_id: String = str(actor.call("get_actor_id"))
		if actor_id.is_empty() or not _stealth_alerts.has_profile(actor_id):
			continue
		if actor.has_method("is_combat_active") and not bool(actor.call("is_combat_active")):
			continue
		result.append(actor)
		seen_ids[actor.get_instance_id()] = true
	return result


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
		elif str(record.get("state", StealthAlertSystem.STATE_CALM)) == StealthAlertSystem.STATE_CALM:
			record = _advance_actor_patrol(actor, record, delta)
	_alert_records[actor_id] = record
	_apply_record_to_actor(actor, record)
	var current_state: String = str(record.get("state", StealthAlertSystem.STATE_CALM))
	if previous_state not in [StealthAlertSystem.STATE_ALERTED, StealthAlertSystem.STATE_COMBAT] and current_state in [StealthAlertSystem.STATE_ALERTED, StealthAlertSystem.STATE_COMBAT]:
		_broadcast_actor_alert(actor, record)
	elif current_state not in [StealthAlertSystem.STATE_ALERTED, StealthAlertSystem.STATE_COMBAT]:
		_alert_broadcasted.erase(actor_id)
	if current_state == StealthAlertSystem.STATE_ALERTED and visible and _patrol_alert_groups.can_start_combat(actor_id):
		_begin_combat_from_alert(actor, record)


func _advance_actor_patrol(actor: Node, record: Dictionary, delta: float) -> Dictionary:
	if GameState.input_locked or actor == null or not (actor is Node2D):
		return record
	var actor_id: String = str(actor.call("get_actor_id"))
	var patrol_result: Dictionary = _patrol_alert_groups.advance_patrol(actor_id, record, (actor as Node2D).global_position, delta)
	var updated_record: Dictionary = patrol_result.get("record", record) as Dictionary
	if not bool(patrol_result.get("active", false)):
		return updated_record
	(actor as Node2D).global_position = patrol_result.get("position", (actor as Node2D).global_position) as Vector2
	var facing: Vector2 = patrol_result.get("facing", Vector2.ZERO) as Vector2
	if facing.length_squared() > 0.0001 and actor.has_method("set_facing_direction"):
		actor.call("set_facing_direction", facing)
	return updated_record


func _broadcast_actor_alert(source_actor: Node, source_record: Dictionary) -> void:
	if source_actor == null or not is_instance_valid(source_actor) or not (source_actor is Node2D) or not source_actor.has_method("get_actor_id"):
		return
	var source_actor_id: String = str(source_actor.call("get_actor_id"))
	if source_actor_id.is_empty() or bool(_alert_broadcasted.get(source_actor_id, false)):
		return
	_alert_broadcasted[source_actor_id] = true
	var source_position: Vector2 = (source_actor as Node2D).global_position
	var source_room_id: String = _stealth_alerts.get_room_id_at(source_position)
	var relayed_count: int = 0
	for listener: Node in _exploration_alert_actors():
		if listener == source_actor or not (listener is Node2D) or not listener.has_method("get_actor_id"):
			continue
		var listener_actor_id: String = str(listener.call("get_actor_id"))
		var listener_position: Vector2 = (listener as Node2D).global_position
		var listener_room_id: String = _stealth_alerts.get_room_id_at(listener_position)
		var audibility: float = _stealth_alerts.noise_multiplier_between_rooms(GameState, source_room_id, listener_room_id)
		if not _patrol_alert_groups.can_relay_alert(source_actor_id, listener_actor_id, source_position, listener_position, audibility):
			continue
		var listener_profile: Dictionary = _stealth_alerts.get_profile(listener_actor_id)
		var listener_record: Dictionary = _record_for_actor(listener_actor_id)
		var relayed_record: Dictionary = _patrol_alert_groups.apply_alert_relay(
			listener_actor_id,
			listener_record,
			source_actor_id,
			source_record,
			listener_profile
		)
		if relayed_record == listener_record:
			continue
		_alert_records[listener_actor_id] = relayed_record
		_apply_record_to_actor(listener, relayed_record)
		_persist_alert_record(listener_actor_id, false)
		if listener.has_method("set_facing_direction"):
			listener.call("set_facing_direction", source_position - listener_position)
		relayed_count += 1
	if relayed_count > 0:
		show_combat_message("Сигнал тревоги передан ближайшему дозору.", false)


func _sync_combat_alert_records() -> void:
	for actor: Node in _exploration_alert_actors():
		var actor_id: String = str(actor.call("get_actor_id"))
		if not _patrol_alert_groups.participates_in_combat(actor_id):
			continue
		var record: Dictionary = _record_for_actor(actor_id)
		record["state"] = StealthAlertSystem.STATE_COMBAT
		record["suspicion"] = StealthAlertSystem.SUSPICION_ALERTED
		record["last_known_position"] = _stealth_alerts.vector_to_value(player.global_position)
		_alert_records[actor_id] = record
		_apply_record_to_actor(actor, record)


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


func get_patrol_actor_for_testing(actor_id: String) -> Node:
	for actor: Node in _exploration_alert_actors():
		if actor.has_method("get_actor_id") and str(actor.call("get_actor_id")) == actor_id:
			return actor
	return null


func force_patrol_tick_for_testing(actor: Node, delta: float) -> void:
	if actor == null or not actor.has_method("get_actor_id"):
		return
	var actor_id: String = str(actor.call("get_actor_id"))
	var record: Dictionary = _record_for_actor(actor_id)
	record["state"] = StealthAlertSystem.STATE_CALM
	record["suspicion"] = 0.0
	record = _advance_actor_patrol(actor, record, delta)
	_alert_records[actor_id] = record
	_apply_record_to_actor(actor, record)


func force_alert_broadcast_for_testing(source_actor: Node, last_known_position: Vector2) -> void:
	if source_actor == null or not source_actor.has_method("get_actor_id"):
		return
	var source_actor_id: String = str(source_actor.call("get_actor_id"))
	_alert_broadcasted.erase(source_actor_id)
	var record: Dictionary = _record_for_actor(source_actor_id)
	record["state"] = StealthAlertSystem.STATE_ALERTED
	record["suspicion"] = StealthAlertSystem.SUSPICION_ALERTED
	record["last_known_position"] = _stealth_alerts.vector_to_value(last_known_position)
	_alert_records[source_actor_id] = record
	_apply_record_to_actor(source_actor, record)
	_broadcast_actor_alert(source_actor, record)
