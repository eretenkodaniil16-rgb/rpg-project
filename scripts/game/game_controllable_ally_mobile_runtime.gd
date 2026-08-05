extends "res://scripts/game/game_controllable_ally_control_runtime.gd"

const PARTY_CONTROL_CONTEXT_SCRIPT: Script = preload("res://scripts/systems/party_combat_control_context.gd")
const PARTY_INPUT_DEAD_ZONE: float = 0.25
const PARTY_INPUT_REPEAT_SECONDS: float = 0.18
const ALLY_WORLD_INTERACTION_PREFIX: String = "world_interact"

var _party_control_context: PartyCombatControlContext = PARTY_CONTROL_CONTEXT_SCRIPT.new() as PartyCombatControlContext
var _party_mobile_vector: Vector2 = Vector2.ZERO
var _party_last_step: Vector2i = Vector2i.ZERO
var _party_move_cooldown: float = 0.0


func _process(delta: float) -> void:
	super._process(delta)
	_process_active_party_movement_input(delta)


func _begin_current_turn() -> void:
	_remember_target_for_active_actor()
	_clear_party_input()
	_clear_movement_plan()
	_invalidate_reachable_area()
	var actor: Node = _turn_system.current_actor()
	if _turn_system.active and _turn_system.is_player_controlled_turn() and is_instance_valid(actor):
		_party_control_context.begin_turn(actor)
	else:
		_party_control_context.begin_turn(null)
	_restore_target_for_active_actor()
	super._begin_current_turn()
	_restore_target_for_active_actor()
	var grid: BattleGrid = _get_battle_grid()
	if grid != null and is_instance_valid(actor):
		grid.set_active_actor(actor)
	_refresh_turn_interface()
	_refresh_action_catalog()
	_refresh_reachable_area(true)


func _advance_combat_turn() -> void:
	_remember_target_for_active_actor()
	_clear_party_input()
	super._advance_combat_turn()


func _stop_turn_based_combat(message: String) -> void:
	_remember_target_for_active_actor()
	_clear_party_input()
	_party_control_context.clear()
	super._stop_turn_based_combat(message)


func is_player_combat_turn() -> bool:
	return (
		_turn_system.active
		and _turn_system.is_player_controlled_turn()
		and not _enemy_turn_running
	)


func is_controlled_actor_input_owner(actor: Node) -> bool:
	if not _turn_system.active:
		return actor == player
	return (
		_turn_system.is_player_controlled_turn()
		and _party_control_context.owns_input(actor)
		and not _enemy_turn_running
	)


func get_active_player_controlled_actor() -> Node:
	return _active_party_actor()


func set_mobile_control_vector(direction: Vector2) -> void:
	var normalized: Vector2 = direction.limit_length(1.0)
	if not _turn_system.active:
		_clear_party_input()
		if is_instance_valid(player) and player.has_method("set_mobile_facing_vector"):
			player.call("set_mobile_facing_vector", normalized)
		return
	if not _turn_system.is_player_controlled_turn() or _enemy_turn_running:
		_clear_party_input()
		_clear_primary_player_facing_input()
		return
	_party_mobile_vector = normalized
	var actor: Node = _active_party_actor()
	if is_instance_valid(actor) and normalized.length() >= PARTY_INPUT_DEAD_ZONE and actor.has_method("set_facing_direction"):
		actor.call("set_facing_direction", normalized)
	if actor == player and is_instance_valid(player) and player.has_method("set_mobile_facing_vector"):
		player.call("set_mobile_facing_vector", normalized)
	else:
		_clear_primary_player_facing_input()


func clear_mobile_control_vector() -> void:
	set_mobile_control_vector(Vector2.ZERO)


func get_mobile_control_vector_for_testing() -> Vector2:
	return _party_mobile_vector


func request_combat_move(step: Vector2i) -> void:
	if not _is_controllable_ally_turn():
		super.request_combat_move(step)
		return
	if not _can_plan_movement() or step == Vector2i.ZERO:
		return
	var actor: Node2D = _active_party_actor() as Node2D
	var grid: BattleGrid = _get_battle_grid()
	if actor == null or grid == null:
		return
	var base_cell: Vector2i = grid.world_to_cell(actor.global_position)
	if not _planned_path.is_empty():
		base_cell = _planned_path[_planned_path.size() - 1]
	_append_drawn_cell(base_cell + step)


