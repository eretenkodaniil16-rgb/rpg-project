extends "res://scripts/game/game_controllable_ally_runtime.gd"

const ALLY_GRID_STEP_FEET: int = 5


func _begin_controllable_ally_turn() -> void:
	super._begin_controllable_ally_turn()
	if not _is_controllable_ally_turn():
		return
	var grid: BattleGrid = _get_battle_grid()
	if grid != null:
		grid.set_active_actor(_controllable_ally)


func _snap_combatants_to_cells() -> void:
	super._snap_combatants_to_cells()
	if not _ally_is_combat_active() or not _controllable_ally is Node2D:
		return
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return
	var occupied: Dictionary = {}
	if is_instance_valid(player):
		occupied[grid.world_to_cell(player.global_position)] = player
	for target: Node in _available_targets():
		if target is Node2D and is_instance_valid(target):
			occupied[grid.world_to_cell((target as Node2D).global_position)] = target
	var ally_cell: Vector2i = grid.snap_actor_to_free_cell(_controllable_ally as Node2D, occupied)
	occupied[ally_cell] = _controllable_ally


func _request_attack() -> void:
	if _is_controllable_ally_turn():
		await _request_controllable_ally_attack()
		return
	await super._request_attack()


func _request_controllable_ally_attack(
	target_override: Node = null,
	roll_override: int = -1
) -> Dictionary:
	if not _ally_turn_input_available():
		return {"success": false, "status": "turn_unavailable"}
	var target: Node = target_override
	if not _target_is_valid(target):
		target = _selected_target
	if not _target_is_valid(target):
		_cycle_ally_target()
		target = _selected_target
	if not _target_is_valid(target):
		show_combat_message("Для атаки Ирны выберите доступного противника.", false)
		return {"success": false, "status": "target_required"}
	if not _controllable_ally.has_method("build_basic_attack_result"):
		return {"success": false, "status": "attack_contract_missing"}
	var result: AttackResult = _controllable_ally.call(
		"build_basic_attack_result",
		target,
		roll_override
	) as AttackResult
	if result == null:
		return {"success": false, "status": "result_missing"}
	if result.out_of_range:
		if _attack_popup != null:
			_attack_popup.show_result(result)
		show_combat_message(result.note, false)
		return {
			"success": false,
			"status": "out_of_range",
			"distance_feet": result.distance_feet
		}
	if not _turn_system.consume_action():
		show_combat_message("Основное действие Ирны уже использовано.", false)
		return {"success": false, "status": "action_spent"}
	_set_selected_target(target)
	_set_combat_busy(true)
	if _controllable_ally.has_method("play_attack_animation") and target is Node2D:
		_controllable_ally.call("play_attack_animation", (target as Node2D).global_position)
	if _attack_popup != null:
		_attack_popup.show_result(result)
	if _target_is_valid(target) and target.has_method("receive_player_attack"):
		target.call("receive_player_attack", result, true)
	_set_combat_busy(false)
	_update_status()
	_after_player_action()
	return {
		"success": true,
		"status": "resolved",
		"hit": result.hit,
		"critical": result.critical,
		"damage": result.damage,
		"natural_roll": result.natural_roll
	}


func request_combat_move(step: Vector2i) -> void:
	if not _is_controllable_ally_turn():
		super.request_combat_move(step)
		return
	_try_move_controllable_ally(step)


func _try_move_controllable_ally(step: Vector2i) -> bool:
	if not _ally_turn_input_available() or step == Vector2i.ZERO:
		return false
	if not _controllable_ally is Node2D:
		return false
	var state: CombatantState = _ally_state()
	if state == null or _srd_rules.effective_speed_feet(_ally_combat_speed(), state) <= 0:
		show_combat_message("Состояние Ирны не позволяет перемещаться.", false)
		return false
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return false
	var ally_node: Node2D = _controllable_ally as Node2D
	var current_cell: Vector2i = grid.world_to_cell(ally_node.global_position)
	var destination_cell: Vector2i = current_cell + step
	if not grid.is_cell_valid(destination_cell):
		show_combat_message("Эта клетка находится за пределами поля боя.", false)
		return false
	if _occupied_cells(_controllable_ally).has(destination_cell):
		show_combat_message("Клетка занята другим участником.", false)
		return false
	if _combat_environment != null:
		if _combat_environment.is_cell_blocked(grid, destination_cell):
			show_combat_message("Клетка перекрыта препятствием.", false)
			return false
		if _combat_environment.is_transition_blocked(grid, current_cell, destination_cell):
			show_combat_message("Между клетками находится стена или закрытая дверь.", false)
			return false
	var destination: Vector2 = grid.cell_to_world_center(destination_cell)
	var difficult: bool = (
		_combat_environment != null
		and _combat_environment.is_difficult_position(destination)
	)
	var movement_cost: int = _srd_rules.movement_cost_feet(
		ALLY_GRID_STEP_FEET,
		state,
		difficult,
		state.has_condition("prone")
	)
	if _turn_system.movement_remaining_feet < movement_cost:
		show_combat_message("Ирне не хватает перемещения: требуется %d футов." % movement_cost, false)
		return false
	if not _turn_system.spend_movement(movement_cost):
		return false
	ally_node.global_position = destination
	_call_ally("set_facing_direction", [Vector2(step)])
	_refresh_turn_interface()
	_update_target_label()
	return true


