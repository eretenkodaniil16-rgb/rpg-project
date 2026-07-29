class_name NpcCombatAiSystem
extends NpcAiSystem

const COMBAT_AI_DATA_PATH: String = "res://data/ai/npc_ai_profiles.json"

const ROLE_MELEE: String = "melee"
const ROLE_RANGED: String = "ranged"
const ROLE_DEFENDER: String = "defender"

const INTENT_REPOSITION: String = "reposition"
const INTENT_INTERCEPT: String = "intercept"
const INTENT_SEARCH: String = "search"
const INTENT_GUARD: String = "guard"

const BLOCKED_SCORE: float = -100000.0
const INTENT_ORDER: Array[String] = [
	INTENT_RETREAT,
	INTENT_ATTACK,
	INTENT_REPOSITION,
	INTENT_INTERCEPT,
	INTENT_ADVANCE,
	INTENT_SEARCH,
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


func get_memory_rounds(actor_id: String) -> int:
	return maxi(int(get_profile(actor_id).get("memory_rounds", 2)), 0)


func get_squad_id(actor_id: String) -> String:
	return str(get_profile(actor_id).get("squad_id", ""))


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


func score_candidate_position(intent_id: String, profile: Dictionary, _context: Dictionary, candidate: Dictionary) -> float:
	if not bool(candidate.get("valid", true)):
		return BLOCKED_SCORE
	var role_id: String = str(profile.get("role", ROLE_MELEE))
	var attack_range_feet: int = maxi(int(profile.get("attack_range_feet", DistanceSystem.MELEE_REACH_FEET)), DistanceSystem.MELEE_REACH_FEET)
	var minimum_range_feet: int = maxi(int(profile.get("minimum_range_feet", 0)), 0)
	var preferred_range_feet: int = clampi(int(profile.get("preferred_range_feet", attack_range_feet)), minimum_range_feet, attack_range_feet)
	var pursuit_leash_feet: int = maxi(int(profile.get("pursuit_leash_feet", 0)), 0)
	var spacing_feet: int = maxi(int(profile.get("spacing_feet", DistanceSystem.MELEE_REACH_FEET)), 0)
	var weights: Dictionary = profile.get("position_weights", {}) as Dictionary if profile.get("position_weights", {}) is Dictionary else {}
	var distance_feet: int = maxi(int(candidate.get("distance_feet", 0)), 0)
	var objective_distance_feet: int = maxi(int(candidate.get("distance_to_objective_feet", distance_feet)), 0)
	var guard_distance_feet: int = maxi(int(candidate.get("distance_from_guard_anchor_feet", 0)), 0)
	var nearest_ally_distance_feet: int = maxi(int(candidate.get("nearest_ally_distance_feet", 9999)), 0)
	var mobility: int = maxi(int(candidate.get("mobility", 0)), 0)
	var path_cost_feet: int = maxi(int(candidate.get("path_cost_feet", 0)), 0)
	var target_visible: bool = bool(candidate.get("target_visible", false))
	var attack_ready: bool = bool(candidate.get("attack_ready", false))

	if role_id == ROLE_DEFENDER and pursuit_leash_feet > 0 and guard_distance_feet > pursuit_leash_feet and intent_id not in [INTENT_GUARD, INTENT_RETREAT]:
		return BLOCKED_SCORE

	var score: float = float(mobility) * float(weights.get("mobility", 1.5))
	score -= float(path_cost_feet) * float(weights.get("movement_cost", 0.08))
	if spacing_feet > 0 and nearest_ally_distance_feet < spacing_feet:
		score -= float(spacing_feet - nearest_ally_distance_feet) * float(weights.get("ally_spacing", 2.0))

	match intent_id:
		INTENT_ATTACK:
			if not attack_ready:
				return BLOCKED_SCORE
			score += float(weights.get("attack_ready", 120.0))
			score -= absf(float(distance_feet - preferred_range_feet)) * float(weights.get("range_error", 0.8))
			if target_visible:
				score += float(weights.get("line_of_sight", 24.0))
		INTENT_ADVANCE, INTENT_INTERCEPT:
			score -= float(objective_distance_feet) * float(weights.get("approach", 1.4))
			if attack_ready:
				score += float(weights.get("attack_ready", 120.0))
			elif target_visible:
				score += float(weights.get("line_of_sight", 24.0))
			if role_id == ROLE_RANGED and target_visible:
				score -= absf(float(distance_feet - preferred_range_feet)) * float(weights.get("range_error", 0.8))
		INTENT_SEARCH:
			score -= float(objective_distance_feet) * float(weights.get("search", 1.65))
			if target_visible:
				score += float(weights.get("reacquire_target", 150.0))
			if attack_ready:
				score += float(weights.get("attack_ready", 120.0))
		INTENT_REPOSITION:
			if distance_feet < minimum_range_feet:
				score -= float(minimum_range_feet - distance_feet) * float(weights.get("create_distance", 2.2))
			else:
				score -= absf(float(distance_feet - preferred_range_feet)) * float(weights.get("range_error", 0.8))
			if attack_ready and distance_feet >= minimum_range_feet:
				score += float(weights.get("mobile_attack", 64.0))
			elif distance_feet > attack_range_feet:
				score -= float(distance_feet - attack_range_feet) * 2.0
		INTENT_RETREAT:
			score += float(distance_feet) * float(weights.get("retreat_distance", 1.8))
			score += float(mobility) * float(weights.get("retreat_mobility", 2.0))
		INTENT_GUARD:
			score -= float(guard_distance_feet) * float(weights.get("guard_return", 2.0))
		INTENT_WAIT:
			score -= float(path_cost_feet) * 10.0
		_:
			return BLOCKED_SCORE
	return score


func _choose_profile_intent(profile: Dictionary, context: Dictionary) -> Dictionary:
	var role_id: String = str(profile.get("role", ROLE_MELEE))
	var utility: Dictionary = profile.get("utility", {}) as Dictionary if profile.get("utility", {}) is Dictionary else {}
	var distance_feet: int = maxi(int(context.get("distance_feet", 0)), 0)
	var actor_health_ratio: float = clampf(float(context.get("actor_health_ratio", 1.0)), 0.0, 1.0)
	var target_visible: bool = bool(context.get("target_visible", true))
	var has_target_memory: bool = bool(context.get("has_target_memory", target_visible))
	var memory_confidence: float = clampf(float(context.get("memory_confidence", 1.0 if target_visible else 0.0)), 0.0, 1.0)
	var can_move: bool = bool(context.get("can_move", false))
	var attack_range_feet: int = maxi(int(profile.get("attack_range_feet", DistanceSystem.MELEE_REACH_FEET)), DistanceSystem.MELEE_REACH_FEET)
	var minimum_range_feet: int = maxi(int(profile.get("minimum_range_feet", 0)), 0)
	var preferred_range_feet: int = clampi(int(profile.get("preferred_range_feet", attack_range_feet)), minimum_range_feet, attack_range_feet)
	var can_attack: bool = bool(context.get("can_attack", distance_feet <= attack_range_feet)) and target_visible and distance_feet <= attack_range_feet
	var retreat_threshold: float = clampf(float(profile.get("retreat_health_ratio", 0.0)), 0.0, 1.0)
	var aggression: float = clampf(float(profile.get("aggression", 0.75)), 0.0, 1.0)
	var morale: float = clampf(float(profile.get("morale", 0.75)), 0.0, 1.0)
	var ally_count: int = maxi(int(context.get("ally_count", 1)), 1)
	var hostile_count: int = maxi(int(context.get("hostile_count", 1)), 1)
	var defeated_ally_count: int = maxi(int(context.get("defeated_ally_count", 0)), 0)
	var escape_route_count: int = maxi(int(context.get("escape_route_count", 1)), 0)
	var morale_pressure: float = _calculate_morale_pressure(ally_count, hostile_count, defeated_ally_count, escape_route_count)
	var low_health: bool = actor_health_ratio <= retreat_threshold
	var tactical_retreat: bool = low_health or (
		bool(profile.get("retreat_when_outnumbered", false))
		and morale_pressure > morale
		and actor_health_ratio <= clampf(float(profile.get("outnumbered_retreat_health_ratio", 0.6)), 0.0, 1.0)
	)
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
		INTENT_SEARCH: BLOCKED_SCORE,
		INTENT_GUARD: BLOCKED_SCORE,
		INTENT_WAIT: float(utility.get("wait", 5.0))
	}
	if tactical_retreat and can_move:
		scores[INTENT_RETREAT] = float(utility.get("retreat", 25.0)) + 90.0 + maxf(retreat_threshold - actor_health_ratio, 0.0) * 100.0 + morale_pressure * 30.0

	match role_id:
		ROLE_RANGED:
			_score_ranged_role(scores, utility, distance_feet, minimum_range_feet, preferred_range_feet, attack_range_feet, target_visible, has_target_memory, memory_confidence, can_attack, can_move, aggression, tactical_retreat)
		ROLE_DEFENDER:
			_score_defender_role(scores, utility, distance_feet, attack_range_feet, target_visible, has_target_memory, memory_confidence, can_attack, can_move, aggression, tactical_retreat, distance_from_guard_anchor_feet, target_distance_from_guard_anchor_feet, guard_radius_feet, pursuit_leash_feet, guard_return_tolerance_feet)
		_:
			_score_melee_role(scores, utility, distance_feet, attack_range_feet, target_visible, has_target_memory, memory_confidence, can_attack, can_move, aggression, tactical_retreat)

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
		"preferred_range_feet": preferred_range_feet,
		"has_target_memory": has_target_memory,
		"memory_confidence": memory_confidence,
		"morale_pressure": morale_pressure
	}


