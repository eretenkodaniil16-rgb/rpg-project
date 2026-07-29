class_name NpcAiSystem
extends RefCounted

const DATA_PATH: String = "res://data/ai/npc_ai_profiles.json"

const INTENT_ATTACK: String = "attack"
const INTENT_ADVANCE: String = "advance"
const INTENT_RETREAT: String = "retreat"
const INTENT_WAIT: String = "wait"

var _profiles: Dictionary = {}


func _init() -> void:
	_load_data()


func has_profile(actor_id: String) -> bool:
	return not get_profile(actor_id).is_empty()


func get_profile(actor_id: String) -> Dictionary:
	var value: Variant = _profiles.get(actor_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func should_join_combat(actor_id: String, distance_feet: int, alert_state: String) -> bool:
	var profile: Dictionary = get_profile(actor_id)
	if profile.is_empty() or not bool(profile.get("join_combat_on_alert", false)):
		return false
	if alert_state not in [StealthAlertSystem.STATE_INVESTIGATING, StealthAlertSystem.STATE_SEARCHING, StealthAlertSystem.STATE_ALERTED, StealthAlertSystem.STATE_COMBAT]:
		return false
	var maximum_distance: int = maxi(int(profile.get("combat_join_radius_feet", 0)), 0)
	return maximum_distance > 0 and distance_feet <= maximum_distance


func choose_combat_intent(actor_id: String, context: Dictionary) -> Dictionary:
	var profile: Dictionary = get_profile(actor_id)
	if profile.is_empty():
		return {"intent": INTENT_WAIT, "score": 0.0, "reason": "Для NPC не задан AI-профиль."}
	var utility: Dictionary = profile.get("utility", {}) as Dictionary if profile.get("utility", {}) is Dictionary else {}
	var distance_feet: int = maxi(int(context.get("distance_feet", 0)), 0)
	var preferred_range: int = maxi(int(profile.get("preferred_range_feet", 5)), 5)
	var actor_health_ratio: float = clampf(float(context.get("actor_health_ratio", 1.0)), 0.0, 1.0)
	var target_visible: bool = bool(context.get("target_visible", true))
	var can_attack: bool = bool(context.get("can_attack", false)) and target_visible
	var can_move: bool = bool(context.get("can_move", false))
	var retreat_threshold: float = clampf(float(profile.get("retreat_health_ratio", 0.0)), 0.0, 1.0)
	var aggression: float = clampf(float(profile.get("aggression", 0.75)), 0.0, 1.0)

	var scores: Dictionary = {
		INTENT_ATTACK: float(utility.get("attack", 100.0)) if can_attack and distance_feet <= preferred_range else -10000.0,
		INTENT_ADVANCE: float(utility.get("advance", 70.0)) if can_move and distance_feet > preferred_range else -10000.0,
		INTENT_RETREAT: float(utility.get("retreat", 25.0)) if can_move and actor_health_ratio <= retreat_threshold else -10000.0,
		INTENT_WAIT: float(utility.get("wait", 5.0))
	}
	if can_attack:
		scores[INTENT_ATTACK] = float(scores[INTENT_ATTACK]) * lerpf(0.7, 1.15, aggression)
	if actor_health_ratio <= retreat_threshold:
		scores[INTENT_RETREAT] = float(scores[INTENT_RETREAT]) + 80.0
	if not target_visible:
		scores[INTENT_ADVANCE] = float(scores[INTENT_ADVANCE]) + 18.0 if can_move else -10000.0

	var selected_intent: String = INTENT_WAIT
	var selected_score: float = -INF
	for intent_value: Variant in scores.keys():
		var intent: String = str(intent_value)
		var score: float = float(scores[intent])
		if score > selected_score:
			selected_score = score
			selected_intent = intent
	return {
		"intent": selected_intent,
		"score": selected_score,
		"role": str(profile.get("role", "generic")),
		"reason": _reason_for_intent(selected_intent)
	}


func _reason_for_intent(intent: String) -> String:
	match intent:
		INTENT_ATTACK: return "Цель находится в предпочтительной дистанции."
		INTENT_ADVANCE: return "Нужно сократить дистанцию или восстановить контакт."
		INTENT_RETREAT: return "Здоровье NPC ниже заданного порога."
		_: return "Полезное действие не найдено."


func _load_data() -> void:
	_profiles.clear()
	if not FileAccess.file_exists(DATA_PATH):
		return
	var file: FileAccess = FileAccess.open(DATA_PATH, FileAccess.READ)
	if file == null:
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		return
	var data: Dictionary = parsed as Dictionary
	_profiles = (data.get("profiles", {}) as Dictionary).duplicate(true) if data.get("profiles", {}) is Dictionary else {}
