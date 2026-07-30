class_name SquadTacticalPlanSystem
extends RefCounted

const DATA_PATH: String = "res://data/ai/squad_tactical_plans.json"
const BLOCKED_SCORE: float = -1000000.0

const PLAN_RESCUE_BOUND_ALLY: String = "rescue_bound_ally"
const PLAN_ORDERLY_WITHDRAWAL: String = "orderly_withdrawal"
const PLAN_HOLD_CHOKEPOINT: String = "hold_chokepoint"
const PLAN_SUPPRESS_AND_FLANK: String = "suppress_and_flank"
const PLAN_SECTOR_SEARCH: String = "sector_search"
const PLAN_COORDINATED_ASSAULT: String = "coordinated_assault"

const DEFAULT_PLAN_ORDER: Array[String] = [
	PLAN_RESCUE_BOUND_ALLY,
	PLAN_ORDERLY_WITHDRAWAL,
	PLAN_HOLD_CHOKEPOINT,
	PLAN_SUPPRESS_AND_FLANK,
	PLAN_SECTOR_SEARCH,
	PLAN_COORDINATED_ASSAULT
]

var _plan_order: Array[String] = []
var _plans: Dictionary = {}
var _role_profiles: Dictionary = {}
var _actor_profiles: Dictionary = {}
var _active_plans: Dictionary = {}
var _actor_failures: Dictionary = {}


func _init() -> void:
	_load_profiles()


func evaluate_squad_plan(squad_id: String, round_number: int, context: Dictionary) -> Dictionary:
	if squad_id.is_empty():
		return {}
	var existing_value: Variant = _active_plans.get(squad_id, {})
	var existing: Dictionary = existing_value as Dictionary if existing_value is Dictionary else {}
	if not existing.is_empty() and round_number <= int(existing.get("expires_round", -1)) and _plan_still_valid(str(existing.get("plan_id", "")), context):
		existing["phase"] = _phase_for(existing, round_number)
		_active_plans[squad_id] = existing
		return existing.duplicate(true)

	var selected_plan_id: String = _select_plan(context)
	if selected_plan_id.is_empty():
		_active_plans.erase(squad_id)
		return {}
	var plan_profile: Dictionary = _dictionary_copy(_plans.get(selected_plan_id, {}))
	var duration: int = maxi(int(plan_profile.get("duration_rounds", 2)), 1)
	var plan: Dictionary = {
		"squad_id": squad_id,
		"plan_id": selected_plan_id,
		"started_round": round_number,
		"expires_round": round_number + duration - 1,
		"duration_rounds": duration,
		"score": _plan_score(selected_plan_id, context),
		"phase": "setup",
		"source_event_id": str(context.get("environment_event_id", ""))
	}
	_active_plans[squad_id] = plan.duplicate(true)
	return plan


