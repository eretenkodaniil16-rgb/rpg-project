extends "res://scripts/game/game_party_control_runtime.gd"


func refresh_active_party_action_catalog() -> void:
	if not _is_controllable_ally_turn() or _action_catalog_ui == null:
		return

	var context_target: Node = _party_control_context.target_for(_controllable_ally)
	var context_target_valid: bool = _ally_target_is_valid(context_target)
	if context_target_valid:
		_party_control_context.set_target(_controllable_ally, context_target)
		if _selected_target != context_target:
			_set_selected_target(context_target)

	var entries: Dictionary = _build_active_irna_catalog_entries(context_target)
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


func _build_active_irna_catalog_entries(context_target: Node) -> Dictionary:
	var entries: Dictionary = super._build_catalog_entries()
	var context_target_valid: bool = _ally_target_is_valid(context_target)
	var distance_feet: int = -1
	if context_target_valid:
		distance_feet = DistanceSystem.distance_feet(
			(_controllable_ally as Node2D).global_position,
			(context_target as Node2D).global_position
		)
	var state: CombatantState = _active_party_state()
	var can_act: bool = (
		state != null
		and _turn_system.action_available
		and _srd_rules.can_take_action(state)
	)
	var target_melee: bool = (
		context_target_valid
		and distance_feet >= 0
		and distance_feet <= DistanceSystem.MELEE_REACH_FEET
	)
	_last_catalog_context_diagnostics = {
		"active_actor_id": (
			_party_control_context.active_actor().get_instance_id()
			if is_instance_valid(_party_control_context.active_actor())
			else 0
		),
		"ally_id": _controllable_ally.get_instance_id() if is_instance_valid(_controllable_ally) else 0,
		"context_target_id": context_target.get_instance_id() if is_instance_valid(context_target) else 0,
		"context_target_valid": context_target_valid,
		"selected_target_id": _selected_target.get_instance_id() if is_instance_valid(_selected_target) else 0,
		"distance_feet": distance_feet,
		"can_act": can_act,
		"target_melee": target_melee
	}

	var action_value: Variant = entries.get("action", [])
	var action_entries: Array = action_value as Array if action_value is Array else []
	for index: int in range(action_entries.size()):
		var value: Variant = action_entries[index]
		if not value is Dictionary:
			continue
		var entry: Dictionary = (value as Dictionary).duplicate(true)
		match str(entry.get("id", "")):
			"attack":
				entry["enabled"] = can_act and target_melee
			"select_ally_target":
				entry["label"] = (
					"СМЕНИТЬ ЦЕЛЬ ИРИНЫ"
					if context_target_valid
					else "ВЫБРАТЬ ЦЕЛЬ ИРИНЫ"
				)
			_:
				pass
		action_entries[index] = entry
	entries["action"] = action_entries
	return entries


func _ally_target_is_valid(target: Node) -> bool:
	if (
		not is_instance_valid(target)
		or not target is Node2D
		or not target.is_in_group("combat_targets")
		or not target.has_method("is_combat_active")
		or not bool(target.call("is_combat_active"))
		or not _controllable_ally is Node2D
	):
		return false
	if _combat_environment != null:
		var cover: Dictionary = _combat_environment.get_cover(
			(_controllable_ally as Node2D).global_position,
			(target as Node2D).global_position
		)
		if bool(cover.get("total_cover", false)):
			return false
	return true


func _cycle_ally_target() -> void:
	var targets: Array[Node] = []
	for candidate: Node in _available_targets():
		if _ally_target_is_valid(candidate):
			targets.append(candidate)
	if targets.is_empty():
		_set_selected_target(null)
		_party_control_context.clear_target(_controllable_ally)
		show_combat_message("Для Ирины нет доступных вражеских целей.", false)
		return
	var current: Node = _party_control_context.target_for(_controllable_ally)
	var current_index: int = targets.find(current)
	var next_target: Node = (
		targets[0]
		if current_index < 0 or current_index + 1 >= targets.size()
		else targets[current_index + 1]
	)
	_party_control_context.set_target(_controllable_ally, next_target)
	_set_selected_target(next_target)
	_update_target_label()
	show_combat_message("Ирина выбирает цель: %s." % _target_name(next_target), true)


func _update_target_label() -> void:
	if not _is_controllable_ally_turn():
		super._update_target_label()
		return
	if _target_label == null:
		return
	var target: Node = _party_control_context.target_for(_controllable_ally)
	if not _ally_target_is_valid(target):
		_target_label.text = "Ход Ирины · цель не выбрана"
		return
	var distance: int = DistanceSystem.distance_feet(
		(_controllable_ally as Node2D).global_position,
		(target as Node2D).global_position
	)
	_target_label.text = "Ирина → %s · %d футов · КД %d" % [
		_target_name(target),
		distance,
		int(target.call("get_armor_class"))
	]


func _request_controllable_ally_attack(
	target_override: Node = null,
	roll_override: int = -1
) -> Dictionary:
	var target: Node = target_override
	if not _ally_target_is_valid(target):
		target = _party_control_context.target_for(_controllable_ally)
	if not _ally_target_is_valid(target):
		show_combat_message("Для атаки Ирины выберите доступного противника.", false)
		return {"success": false, "status": "target_required"}

	# The inherited combat routine still calls the main-hero visibility validator.
	# Temporarily bypass only that visibility clause after Irina's own line-of-sight
	# and combat-participation checks have already succeeded.
	var hidden_trigger_before: bool = _allow_hidden_combat_trigger
	_allow_hidden_combat_trigger = true
	var result: Dictionary = await super._request_controllable_ally_attack(target, roll_override)
	_allow_hidden_combat_trigger = hidden_trigger_before
	return result