func _score_melee_role(scores: Dictionary, utility: Dictionary, distance_feet: int, attack_range_feet: int, target_visible: bool, has_target_memory: bool, memory_confidence: float, can_attack: bool, can_move: bool, aggression: float, tactical_retreat: bool) -> void:
	if can_attack:
		scores[INTENT_ATTACK] = float(utility.get("attack", 100.0)) * lerpf(0.72, 1.16, aggression)
	if can_move and not tactical_retreat and target_visible and distance_feet > attack_range_feet:
		scores[INTENT_ADVANCE] = float(utility.get("advance", 72.0)) + minf(float(distance_feet - attack_range_feet), 30.0) * 0.7
	elif can_move and not tactical_retreat and not target_visible and has_target_memory:
		scores[INTENT_SEARCH] = float(utility.get("search", 68.0)) + memory_confidence * 28.0


func _score_ranged_role(scores: Dictionary, utility: Dictionary, distance_feet: int, minimum_range_feet: int, preferred_range_feet: int, attack_range_feet: int, target_visible: bool, has_target_memory: bool, memory_confidence: float, can_attack: bool, can_move: bool, aggression: float, tactical_retreat: bool) -> void:
	if can_move and not tactical_retreat and target_visible and distance_feet < minimum_range_feet:
		scores[INTENT_REPOSITION] = float(utility.get("reposition", 90.0)) + float(minimum_range_feet - distance_feet) * 3.0
	if can_attack and distance_feet >= minimum_range_feet:
		var range_error: float = absf(float(distance_feet - preferred_range_feet))
		scores[INTENT_ATTACK] = float(utility.get("attack", 96.0)) * lerpf(0.8, 1.1, aggression) - range_error * 0.35
	if can_move and not tactical_retreat and target_visible and distance_feet > attack_range_feet:
		scores[INTENT_ADVANCE] = float(utility.get("advance", 64.0)) + minf(float(distance_feet - attack_range_feet), 40.0)
	elif can_move and not tactical_retreat and not target_visible and has_target_memory:
		scores[INTENT_SEARCH] = float(utility.get("search", 72.0)) + memory_confidence * 30.0


