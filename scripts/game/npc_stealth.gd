class_name StealthCombatNpc
extends "res://scripts/game/npc.gd"

@export var actor_id: String = "caretaker"
@export var default_facing_direction: Vector2 = Vector2.LEFT

var detection_state: String = StealthAlertSystem.STATE_CALM
var suspicion: float = 0.0
var last_known_position: Vector2 = Vector2.ZERO
var _facing_direction: Vector2 = Vector2.LEFT
var _alert_label: Label


func _ready() -> void:
	_facing_direction = default_facing_direction.normalized() if default_facing_direction.length_squared() > 0.0001 else Vector2.LEFT
	super._ready()
	_build_alert_label()
	_restore_alert_record()
	_update_alert_visuals()


func _process(delta: float) -> void:
	super._process(delta)
	_update_alert_visuals()


func get_actor_id() -> String:
	return actor_id


func get_facing_direction() -> Vector2:
	return _facing_direction


func set_facing_direction(direction: Vector2) -> void:
	if direction.length_squared() <= 0.0001:
		return
	_facing_direction = direction.normalized()


func get_passive_perception() -> int:
	var profile: Dictionary = GameState.call("get_stealth_profile", actor_id) as Dictionary if GameState.has_method("get_stealth_profile") else {}
	return maxi(int(profile.get("passive_perception", 10)), 1)


func get_perception_modifier() -> int:
	var profile: Dictionary = GameState.call("get_stealth_profile", actor_id) as Dictionary if GameState.has_method("get_stealth_profile") else {}
	return int(profile.get("perception_modifier", 0))


func get_tracking_modifier() -> int:
	var profile: Dictionary = GameState.call("get_stealth_profile", actor_id) as Dictionary if GameState.has_method("get_stealth_profile") else {}
	return int(profile.get("tracking_modifier", 0))


func set_exploration_alert_state(new_state: String, new_suspicion: float, new_last_known_position: Vector2) -> void:
	detection_state = new_state
	suspicion = clampf(new_suspicion, 0.0, StealthAlertSystem.SUSPICION_ALERTED)
	last_known_position = new_last_known_position
	_update_alert_visuals()


func set_detection_state(new_state: String, new_last_known_position: Vector2 = Vector2.ZERO) -> void:
	last_known_position = new_last_known_position
	match new_state:
		"aware":
			detection_state = StealthAlertSystem.STATE_ALERTED
			suspicion = StealthAlertSystem.SUSPICION_ALERTED
		"pursuing_last_seen", "tracking":
			detection_state = StealthAlertSystem.STATE_INVESTIGATING
			suspicion = maxf(suspicion, StealthAlertSystem.SUSPICION_INVESTIGATING)
		"searching":
			detection_state = StealthAlertSystem.STATE_SEARCHING
			suspicion = maxf(suspicion, StealthAlertSystem.SUSPICION_SUSPICIOUS)
		"lost":
			detection_state = StealthAlertSystem.STATE_SUSPICIOUS
			suspicion = maxf(suspicion, StealthAlertSystem.SUSPICION_SUSPICIOUS)
		_:
			detection_state = new_state
	_update_alert_visuals()


func get_detection_state() -> String:
	return detection_state


func get_suspicion() -> float:
	return suspicion


func get_last_known_position() -> Vector2:
	return last_known_position


func enter_combat_hostile() -> void:
	super.enter_combat_hostile()
	detection_state = StealthAlertSystem.STATE_COMBAT
	suspicion = StealthAlertSystem.SUSPICION_ALERTED
	_update_alert_visuals()


func reset_combat_state(full_restore: bool = true) -> void:
	super.reset_combat_state(full_restore)
	_restore_alert_record()


func _restore_alert_record() -> void:
	if actor_id.is_empty() or not GameState.has_method("get_stealth_alert_record"):
		return
	var record: Dictionary = GameState.call("get_stealth_alert_record", actor_id) as Dictionary
	detection_state = str(record.get("state", StealthAlertSystem.STATE_CALM))
	suspicion = float(record.get("suspicion", 0.0))
	last_known_position = StealthAlertSystem.new().vector_from_value(record.get("last_known_position", []))


func _build_alert_label() -> void:
	_alert_label = Label.new()
	_alert_label.name = "StealthAlertLabel"
	_alert_label.position = Vector2(-82.0, -144.0)
	_alert_label.size = Vector2(164.0, 28.0)
	_alert_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_alert_label.add_theme_font_size_override("font_size", 14)
	_alert_label.z_index = 8
	add_child(_alert_label)


func _update_alert_visuals() -> void:
	if _alert_label == null:
		return
	var state_label: String = {
		StealthAlertSystem.STATE_CALM: "СПОКОЕН",
		StealthAlertSystem.STATE_SUSPICIOUS: "ПОДОЗРЕНИЕ",
		StealthAlertSystem.STATE_INVESTIGATING: "ПРОВЕРЯЕТ",
		StealthAlertSystem.STATE_SEARCHING: "ИЩЕТ",
		StealthAlertSystem.STATE_ALERTED: "ТРЕВОГА",
		StealthAlertSystem.STATE_COMBAT: "БОЙ"
	}.get(detection_state, detection_state.to_upper())
	_alert_label.text = "%s · %d%%" % [state_label, roundi(suspicion)]
	_alert_label.visible = detection_state != StealthAlertSystem.STATE_CALM or suspicion > 0.5
	var alert_color: Color = Color(0.62, 0.86, 0.64, 1.0)
	if detection_state in [StealthAlertSystem.STATE_SUSPICIOUS, StealthAlertSystem.STATE_INVESTIGATING, StealthAlertSystem.STATE_SEARCHING]:
		alert_color = Color(1.0, 0.78, 0.28, 1.0)
	elif detection_state in [StealthAlertSystem.STATE_ALERTED, StealthAlertSystem.STATE_COMBAT]:
		alert_color = Color(1.0, 0.34, 0.28, 1.0)
	_alert_label.add_theme_color_override("font_color", alert_color)