func get_actor_assignment(squad_id: String, actor_id: String, role_id: String, actor_index: int, round_number: int) -> Dictionary:
	var plan_value: Variant = _active_plans.get(squad_id, {})
	if not plan_value is Dictionary:
		return {}
	var plan: Dictionary = plan_value as Dictionary
	if plan.is_empty() or round_number > int(plan.get("expires_round", -1)):
		return {}
	var plan_profile: Dictionary = _dictionary_copy(_plans.get(str(plan.get("plan_id", "")), {}))
	var assignments_value: Variant = plan_profile.get("assignments", {})
	if not assignments_value is Dictionary:
		return {}
	var assignments: Dictionary = assignments_value as Dictionary
	var assignment: Dictionary = _dictionary_copy(assignments.get(role_id, assignments.get("melee", {})))
	if assignment.is_empty():
		return {}
	var actor_profile: Dictionary = get_actor_plan_profile(actor_id, role_id)
	var slots: Array[String] = _string_array(assignment.get("slots", []))
	var slot: String = slots[posmod(actor_index, slots.size())] if not slots.is_empty() else "front"
	var action: String = str(assignment.get("action", ""))
	var failure_count: int = get_actor_failure_count(squad_id, actor_id, action, round_number)
	var tolerance: int = maxi(int(actor_profile.get("failure_tolerance", 2)), 0)
	var commitment: float = clampf(float(actor_profile.get("plan_commitment", 0.75)), 0.0, 1.0)
	var score: float = float(assignment.get("score", 100.0)) + float(plan.get("score", 0.0)) * commitment * 0.12
	score -= float(failure_count) * 28.0

	if failure_count > tolerance:
		assignment["action"] = "recover_after_failure"
		assignment["intent"] = "dodge" if role_id in ["ranged", "caster"] else "regroup"
		assignment["objective"] = "nearest_ally"
		score = maxf(score, 74.0)

	assignment["score"] = score
	assignment["slot"] = slot
	assignment["plan_id"] = str(plan.get("plan_id", ""))
	assignment["plan_phase"] = _phase_for(plan, round_number)
	assignment["squad_id"] = squad_id
	assignment["actor_id"] = actor_id
	assignment["failure_count"] = failure_count
	assignment["reservation_spacing_feet"] = maxi(int(actor_profile.get("reservation_spacing_feet", 5)), 0)
	return assignment


func get_actor_plan_profile(actor_id: String, role_id: String) -> Dictionary:
	var role_profile: Dictionary = _dictionary_copy(_role_profiles.get(role_id, {}))
	var actor_profile: Dictionary = _dictionary_copy(_actor_profiles.get(actor_id, {}))
	role_profile.merge(actor_profile, true)
	return role_profile


func record_actor_outcome(squad_id: String, actor_id: String, action_id: String, round_number: int, success: bool) -> void:
	if squad_id.is_empty() or actor_id.is_empty() or action_id.is_empty():
		return
	var key: String = _failure_key(squad_id, actor_id, action_id)
	if success:
		_actor_failures.erase(key)
		return
	var value: Variant = _actor_failures.get(key, {})
	var record: Dictionary = value as Dictionary if value is Dictionary else {}
	record["count"] = maxi(int(record.get("count", 0)), 0) + 1
	record["last_round"] = round_number
	_actor_failures[key] = record


func get_actor_failure_count(squad_id: String, actor_id: String, action_id: String, round_number: int) -> int:
	var key: String = _failure_key(squad_id, actor_id, action_id)
	var value: Variant = _actor_failures.get(key, {})
	if not value is Dictionary:
		return 0
	var record: Dictionary = value as Dictionary
	if round_number - int(record.get("last_round", round_number)) > 3:
		_actor_failures.erase(key)
		return 0
	return maxi(int(record.get("count", 0)), 0)


