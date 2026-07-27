class_name SkillCheckResult
extends RefCounted

var ability_id: String = ""
var ability_name: String = ""
var skill_id: String = ""
var first_roll: int = 1
var second_roll: int = 0
var natural_roll: int = 1
var advantage: bool = false
var disadvantage: bool = false
var ability_modifier: int = 0
var bonus: int = 0
var total: int = 1
var difficulty: int = 10
var success: bool = false


func to_dict() -> Dictionary:
	return {
		"ability_id": ability_id,
		"ability_name": ability_name,
		"skill_id": skill_id,
		"first_roll": first_roll,
		"second_roll": second_roll,
		"natural_roll": natural_roll,
		"advantage": advantage,
		"disadvantage": disadvantage,
		"ability_modifier": ability_modifier,
		"bonus": bonus,
		"total": total,
		"difficulty": difficulty,
		"success": success
	}
