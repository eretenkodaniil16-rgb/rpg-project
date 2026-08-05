extends "res://scripts/game/game_party_control_runtime.gd"

const IRINA_ACTION_LABELS: Dictionary = {
	"attack": "АТАКА КОРОТКИМ МЕЧОМ",
	"confirm_move": "ПОДТВЕРДИТЬ ПЕРЕМЕЩЕНИЕ",
	"cancel_move": "ОТМЕНИТЬ ПУТЬ",
	"dash": "РЫВОК",
	"disengage": "ОТХОД",
	"dodge": "УКЛОНЕНИЕ",
	"end_turn": "ЗАВЕРШИТЬ ХОД",
	"reaction_status": "РЕАКЦИЯ"
}


func _on_catalog_action_requested(action_id: String) -> void:
	# Keep the legacy direct runtime facade stable for tests and integrations.
	# The UI signal itself remains connected only to the two actor-gated handlers,
	# so this compatibility entry point cannot execute an action twice.
	if _is_controllable_ally_turn():
		_on_party_catalog_action_requested(action_id)
		return
	_on_feedback_catalog_action_requested(action_id)


func refresh_active_party_action_catalog() -> void:
	if not _is_controllable_ally_turn() or _action_catalog_ui == null:
		return

	var context_target: Node = _party_control_context.target_for(_controllable_ally)
	var context_target_valid: bool = _ally_target_is_valid(context_target)
	if context_target_valid:
		_party_control_context.set_target(_controllable_ally, context_target)
		if _selected_target != context_target:
			_set_selected_target(context_target)

	var entries: Dictionary = _build_active_irina_catalog_entries(context_target)
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


func _build_active_irina_catalog_entries(context_target: Node) -> Dictionary:
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

	for category_id: String in ["action", "bonus", "free", "reaction"]:
		var category_value: Variant = entries.get(category_id, [])
		if not category_value is Array:
			continue
		var playable_entries: Array = []
		for value: Variant in category_value as Array:
			if not value is Dictionary:
				continue
			var entry: Dictionary = (value as Dictionary).duplicate(true)
			var action_id: String = str(entry.get("id", ""))
			# Target selection belongs to the same dedicated target button used by the
			# main hero. It is not an action-catalog command for a second-class NPC.
			if action_id == "select_ally_target":
				continue
			_normalize_irina_action_entry(entry)
			if action_id == "attack":
				entry["enabled"] = can_act and target_melee
			playable_entries.append(entry)
		entries[category_id] = playable_entries
	return entries


func _normalize_irina_action_entry(entry: Dictionary) -> void:
	var action_id: String = str(entry.get("id", ""))
	if IRINA_ACTION_LABELS.has(action_id):
		var label: String = str(IRINA_ACTION_LABELS[action_id])
		if action_id == "reaction_status":
			label += " ГОТОВА" if bool(entry.get("enabled", false)) else " ИСПОЛЬЗОВАНА"
		entry["label"] = label
	match action_id:
		"confirm_move":
			entry["description"] = "Выполнить выбранный маршрут."
		"cancel_move":
			entry["description"] = "Очистить выбранный маршрут."
		"dash":
			entry["description"] = "Получить дополнительное перемещение за основное действие."
		"disengage":
			entry["description"] = "До конца хода не провоцировать атаки по возможности."
		"dodge":
			entry["description"] = "Атаки видимых противников совершаются с помехой до следующего хода."
		"end_turn":
			entry["description"] = "Завершить текущий ход."
		"reaction_status":
			entry["description"] = "Реакция текущего персонажа."


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
		show_combat_message("Для атаки выберите доступного противника.", false)
		return {"success": false, "status": "target_required"}

	var hidden_trigger_before: bool = _allow_hidden_combat_trigger
	_allow_hidden_combat_trigger = true
	var result: Dictionary = await super._request_controllable_ally_attack(target, roll_override)
	_allow_hidden_combat_trigger = hidden_trigger_before
	return result


func set_party_target_for_testing(actor: Node, target: Node) -> void:
	# The full scenario must test restoration of a target that is actually legal for
	# the corresponding actor. Stable fixtures are created independently of the
	# level geometry, so place the hero fixture in a visible free cell before it is
	# stored. Production targeting remains unchanged.
	if actor == player and is_instance_valid(target) and not _target_is_valid(target):
		_place_test_target_visible_to_player(target)
	super.set_party_target_for_testing(actor, target)


func _place_test_target_visible_to_player(target: Node) -> bool:
	if not target is Node2D or not is_instance_valid(player):
		return false
	if _target_is_valid(target):
		return true
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return false
	var target_node: Node2D = target as Node2D
	var original_position: Vector2 = target_node.global_position
	var origin_cell: Vector2i = grid.world_to_cell(player.global_position)
	var occupied: Dictionary = _occupied_cells(target)
	for radius: int in range(1, 5):
		for y: int in range(-radius, radius + 1):
			for x: int in range(-radius, radius + 1):
				if maxi(absi(x), absi(y)) != radius:
					continue
				var candidate := origin_cell + Vector2i(x, y)
				if not grid.is_cell_valid(candidate) or occupied.has(candidate):
					continue
				if _combat_environment != null and _combat_environment.is_cell_blocked(grid, candidate):
					continue
				target_node.global_position = grid.cell_to_world_center(candidate)
				if _target_is_valid(target):
					return true
	target_node.global_position = original_position
	return false