func get_active_plan(squad_id: String) -> Dictionary:
	var value: Variant = _active_plans.get(squad_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func clear() -> void:
	_active_plans.clear()
	_actor_failures.clear()


func _select_plan(context: Dictionary) -> String:
	var selected: String = ""
	var selected_score: float = BLOCKED_SCORE
	for plan_id: String in _plan_order:
		var score: float = _plan_score(plan_id, context)
		if score > selected_score + 0.0001:
			selected = plan_id
			selected_score = score
	return selected if selected_score > BLOCKED_SCORE * 0.5 else ""


func _plan_score(plan_id: String, context: Dictionary) -> float:
	var profile: Dictionary = _dictionary_copy(_plans.get(plan_id, {}))
	if profile.is_empty():
		return BLOCKED_SCORE
	var base_score: float = float(profile.get("base_score", 100.0))
	var ally_count: int = maxi(int(context.get("ally_count", 1)), 0)
	var casualty_count: int = maxi(int(context.get("casualty_count", 0)), 0)
	var health_ratio: float = clampf(float(context.get("average_health_ratio", 1.0)), 0.0, 1.0)
	var morale: float = clampf(float(context.get("average_morale", 1.0)), 0.0, 1.0)
	var target_visible: bool = bool(context.get("target_visible", false))
	var target_memory: bool = bool(context.get("has_target_memory", false))
	match plan_id:
		PLAN_RESCUE_BOUND_ALLY:
			return base_score + float(ally_count) * 5.0 if bool(context.get("bound_ally_visible", false)) and ally_count > 1 else BLOCKED_SCORE
		PLAN_ORDERLY_WITHDRAWAL:
			if casualty_count >= 2 or health_ratio <= 0.35 or morale <= 0.32:
				return base_score + float(casualty_count) * 18.0 + (1.0 - health_ratio) * 50.0
			return BLOCKED_SCORE
		PLAN_HOLD_CHOKEPOINT:
			return base_score + 20.0 if bool(context.get("passage_relevant", false)) and bool(context.get("has_defender", false)) else BLOCKED_SCORE
		PLAN_SUPPRESS_AND_FLANK:
			var combined_arms: bool = bool(context.get("has_melee", false)) and (bool(context.get("has_ranged", false)) or bool(context.get("has_caster", false)))
			return base_score + float(int(context.get("flank_route_count", 0))) * 8.0 if target_visible and ally_count >= 3 and combined_arms else BLOCKED_SCORE
		PLAN_SECTOR_SEARCH:
			return base_score + float(ally_count) * 4.0 if not target_visible and target_memory and ally_count >= 2 else BLOCKED_SCORE
		PLAN_COORDINATED_ASSAULT:
			return base_score + float(ally_count) * 6.0 if target_visible and ally_count >= 2 else BLOCKED_SCORE
		_:
			return BLOCKED_SCORE


func _plan_still_valid(plan_id: String, context: Dictionary) -> bool:
	match plan_id:
		PLAN_RESCUE_BOUND_ALLY:
			return bool(context.get("bound_ally_visible", false))
		PLAN_ORDERLY_WITHDRAWAL:
			return int(context.get("casualty_count", 0)) >= 1 or float(context.get("average_health_ratio", 1.0)) <= 0.55
		PLAN_HOLD_CHOKEPOINT:
			return bool(context.get("passage_relevant", false))
		PLAN_SUPPRESS_AND_FLANK, PLAN_COORDINATED_ASSAULT:
			return bool(context.get("target_visible", false)) or bool(context.get("has_target_memory", false))
		PLAN_SECTOR_SEARCH:
			return bool(context.get("has_target_memory", false)) and not bool(context.get("target_visible", false))
		_:
			return false


func _phase_for(plan: Dictionary, round_number: int) -> String:
	var age: int = maxi(round_number - int(plan.get("started_round", round_number)), 0)
	var duration: int = maxi(int(plan.get("duration_rounds", 1)), 1)
	if age <= 0:
		return "setup"
	if age >= duration - 1:
		return "consolidate"
	return "execute"


func _failure_key(squad_id: String, actor_id: String, action_id: String) -> String:
	return "%s|%s|%s" % [squad_id, actor_id, action_id]


func _dictionary_copy(value: Variant) -> Dictionary:
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func _string_array(value: Variant) -> Array[String]:
	var result: Array[String] = []
	if value is Array:
		for entry: Variant in value:
			result.append(str(entry))
	return result


func _load_profiles() -> void:
	_plan_order = DEFAULT_PLAN_ORDER.duplicate()
	_plans.clear()
	_role_profiles.clear()
	_actor_profiles.clear()
	if not FileAccess.file_exists(DATA_PATH):
		return
	var file: FileAccess = FileAccess.open(DATA_PATH, FileAccess.READ)
	if file == null:
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		return
	var data: Dictionary = parsed as Dictionary
	var order: Array[String] = _string_array(data.get("plan_order", []))
	if not order.is_empty():
		_plan_order = order
	_plans = _dictionary_copy(data.get("plans", {}))
	_role_profiles = _dictionary_copy(data.get("role_profiles", {}))
	_actor_profiles = _dictionary_copy(data.get("profiles", {}))