func _score_defender_role(scores: Dictionary, utility: Dictionary, distance_feet: int, attack_range_feet: int, target_visible: bool, has_target_memory: bool, memory_confidence: float, can_attack: bool, can_move: bool, aggression: float, tactical_retreat: bool, distance_from_guard_anchor_feet: int, target_distance_from_guard_anchor_feet: int, guard_radius_feet: int, pursuit_leash_feet: int, guard_return_tolerance_feet: int) -> void:
	var target_inside_guard_zone: bool = guard_radius_feet <= 0 or target_distance_from_guard_anchor_feet <= guard_radius_feet
	var actor_outside_leash: bool = pursuit_leash_feet > 0 and distance_from_guard_anchor_feet > pursuit_leash_feet
	if can_attack and not actor_outside_leash:
		scores[INTENT_ATTACK] = float(utility.get("attack", 100.0)) * lerpf(0.78, 1.12, aggression)
	if can_move and not tactical_retreat and target_visible and target_inside_guard_zone and not actor_outside_leash and distance_feet > attack_range_feet:
		scores[INTENT_INTERCEPT] = float(utility.get("intercept", 82.0)) + minf(float(distance_feet - attack_range_feet), 30.0) * 0.8
	elif can_move and not tactical_retreat and not target_visible and has_target_memory and target_inside_guard_zone and not actor_outside_leash:
		scores[INTENT_SEARCH] = float(utility.get("search", 66.0)) + memory_confidence * 24.0
	if can_move and not tactical_retreat and (actor_outside_leash or (not target_inside_guard_zone and distance_from_guard_anchor_feet > guard_return_tolerance_feet)):
		scores[INTENT_GUARD] = float(utility.get("guard", 66.0)) + float(distance_from_guard_anchor_feet) * 1.2


