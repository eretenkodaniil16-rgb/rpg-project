class_name ExplorationStealthPerceptionSystem
extends RefCounted

const DATA_PATH: String = "res://data/ai/stealth_perception_v2.json"

const DEFAULT_HIDE_ENTRY_DC: int = 15
const DEFAULT_PERCEPTION_TICK_SECONDS: float = 0.125
const DEFAULT_ACTIVE_SEARCH_INTERVAL_SECONDS: float = 1.75
const DEFAULT_ACTIVE_SEARCH_MAX_DISTANCE_FEET: int = 45
const DEFAULT_MIN_AUTO_DETECTION_FEET: int = 5
const DEFAULT_MAX_AUTO_DETECTION_FEET: int = 20
const DEFAULT_FEET_REDUCTION_PER_MARGIN: int = 2
const DEFAULT_CONCEALED_AUTO_DETECTION_FEET: int = 5

var _config: Dictionary = {}


func _init() -> void:
	_load_config()


func get_hide_entry_dc() -> int:
	return maxi(int(_config.get("hide_entry_dc", DEFAULT_HIDE_ENTRY_DC)), 1)


func get_perception_tick_seconds() -> float:
	return maxf(float(_config.get("perception_tick_seconds", DEFAULT_PERCEPTION_TICK_SECONDS)), 0.05)


func get_active_search_interval_seconds() -> float:
	return maxf(float(_config.get("active_search_interval_seconds", DEFAULT_ACTIVE_SEARCH_INTERVAL_SECONDS)), 0.25)


func get_active_search_max_distance_feet() -> int:
	return maxi(int(_config.get("active_search_max_distance_feet", DEFAULT_ACTIVE_SEARCH_MAX_DISTANCE_FEET)), 5)


func is_active_search_state(state_id: String) -> bool:
	var states_value: Variant = _config.get("active_search_states", ["investigating", "searching", "alerted"])
	if not states_value is Array:
		return state_id in ["investigating", "searching", "alerted"]
	for value: Variant in states_value as Array:
		if str(value) == state_id:
			return true
	return false


func resolve_passive_detection(
	stealth_total: int,
	passive_perception: int,
	distance_feet: int,
	geometric_visible: bool,
	fully_concealed: bool = false
) -> Dictionary:
	if not geometric_visible:
		return {
			"detected": false,
			"reason": "no_geometric_contact",
			"margin": stealth_total - passive_perception,
			"automatic_detection_distance_feet": 0
		}
	if stealth_total <= 0:
		return {
			"detected": true,
			"reason": "not_hidden",
			"margin": 0,
			"automatic_detection_distance_feet": 0
		}

	var perception: int = maxi(passive_perception, 0)
	var margin: int = stealth_total - perception
	if margin <= 0:
		return {
			"detected": true,
			"reason": "passive_perception",
			"margin": margin,
			"automatic_detection_distance_feet": 0
		}

	var minimum_distance: int = maxi(int(_config.get("min_auto_detection_feet", DEFAULT_MIN_AUTO_DETECTION_FEET)), 0)
	var maximum_distance: int = maxi(int(_config.get("max_auto_detection_feet", DEFAULT_MAX_AUTO_DETECTION_FEET)), minimum_distance)
	var reduction_per_margin: int = maxi(int(_config.get("feet_reduction_per_stealth_margin", DEFAULT_FEET_REDUCTION_PER_MARGIN)), 0)
	var automatic_distance: int = clampi(
		maximum_distance - margin * reduction_per_margin,
		minimum_distance,
		maximum_distance
	)
	if fully_concealed:
		automatic_distance = mini(
			automatic_distance,
			maxi(int(_config.get("concealed_auto_detection_feet", DEFAULT_CONCEALED_AUTO_DETECTION_FEET)), 0)
		)
	var detected: bool = distance_feet <= automatic_distance
	return {
		"detected": detected,
		"reason": "close_contact" if detected else "stealth_beats_passive",
		"margin": margin,
		"automatic_detection_distance_feet": automatic_distance
	}


func resolve_active_search(
	stealth_total: int,
	perception_modifier: int,
	natural_roll: int
) -> Dictionary:
	var natural: int = clampi(natural_roll, 1, 20)
	var total: int = natural + perception_modifier
	return {
		"natural": natural,
		"modifier": perception_modifier,
		"total": total,
		"difficulty": maxi(stealth_total, 1),
		"success": total >= maxi(stealth_total, 1)
	}


func _load_config() -> void:
	_config.clear()
	if not FileAccess.file_exists(DATA_PATH):
		return
	var file: FileAccess = FileAccess.open(DATA_PATH, FileAccess.READ)
	if file == null:
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if parsed is Dictionary:
		_config = (parsed as Dictionary).duplicate(true)