func _process_active_party_movement_input(delta: float) -> void:
	_party_move_cooldown = maxf(_party_move_cooldown - delta, 0.0)
	var actor: Node = _active_party_actor()
	if not is_instance_valid(actor):
		_clear_party_input()
		return
	var input_vector: Vector2 = _party_mobile_vector
	if actor != player:
		input_vector += Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	if input_vector.length_squared() > 1.0:
		input_vector = input_vector.normalized()
	var step := Vector2i(
		int(signf(input_vector.x)) if absf(input_vector.x) >= PARTY_INPUT_DEAD_ZONE else 0,
		int(signf(input_vector.y)) if absf(input_vector.y) >= PARTY_INPUT_DEAD_ZONE else 0
	)
	if step == Vector2i.ZERO:
		_party_last_step = Vector2i.ZERO
		_party_move_cooldown = 0.0
		return
	if not _party_turn_input_available():
		return
	if step == _party_last_step and _party_move_cooldown > 0.0:
		return
	if _action_catalog_ui != null and _action_catalog_ui.is_catalog_open():
		_action_catalog_ui.close_catalog()
	if actor.has_method("set_facing_direction"):
		actor.call("set_facing_direction", Vector2(step))
	_party_last_step = step
	request_combat_move(step)
	_party_move_cooldown = PARTY_INPUT_REPEAT_SECONDS


func _append_drawn_cell(destination_cell: Vector2i) -> void:
	if not _is_controllable_ally_turn():
		super._append_drawn_cell(destination_cell)
		return
	if not _can_plan_movement():
		return
	var actor: Node2D = _active_party_actor() as Node2D
	var state: CombatantState = _active_party_state()
	var grid: BattleGrid = _get_battle_grid()
	if actor == null or state == null or grid == null or not grid.is_cell_valid(destination_cell):
		return
	if _planned_path.is_empty():
		_planned_path = [grid.world_to_cell(actor.global_position)]
	if _planned_path.has(destination_cell):
		_trim_route_from_cell(destination_cell)
		return
	var tail: Vector2i = _planned_path[_planned_path.size() - 1]
	var occupied: Dictionary = _occupied_cells(actor)
	if _combat_environment != null and _combat_environment.is_cell_blocked(grid, destination_cell):
		var blocked_delta: Vector2i = destination_cell - tail
		if maxi(absi(blocked_delta.x), absi(blocked_delta.y)) == 1 and _combat_environment.is_jumpable_cell(grid, destination_cell):
			_pending_jump_direction = Vector2i(signi(blocked_delta.x), signi(blocked_delta.y))
		return
	if _pending_jump_direction != Vector2i.ZERO and _combat_environment != null:
		var landing: Vector2i = _combat_environment.get_jump_landing_cell(grid, tail, _pending_jump_direction, occupied)
		if destination_cell == landing:
			var jump_candidate: Array[Vector2i] = _planned_path.duplicate()
			jump_candidate.append(destination_cell)
			_pending_jump_direction = Vector2i.ZERO
			_apply_candidate_path(jump_candidate)
			return
		_pending_jump_direction = Vector2i.ZERO
	var delta: Vector2i = destination_cell - tail
	if maxi(absi(delta.x), absi(delta.y)) == 1:
		var direct_candidate: Array[Vector2i] = _planned_path.duplicate()
		direct_candidate.append(destination_cell)
		_apply_candidate_path(direct_candidate)
		return
	var remaining_budget: int = maxi(_turn_system.movement_remaining_feet - _planned_cost_feet, 0)
	var segment: Dictionary = _movement_planner.build_path(
		grid,
		tail,
		destination_cell,
		occupied,
		_combat_environment,
		state,
		remaining_budget,
		state.grappling_target_id != 0,
		true
	)
	if not bool(segment.get("reachable", false)):
		return
	var segment_path: Array[Vector2i] = segment.get("path", []) as Array[Vector2i]
	var combined: Array[Vector2i] = _planned_path.duplicate()
	for index: int in range(1, segment_path.size()):
		combined.append(segment_path[index])
	_apply_candidate_path(combined)