func _calculate_morale_pressure(ally_count: int, hostile_count: int, defeated_ally_count: int, escape_route_count: int) -> float:
	var numerical_pressure: float = clampf(float(hostile_count - ally_count) * 0.22, 0.0, 0.55)
	var casualty_pressure: float = clampf(float(defeated_ally_count) * 0.18, 0.0, 0.45)
	var trapped_pressure: float = 0.25 if escape_route_count <= 0 else (0.1 if escape_route_count == 1 else 0.0)
	return clampf(numerical_pressure + casualty_pressure + trapped_pressure, 0.0, 1.0)


func _reason_for_role_intent(intent: String, role_id: String) -> String:
	match intent:
		INTENT_ATTACK: return "Роль %s может атаковать цель с текущей позиции." % role_id
		INTENT_ADVANCE: return "Роль %s сокращает дистанцию и ищет позицию для атаки." % role_id
		INTENT_RETREAT: return "Здоровье или мораль NPC ниже безопасного порога."
		INTENT_REPOSITION: return "Стрелок увеличивает дистанцию до безопасного диапазона."
		INTENT_INTERCEPT: return "Защитник перехватывает цель внутри охраняемой зоны."
		INTENT_SEARCH: return "NPC движется к последней подтверждённой позиции цели."
		INTENT_GUARD: return "Защитник возвращается к закреплённой позиции."
		_: return "Роль %s не располагает подтверждённой целью или полезным действием." % role_id


func _merge_profiles(base_profile: Dictionary, overrides: Dictionary) -> Dictionary:
	var result: Dictionary = base_profile.duplicate(true)
	for key_value: Variant in overrides.keys():
		var key: String = str(key_value)
		var override_value: Variant = overrides[key_value]
		if key in ["utility", "position_weights"] and override_value is Dictionary:
			var merged_dictionary: Dictionary = result.get(key, {}) as Dictionary if result.get(key, {}) is Dictionary else {}
			merged_dictionary = merged_dictionary.duplicate(true)
			merged_dictionary.merge((override_value as Dictionary).duplicate(true), true)
			result[key] = merged_dictionary
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
