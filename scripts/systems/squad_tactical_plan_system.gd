class_name SquadTacticalPlanSystem
extends RefCounted

const DATA_PATH: String = "res://data/ai/squad_tactical_plans.json"
const BLOCKED_SCORE: float = -1000000.0

const PLAN_RESCUE_BOUND_ALLY: String = "rescue_bound_ally"
const PLAN_ORDERLY_WITHDRAWAL: String = "orderly_withdrawal"
const PLAN_CASUALTY_REGROUP: String = "casualty_regroup"
const PLAN_PROTECT_WOUNDED_ALLY: String = "protect_wounded_ally"
const PLAN_HOLD_CHOKEPOINT: String = "hold_chokepoint"
const PLAN_SUPPRESS_AND_FLANK: String = "suppress_and_flank"
const PLAN_SECTOR_SEARCH: String = "sector_search"
const PLAN_COORDINATED_ASSAULT: String = "coordinated_assault"

const DEFAULT_PLAN_ORDER: Array[String] = [
	PLAN_RESCUE_BOUND_ALLY,
	PLAN_ORDERLY_WITHDRAWAL,
	PLAN_CASUALTY_REGROUP,
	PLAN_PROTECT_WOUNDED_ALLY,
	PLAN_HOLD_CHOKEPOINT,
	PLAN_SUPPRESS_AND_FLANK,
	PLAN_SECTOR_SEARCH,
	PLAN_COORDINATED_ASSAULT
]

var _plan_order: Array[String] = []
var _plans: Dictionary = {}
var _role_profiles: Dictionary = {}
var _actor_profiles: Dictionary = {}
var _replanning: Dictionary = {}
var _active_plans: Dictionary = {}
var _actor_failures: Dictionary = {}


func _init() -> void:
	_load_profiles()


func evaluate_squad_plan(squad_id: String, round_number: int, context: Dictionary) -> Dictionary:
	if squad_id.is_empty():
		return {}
	var safe_round: int = maxi(round_number, 0)
	var existing_value: Variant = _active_plans.get(squad_id, {})
	var existing: Dictionary = existing_value as Dictionary if existing_value is Dictionary else {}
	var best: Dictionary = _best_plan(context)
	var selected_plan_id: String = str(best.get("plan_id", ""))
	var selected_score: float = float(best.get("score", BLOCKED_SCORE))

	if existing.is_empty():
		if selected_plan_id.is_empty():
			return {}
		return _activate_plan(squad_id, selected_plan_id, selected_score, safe_round, context, {}, "initial")

	var existing_plan_id: String = str(existing.get("plan_id", ""))
	var expired: bool = safe_round > int(existing.get("expires_round", -1))
	var still_valid: bool = _plan_still_valid(existing_plan_id, context)
	if expired or not still_valid:
		if selected_plan_id.is_empty():
			_active_plans.erase(squad_id)
			return {}
		return _activate_plan(
			squad_id,
			selected_plan_id,
			selected_score,
			safe_round,
			context,
			existing,
			"expired" if expired else "existing_invalid"
		)

	var existing_score: float = _plan_score(existing_plan_id, context)
	existing["score"] = existing_score
	existing["phase"] = _phase_for(existing, safe_round)
	_update_plan_focus(existing, context)

	if selected_plan_id.is_empty() or selected_plan_id == existing_plan_id:
		_active_plans[squad_id] = existing.duplicate(true)
		return existing.duplicate(true)

	if _should_switch_plan(existing, existing_score, selected_plan_id, selected_score, safe_round):
		return _activate_plan(
			squad_id,
			selected_plan_id,
			selected_score,
			safe_round,
			context,
			existing,
			_switch_reason(existing_plan_id, selected_plan_id)
		)

	_active_plans[squad_id] = existing.duplicate(true)
	return existing.duplicate(true)


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


