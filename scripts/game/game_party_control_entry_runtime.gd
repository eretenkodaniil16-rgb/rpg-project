extends "res://scripts/game/game_party_control_runtime.gd"


func refresh_active_party_action_catalog() -> void:
	# Unique public entry point for the party-aware mobile controller. Do not call
	# the inherited `_refresh_action_catalog` name here: this project has a long
	# runtime inheritance chain and older script-level implementations can win that
	# dispatch. Build and submit Irna's catalogue explicitly at the final leaf.
	if not _is_controllable_ally_turn() or _action_catalog_ui == null:
		return

	var context_target: Node = _party_control_context.target_for(_controllable_ally)
	var context_target_valid: bool = _target_is_valid(context_target)
	if context_target_valid:
		_party_control_context.set_target(_controllable_ally, context_target)
		if _selected_target != context_target:
			_set_selected_target(context_target)

	var entries_value: Variant = call("_build_irna_catalog_entries", context_target)
	var entries: Dictionary = entries_value as Dictionary if entries_value is Dictionary else {}
	var has_plan: bool = _planned_path.size() > 1
	var target_text: String = "цель не выбрана"
	if context_target_valid:
		target_text = "цель: %s" % _target_name(context_target)

	_action_catalog_ui.refresh(
		true,
		true,
		_any_overlay_visible(),
		entries,
		"Ирина · Раунд %d · Действие: %s · Реакция: %s · Перемещение: %d футов" % [
			_turn_system.round_number,
			"готово" if _turn_system.action_available else "использовано",
			"готова" if _turn_system.has_reaction(_controllable_ally) else "использована",
			_turn_system.movement_remaining_feet
		],
		"%s · %s" % [
			target_text,
			"маршрут не выбран" if not has_plan else "маршрут: %d футов" % _planned_cost_feet
		],
		has_plan,
		_planned_cost_feet
	)
