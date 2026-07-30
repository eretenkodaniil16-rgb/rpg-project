class_name AttackResult
extends RefCounted

var attacker_name: String = "Герой"
var attack_name: String = "Безоружный удар"
var target_name: String = "Цель"
var ability_name: String = "Сила"
var damage_type: String = "дробящий"
var is_spell: bool = false
var is_reaction: bool = false
var automatic_hit: bool = false
var melee_attack: bool = false
var nonlethal_knockout: bool = false
var natural_roll: int = 1
var first_roll: int = 1
var second_roll: int = 0
var advantage: bool = false
var disadvantage: bool = false
var ability_modifier: int = 0
var proficiency_bonus: int = 0
var attack_bonus: int = 0
var total: int = 1
var target_armor_class: int = 10
var cover_bonus: int = 0
var distance_feet: int = 0
var range_state: String = "melee"
var out_of_range: bool = false
var no_ammunition: bool = false
var hit: bool = false
var critical: bool = false
var automatic_miss: bool = false
var damage: int = 0
var damage_before_mitigation: int = 0
var bonus_damage: int = 0
var target_health_after: int = 0
var target_max_health: int = 0
var note: String = ""


func to_dict() -> Dictionary:
	return {
		"attacker_name": attacker_name,
		"attack_name": attack_name,
		"target_name": target_name,
		"ability_name": ability_name,
		"damage_type": damage_type,
		"is_spell": is_spell,
		"is_reaction": is_reaction,
		"automatic_hit": automatic_hit,
		"melee_attack": melee_attack,
		"nonlethal_knockout": nonlethal_knockout,
		"natural_roll": natural_roll,
		"first_roll": first_roll,
		"second_roll": second_roll,
		"advantage": advantage,
		"disadvantage": disadvantage,
		"ability_modifier": ability_modifier,
		"proficiency_bonus": proficiency_bonus,
		"attack_bonus": attack_bonus,
		"total": total,
		"target_armor_class": target_armor_class,
		"cover_bonus": cover_bonus,
		"distance_feet": distance_feet,
		"range_state": range_state,
		"out_of_range": out_of_range,
		"no_ammunition": no_ammunition,
		"hit": hit,
		"critical": critical,
		"automatic_miss": automatic_miss,
		"damage": damage,
		"damage_before_mitigation": damage_before_mitigation,
		"bonus_damage": bonus_damage,
		"target_health_after": target_health_after,
		"target_max_health": target_max_health,
		"note": note
	}
