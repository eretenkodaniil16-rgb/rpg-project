class_name NpcCombatAiSystem
extends NpcAiSystem

const COMBAT_AI_DATA_PATH: String = "res://data/ai/npc_ai_profiles.json"

const ROLE_MELEE: String = "melee"
const ROLE_RANGED: String = "ranged"
const ROLE_DEFENDER: String = "defender"

const INTENT_REPOSITION: String = "reposition"
const INTENT_INTERCEPT: String = "intercept"
const INTENT_GUARD: String = "guard"

const BLOCKED_SCORE: float = -100000.0
const INTENT_ORDER: Array[String] = [
	INTENT_RETREAT,
	INTENT_ATTACK,
	INTENT_REPOSITION,
	INTENT_INTERCEPT,
	INTENT_ADVANCE,
	INTENT_GUARD,
	INTENT_WAIT
]

var _role_profiles: Dictionary = {}


func get_role_profile(role_id: String) -> Dictionary:
	if _role_profiles.is_empty():
		_load_role_profiles()
	var value: Variant = _role_profiles.get(role_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func get_profile(actor_id: String) -> Dictionary:
	var actor_profile: Dictionary = super.get_profile(actor_id)
	if actor_profile.is_empty():
		return {}
	var role_id: String = str(actor_profile.get("role", ROLE_MELEE))
	return _merge_profiles(get_role_profile(role_id), actor_profile)


func get_attack_range_feet(actor_id: String) -> int:
	return maxi(int(get_profile(actor_id).get("attack_range_feet", DistanceSystem.MELEE_REACH_FEET)), DistanceSystem.MELEE_REACH_FEET)


func get_minimum_range_feet(actor_id: String) -> int:
	return maxi(int(get_profile(actor_id).get("minimum_range_feet", 0)), 0)


func get_preferred_range_feet(actor_id: String) -> int:
	var profile: Dictionary = get_profile(actor_id)
	return clampi(int(profile.get("preferred_range_feet", get_attack_range_feet(actor_id))), 0, get_attack_range_feet(actor_id))


func choose_combat_intent(actor_id: String, context: Dictionary) -> Dictionary:
	var profile: Dictionary = get_profile(actor_id)
	if profile.is_empty():
		return super.choose_combat_intent(actor_id, context)
	return _choose_profile_intent(profile, context)


func choose_role_intent(role_id: String, context: Dictionary, overrides: Dictionary = {}) -> Dictionary:
	var profile: Dictionary = _merge_profiles(get_role_profile(role_id), overrides)
	if profile.is_empty():
		return {"intent": INTENT_WAIT, "score": 0.0, "role": role_id, "reason": "Для роли не задан AI-профиль."}
	profile["role"] = role_id
	return _choose_profile_intent(profile, context)


func _choose_profile_intent(profile: Dictionary, context: Dictionary) -> Dictionary:
	var role_id: String = str(profile.get("role", ROLE_MELEE))
	var utility: Dictionary = profile.get("utility", {}) as Dictionary if profile.get("utility", {}) is Dictionary else {}
	var distance_feet: int = maxi(int(context.get("distance_feet", 0)), 0)
	var actor_health_ratio: float = clampf(float(context.get("actor_health_ratio", 1.0)), 0.0, 1.0)
	var target_visible: bool = bool(context.get("target_visible", true))
	var can_move: bool = bool(context.get("can_move", false))
	var attack_range_feet: int = maxi(int(profile.get("attack_range_feet", DistanceSystem.MELEE_REACH_FEET)), DistanceSystem.MELEE_REACH_FEET)
	var minimum_range_feet: int = maxi(int(profile.get("minimum_range_feet", 0)), 0)
	var preferred_range_feet: int = clampi(int(profile.get("preferred_range_feet", attack_range_feet)), minimum_range_feet, attack_range_feet)
	var can_attack: bool = bool(context.get("can_attack", distance_feet <= attack_range_feet)) and target_visible and distance_feet <= attack_range_feet
	var retreat_threshold: float = clampf(float(profile.get("retreat_health_ratio", 0.0)), 0.0, 1.0)
	var aggression: float = clampf(float(profile.get("aggression", 0.75)), 0.0, 1.0)
	var low_health: bool = actor_health_ratio <= retreat_threshold
	var distance_from_guard_anchor_feet: int = maxi(int(context.get("distance_from_guard_anchor_feet", 0)), 0)
	var target_distance_from_guard_anchor_feet: int = maxi(int(context.get("target_distance_from_guard_anchor_feet", 0)), 0)
	var guard_radius_feet: int = maxi(int(profile.get("guard_radius_feet", 0)), 0)
	var pursuit_leash_feet: int = maxi(int(profile.get("pursuit_leash_feet", guard_radius_feet)), guard_radius_feet)
	var guard_return_tolerance_feet: int = maxi(int(profile.get("guard_return_tolerance_feet", DistanceSystem.MELEE_REACH_FEET)), 0)

	var scores: Dictionary = {
		INTENT_ATTACK: BLOCKED_SCORE,
		INTENT_ADVANCE: BLOCKED_SCORE,
		INTENT_RETREAT: BLOCKED_SCORE,
		INTENT_REPOSITION: BLOCKED_SCORE,
		INTENT_INTERCEPT: BLOCKED_SCORE,
		INTENT_GUARD: BLOCKED_SCORE,
		INTENT_WAIT: float(utility.get("wait", 5.0))
	}

	if low_health and can_move:
		scores[INTENT_RETREAT] = float(utility.get("retreat", 25.0)) + 90.0 + (retreat_threshold - actor_health_ratio) * 100.0

	match role_id:
		ROLE_RANGED:
			_score_ranged_role(
				scores,
				utility,
				distance_feet,
				minimum_range_feet,
				preferred_range_feet,
				attack_range_feet,
				target_visible,
				can_attack,
				can_move,
				aggression,
				low_health
			)
		ROLE_DEFENDER:
			_score_defender_role(
				scores,
				utility,
				distance_feet,
				attack_range_feet,
				target_visible,
				can_attack,
				can_move,
				aggression,
				low_health,
				distance_from_guard_anchor_feet,
				target_distance_from_guard_anchor_feet,
				guard_radius_feet,
				pursuit_leash_feet,
				guard_return_tolerance_feet
			)
		_:
			_score_melee_role(scores, utility, distance_feet, attack_range_feet, target_visible, can_attack, can_move, aggression, low_health)

	var selected_intent: String = INTENT_WAIT
	var selected_score: float = BLOCKED_SCORE
	for intent_id: String in INTENT_ORDER:
		var score: float = float(scores.get(intent_id, BLOCKED_SCORE))
		if score > selected_score:
			selected_score = score
			selected_intent = intent_id
	return {
		"intent": selected_intent,
		"score": selected_score,
		"role": role_id,
		"reason": _reason_for_role_intent(selected_intent, role_id),
		"attack_range_feet": attack_range_feet,
		"minimum_range_feet": minimum_range_feet,
		"preferred_range_feet": preferred_range_feet
	}


func _score_melee_role(
	scores: Dictionary,
	utility: Dictionary,
	distance_feet: int,
	attack_range_feet: int,
	target_visible: bool,
	can_attack: bool,
	can_move: bool,
	aggression: float,
	low_health: bool
) -> void:
	if can_attack:
		scores[INTENT_ATTACK] = float(utility.get("attack", 100.0)) * lerpf(0.72, 1.16, aggression)
	if can_move and not low_health and (distance_feet > attack_range_feet or not target_visible):
		scores[INTENT_ADVANCE] = float(utility.get("advance", 72.0)) + minf(float(distance_feet - attack_range_feet), 30.0) * 0.7
		if not target_visible:
			scores[INTENT_ADVANCE] = float(scores[INTENT_ADVANCE]) + 16.0


func _score_ranged_role(
	scores: Dictionary,
	utility: Dictionary,
	distance_feet: int,
	minimum_range_feet: int,
	preferred_range_feet: int,
	attack_range_feet: int,
	target_visible: bool,
	can_attack: bool,
	can_move: bool,
	aggression: float,
	low_health: bool
) -> void:
	if can_move and not low_health and distance_feet < minimum_range_feet:
		scores[INTENT_REPOSITION] = float(utility.get("reposition", 90.0)) + float(minimum_range_feet - distance_feet) * 3.0
	if can_attack and distance_feet >= minimum_range_feet:
		var range_error: float = absf(float(distance_feet - preferred_range_feet))
		scores[INTENT_ATTACK] = float(utility.get("attack", 96.0)) * lerpf(0.8, 1.1, aggression) - range_error * 0.35
	if can_move and not low_health and (distance_feet > attack_range_feet or not target_visible):
		scores[INTENT_ADVANCE] = float(utility.get("advance", 64.0)) + minf(float(distance_feet - attack_range_feet), 40.0)
		if not target_visible:
			scores[INTENT_ADVANCE] = float(scores[INTENT_ADVANCE]) + 20.0


func _score_defender_role(
	scores: Dictionary,
	utility: Dictionary,
	distance_feet: int,
	attack_range_feet: int,
	target_visible: bool,
	can_attack: bool,
	can_move: bool,
	aggression: float,
	low_health: bool,
	distance_from_guard_anchor_feet: int,
	target_distance_from_guard_anchor_feet: int,
	guard_radius_feet: int,
	pursuit_leash_feet: int,
	guard_return_tolerance_feet: int
) -> void:
	var target_inside_guard_zone: bool = guard_radius_feet <= 0 or target_distance_from_guard_anchor_feet <= guard_radius_feet
	var actor_outside_leash: bool = pursuit_leash_feet > 0 and distance_from_guard_anchor_feet > pursuit_leash_feet
	if can_attack and not actor_outside_leash:
		scores[INTENT_ATTACK] = float(utility.get("attack", 100.0)) * lerpf(0.78, 1.12, aggression)
	if can_move and not low_health and target_inside_guard_zone and not actor_outside_leash and (distance_feet > attack_range_feet or not target_visible):
		scores[INTENT_INTERCEPT] = float(utility.get("intercept", 82.0)) + minf(float(distance_feet - attack_range_feet), 30.0) * 0.8
		if not target_visible:
			scores[INTENT_INTERCEPT] = float(scores[INTENT_INTERCEPT]) + 12.0
	if can_move and not low_health and (actor_outside_leash or (not target_inside_guard_zone and distance_from_guard_anchor_feet > guard_return_tolerance_feet)):
		scores[INTENT_GUARD] = float(utility.get("guard", 66.0)) + float(distance_from_guard_anchor_feet) * 1.2


func _reason_for_role_intent(intent: String, role_id: String) -> String:
	match intent:
		INTENT_ATTACK: return "Роль %s может атаковать цель с текущей позиции." % role_id
		INTENT_ADVANCE: return "Роль %s сокращает дистанцию или восстанавливает линию атаки." % role_id
		INTENT_RETREAT: return "Здоровье NPC ниже порога безопасного продолжения боя."
		INTENT_REPOSITION: return "Стрелок увеличивает дистанцию до безопасного диапазона."
		INTENT_INTERCEPT: return "Защитник перехватывает цель внутри охраняемой зоны."
		INTENT_GUARD: return "Защитник возвращается к закреплённой позиции."
		_: return "Роль %s не нашла полезного действия." % role_id


func _merge_profiles(base_profile: Dictionary, overrides: Dictionary) -> Dictionary:
	var result: Dictionary = base_profile.duplicate(true)
	for key_value: Variant in overrides.keys():
		var key: String = str(key_value)
		var override_value: Variant = overrides[key_value]
		if key == "utility" and override_value is Dictionary:
			var merged_utility: Dictionary = result.get("utility", {}) as Dictionary if result.get("utility", {}) is Dictionary else {}
			merged_utility = merged_utility.duplicate(true)
			merged_utility.merge((override_value as Dictionary).duplicate(true), true)
			result[key] = merged_utility
		else:
			result[key] = override_value
	return result


func _load_role_profiles() -> void:
	_role_profiles.clear()
	if not FileAccess.file_exists(COMBAT_AI_DATA_PATH):
		return
	var file: FileAccess = FileAccess.open(COMBAT_AI_DATA_PATH, FileAccess.READ)
	if file == null:
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		return
	var data: Dictionary = parsed as Dictionary
	_role_profiles = (data.get("role_profiles", {}) as Dictionary).duplicate(true) if data.get("role_profiles", {}) is Dictionary else {}
