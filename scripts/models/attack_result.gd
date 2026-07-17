class_name AttackResult
extends RefCounted

var attack_name: String = "Безоружный удар"
var ability_name: String = "Сила"
var damage_type: String = "дробящий"
var is_spell: bool = false
var automatic_hit: bool = false
var natural_roll: int = 1
var ability_modifier: int = 0
var proficiency_bonus: int = 0
var attack_bonus: int = 0
var total: int = 1
var target_armor_class: int = 10
var hit: bool = false
var critical: bool = false
var automatic_miss: bool = false
var damage: int = 0
var bonus_damage: int = 0
var target_health_after: int = 0
var target_max_health: int = 0
var note: String = ""


func to_dict() -> Dictionary:
	return {
		"attack_name": attack_name,
		"ability_name": ability_name,
		"damage_type": damage_type,
		"is_spell": is_spell,
		"automatic_hit": automatic_hit,
		"natural_roll": natural_roll,
		"ability_modifier": ability_modifier,
		"proficiency_bonus": proficiency_bonus,
		"attack_bonus": attack_bonus,
		"total": total,
		"target_armor_class": target_armor_class,
		"hit": hit,
		"critical": critical,
		"automatic_miss": automatic_miss,
		"damage": damage,
		"bonus_damage": bonus_damage,
		"target_health_after": target_health_after,
		"target_max_health": target_max_health,
		"note": note
	}
