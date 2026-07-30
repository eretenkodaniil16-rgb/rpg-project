class_name AdvancedNpcCombatAiSystem
extends NpcCombatAiSystem

const ADVANCED_DATA_PATH: String = "res://data/ai/npc_advanced_tactics.json"

const ROLE_CASTER: String = "caster"

const INTENT_CAST_SPELL: String = "cast_spell"
const INTENT_TAKE_COVER: String = "take_cover"
const INTENT_DODGE: String = "dodge"
const INTENT_SHOVE: String = "shove"
const INTENT_RALLY: String = "rally"
const INTENT_REGROUP: String = "regroup"

const ADVANCED_INTENT_ORDER: Array[String] = [
	INTENT_RALLY,
	INTENT_CAST_SPELL,
	INTENT_SHOVE,
	INTENT_TAKE_COVER,
	INTENT_REGROUP,
	INTENT_DODGE
]

var _advanced_role_profiles: Dictionary = {}
var _advanced_actor_profiles: Dictionary = {}


func _init() -> void:
	super._init()
	_load_advanced_profiles()


func get_profile(actor_id: String) -> Dictionary:
	var base_profile: Dictionary = super.get_profile(actor_id)
	var actor_advanced: Dictionary = _dictionary_copy(_advanced_actor_profiles.get(actor_id, {}))
	var role_id: String = str(actor_advanced.get("role", base_profile.get("role", ROLE_MELEE)))
	var advanced_role: Dictionary = _dictionary_copy(_advanced_role_profiles.get(role_id, {}))
	var result: Dictionary = base_profile.duplicate(true)
	if result.is_empty() and role_id == ROLE_CASTER:
		result = advanced_role.duplicate(true)
	else:
		result = _merge_advanced(result, advanced_role)
	result = _merge_advanced(result, actor_advanced)
	if not result.is_empty():
		result["role"] = role_id
		result["actor_id"] = actor_id
	return result


func get_advanced_role_profile(role_id: String) -> Dictionary:
	return _dictionary_copy(_advanced_role_profiles.get(role_id, {}))


func choose_combat_intent(actor_id: String, context: Dictionary) -> Dictionary:
	var profile: Dictionary = get_profile(actor_id)
	if profile.is_empty():
		return super.choose_combat_intent(actor_id, context)
	var role_id: String = str(profile.get("role", ROLE_MELEE))
	var selected: Dictionary = _choose_caster_baseline(profile, context) if role_id == ROLE_CASTER else super.choose_combat_intent(actor_id, context)
	return _choose_tactical_override(profile, context, selected)


func score_candidate_position(intent_id: String, profile: Dictionary, context: Dictionary, candidate: Dictionary) -> float:
	var role_id: String = str(profile.get("role", ROLE_MELEE))
	if intent_id in [INTENT_TAKE_COVER, INTENT_REGROUP, INTENT_CAST_SPELL] or role_id == ROLE_CASTER:
		return _score_advanced_position(intent_id, profile, candidate)
	return super.score_candidate_position(intent_id, profile, context, candidate)


func _choose_caster_baseline(profile: Dictionary, context: Dictionary) -> Dictionary:
	var distance_feet: int = maxi(int(context.get("distance_feet", 0)), 0)
	var visible: bool = bool(context.get("target_visible", false))
	var memory: bool = bool(context.get("has_target_memory", false))
	var can_move: bool = bool(context.get("can_move", true))
	var health_ratio: float = clampf(float(context.get("actor_health_ratio", 1.0)), 0.0, 1.0)
	var minimum_range: int = maxi(int(profile.get("minimum_range_feet", 20)), 0)
	var retreat_threshold: float = clampf(float(profile.get("retreat_health_ratio", 0.28)), 0.0, 1.0)
	var intent: String = INTENT_WAIT
	var score: float = float((profile.get("utility", {}) as Dictionary).get("wait", 5.0))
	if health_ratio <= retreat_threshold and can_move:
		intent = INTENT_RETREAT
		score = 145.0
	elif visible and distance_feet < minimum_range and can_move:
		intent = INTENT_REPOSITION
		score = 132.0 + float(minimum_range - distance_feet)
	elif visible:
		intent = INTENT_CAST_SPELL
		score = float(context.get("spell_plan_score", BLOCKED_SCORE))
	elif memory and can_move:
		intent = INTENT_SEARCH
		score = 84.0 + float(context.get("memory_confidence", 0.0)) * 24.0
	return _decision(intent, score, role_id(profile), profile, "Заклинатель выбирает безопасную позицию и подходящее заклинание.")


