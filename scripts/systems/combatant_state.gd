class_name CombatantState
extends RefCounted

const VALID_CONDITIONS: Array[String] = [
	"blinded", "charmed", "deafened", "exhaustion", "frightened", "grappled",
	"incapacitated", "invisible", "paralyzed", "petrified", "poisoned", "prone",
	"restrained", "stunned", "unconscious"
]

var conditions: Dictionary = {}
var condition_immunities: Array[String] = []
var damage_resistances: Array[String] = []
var damage_immunities: Array[String] = []
var damage_vulnerabilities: Array[String] = []
var temporary_hit_points: int = 0
var death_save_successes: int = 0
var death_save_failures: int = 0
var stable: bool = false
var dead: bool = false
var concentrating_on: String = ""
var concentration_source_id: int = 0
var hidden: bool = false
var helped_attack: bool = false
var readied_attack: bool = false
var grappled_by_id: int = 0
var grappling_target_id: int = 0


func add_condition(
	condition_id: String,
	duration_rounds: int = -1,
	source_id: int = 0,
	save_ability: String = "",
	save_dc: int = 0,
	end_timing: String = "end_turn"
) -> bool:
	if condition_id not in VALID_CONDITIONS or condition_id in condition_immunities:
		return false
	if condition_id == "exhaustion":
		var current_level: int = int(conditions.get("exhaustion", {}).get("level", 0))
		conditions["exhaustion"] = {"level": clampi(current_level + 1, 1, 6)}
		return true
	conditions[condition_id] = {
		"remaining_rounds": duration_rounds,
		"source_id": source_id,
		"save_ability": save_ability,
		"save_dc": save_dc,
		"end_timing": end_timing
	}
	return true


func remove_condition(condition_id: String) -> bool:
	if not conditions.has(condition_id):
		return false
	conditions.erase(condition_id)
	if condition_id == "grappled":
		grappled_by_id = 0
	return true


func has_condition(condition_id: String) -> bool:
	return conditions.has(condition_id)


func get_condition_ids() -> Array[String]:
	var result: Array[String] = []
	for value: Variant in conditions.keys():
		result.append(str(value))
	return result


func get_exhaustion_level() -> int:
	return clampi(int(conditions.get("exhaustion", {}).get("level", 0)), 0, 6)


func reduce_exhaustion(amount: int = 1) -> void:
	var next_level: int = maxi(get_exhaustion_level() - maxi(amount, 1), 0)
	if next_level <= 0:
		conditions.erase("exhaustion")
	else:
		conditions["exhaustion"] = {"level": next_level}


func tick_conditions(timing: String) -> Array[String]:
	var expired: Array[String] = []
	for value: Variant in conditions.keys():
		var condition_id: String = str(value)
		if condition_id == "exhaustion":
			continue
		var data: Dictionary = conditions.get(condition_id, {}) as Dictionary
		if str(data.get("end_timing", "end_turn")) != timing:
			continue
		var remaining: int = int(data.get("remaining_rounds", -1))
		if remaining < 0:
			continue
		remaining -= 1
		if remaining <= 0:
			expired.append(condition_id)
		else:
			data["remaining_rounds"] = remaining
			conditions[condition_id] = data
	for condition_id: String in expired:
		remove_condition(condition_id)
	return expired


func set_concentration(effect_id: String, source_id: int = 0) -> void:
	concentrating_on = effect_id
	concentration_source_id = source_id


func clear_concentration() -> String:
	var previous: String = concentrating_on
	concentrating_on = ""
	concentration_source_id = 0
	return previous


func reset_death_saves() -> void:
	death_save_successes = 0
	death_save_failures = 0
	stable = false
	dead = false


func enter_dying() -> void:
	stable = false
	dead = false
	death_save_successes = 0
	death_save_failures = 0
	add_condition("unconscious")
	add_condition("incapacitated")
	clear_concentration()


func recover_from_zero_hit_points() -> void:
	remove_condition("unconscious")
	remove_condition("incapacitated")
	reset_death_saves()


func to_dict() -> Dictionary:
	return {
		"conditions": conditions.duplicate(true),
		"condition_immunities": condition_immunities.duplicate(),
		"damage_resistances": damage_resistances.duplicate(),
		"damage_immunities": damage_immunities.duplicate(),
		"damage_vulnerabilities": damage_vulnerabilities.duplicate(),
		"temporary_hit_points": temporary_hit_points,
		"death_save_successes": death_save_successes,
		"death_save_failures": death_save_failures,
		"stable": stable,
		"dead": dead,
		"concentrating_on": concentrating_on
	}


static func from_dict(data: Dictionary) -> CombatantState:
	var state := CombatantState.new()
	var conditions_value: Variant = data.get("conditions", {})
	state.conditions = (conditions_value as Dictionary).duplicate(true) if conditions_value is Dictionary else {}
	state.condition_immunities = _string_array(data.get("condition_immunities", []))
	state.damage_resistances = _string_array(data.get("damage_resistances", []))
	state.damage_immunities = _string_array(data.get("damage_immunities", []))
	state.damage_vulnerabilities = _string_array(data.get("damage_vulnerabilities", []))
	state.temporary_hit_points = maxi(int(data.get("temporary_hit_points", 0)), 0)
	state.death_save_successes = clampi(int(data.get("death_save_successes", 0)), 0, 3)
	state.death_save_failures = clampi(int(data.get("death_save_failures", 0)), 0, 3)
	state.stable = bool(data.get("stable", false))
	state.dead = bool(data.get("dead", false))
	state.concentrating_on = str(data.get("concentrating_on", ""))
	return state


static func _string_array(value: Variant) -> Array[String]:
	var result: Array[String] = []
	if value is Array:
		for item: Variant in value:
			result.append(str(item))
	return result