func _plan_to_cell(destination_cell: Vector2i) -> void:
	if not _is_controllable_ally_turn():
		super._plan_to_cell(destination_cell)
		return
	if not _can_plan_movement():
		return
	var actor: Node2D = _active_party_actor() as Node2D
	var state: CombatantState = _active_party_state()
	var grid: BattleGrid = _get_battle_grid()
	if actor == null or state == null or grid == null:
		return
	if not grid.is_cell_valid(destination_cell):
		show_combat_message("Выбранная клетка находится за пределами поля боя.", false)
		return
	if _combat_environment != null and _combat_environment.is_cell_blocked(grid, destination_cell):
		show_combat_message("Нельзя закончить перемещение Ирины в клетке препятствия.", false)
		return
	var result: Dictionary = _movement_planner.build_path(
		grid,
		grid.world_to_cell(actor.global_position),
		destination_cell,
		_occupied_cells(actor),
		_combat_environment,
		state,
		_turn_system.movement_remaining_feet,
		state.grappling_target_id != 0,
		true
	)
	if not bool(result.get("reachable", false)):
		show_combat_message(str(result.get("reason", "Путь Ирины недоступен.")), false)
		return
	_set_plan_from_result(result)


func _apply_candidate_path(candidate: Array[Vector2i]) -> void:
	if not _is_controllable_ally_turn():
		super._apply_candidate_path(candidate)
		return
	var actor: Node2D = _active_party_actor() as Node2D
	var state: CombatantState = _active_party_state()
	var grid: BattleGrid = _get_battle_grid()
	if actor == null or state == null or grid == null:
		return
	var result: Dictionary = _movement_planner.evaluate_path(
		grid,
		candidate,
		_occupied_cells(actor),
		_combat_environment,
		state,
		_turn_system.movement_remaining_feet,
		state.grappling_target_id != 0
	)
	if not bool(result.get("reachable", false)):
		show_combat_message(str(result.get("reason", "Эту часть маршрута Ирины добавить нельзя.")), false)
		return
	_set_plan_from_result(result)


func _execute_planned_path() -> void:
	if not _is_controllable_ally_turn():
		super._execute_planned_path()
		return
	var actor: Node2D = _active_party_actor() as Node2D
	var state: CombatantState = _active_party_state()
	var grid: BattleGrid = _get_battle_grid()
	if actor == null or state == null or grid == null:
		return
	var validation: Dictionary = _movement_planner.evaluate_path(
		grid,
		_planned_path,
		_occupied_cells(actor),
		_combat_environment,
		state,
		_turn_system.movement_remaining_feet,
		state.grappling_target_id != 0
	)
	if not bool(validation.get("reachable", false)):
		show_combat_message(str(validation.get("reason", "Маршрут Ирины больше недоступен.")), false)
		_clear_movement_plan()
		return
	_movement_execution_running = true
	if _action_catalog_ui != null:
		_action_catalog_ui.close_catalog()
	var path_copy: Array[Vector2i] = _planned_path.duplicate()
	for index: int in range(1, path_copy.size()):
		if not _is_controllable_ally_turn() or not is_instance_valid(actor):
			break
		var from_cell: Vector2i = grid.world_to_cell(actor.global_position)
		var destination_cell: Vector2i = path_copy[index]
		var transition: Dictionary = _movement_planner.evaluate_path(
			grid,
			[from_cell, destination_cell],
			_occupied_cells(actor),
			_combat_environment,
			state,
			_turn_system.movement_remaining_feet,
			state.grappling_target_id != 0
		)
		if not bool(transition.get("reachable", false)):
			show_combat_message("Маршрут Ирины прерван: следующая клетка стала недоступной.", false)
			break
		var movement_cost: int = int(transition.get("cost_feet", 0))
		var destination: Vector2 = grid.cell_to_world_center(destination_cell)
		if not _turn_system.disengaged:
			_trigger_enemy_opportunity_attacks(actor.global_position, destination)
			if state.dead or _ally_current_health() <= 0:
				break
		if not _turn_system.spend_movement(movement_cost):
			break
		var previous_position: Vector2 = actor.global_position
		var direction: Vector2 = destination - previous_position
		if actor.has_method("set_facing_direction"):
			actor.call("set_facing_direction", direction)
		var is_jump: bool = maxi(absi(destination_cell.x - from_cell.x), absi(destination_cell.y - from_cell.y)) > 1
		if is_jump:
			await _animate_party_combat_jump(actor, destination, direction)
		else:
			var tween: Tween = create_tween()
			tween.tween_property(actor, "global_position", destination, 0.12)
			await tween.finished
	_clear_movement_plan()
	_movement_execution_running = false
	_invalidate_reachable_area()
	_refresh_turn_interface()
	_refresh_action_catalog()
	_update_target_label()