func _choose_tactical_override(profile: Dictionary, context: Dictionary, baseline: Dictionary) -> Dictionary:
	var allowed: Array[String] = _string_array(profile.get("tactical_actions", []))
	var candidates: Dictionary = {}
	var new_casualty: bool = bool(context.get("new_casualty_seen", false))
	var casualty_count: int = maxi(int(context.get("casualty_count", 0)), 0)
	var leadership: float = clampf(float(profile.get("leadership", 0.0)), 0.0, 1.0)
	var rally_active: bool = bool(context.get("rally_active", false))
	var ally_count: int = maxi(int(context.get("ally_count", 1)), 1)
	var health_ratio: float = clampf(float(context.get("actor_health_ratio", 1.0)), 0.0, 1.0)
	var role: String = role_id(profile)

	if "rally" in allowed and new_casualty and not rally_active and ally_count > 1 and leadership >= 0.55:
		candidates[INTENT_RALLY] = 138.0 + leadership * 30.0 + float(casualty_count) * 5.0
	if "cast_spell" in allowed and float(context.get("spell_plan_score", BLOCKED_SCORE)) > BLOCKED_SCORE * 0.5:
		candidates[INTENT_CAST_SPELL] = float(context.get("spell_plan_score", BLOCKED_SCORE))
	if "shove" in allowed and bool(context.get("can_shove", false)) and not bool(context.get("target_prone", false)):
		var shove_preference: float = clampf(float(profile.get("shove_preference", 0.0)), 0.0, 1.0)
		candidates[INTENT_SHOVE] = 82.0 + shove_preference * 42.0 + (18.0 if bool(context.get("target_near_hazard", false)) else 0.0)
	if "take_cover" in allowed and bool(context.get("better_cover_available", false)):
		var cover_preference: float = clampf(float(profile.get("cover_preference", 0.0)), 0.0, 1.0)
		candidates[INTENT_TAKE_COVER] = 70.0 + cover_preference * 48.0 + (18.0 if role in [ROLE_RANGED, ROLE_CASTER] else 0.0)
	if "regroup" in allowed and ally_count > 1 and int(context.get("nearest_ally_distance_feet", 0)) > 25 and (new_casualty or health_ratio < 0.55):
		candidates[INTENT_REGROUP] = 88.0 + float(casualty_count) * 6.0
	if "dodge" in allowed and bool(context.get("can_dodge", true)) and (bool(context.get("no_useful_attack", false)) or bool(context.get("no_safe_retreat", false))):
		candidates[INTENT_DODGE] = 78.0 + (30.0 if health_ratio < 0.45 else 0.0)

	var selected: Dictionary = baseline.duplicate(true)
	var selected_score: float = float(selected.get("score", BLOCKED_SCORE))
	for intent_id: String in ADVANCED_INTENT_ORDER:
		var tactical_score: float = float(candidates.get(intent_id, BLOCKED_SCORE))
		if tactical_score > selected_score + 0.0001:
			selected = _decision(intent_id, tactical_score, role, profile, _advanced_reason(intent_id, new_casualty))
			selected_score = tactical_score
	return selected