func _on_dash_requested() -> void:
	if not _is_controllable_ally_turn():
		super._on_dash_requested()
		return
	if not _ally_turn_input_available():
		return
	var speed: int = _ally_combat_speed()
	if _turn_system.use_dash(speed):
		show_combat_message("Ирна выполняет Рывок: добавлено %d футов." % speed, true)
	else:
		show_combat_message("Для Рывка Ирне требуется свободное действие.", false)
	_refresh_turn_interface()


func _on_disengage_requested() -> void:
	if not _is_controllable_ally_turn():
		super._on_disengage_requested()
		return
	if not _ally_turn_input_available():
		return
	if _turn_system.use_disengage():
		show_combat_message("Ирна выполняет Отход.", true)
	else:
		show_combat_message("Для Отхода Ирне требуется свободное действие.", false)
	_refresh_turn_interface()


func _on_dodge_requested() -> void:
	if not _is_controllable_ally_turn():
		super._on_dodge_requested()
		return
	if not _ally_turn_input_available():
		return
	if _turn_system.consume_action():
		_call_ally("set_dodging", [true])
		show_combat_message("Ирна уклоняется до начала своего следующего хода.", true)
	else:
		show_combat_message("Для Уклонения Ирне требуется свободное действие.", false)
	_refresh_turn_interface()


func _on_end_turn_requested() -> void:
	if _is_controllable_ally_turn():
		if _ally_turn_input_available():
			_advance_combat_turn()
		return
	super._on_end_turn_requested()


func _cycle_target() -> void:
	if _is_controllable_ally_turn():
		_cycle_ally_target()
		return
	super._cycle_target()


func _on_feedback_target_requested() -> void:
	if _is_controllable_ally_turn():
		_close_action_catalog_immediately()
		_cycle_ally_target()
		return
	super._on_feedback_target_requested()


func _cycle_ally_target() -> void:
	var targets: Array[Node] = []
	for candidate: Node in _available_targets():
		if _target_is_valid(candidate):
			targets.append(candidate)
	if targets.is_empty():
		_set_selected_target(null)
		show_combat_message("Для Ирны нет доступных вражеских целей.", false)
		return
	var current_index: int = targets.find(_selected_target)
	if current_index < 0 or current_index + 1 >= targets.size():
		_set_selected_target(targets[0])
	else:
		_set_selected_target(targets[current_index + 1])
	_update_target_label()


func _update_target_label() -> void:
	super._update_target_label()
	if (
		_target_label == null
		or not _is_controllable_ally_turn()
		or not _target_is_valid(_selected_target)
		or not _controllable_ally is Node2D
	):
		return
	var distance: int = DistanceSystem.distance_feet(
		(_controllable_ally as Node2D).global_position,
		(_selected_target as Node2D).global_position
	)
	_target_label.text = "Ирна → %s · %d футов · КД %d" % [
		_target_name(_selected_target),
		distance,
		int(_selected_target.call("get_armor_class"))
	]


func _occupied_cells(excluded_actor: Node = null) -> Dictionary:
	var occupied: Dictionary = super._occupied_cells(excluded_actor)
	if (
		_controllable_ally != excluded_actor
		and _ally_is_combat_active()
		and _controllable_ally is Node2D
	):
		var grid: BattleGrid = _get_battle_grid()
		if grid != null:
			occupied[grid.world_to_cell((_controllable_ally as Node2D).global_position)] = _controllable_ally
	return occupied


func _update_combat_controls() -> void:
	super._update_combat_controls()
	if not _is_controllable_ally_turn():
		return
	if _attack_button != null:
		_attack_button.disabled = (
			_attack_in_progress
			or _enemy_turn_running
			or not _turn_system.action_available
		)
	if _target_button != null:
		_target_button.disabled = _attack_in_progress or _enemy_turn_running


func _is_controllable_ally_turn() -> bool:
	return (
		_turn_system.active
		and is_instance_valid(_controllable_ally)
		and _turn_system.is_actor_turn(_controllable_ally)
		and not _enemy_turn_running
	)


func _ally_turn_input_available() -> bool:
	if not _is_controllable_ally_turn():
		return false
	return not GameState.input_locked and not _any_overlay_visible() and not _attack_in_progress


func _ally_combat_speed() -> int:
	return int(_controllable_ally.call("get_combat_speed_feet")) if is_instance_valid(_controllable_ally) and _controllable_ally.has_method("get_combat_speed_feet") else 30


func force_controllable_ally_turn_for_testing() -> void:
	if _turn_system.active and is_instance_valid(_controllable_ally):
		_turn_system.force_current_actor_for_testing(_controllable_ally)
		_begin_current_turn()


func move_controllable_ally_for_testing(step: Vector2i) -> bool:
	return _try_move_controllable_ally(step)


func place_controllable_ally_adjacent_for_testing(target: Node) -> bool:
	if not is_instance_valid(target) or not target is Node2D or not _controllable_ally is Node2D:
		return false
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return false
	var target_cell: Vector2i = grid.world_to_cell((target as Node2D).global_position)
	var occupied: Dictionary = _occupied_cells(_controllable_ally)
	for offset: Vector2i in [Vector2i.LEFT, Vector2i.RIGHT, Vector2i.UP, Vector2i.DOWN]:
		var candidate: Vector2i = target_cell + offset
		if not grid.is_cell_valid(candidate) or occupied.has(candidate):
			continue
		if _combat_environment != null and _combat_environment.is_cell_blocked(grid, candidate):
			continue
		(_controllable_ally as Node2D).global_position = grid.cell_to_world_center(candidate)
		return true
	return false


func perform_controllable_ally_attack_for_testing(
	target: Node,
	roll_override: int
) -> Dictionary:
	return await _request_controllable_ally_attack(target, roll_override)
