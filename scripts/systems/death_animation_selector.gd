class_name DeathAnimationSelector
extends RefCounted

const DEFAULT_FALLBACK_VARIANT_ID: String = "death_01_base"

var _rng: RandomNumberGenerator = RandomNumberGenerator.new()


func _init(seed_value: int = -1) -> void:
	if seed_value >= 0:
		_rng.seed = seed_value
	else:
		_rng.randomize()


func select_variant(
	entries: Array[Dictionary],
	previous_variant_id: String = "",
	roll_override: float = -1.0
) -> String:
	var candidates: Array[Dictionary] = _normalized_entries(entries)
	if candidates.is_empty():
		return ""
	if candidates.size() > 1 and not previous_variant_id.is_empty():
		var without_previous: Array[Dictionary] = []
		for entry: Dictionary in candidates:
			if str(entry.get("death_variant_id", "")) != previous_variant_id:
				without_previous.append(entry)
		if not without_previous.is_empty():
			candidates = without_previous

	var total_weight: float = 0.0
	for entry: Dictionary in candidates:
		total_weight += float(entry.get("weight", 0.0))
	if total_weight <= 0.0:
		return ""

	var normalized_roll: float = (
		clampf(roll_override, 0.0, 0.999999)
		if roll_override >= 0.0
		else _rng.randf()
	)
	var threshold: float = normalized_roll * total_weight
	var accumulated: float = 0.0
	for entry: Dictionary in candidates:
		accumulated += float(entry.get("weight", 0.0))
		if threshold < accumulated:
			return str(entry.get("death_variant_id", ""))
	return str(candidates[-1].get("death_variant_id", ""))


func resolve_available_variant(
	requested_variant_id: String,
	entries: Array[Dictionary],
	fallback_variant_id: String = DEFAULT_FALLBACK_VARIANT_ID
) -> String:
	if _contains_variant(entries, requested_variant_id):
		return requested_variant_id
	if _contains_variant(entries, fallback_variant_id):
		return fallback_variant_id
	return ""


func _normalized_entries(entries: Array[Dictionary]) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	var seen: Dictionary = {}
	for source: Dictionary in entries:
		var death_variant_id: String = str(source.get("death_variant_id", ""))
		var set_id: String = str(source.get("set_id", ""))
		var weight: float = float(source.get("weight", 0.0))
		if death_variant_id.is_empty() or set_id.is_empty() or weight <= 0.0 or seen.has(death_variant_id):
			continue
		seen[death_variant_id] = true
		result.append({
			"death_variant_id": death_variant_id,
			"set_id": set_id,
			"weight": weight
		})
	return result


func _contains_variant(entries: Array[Dictionary], death_variant_id: String) -> bool:
	if death_variant_id.is_empty():
		return false
	for entry: Dictionary in _normalized_entries(entries):
		if str(entry.get("death_variant_id", "")) == death_variant_id:
			return true
	return false
