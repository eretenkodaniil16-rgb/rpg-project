class_name SkillCheckResult
extends RefCounted

var ability_id: String = ""
var ability_name: String = ""
var natural_roll: int = 1
var ability_modifier: int = 0
var bonus: int = 0
var total: int = 1
var difficulty: int = 10
var success: bool = false


func to_dict() -> Dictionary:
	return {
		"ability_id": ability_id,
		"ability_name": ability_name,
		"natural_roll": natural_roll,
		"ability_modifier": ability_modifier,
		"bonus": bonus,
		"total": total,
		"difficulty": difficulty,
		"success": success
	}