func _score_advanced_position(intent_id: String, profile: Dictionary, candidate: Dictionary) -> float:
	if not bool(candidate.get("valid", true)):
		return BLOCKED_SCORE
	var weights: Dictionary = profile.get("position_weights", {}) as Dictionary if profile.get("position_weights", {}) is Dictionary else {}
	var preferred: int = maxi(int(profile.get("preferred_range_feet", 35)), 0)
	var minimum: int = maxi(int(profile.get("minimum_range_feet", 0)), 0)
	var distance: int = maxi(int(candidate.get("distance_feet", 0)), 0)
	var objective_distance: int = maxi(int(candidate.get("distance_to_objective_feet", distance)), 0)
	var ally_distance: int = maxi(int(candidate.get("nearest_ally_distance_feet", 9999)), 0)
	var spacing: int = maxi(int(profile.get("spacing_feet", 5)), 0)
	var mobility: int = maxi(int(candidate.get("mobility", 0)), 0)
	var path_cost: int = maxi(int(candidate.get("path_cost_feet", 0)), 0)
	var cover_bonus: int = maxi(int(candidate.get("cover_bonus", 0)), 0)
	var visible: bool = bool(candidate.get("target_visible", false))
	var spell_score: float = float(candidate.get("spell_plan_score", BLOCKED_SCORE))
	var score: float = float(mobility) * float(weights.get("mobility", 1.5)) - float(path_cost) * float(weights.get("movement_cost", 0.06))
	if spacing > 0 and ally_distance < spacing:
		score -= float(spacing - ally_distance) * float(weights.get("ally_spacing", 2.0))
	match intent_id:
		INTENT_CAST_SPELL:
			if spell_score <= BLOCKED_SCORE * 0.5:
				return BLOCKED_SCORE
			score += spell_score
			score -= absf(float(distance - preferred)) * float(weights.get("range_error", 1.0))
			score += float(cover_bonus) * float(weights.get("cover", 16.0))
		INTENT_TAKE_COVER:
			score += float(cover_bonus) * 34.0
			score -= absf(float(distance - preferred)) * 0.8
			if visible:
				score += 18.0
		INTENT_REGROUP:
			score -= absf(float(ally_distance - maxi(spacing, 10))) * 2.0
			score -= float(objective_distance) * 0.2
		INTENT_REPOSITION:
			if distance < minimum:
				score += float(distance) * 3.0
			else:
				score -= absf(float(distance - preferred)) * 1.4
			score += float(cover_bonus) * 12.0
		INTENT_ADVANCE, INTENT_SEARCH:
			score -= float(objective_distance) * 1.35
			score += float(cover_bonus) * 8.0
		_:
			return super.score_candidate_position(intent_id, profile, {}, candidate)
	return score


func _decision(intent: String, score: float, role: String, profile: Dictionary, reason: String) -> Dictionary:
	return {
		"intent": intent,
		"score": score,
		"role": role,
		"reason": reason,
		"attack_range_feet": int(profile.get("attack_range_feet", DistanceSystem.MELEE_REACH_FEET)),
		"minimum_range_feet": int(profile.get("minimum_range_feet", 0)),
		"preferred_range_feet": int(profile.get("preferred_range_feet", DistanceSystem.MELEE_REACH_FEET))
	}


func _advanced_reason(intent_id: String, casualty: bool) -> String:
	match intent_id:
		INTENT_CAST_SPELL: return "Маг выбирает заклинание и точку применения без риска для союзников."
		INTENT_TAKE_COVER: return "NPC меняет позицию, чтобы использовать укрытие и сохранить линию давления."
		INTENT_DODGE: return "NPC отказывается от слабой атаки и сосредотачивается на защите."
		INTENT_SHOVE: return "NPC пытается лишить героя выгодной стойки толчком."
		INTENT_RALLY: return "NPC реагирует на потерю союзника и восстанавливает строй отряда."
		INTENT_REGROUP: return "NPC сближается с союзниками вместо изолированной атаки."
		_: return "Тактическое действие выбрано по utility-оценке."


func role_id(profile: Dictionary) -> String:
	return str(profile.get("role", ROLE_MELEE))


func _merge_advanced(base: Dictionary, override: Dictionary) -> Dictionary:
	var result: Dictionary = base.duplicate(true)
	for key_value: Variant in override.keys():
		var key: String = str(key_value)
		var value: Variant = override[key_value]
		if key in ["utility", "position_weights"] and value is Dictionary:
			var nested: Dictionary = _dictionary_copy(result.get(key, {}))
			nested.merge((value as Dictionary).duplicate(true), true)
			result[key] = nested
		else:
			result[key] = value
	return result


func _dictionary_copy(value: Variant) -> Dictionary:
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func _string_array(value: Variant) -> Array[String]:
	var result: Array[String] = []
	if value is Array:
		for entry: Variant in value:
			result.append(str(entry))
	return result


func _load_advanced_profiles() -> void:
	_advanced_role_profiles.clear()
	_advanced_actor_profiles.clear()
	if not FileAccess.file_exists(ADVANCED_DATA_PATH):
		return
	var file: FileAccess = FileAccess.open(ADVANCED_DATA_PATH, FileAccess.READ)
	if file == null:
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		return
	var data: Dictionary = parsed as Dictionary
	_advanced_role_profiles = _dictionary_copy(data.get("role_profiles", {}))
	_advanced_actor_profiles = _dictionary_copy(data.get("profiles", {}))