func _animate_party_combat_jump(actor: Node2D, destination: Vector2, direction: Vector2) -> void:
	var body: Node2D = actor.get_node_or_null("Body") as Node2D
	var original_body_position: Vector2 = body.position if body != null else Vector2.ZERO
	var duration: float = clampf(actor.global_position.distance_to(destination) / 420.0, 0.28, 0.52)
	var movement_tween: Tween = create_tween()
	movement_tween.set_trans(Tween.TRANS_SINE)
	movement_tween.set_ease(Tween.EASE_IN_OUT)
	movement_tween.tween_property(actor, "global_position", destination, duration)
	if body != null:
		var arc_tween: Tween = create_tween()
		arc_tween.tween_property(body, "position", original_body_position + Vector2(0.0, -34.0), duration * 0.5)
		arc_tween.tween_property(body, "position", original_body_position, duration * 0.5)
	await movement_tween.finished
	actor.global_position = destination
	if actor.has_method("set_facing_direction"):
		actor.call("set_facing_direction", direction)


func _can_plan_movement() -> bool:
	if not _is_controllable_ally_turn():
		return super._can_plan_movement()
	var state: CombatantState = _active_party_state()
	return (
		state != null
		and _party_turn_input_available()
		and not _movement_execution_running
		and (_action_catalog_ui == null or not _action_catalog_ui.is_catalog_open())
		and _srd_rules.effective_speed_feet(_active_party_speed_feet(), state) > 0
	)


func _refresh_reachable_area(force: bool = false) -> void:
	if not _is_controllable_ally_turn():
		super._refresh_reachable_area(force)
		return
	if _movement_plan_overlay == null:
		return
	var actor: Node2D = _active_party_actor() as Node2D
	var state: CombatantState = _active_party_state()
	var grid: BattleGrid = _get_battle_grid()
	if actor == null or state == null or grid == null:
		_movement_plan_overlay.clear_reachable_cells()
		return
	var occupied: Dictionary = _occupied_cells(actor)
	var occupied_parts: Array[String] = []
	for key: Variant in occupied.keys():
		occupied_parts.append(str(key))
	occupied_parts.sort()
	var signature: String = "|".join([
		str(actor.get_instance_id()),
		str(grid.world_to_cell(actor.global_position)),
		str(_turn_system.movement_remaining_feet),
		str(state.has_condition("prone")),
		str(state.has_condition("grappled")),
		str(state.has_condition("restrained")),
		str(state.grappling_target_id),
		",".join(occupied_parts)
	])
	if not force and signature == _reachable_signature:
		return
	_reachable_signature = signature
	var reachable: Dictionary = _movement_planner.calculate_reachable_cells(
		grid,
		grid.world_to_cell(actor.global_position),
		occupied,
		_combat_environment,
		state,
		_turn_system.movement_remaining_feet,
		state.grappling_target_id != 0,
		true
	)
	_movement_plan_overlay.set_reachable_cells(reachable, _turn_system.movement_remaining_feet)


