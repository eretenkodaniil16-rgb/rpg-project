class_name PresentingSrdCombatRules
extends SrdCombatRules


func resolve_d20_test(
	modifier: int,
	dc: int,
	advantage: bool = false,
	disadvantage: bool = false,
	overrides: Array[int] = [],
	reroll_natural_one: bool = false,
	reroll_overrides: Array[int] = []
) -> Dictionary:
	var result: Dictionary = super.resolve_d20_test(modifier, dc, advantage, disadvantage, overrides, reroll_natural_one, reroll_overrides)
	_present("Участник", "Проверка d20", result, bool(result.get("success", false)), dc, modifier)
	return result


func resolve_death_save(state: CombatantState, roll_override: int = -1, lucky_reroll_override: int = -1) -> Dictionary:
	var result: Dictionary = super.resolve_death_save(state, roll_override, lucky_reroll_override)
	if bool(result.get("resolved", false)):
		var success: bool = bool(result.get("regained_hit_point", false)) or int(result.get("natural", 0)) >= 10
		_present("Герой", "Спасбросок смерти", result, success, 10, 0)
	return result


func _present(actor_name: String, purpose: String, result: Dictionary, success: bool, target_number: int = 0, modifier: int = 0) -> void:
	var tree: SceneTree = Engine.get_main_loop() as SceneTree
	if tree == null:
		return
	var natural: int = int(result.get("natural", 0))
	if natural <= 0:
		return
	tree.call_group(
		"dice_presenter",
		"show_d20_roll",
		actor_name,
		purpose,
		natural,
		int(result.get("total", natural)),
		success,
		int(result.get("first", natural)),
		int(result.get("second", 0)),
		target_number,
		modifier
	)
