extends "res://scripts/game/game_racial_planned.gd"


func _predict_directional_target(weapon: Dictionary) -> Node:
	if DistanceSystem.is_ranged_weapon(weapon):
		return super._predict_directional_target(weapon)
	return _find_directional_melee_target(weapon)


func _weapon_attempt_is_valid(weapon: Dictionary, selected_target: Node, predicted_target: Node) -> bool:
	if _target_is_valid(selected_target) or DistanceSystem.is_ranged_weapon(weapon):
		return super._weapon_attempt_is_valid(weapon, selected_target, predicted_target)
	return maxi(int(weapon.get("reach_ft", 5)), 0) > 0


func show_combat_message(message: String, positive: bool) -> void:
	super.show_combat_message(_russianize_visible_text(message), positive)


func _russianize_visible_text(value: String) -> String:
	return value.replace("временные HP", "временное здоровье").replace("Временные HP", "Временное здоровье").replace(" HP", " здоровья").replace("HP:", "Здоровье:")