func _build_catalog_entries() -> Dictionary:
	if not _is_controllable_ally_turn():
		return super._build_catalog_entries()
	var state: CombatantState = _active_party_state()
	var can_act: bool = state != null and _turn_system.action_available and _srd_rules.can_take_action(state)
	var has_target: bool = _target_is_valid(_selected_target)
	var target_melee: bool = (
		has_target
		and _controllable_ally is Node2D
		and DistanceSystem.distance_feet(
			(_controllable_ally as Node2D).global_position,
			(_selected_target as Node2D).global_position
		) <= DistanceSystem.MELEE_REACH_FEET
	)
	var has_plan: bool = _planned_path.size() > 1
	var target_label: String = "ВЫБРАТЬ ЦЕЛЬ ИРИНЫ" if not has_target else "СМЕНИТЬ ЦЕЛЬ ИРИНЫ"
	var action_entries: Array[Dictionary] = [
		_entry("select_ally_target", target_label, true, "Выбрать отдельную цель для хода Ирины.", "target"),
		_entry("attack", "АТАКА КОРОТКИМ МЕЧОМ", can_act and target_melee, "Атаковать выбранную Ириной соседнюю цель. Расходует её основное действие.", "attack"),
		_entry("confirm_move", "ПОДТВЕРДИТЬ ПЕРЕМЕЩЕНИЕ ИРИНЫ", has_plan, "Выполнить выбранный маршрут и потратить перемещение Ирины.", "movement"),
		_entry("cancel_move", "ОТМЕНИТЬ ПУТЬ ИРИНЫ", has_plan, "Удалить маршрут Ирины без расхода перемещения.", "movement"),
		_entry("dash", "РЫВОК ИРИНЫ", can_act, "Добавить скорость Ирины к её перемещению. Расходует её основное действие.", "movement"),
		_entry("disengage", "ОТХОД ИРИНЫ", can_act, "Перемещение Ирины не вызывает атак по возможности до конца её хода.", "movement"),
		_entry("dodge", "УКЛОНЕНИЕ ИРИНЫ", can_act, "Атаки по Ирине получают помеху до начала её следующего хода.", "tactic"),
		_entry("end_turn", "ЗАВЕРШИТЬ ХОД ИРИНЫ", true, "Передать инициативу следующему участнику.", "tactic")
	]
	var reaction_entries: Array[Dictionary] = [
		_entry(
			"ally_reaction_status",
			"РЕАКЦИЯ ИРИНЫ ГОТОВА" if _turn_system.has_reaction(_controllable_ally) else "РЕАКЦИЯ ИРИНЫ ИСПОЛЬЗОВАНА",
			false,
			"Реакция принадлежит Ирине и восстанавливается в начале её хода.",
			"tactic"
		)
	]
	return {"action": action_entries, "bonus": [], "reaction": reaction_entries}


func _refresh_action_catalog() -> void:
	if not _is_controllable_ally_turn():
		super._refresh_action_catalog()
		return
	if _action_catalog_ui == null:
		return
	var has_plan: bool = _planned_path.size() > 1
	var target_text: String = "цель не выбрана"
	if _target_is_valid(_selected_target):
		target_text = "цель: %s" % _target_name(_selected_target)
	_action_catalog_ui.refresh(
		true,
		true,
		_any_overlay_visible(),
		_build_catalog_entries(),
		"Ирина · Раунд %d · Действие: %s · Реакция: %s · Перемещение: %d футов" % [
			_turn_system.round_number,
			"готово" if _turn_system.action_available else "использовано",
			"готова" if _turn_system.has_reaction(_controllable_ally) else "использована",
			_turn_system.movement_remaining_feet
		],
		"%s · %s" % [target_text, "маршрут не выбран" if not has_plan else "маршрут: %d футов" % _planned_cost_feet],
		has_plan,
		_planned_cost_feet
	)


func _on_feedback_catalog_action_requested(action_id: String) -> void:
	if not _is_controllable_ally_turn():
		super._on_feedback_catalog_action_requested(action_id)
		return
	if action_id.begins_with(ALLY_WORLD_INTERACTION_PREFIX):
		show_combat_message("Взаимодействия с миром выполняет основной герой на своём ходу.", false)
		return
	match action_id:
		"select_ally_target": _cycle_ally_target()
		"confirm_move": _confirm_planned_movement()
		"cancel_move": _cancel_planned_movement()
		"attack": _request_controllable_ally_attack()
		"dash": _on_dash_requested()
		"disengage": _on_disengage_requested()
		"dodge": _on_dodge_requested()
		"end_turn": _on_end_turn_requested()
		_: show_combat_message("Это действие недоступно Ирине.", false)
	_invalidate_reachable_area()
	_refresh_action_catalog()


func _on_feedback_target_requested() -> void:
	if _is_controllable_ally_turn():
		_close_action_catalog_immediately()
		_cycle_ally_target()
		return
	super._on_feedback_target_requested()
	if _turn_system.active and _turn_system.is_actor_turn(player):
		_party_control_context.set_target(player, _selected_target)


