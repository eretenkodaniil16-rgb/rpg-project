class_name NpcSpellSelectionSystem
extends RefCounted

const ABILITIES_PATH: String = "res://data/abilities/abilities.json"
const BLOCKED_SCORE: float = -100000.0

var _abilities: Dictionary = {}


func _init() -> void:
	_load_abilities()


func get_spell(spell_id: String) -> Dictionary:
	var value: Variant = _abilities.get(spell_id, {})
	if not value is Dictionary:
		return {}
	var spell: Dictionary = (value as Dictionary).duplicate(true)
	return spell if bool(spell.get("is_spell", false)) else {}


func choose_spell(spell_ids: Array[String], context_by_spell: Dictionary, policy: Dictionary = {}) -> Dictionary:
	var best: Dictionary = {}
	var best_score: float = BLOCKED_SCORE
	for spell_id: String in spell_ids:
		var spell: Dictionary = get_spell(spell_id)
		if spell.is_empty():
			continue
		var value: Variant = context_by_spell.get(spell_id, {})
		if not value is Dictionary:
			continue
		var option: Dictionary = (value as Dictionary).duplicate(true)
		option["spell_id"] = spell_id
		option["spell"] = spell
		var score: float = score_spell_option(spell, option, policy)
		option["score"] = score
		if score > best_score + 0.0001 or (is_equal_approx(score, best_score) and (best.is_empty() or spell_id < str(best.get("spell_id", "")))):
			best = option
			best_score = score
	if best_score <= BLOCKED_SCORE * 0.5:
		return {}
	return best


func score_spell_option(spell: Dictionary, option: Dictionary, policy: Dictionary = {}) -> float:
	if spell.is_empty() or not bool(option.get("available", true)) or not bool(option.get("line_of_sight", true)):
		return BLOCKED_SCORE
	var hostile_hits: int = maxi(int(option.get("hostile_hits", 0)), 0)
	var friendly_hits: int = maxi(int(option.get("friendly_hits", 0)), 0)
	var caster_hit: bool = bool(option.get("caster_hit", false))
	var tolerance: int = maxi(int(policy.get("friendly_fire_tolerance", 0)), 0)
	if hostile_hits <= 0 or friendly_hits > tolerance or caster_hit:
		return BLOCKED_SCORE
	var range_feet: int = maxi(int(spell.get("range_ft", 0)), 0)
	var distance_feet: int = maxi(int(option.get("distance_feet", 0)), 0)
	if range_feet > 0 and distance_feet > range_feet:
		return BLOCKED_SCORE
	var spell_level: int = maxi(int(spell.get("spell_level", 0)), 0)
	var slots_remaining: int = maxi(int(option.get("slots_remaining", 0)), 0)
	if spell_level > 0 and slots_remaining <= 0:
		return BLOCKED_SCORE

	var expected_damage: float = maxf(float(option.get("expected_damage", expected_damage_for(spell))), 0.0)
	var control_value: float = maxf(float(option.get("control_value", control_value_for(spell))), 0.0)
	var target_health_ratio: float = clampf(float(option.get("target_health_ratio", 1.0)), 0.0, 1.0)
	var target_wounded: bool = bool(option.get("target_wounded", target_health_ratio < 1.0))
	var score: float = expected_damage * 7.5
	score += control_value * 18.0
	score += float(hostile_hits) * 26.0
	score -= float(friendly_hits) * 250.0

	var effect: String = str(spell.get("effect", ""))
	var spell_id: String = str(spell.get("id", ""))
	if effect == "area_saving_throw_spell":
		score += float(maxi(hostile_hits - 1, 0)) * 34.0
	if spell_id == "magic_missile":
		score += 46.0 if target_health_ratio <= 0.3 else 8.0
	if spell_id == "ray_of_sickness":
		score += 24.0 if target_health_ratio >= 0.55 else 4.0
	if spell_id == "thunderwave":
		score += 30.0 if distance_feet <= 10 else 0.0
	if spell_id == "burning_hands":
		score += 22.0 if distance_feet <= 15 else 0.0
	if spell_id == "sorcerous_burst" and target_wounded:
		score += 5.0

	if spell_level > 0:
		var reserve: int = maxi(int(policy.get("slot_reserve", 0)), 0)
		var conservation: float = clampf(float(policy.get("slot_conservation", 0.55)), 0.0, 1.0)
		var scarcity: float = 1.0 if slots_remaining <= reserve else 0.35
		score -= float(spell_level) * 24.0 * conservation * scarcity
	else:
		score += 10.0
	return score


func expected_damage_for(spell: Dictionary) -> float:
	var dice_value: Variant = spell.get("damage_dice", [])
	var expected: float = float(spell.get("damage_bonus", 0))
	if dice_value is Array and (dice_value as Array).size() >= 2:
		var count: int = maxi(int((dice_value as Array)[0]), 0)
		var sides: int = maxi(int((dice_value as Array)[1]), 0)
		expected += float(count) * (float(sides) + 1.0) * 0.5
	return expected


func control_value_for(spell: Dictionary) -> float:
	var value: float = 0.0
	if not str(spell.get("on_hit_condition", "")).is_empty():
		value += 1.4
	if int(spell.get("push_feet_on_failed_save", 0)) > 0:
		value += 1.7
	if str(spell.get("effect", "")) == "auto_hit_spell":
		value += 0.8
	return value


func _load_abilities() -> void:
	_abilities.clear()
	if not FileAccess.file_exists(ABILITIES_PATH):
		return
	var file: FileAccess = FileAccess.open(ABILITIES_PATH, FileAccess.READ)
	if file == null:
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if parsed is Dictionary:
		_abilities = (parsed as Dictionary).duplicate(true)
