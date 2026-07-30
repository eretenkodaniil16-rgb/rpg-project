class_name StealthCombatNpc
extends "res://scripts/game/npc_body_runtime.gd"

const TACTICAL_SQUAD_TRIGGER_ACTOR_IDS: Array[String] = ["caretaker", "service_guard"]

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
	var profile: Dictionary = _get_stealth_profile()
	return maxi(int(profile.get("passive_perception", 10)), 1)


func get_perception_modifier() -> int:
	return int(_get_stealth_profile().get("perception_modifier", 0))


func get_tracking_modifier() -> int:
	return int(_get_stealth_profile().get("tracking_modifier", 0))


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


func get_maximum_health() -> int:
	return maximum_health


func get_observable_alert_state_label() -> String:
	return {
		StealthAlertSystem.STATE_CALM: "спокоен",
		StealthAlertSystem.STATE_SUSPICIOUS: "насторожен",
		StealthAlertSystem.STATE_INVESTIGATING: "проверяет источник",
		StealthAlertSystem.STATE_SEARCHING: "обыскивает область",
		StealthAlertSystem.STATE_ALERTED: "поднял тревогу",
		StealthAlertSystem.STATE_COMBAT: "ведёт бой"
	}.get(detection_state, "поведение неясно")


func get_observable_health_label() -> String:
	if is_dead_body():
		return "мёртв"
	if is_unconscious_body() or current_health <= 0:
		return "без сознания"
	var ratio: float = float(current_health) / float(maxi(maximum_health, 1))
	if ratio >= 0.85:
		return "выглядит невредимым"
	if ratio >= 0.5:
		return "заметно ранен"
	if ratio >= 0.25:
		return "тяжело ранен"
	return "едва держится"


func get_context_status_text() -> String:
	if is_body_interactable():
		return super.get_context_status_text()
	var relation: String = "враждебен" if is_hostile() else "не проявляет открытой враждебности"
	return "Поведение: %s. Отношение: %s. Состояние: %s." % [get_observable_alert_state_label(), relation, get_observable_health_label()]


func enter_combat_hostile() -> void:
	if actor_id in TACTICAL_SQUAD_TRIGGER_ACTOR_IDS:
		get_tree().call_group("stealth_world", "activate_tactical_training_squad")
	super.enter_combat_hostile()
	detection_state = StealthAlertSystem.STATE_COMBAT
	suspicion = StealthAlertSystem.SUSPICION_ALERTED
	_update_alert_visuals()


func reset_combat_state(full_restore: bool = true) -> void:
	super.reset_combat_state(full_restore)
	_restore_alert_record()


func _update_combat_visuals() -> void:
	super._update_combat_visuals()
	if _health_label != null:
		_health_label.text = ""
		_health_label.hide()


func _get_game_state() -> Node:
	return get_tree().root.get_node_or_null("GameState") if is_inside_tree() else null


func _get_stealth_profile() -> Dictionary:
	var state: Node = _get_game_state()
	if state == null or not state.has_method("get_stealth_profile"):
		return {}
	return state.call("get_stealth_profile", actor_id) as Dictionary


func _restore_alert_record() -> void:
	var state: Node = _get_game_state()
	if actor_id.is_empty() or state == null or not state.has_method("get_stealth_alert_record"):
		return
	var record: Dictionary = state.call("get_stealth_alert_record", actor_id) as Dictionary
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
	_alert_label.hide()
	add_child(_alert_label)