func _cycle_ally_target() -> void:
	var targets: Array[Node] = []
	for candidate: Node in _available_targets():
		if _target_is_valid(candidate):
			targets.append(candidate)
	if targets.is_empty():
		_set_selected_target(null)
		_party_control_context.clear_target(_controllable_ally)
		show_combat_message("Для Ирины нет доступных вражеских целей.", false)
		return
	var current: Node = _party_control_context.target_for(_controllable_ally)
	var current_index: int = targets.find(current)
	var next_target: Node = targets[0] if current_index < 0 or current_index + 1 >= targets.size() else targets[current_index + 1]
	_party_control_context.set_target(_controllable_ally, next_target)
	_set_selected_target(next_target)
	_update_target_label()
	show_combat_message("Ирина выбирает цель: %s." % _target_name(next_target), true)


func _update_target_label() -> void:
	super._update_target_label()
	if _target_label == null or not _is_controllable_ally_turn():
		return
	if not _target_is_valid(_selected_target) or not _controllable_ally is Node2D:
		_target_label.text = "Ход Ирины · цель не выбрана"
		return
	var distance: int = DistanceSystem.distance_feet(
		(_controllable_ally as Node2D).global_position,
		(_selected_target as Node2D).global_position
	)
	_target_label.text = "Ирина → %s · %d футов · КД %d" % [
		_target_name(_selected_target),
		distance,
		int(_selected_target.call("get_armor_class"))
	]


func _clear_party_input() -> void:
	_party_mobile_vector = Vector2.ZERO
	_party_last_step = Vector2i.ZERO
	_party_move_cooldown = 0.0
	_clear_primary_player_facing_input()


func _clear_primary_player_facing_input() -> void:
	if is_instance_valid(player) and player.has_method("clear_mobile_facing_input"):
		player.call("clear_mobile_facing_input")


func _active_party_actor() -> Node:
	if not _turn_system.active or not _turn_system.is_player_controlled_turn() or _enemy_turn_running:
		return null
	var actor: Node = _turn_system.current_actor()
	if actor == player or actor == _controllable_ally:
		return actor
	return null


func _active_party_state() -> CombatantState:
	var actor: Node = _active_party_actor()
	return _state_for(actor) if is_instance_valid(actor) else null


func _active_party_speed_feet() -> int:
	var actor: Node = _active_party_actor()
	if is_instance_valid(actor) and actor.has_method("get_combat_speed_feet"):
		return maxi(int(actor.call("get_combat_speed_feet")), 0)
	return 30


func _party_turn_input_available() -> bool:
	return (
		is_instance_valid(_active_party_actor())
		and not GameState.input_locked
		and not _any_overlay_visible()
		and not _attack_in_progress
		and not _enemy_turn_running
	)


func _remember_target_for_active_actor() -> void:
	var actor: Node = _party_control_context.active_actor()
	if is_instance_valid(actor):
		_party_control_context.set_target(actor, _selected_target)


func _restore_target_for_active_actor() -> void:
	var actor: Node = _party_control_context.active_actor()
	if not is_instance_valid(actor):
		return
	var target: Node = _party_control_context.target_for(actor)
	if not _target_is_valid(target):
		_party_control_context.clear_target(actor)
		target = null
	_set_selected_target(target)
	_update_target_label()


func get_active_controlled_actor_instance_id_for_testing() -> int:
	var actor: Node = _active_party_actor()
	return actor.get_instance_id() if is_instance_valid(actor) else 0


func set_party_target_for_testing(actor: Node, target: Node) -> void:
	_party_control_context.set_target(actor, target)
	if _party_control_context.owns_input(actor):
		_set_selected_target(target)
		_update_target_label()


func get_party_target_instance_id_for_testing(actor: Node) -> int:
	return _party_control_context.get_target_instance_id_for_testing(actor)


func get_planned_movement_owner_instance_id_for_testing() -> int:
	var actor: Node = _active_party_actor()
	return actor.get_instance_id() if _planned_path.size() > 1 and is_instance_valid(actor) else 0


func get_planned_path_for_testing() -> Array[Vector2i]:
	return _planned_path.duplicate()


func plan_active_actor_to_cell_for_testing(cell: Vector2i) -> void:
	_plan_to_cell(cell)


func confirm_active_actor_movement_for_testing() -> void:
	_confirm_planned_movement()