func _activate_plan(
	squad_id: String,
	plan_id: String,
	score: float,
	round_number: int,
	context: Dictionary,
	previous: Dictionary,
	reason: String
) -> Dictionary:
	var plan_profile: Dictionary = _dictionary_copy(_plans.get(plan_id, {}))
	var duration: int = maxi(int(plan_profile.get("duration_rounds", 2)), 1)
	var previous_id: String = str(previous.get("plan_id", ""))
	var replan_count: int = maxi(int(previous.get("replan_count", 0)), 0)
	if not previous.is_empty():
		replan_count += 1
	var plan: Dictionary = {
		"squad_id": squad_id,
		"plan_id": plan_id,
		"started_round": round_number,
		"expires_round": round_number + duration - 1,
		"duration_rounds": duration,
		"score": score,
		"phase": "setup",
		"source_event_id": str(context.get("environment_event_id", "")),
		"interrupt_priority": _plan_interrupt_priority(plan_id),
		"last_switch_round": round_number,
		"previous_plan_id": previous_id,
		"replan_count": replan_count,
		"switch_reason": reason
	}
	_update_plan_focus(plan, context)
	_active_plans[squad_id] = plan.duplicate(true)
	return plan


func _best_plan(context: Dictionary) -> Dictionary:
	var selected: String = ""
	var selected_score: float = BLOCKED_SCORE
	var selected_priority: int = -1
	for plan_id: String in _plan_order:
		var score: float = _plan_score(plan_id, context)
		if score <= BLOCKED_SCORE * 0.5:
			continue
		var priority: int = _plan_interrupt_priority(plan_id)
		if priority > selected_priority or (priority == selected_priority and score > selected_score + 0.0001):
			selected = plan_id
			selected_score = score
			selected_priority = priority
	if selected.is_empty():
		return {}
	return {
		"plan_id": selected,
		"score": selected_score,
		"interrupt_priority": selected_priority
	}


func _select_plan(context: Dictionary) -> String:
	return str(_best_plan(context).get("plan_id", ""))


func _should_switch_plan(
	existing: Dictionary,
	existing_score: float,
	candidate_plan_id: String,
	candidate_score: float,
	round_number: int
) -> bool:
	var existing_plan_id: String = str(existing.get("plan_id", ""))
	var existing_priority: int = _plan_interrupt_priority(existing_plan_id)
	var candidate_priority: int = _plan_interrupt_priority(candidate_plan_id)
	if candidate_priority > existing_priority:
		return true
	if candidate_priority < existing_priority:
		return false
	var age: int = maxi(round_number - int(existing.get("started_round", round_number)), 0)
	var min_commitment: int = maxi(int(_replanning.get("min_commitment_rounds", 1)), 0)
	if age < min_commitment:
		return false
	var same_round: bool = round_number <= int(existing.get("last_switch_round", -1))
	var margin_key: String = "same_round_switch_score_margin" if same_round else "switch_score_margin"
	var margin: float = maxf(float(_replanning.get(margin_key, 20.0)), 0.0)
	return candidate_score >= existing_score + margin


func _switch_reason(existing_plan_id: String, candidate_plan_id: String) -> String:
	var existing_priority: int = _plan_interrupt_priority(existing_plan_id)
	var candidate_priority: int = _plan_interrupt_priority(candidate_plan_id)
	if candidate_priority > existing_priority:
		return "priority_interrupt"
	return "score_margin"


