class_name StealthPatrolObserver
extends Node2D

@export var actor_id: String = "service_guard"
@export var display_name: String = "Служебный дозорный"
@export var default_facing_direction: Vector2 = Vector2.RIGHT

var detection_state: String = StealthAlertSystem.STATE_CALM
var suspicion: float = 0.0
var last_known_position: Vector2 = Vector2.ZERO
var _facing_direction: Vector2 = Vector2.RIGHT
var _body_visual: Polygon2D
var _name_label: Label
var _alert_label: Label


func _ready() -> void:
	add_to_group("stealth_alert_actors")
	_facing_direction = default_facing_direction.normalized() if default_facing_direction.length_squared() > 0.0001 else Vector2.RIGHT
	_build_visuals()
	_restore_alert_record()
	_update_alert_visuals()


func get_actor_id() -> String:
	return actor_id


func get_combat_name() -> String:
	return display_name


func get_facing_direction() -> Vector2:
	return _facing_direction


func set_facing_direction(direction: Vector2) -> void:
	if direction.length_squared() <= 0.0001:
		return
	_facing_direction = direction.normalized()
	if _body_visual != null:
		_body_visual.rotation = _facing_direction.angle()


func is_combat_active() -> bool:
	return true


func set_exploration_alert_state(new_state: String, new_suspicion: float, new_last_known_position: Vector2) -> void:
	detection_state = new_state
	suspicion = clampf(new_suspicion, 0.0, StealthAlertSystem.SUSPICION_ALERTED)
	last_known_position = new_last_known_position
	_update_alert_visuals()


func get_detection_state() -> String:
	return detection_state


func get_suspicion() -> float:
	return suspicion


func get_last_known_position() -> Vector2:
	return last_known_position


func _restore_alert_record() -> void:
	if actor_id.is_empty() or not GameState.has_method("get_stealth_alert_record"):
		return
	var record: Dictionary = GameState.call("get_stealth_alert_record", actor_id) as Dictionary
	detection_state = str(record.get("state", StealthAlertSystem.STATE_CALM))
	suspicion = float(record.get("suspicion", 0.0))
	last_known_position = StealthAlertSystem.new().vector_from_value(record.get("last_known_position", []))


func _build_visuals() -> void:
	_body_visual = Polygon2D.new()
	_body_visual.name = "Body"
	_body_visual.polygon = PackedVector2Array([
		Vector2(20.0, 0.0),
		Vector2(-14.0, -17.0),
		Vector2(-9.0, 0.0),
		Vector2(-14.0, 17.0)
	])
	_body_visual.color = Color(0.38, 0.56, 0.66, 1.0)
	_body_visual.z_index = 3
	add_child(_body_visual)
	set_facing_direction(_facing_direction)

	_name_label = Label.new()
	_name_label.name = "NameLabel"
	_name_label.position = Vector2(-88.0, -56.0)
	_name_label.size = Vector2(176.0, 26.0)
	_name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_name_label.add_theme_font_size_override("font_size", 14)
	_name_label.text = display_name
	_name_label.z_index = 4
	add_child(_name_label)

	_alert_label = Label.new()
	_alert_label.name = "StealthAlertLabel"
	_alert_label.position = Vector2(-88.0, -82.0)
	_alert_label.size = Vector2(176.0, 24.0)
	_alert_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_alert_label.add_theme_font_size_override("font_size", 13)
	_alert_label.z_index = 5
	add_child(_alert_label)


func _update_alert_visuals() -> void:
	if _alert_label == null:
		return
	var state_label: String = {
		StealthAlertSystem.STATE_CALM: "",
		StealthAlertSystem.STATE_SUSPICIOUS: "НАСТОРОЖЕН",
		StealthAlertSystem.STATE_INVESTIGATING: "ПРОВЕРЯЕТ",
		StealthAlertSystem.STATE_SEARCHING: "ИЩЕТ",
		StealthAlertSystem.STATE_ALERTED: "ТРЕВОГА",
		StealthAlertSystem.STATE_COMBAT: "БОЙ"
	}.get(detection_state, detection_state.to_upper())
	_alert_label.text = state_label
	_alert_label.visible = not state_label.is_empty()
	var alert_color: Color = Color(1.0, 0.78, 0.28, 1.0)
	if detection_state in [StealthAlertSystem.STATE_ALERTED, StealthAlertSystem.STATE_COMBAT]:
		alert_color = Color(1.0, 0.34, 0.28, 1.0)
	_alert_label.add_theme_color_override("font_color", alert_color)
