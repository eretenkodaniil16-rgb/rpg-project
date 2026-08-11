class_name NpcTacticalTargetingSystem
extends RefCounted

const DATA_PATH: String = "res://data/ai/npc_tactical_targeting_v2.json"
const BLOCKED_SCORE: float = -1000000.0

var _config: Dictionary = {}
var _weights: Dictionary = {}


func _init() -> void:
	_load_config()


func choose_target(candidates: Array[Dictionary], previous_target_id: int = 0) -> Dictionary:
	if candidates.is_empty():
		return {}
	var selected: Dictionary = {}
	var selected_score: float = BLOCKED_SCORE
	var previous: Dictionary = {}
	var previous_score: float = BLOCKED_SCORE

	for candidate_value: Dictionary in candidates:
		var candidate: Dictionary = candidate_value.duplicate(true)
		var score: float = score_target(candidate)
		candidate["utility_score"] = score
		var target_id: int = int(candidate.get("target_id", 0))
		if target_id == previous_target_id:
			previous = candidate.duplicate(true)
			previous_score = score
		if _candidate_is_better(candidate, score, selected, selected_score):
			selected = candidate.duplicate(true)
			selected_score = score

	if not previous.is_empty():
		var hysteresis: float = maxf(float(_config.get("target_switch_hysteresis", 24.0)), 0.0)
		if previous_score >= selected_score - hysteresis:
			return previous
	return selected


func score_target(context: Dictionary) -> float:
	if not bool(context.get("available", true)) or not bool(context.get("visible", false)):
		return BLOCKED_SCORE
	var score: float = _weight("base", 100.0)
	if bool(context.get("visible", false)):
		score += _weight("visible", 65.0)
	if bool(context.get("attack_ready", false)):
		score += _weight("attack_ready", 185.0)

	var health_ratio: float = clampf(float(context.get("health_ratio", 1.0)), 0.0, 1.0)
	score += (1.0 - health_ratio) * _weight("health_vulnerability", 62.0)
	var distance_feet: int = maxi(int(context.get("distance_feet", 0)), 0)
	score += float(distance_feet) * _weight("distance", -0.22)

	var preferred_range: int = maxi(int(context.get("preferred_range_feet", 5)), 0)
	score += float(absi(distance_feet - preferred_range)) * _weight("range_error", -1.45)
	if bool(context.get("previous_target", false)):
		score += _weight("previous_target", 34.0)
	var claim_count: int = maxi(int(context.get("claim_count", 0)), 0)
	score += float(claim_count) * _weight("claim_penalty", -31.0)
	if bool(context.get("immediate_melee_threat", false)):
		score += _weight("immediate_melee_threat", 28.0)

	var full_tactics: bool = bool(context.get("full_tactics_supported", true))
	var role_id: String = str(context.get("role", "melee"))
	if full_tactics:
		score += _weight("full_tactics_capability", 20.0)
	elif role_id == "caster":
		score += _weight("limited_tactics_penalty_caster", -42.0)
	elif role_id == "ranged":
		score += _weight("limited_tactics_penalty_ranged", -10.0)
	return score


func _candidate_is_better(
	candidate: Dictionary,
	score: float,
	selected: Dictionary,
	selected_score: float
) -> bool:
	if selected.is_empty() or score > selected_score + 0.0001:
		return true
	if not is_equal_approx(score, selected_score):
		return false
	var candidate_id: int = int(candidate.get("target_id", 0))
	var selected_id: int = int(selected.get("target_id", 0))
	return candidate_id < selected_id


func _weight(weight_id: String, fallback: float) -> float:
	return float(_weights.get(weight_id, fallback))


func _load_config() -> void:
	_config.clear()
	_weights.clear()
	if not FileAccess.file_exists(DATA_PATH):
		return
	var file: FileAccess = FileAccess.open(DATA_PATH, FileAccess.READ)
	if file == null:
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		return
	_config = (parsed as Dictionary).duplicate(true)
	var weights_value: Variant = _config.get("weights", {})
	if weights_value is Dictionary:
		_weights = (weights_value as Dictionary).duplicate(true)