func _plan_interrupt_priority(plan_id: String) -> int:
	return maxi(int(_dictionary_copy(_plans.get(plan_id, {})).get("interrupt_priority", 0)), 0)


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
	var memory_confidence: float = clampf(float(context.get("memory_confidence", 0.0)), 0.0, 1.0)
	var wounded_count: int = maxi(int(context.get("wounded_ally_count", 0)), 0)
	var critical_count: int = maxi(int(context.get("critical_ally_count", 0)), 0)
	var lowest_health_ratio: float = clampf(float(context.get("lowest_health_ratio", 1.0)), 0.0, 1.0)
	match plan_id:
		PLAN_RESCUE_BOUND_ALLY:
			return base_score + float(ally_count) * 5.0 if bool(context.get("bound_ally_visible", false)) and ally_count > 1 else BLOCKED_SCORE
		PLAN_ORDERLY_WITHDRAWAL:
			if casualty_count >= 2 or health_ratio <= 0.35 or morale <= 0.32:
				return base_score + float(casualty_count) * 18.0 + (1.0 - health_ratio) * 50.0
			return BLOCKED_SCORE
		PLAN_CASUALTY_REGROUP:
			if bool(context.get("recent_casualty", false)) and casualty_count >= 1 and ally_count >= 2 and health_ratio > 0.35:
				return base_score + float(casualty_count) * 12.0 + (1.0 - health_ratio) * 24.0
			return BLOCKED_SCORE
		PLAN_PROTECT_WOUNDED_ALLY:
			if ally_count >= 2 and casualty_count < 2 and health_ratio > 0.35 and (critical_count >= 1 or (wounded_count >= 2 and lowest_health_ratio <= 0.4)):
				return base_score + float(critical_count) * 20.0 + float(wounded_count) * 6.0 + (1.0 - lowest_health_ratio) * 36.0
			return BLOCKED_SCORE
		PLAN_HOLD_CHOKEPOINT:
			return base_score + 20.0 if bool(context.get("passage_relevant", false)) and bool(context.get("has_defender", false)) else BLOCKED_SCORE
		PLAN_SUPPRESS_AND_FLANK:
			var combined_arms: bool = bool(context.get("has_melee", false)) and (bool(context.get("has_ranged", false)) or bool(context.get("has_caster", false)))
			return base_score + float(int(context.get("flank_route_count", 0))) * 8.0 if target_visible and ally_count >= 3 and combined_arms else BLOCKED_SCORE
		PLAN_SECTOR_SEARCH:
			return base_score + float(ally_count) * 4.0 + memory_confidence * 20.0 if not target_visible and target_memory and ally_count >= 2 else BLOCKED_SCORE
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
		PLAN_CASUALTY_REGROUP:
			return bool(context.get("recent_casualty", false)) and int(context.get("casualty_count", 0)) >= 1 and int(context.get("ally_count", 0)) >= 2
		PLAN_PROTECT_WOUNDED_ALLY:
			return int(context.get("critical_ally_count", 0)) >= 1 and int(context.get("ally_count", 0)) >= 2 and float(context.get("average_health_ratio", 1.0)) > 0.30
		PLAN_HOLD_CHOKEPOINT:
			return bool(context.get("passage_relevant", false))
		PLAN_SUPPRESS_AND_FLANK, PLAN_COORDINATED_ASSAULT:
			return bool(context.get("target_visible", false))
		PLAN_SECTOR_SEARCH:
			return bool(context.get("has_target_memory", false)) and not bool(context.get("target_visible", false))
		_:
			return false


func _update_plan_focus(plan: Dictionary, context: Dictionary) -> void:
	plan.erase("focus_actor_id")
	plan.erase("focus_position")
	match str(plan.get("plan_id", "")):
		PLAN_CASUALTY_REGROUP:
			plan["focus_actor_id"] = str(context.get("latest_casualty_actor_id", ""))
			if context.get("latest_casualty_position", null) is Vector2:
				plan["focus_position"] = context.get("latest_casualty_position") as Vector2
		PLAN_PROTECT_WOUNDED_ALLY:
			plan["focus_actor_id"] = str(context.get("wounded_ally_actor_id", ""))
			if context.get("wounded_ally_position", null) is Vector2:
				plan["focus_position"] = context.get("wounded_ally_position") as Vector2


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
	_replanning.clear()
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
	_replanning = _dictionary_copy(data.get("replanning", {}))