extends "res://scripts/game/game_srd_combat.gd"

const PLANNED_MOVEMENT_SYSTEM_SCRIPT: Script = preload("res://scripts/systems/planned_movement_system.gd")
const MOVEMENT_PLAN_OVERLAY_SCRIPT: Script = preload("res://scripts/game/movement_plan_overlay.gd")
const ACTION_CATALOG_UI_SCRIPT: Script = preload("res://scripts/ui/action_catalog_ui.gd")
const INVALID_ROUTE_CELL: Vector2i = Vector2i(-99999, -99999)

var _movement_planner: PlannedMovementSystem = PLANNED_MOVEMENT_SYSTEM_SCRIPT.new() as PlannedMovementSystem
var _movement_plan_overlay: MovementPlanOverlay
var _action_catalog_ui: ActionCatalogUI
var _planned_path: Array[Vector2i] = []
var _planned_jump_indices: Array[int] = []
var _planned_cost_feet: int = 0
var _movement_execution_running: bool = false
var _jump_in_progress: bool = false
var _route_pointer_index: int = -1
var _route_drawing: bool = false
var _last_route_pointer_cell: Vector2i = INVALID_ROUTE_CELL
var _pending_jump_direction: Vector2i = Vector2i.ZERO
var _reachable_signature: String = ""


func _ready() -> void:
	super._ready()
	_movement_plan_overlay = MOVEMENT_PLAN_OVERLAY_SCRIPT.new() as MovementPlanOverlay
	_movement_plan_overlay.name = "MovementPlanOverlay"
	add_child(_movement_plan_overlay)
	_movement_plan_overlay.bind_grid(_get_battle_grid())
	_action_catalog_ui = ACTION_CATALOG_UI_SCRIPT.new() as ActionCatalogUI
	_action_catalog_ui.name = "ActionCatalogUI"
	$Interface.add_child(_action_catalog_ui)
	_action_catalog_ui.action_requested.connect(_on_catalog_action_requested)
	_action_catalog_ui.jump_requested.connect(_on_exploration_jump_requested)
	_refresh_reachable_area(true)
	_refresh_action_catalog()


func _process(delta: float) -> void:
	super._process(delta)
	_apply_catalog_visibility_rules()
	_refresh_reachable_area()
	_refresh_action_catalog()


func _unhandled_input(event: InputEvent) -> void:
	if _can_plan_movement():
		if event is InputEventScreenTouch:
			var touch := event as InputEventScreenTouch
			if touch.pressed and _route_pointer_index < 0:
				var touch_cell: Vector2i = _cell_from_screen_position(touch.position)
				if touch_cell != INVALID_ROUTE_CELL:
					_route_pointer_index = touch.index
					_route_drawing = true
					_last_route_pointer_cell = touch_cell
					_pending_jump_direction = Vector2i.ZERO
					_handle_route_press(touch_cell)
					get_viewport().set_input_as_handled()
					return
			elif not touch.pressed and touch.index == _route_pointer_index:
				_end_route_pointer()
				get_viewport().set_input_as_handled()
				return
		elif event is InputEventScreenDrag:
			var drag := event as InputEventScreenDrag
			if drag.index == _route_pointer_index and _route_drawing:
				var drag_cell: Vector2i = _cell_from_screen_position(drag.position)
				if drag_cell != INVALID_ROUTE_CELL:
					_handle_route_drag(drag_cell)
					get_viewport().set_input_as_handled()
					return
		elif event is InputEventMouseButton:
			var mouse := event as InputEventMouseButton
			if mouse.button_index == MOUSE_BUTTON_LEFT:
				if mouse.pressed and _route_pointer_index < 0:
					var mouse_cell: Vector2i = _cell_from_screen_position(mouse.position)
					if mouse_cell != INVALID_ROUTE_CELL:
						_route_pointer_index = -2
						_route_drawing = true
						_last_route_pointer_cell = mouse_cell
						_pending_jump_direction = Vector2i.ZERO
						_handle_route_press(mouse_cell)
						get_viewport().set_input_as_handled()
						return
				elif not mouse.pressed and _route_pointer_index == -2:
					_end_route_pointer()
					get_viewport().set_input_as_handled()
					return
		elif event is InputEventMouseMotion and _route_pointer_index == -2 and _route_drawing:
			var motion := event as InputEventMouseMotion
			var motion_cell: Vector2i = _cell_from_screen_position(motion.position)
			if motion_cell != INVALID_ROUTE_CELL:
				_handle_route_drag(motion_cell)
				get_viewport().set_input_as_handled()
				return
	super._unhandled_input(event)


func request_combat_move(step: Vector2i) -> void:
	if not _can_plan_movement() or step == Vector2i.ZERO:
		return
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return
	var base_cell: Vector2i = grid.world_to_cell(player.global_position)
	if not _planned_path.is_empty():
		base_cell = _planned_path[_planned_path.size() - 1]
	_append_drawn_cell(base_cell + step)


func _cell_from_screen_position(screen_position: Vector2) -> Vector2i:
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return INVALID_ROUTE_CELL
	var world_position: Vector2 = get_viewport().get_canvas_transform().affine_inverse() * screen_position
	var cell: Vector2i = grid.world_to_cell(world_position)
	return cell if grid.is_cell_valid(cell) else INVALID_ROUTE_CELL


func _handle_route_press(cell: Vector2i) -> void:
	if _planned_path.has(cell):
		_trim_route_from_cell(cell)
		return
	_plan_to_cell(cell)


func _handle_route_drag(cell: Vector2i) -> void:
	if cell == _last_route_pointer_cell:
		return
	var cells: Array[Vector2i] = _cells_along_line(_last_route_pointer_cell, cell)
	for index: int in range(1, cells.size()):
		_append_drawn_cell(cells[index])
	_last_route_pointer_cell = cell


func _end_route_pointer() -> void:
	_route_pointer_index = -1
	_route_drawing = false
	_last_route_pointer_cell = INVALID_ROUTE_CELL
	_pending_jump_direction = Vector2i.ZERO


func _cells_along_line(start_cell: Vector2i, end_cell: Vector2i) -> Array[Vector2i]:
	var result: Array[Vector2i] = []
	var delta: Vector2i = end_cell - start_cell
	var steps: int = maxi(absi(delta.x), absi(delta.y))
	if steps <= 0:
		return [start_cell]
	for index: int in range(steps + 1):
		var ratio: float = float(index) / float(steps)
		var cell := Vector2i(
			roundi(lerpf(float(start_cell.x), float(end_cell.x), ratio)),
			roundi(lerpf(float(start_cell.y), float(end_cell.y), ratio))
		)
		if result.is_empty() or result[result.size() - 1] != cell:
			result.append(cell)
	return result


func _append_drawn_cell(destination_cell: Vector2i) -> void:
	if not _can_plan_movement():
		return
	var grid: BattleGrid = _get_battle_grid()
	if grid == null or not grid.is_cell_valid(destination_cell):
		return
	if _planned_path.is_empty():
		_planned_path = [grid.world_to_cell(player.global_position)]
	if _planned_path.has(destination_cell):
		_trim_route_from_cell(destination_cell)
		return
	var tail: Vector2i = _planned_path[_planned_path.size() - 1]
	var occupied: Dictionary = _occupied_cells(player)
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
	var distance_cells: int = maxi(absi(delta.x), absi(delta.y))
	if distance_cells == 1:
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
		_player_combat_state,
		remaining_budget,
		_player_combat_state.grappling_target_id != 0,
		true
	)
	if not bool(segment.get("reachable", false)):
		return
	var segment_path: Array[Vector2i] = segment.get("path", []) as Array[Vector2i]
	var combined: Array[Vector2i] = _planned_path.duplicate()
	for index: int in range(1, segment_path.size()):
		combined.append(segment_path[index])
	_apply_candidate_path(combined)


func _plan_to_world_position(world_position: Vector2) -> void:
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return
	_plan_to_cell(grid.world_to_cell(world_position))


func _plan_to_cell(destination_cell: Vector2i) -> void:
	if not _can_plan_movement():
		return
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return
	if not grid.is_cell_valid(destination_cell):
		show_combat_message("Выбранная клетка находится за пределами поля боя.", false)
		return
	if _combat_environment != null and _combat_environment.is_cell_blocked(grid, destination_cell):
		show_combat_message("Нельзя закончить перемещение в клетке препятствия.", false)
		return
	var start_cell: Vector2i = grid.world_to_cell(player.global_position)
	var result: Dictionary = _movement_planner.build_path(
		grid,
		start_cell,
		destination_cell,
		_occupied_cells(player),
		_combat_environment,
		_player_combat_state,
		_turn_system.movement_remaining_feet,
		_player_combat_state.grappling_target_id != 0,
		true
	)
	if not bool(result.get("reachable", false)):
		show_combat_message(str(result.get("reason", "Путь недоступен.")), false)
		return
	_set_plan_from_result(result)


func _apply_candidate_path(candidate: Array[Vector2i]) -> void:
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return
	var result: Dictionary = _movement_planner.evaluate_path(
		grid,
		candidate,
		_occupied_cells(player),
		_combat_environment,
		_player_combat_state,
		_turn_system.movement_remaining_feet,
		_player_combat_state.grappling_target_id != 0
	)
	if not bool(result.get("reachable", false)):
		show_combat_message(str(result.get("reason", "Эту часть маршрута добавить нельзя.")), false)
		return
	_set_plan_from_result(result)


func _set_plan_from_result(result: Dictionary) -> void:
	_planned_path = result.get("path", []) as Array[Vector2i]
	_planned_cost_feet = int(result.get("cost_feet", 0))
	_planned_jump_indices = result.get("jump_indices", []) as Array[int]
	_movement_plan_overlay.set_plan(_planned_path, _planned_cost_feet, true, _planned_jump_indices)
	var warning: String = _opportunity_warning_for_path(_planned_path)
	var message: String = "Маршрут выбран: %d футов." % _planned_cost_feet
	if not _planned_jump_indices.is_empty():
		message += " Прыжок будет выполнен автоматически."
	if not warning.is_empty():
		message += " %s" % warning
	show_combat_message(message, warning.is_empty())
	_refresh_action_catalog()


func _trim_route_from_cell(cell: Vector2i) -> void:
	var index: int = _planned_path.find(cell)
	if index < 0:
		return
	if index <= 1:
		_clear_movement_plan()
		show_combat_message("Маршрут удалён от выбранной клетки до конца.", true)
		return
	var shortened: Array[Vector2i] = []
	for path_index: int in range(index):
		shortened.append(_planned_path[path_index])
	_apply_candidate_path(shortened)
	show_combat_message("Хвост маршрута удалён, включая нажатую клетку.", true)


func _confirm_planned_movement() -> void:
	if _movement_execution_running or not _can_plan_movement() or _planned_path.size() < 2:
		return
	_execute_planned_path()


func _execute_planned_path() -> void:
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return
	var validation: Dictionary = _movement_planner.evaluate_path(
		grid,
		_planned_path,
		_occupied_cells(player),
		_combat_environment,
		_player_combat_state,
		_turn_system.movement_remaining_feet,
		_player_combat_state.grappling_target_id != 0
	)
	if not bool(validation.get("reachable", false)):
		show_combat_message(str(validation.get("reason", "Маршрут больше недоступен.")), false)
		_clear_movement_plan()
		return
	_movement_execution_running = true
	if _action_catalog_ui != null:
		_action_catalog_ui.close_catalog()
	var path_copy: Array[Vector2i] = _planned_path.duplicate()
	for index: int in range(1, path_copy.size()):
		if not _turn_system.active or not _turn_system.is_player_turn(player):
			break
		var from_cell: Vector2i = grid.world_to_cell(player.global_position)
		var destination_cell: Vector2i = path_copy[index]
		var transition_path: Array[Vector2i] = [from_cell, destination_cell]
		var transition: Dictionary = _movement_planner.evaluate_path(
			grid,
			transition_path,
			_occupied_cells(player),
			_combat_environment,
			_player_combat_state,
			_turn_system.movement_remaining_feet,
			_player_combat_state.grappling_target_id != 0
		)
		if not bool(transition.get("reachable", false)):
			show_combat_message("Маршрут прерван: следующая часть стала недоступной.", false)
			break
		var movement_cost: int = int(transition.get("cost_feet", 0))
		var destination: Vector2 = grid.cell_to_world_center(destination_cell)
		if not _turn_system.disengaged:
			_trigger_enemy_opportunity_attacks(player.global_position, destination)
			if _player_combat_state.dead or GameState.player_character.current_health <= 0:
				break
		if not _turn_system.spend_movement(movement_cost):
			break
		var previous_position: Vector2 = player.global_position
		var direction: Vector2 = destination - previous_position
		if player.has_method("set_facing_direction"):
			player.call("set_facing_direction", direction)
		var is_jump: bool = maxi(absi(destination_cell.x - from_cell.x), absi(destination_cell.y - from_cell.y)) > 1
		if is_jump:
			await _animate_combat_jump(destination, direction)
		else:
			var tween: Tween = create_tween()
			tween.tween_property(player, "global_position", destination, 0.12)
			await tween.finished
		GameState.player_position = destination
		_drag_grappled_target(previous_position)
	_clear_movement_plan()
	_movement_execution_running = false
	_invalidate_reachable_area()
	_refresh_turn_interface()
	_refresh_srd_interface()
	_refresh_action_catalog()


func _animate_combat_jump(destination: Vector2, direction: Vector2) -> void:
	var body: Node2D = player.get_node_or_null("Body") as Node2D
	var original_body_position: Vector2 = body.position if body != null else Vector2.ZERO
	var distance: float = player.global_position.distance_to(destination)
	var duration: float = clampf(distance / 420.0, 0.28, 0.52)
	var movement_tween: Tween = create_tween()
	movement_tween.set_trans(Tween.TRANS_SINE)
	movement_tween.set_ease(Tween.EASE_IN_OUT)
	movement_tween.tween_property(player, "global_position", destination, duration)
	if body != null:
		var arc_tween: Tween = create_tween()
		arc_tween.tween_property(body, "position", original_body_position + Vector2(0.0, -34.0), duration * 0.5)
		arc_tween.tween_property(body, "position", original_body_position, duration * 0.5)
	await movement_tween.finished
	player.global_position = destination
	if player.has_method("set_facing_direction"):
		player.call("set_facing_direction", direction)


func _cancel_planned_movement() -> void:
	_clear_movement_plan()
	show_combat_message("Запланированный маршрут отменён.", true)


func _clear_movement_plan() -> void:
	_planned_path.clear()
	_planned_jump_indices.clear()
	_planned_cost_feet = 0
	_pending_jump_direction = Vector2i.ZERO
	if _movement_plan_overlay != null:
		_movement_plan_overlay.clear_plan()
	_refresh_action_catalog()


func _begin_current_turn() -> void:
	_clear_movement_plan()
	_invalidate_reachable_area()
	super._begin_current_turn()


func _advance_combat_turn() -> void:
	_clear_movement_plan()
	if _action_catalog_ui != null:
		_action_catalog_ui.close_catalog()
	_invalidate_reachable_area()
	super._advance_combat_turn()


func _stop_turn_based_combat(message: String) -> void:
	_clear_movement_plan()
	if _action_catalog_ui != null:
		_action_catalog_ui.close_catalog()
	if _movement_plan_overlay != null:
		_movement_plan_overlay.clear_reachable_cells()
	_reachable_signature = ""
	super._stop_turn_based_combat(message)
	_refresh_action_catalog()


func _snap_combatants_to_cells() -> void:
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return
	var occupied: Dictionary = {}
	var player_cell: Vector2i = _nearest_walkable_cell(grid, player.global_position, occupied)
	player.global_position = grid.cell_to_world_center(player_cell)
	occupied[player_cell] = player
	GameState.player_position = player.global_position
	for target: Node in _available_targets():
		if target is Node2D:
			var target_cell: Vector2i = _nearest_walkable_cell(grid, (target as Node2D).global_position, occupied)
			(target as Node2D).global_position = grid.cell_to_world_center(target_cell)
			occupied[target_cell] = target


func _nearest_walkable_cell(grid: BattleGrid, world_position: Vector2, occupied: Dictionary) -> Vector2i:
	var field: Rect2 = grid.get_field_rect()
	var size: float = grid.get_cell_size()
	var columns: int = maxi(floori(field.size.x / size), 1)
	var rows: int = maxi(floori(field.size.y / size), 1)
	var origin: Vector2i = grid.world_to_cell(world_position)
	origin.x = clampi(origin.x, 0, columns - 1)
	origin.y = clampi(origin.y, 0, rows - 1)
	var maximum_radius: int = maxi(columns, rows)
	for radius: int in range(0, maximum_radius + 1):
		var best_cell: Vector2i = origin
		var best_distance: float = INF
		for x_offset: int in range(-radius, radius + 1):
			for y_offset: int in range(-radius, radius + 1):
				if radius > 0 and maxi(absi(x_offset), absi(y_offset)) != radius:
					continue
				var candidate: Vector2i = origin + Vector2i(x_offset, y_offset)
				if not grid.is_cell_valid(candidate) or occupied.has(candidate):
					continue
				if _combat_environment != null and _combat_environment.is_cell_blocked(grid, candidate):
					continue
				var distance: float = grid.cell_to_world_center(candidate).distance_squared_to(world_position)
				if distance < best_distance:
					best_distance = distance
					best_cell = candidate
		if best_distance < INF:
			return best_cell
	return grid.nearest_free_cell(world_position, occupied)


func _on_exploration_jump_requested() -> void:
	if _turn_system.active or _jump_in_progress or GameState.input_locked or _any_overlay_visible():
		return
	var grid: BattleGrid = _get_battle_grid()
	if grid == null or _combat_environment == null:
		return
	var facing: Vector2 = _get_player_facing_direction()
	var step := Vector2i(
		int(signf(facing.x)) if absf(facing.x) >= 0.25 else 0,
		int(signf(facing.y)) if absf(facing.y) >= 0.25 else 0
	)
	if step == Vector2i.ZERO:
		step = Vector2i.RIGHT
	var origin_cell: Vector2i = grid.world_to_cell(player.global_position)
	var landing_cell: Vector2i = _combat_environment.get_jump_landing_cell(grid, origin_cell, step, _occupied_cells(player))
	if landing_cell == CombatEnvironment.INVALID_CELL:
		show_combat_message("В направлении движения нет подходящего препятствия или свободной клетки приземления.", false)
		return
	_perform_exploration_jump(grid.cell_to_world_center(landing_cell), Vector2(step))


func _perform_exploration_jump(landing_position: Vector2, direction: Vector2) -> void:
	_jump_in_progress = true
	GameState.input_locked = true
	if player.has_method("set_facing_direction"):
		player.call("set_facing_direction", direction)
	var body: Node2D = player.get_node_or_null("Body") as Node2D
	var original_body_position: Vector2 = body.position if body != null else Vector2.ZERO
	var movement_tween: Tween = create_tween()
	movement_tween.set_trans(Tween.TRANS_SINE)
	movement_tween.set_ease(Tween.EASE_IN_OUT)
	movement_tween.tween_property(player, "global_position", landing_position, 0.38)
	if body != null:
		var arc_tween: Tween = create_tween()
		arc_tween.tween_property(body, "position", original_body_position + Vector2(0.0, -28.0), 0.19)
		arc_tween.tween_property(body, "position", original_body_position, 0.19)
	await movement_tween.finished
	player.global_position = landing_position
	GameState.player_position = landing_position
	GameState.input_locked = false
	_jump_in_progress = false
	show_combat_message("Прыжок выполнен.", true)


func _on_catalog_action_requested(action_id: String) -> void:
	match action_id:
		"confirm_move": _confirm_planned_movement()
		"cancel_move": _cancel_planned_movement()
		"attack": _request_attack()
		"dash": _on_dash_requested()
		"disengage": _on_disengage_requested()
		"dodge": _on_dodge_requested()
		"prone_toggle": _on_prone_toggle_requested()
		"grapple": _on_grapple_requested()
		"shove_prone": _on_shove_prone_requested()
		"shove_push": _on_shove_push_requested()
		"escape_grapple": _on_escape_grapple_requested()
		"ready_attack": _on_ready_attack_requested()
		"hide": _on_hide_requested()
		"end_turn": _on_end_turn_requested()
		_:
			if action_id.begins_with("ability:"):
				_on_ability_requested(action_id.trim_prefix("ability:"))
	_invalidate_reachable_area()
	_refresh_action_catalog()


func _build_catalog_entries() -> Dictionary:
	var player_turn: bool = _turn_system.active and _turn_system.is_player_turn(player) and not _enemy_turn_running
	var can_act: bool = player_turn and _turn_system.action_available and _srd_rules.can_take_action(_player_combat_state)
	var can_bonus: bool = player_turn and _turn_system.bonus_action_available and _srd_rules.can_take_action(_player_combat_state)
	var target_melee: bool = _target_is_valid(_selected_target) and DistanceSystem.distance_feet(player.global_position, (_selected_target as Node2D).global_position) <= 5
	var action_entries: Array[Dictionary] = [
		_entry("attack", "АТАКА", can_act, "Обычная атака экипированным оружием. Расходует действие.", "attack"),
		_entry("grapple", "ЗАХВАТ", can_act and target_melee, "Попытаться захватить выбранную соседнюю цель.", "attack"),
		_entry("shove_prone", "СБИТЬ", can_act and target_melee, "Попытаться сбить выбранную соседнюю цель с ног.", "attack"),
		_entry("shove_push", "ТОЛКНУТЬ", can_act and target_melee, "Попытаться оттолкнуть цель на одну клетку.", "attack"),
		_entry("ready_attack", "ПОДГОТОВИТЬ АТАКУ", can_act, "Потратить действие и атаковать реакцией при выполнении условия.", "attack"),
		_entry("cancel_move", "ОТМЕНИТЬ ПУТЬ", _planned_path.size() > 1 and player_turn, "Удалить весь выбранный маршрут без расхода перемещения.", "movement"),
		_entry("dash", "РЫВОК", can_act, "Добавить к перемещению значение скорости. Расходует действие.", "movement"),
		_entry("disengage", "ОТХОД", can_act, "До конца хода выход из досягаемости не вызывает атак по возможности.", "movement"),
		_entry("prone_toggle", "ВСТАТЬ" if _player_combat_state.has_condition("prone") else "ЛЕЧЬ", player_turn and not _player_combat_state.has_condition("grappled") and (not _player_combat_state.has_condition("prone") or _turn_system.movement_remaining_feet >= 15), "Лечь бесплатно или встать, потратив половину базовой скорости.", "movement"),
		_entry("escape_grapple", "ВЫРВАТЬСЯ", can_act and _player_combat_state.has_condition("grappled"), "Попытаться освободиться из захвата.", "movement"),
		_entry("dodge", "УКЛОНЕНИЕ", can_act, "Атаки видимых противников получают помеху до начала следующего хода.", "tactic"),
		_entry("hide", "СКРЫТЬСЯ", can_act, "Попытаться скрыться от противников. Расходует действие.", "tactic")
	]
	var bonus_entries: Array[Dictionary] = []
	var signature: Dictionary = _class_data.get_signature_ability(GameState.player_character)
	if not signature.is_empty():
		var ability_id: String = str(signature.get("id", GameState.player_character.signature_ability_id))
		var label: String = str(signature.get("name", "Классовая способность"))
		var kind: String = _ability_action_kind(ability_id, signature)
		var enabled: bool = (can_bonus if kind == "bonus" else can_act) and _ability_attempt_is_valid(signature)
		var ability_entry: Dictionary = _entry(
			"ability:%s" % ability_id,
			label,
			enabled,
			"%s. Ресурс: %s." % ["Дополнительное действие" if kind == "bonus" else "Действие", _class_data.get_resource_text(GameState.player_character, signature)],
			_ability_catalog_group(signature)
		)
		if kind == "bonus":
			bonus_entries.append(ability_entry)
		else:
			action_entries.append(ability_entry)
	var reaction_entries: Array[Dictionary] = [
		_entry("reaction_status", "РЕАКЦИЯ ГОТОВА" if _turn_system.has_reaction(player) else "РЕАКЦИЯ ИСПОЛЬЗОВАНА", false, "Реакция расходуется атакой по возможности или подготовленным действием.", "tactic"),
		_entry("ready_status", "АТАКА ПОДГОТОВЛЕНА" if _player_combat_state.readied_attack else "НЕТ ПОДГОТОВЛЕННОЙ АТАКИ", false, "Подготовленная атака срабатывает автоматически при выполнении условия.", "tactic")
	]
	return {"action": action_entries, "bonus": bonus_entries, "reaction": reaction_entries}


func _ability_catalog_group(ability: Dictionary) -> String:
	var effect: String = str(ability.get("effect", ""))
	var resource_key: String = str(ability.get("resource_key", ""))
	if "spell" in effect or "spell_slot" in resource_key or bool(ability.get("is_spell", false)):
		return "spell"
	return "tactic"


func _entry(action_id: String, label: String, enabled: bool, description: String, group: String = "tactic") -> Dictionary:
	return {"id": action_id, "label": label, "enabled": enabled, "description": description, "group": group}


func _refresh_action_catalog() -> void:
	if _action_catalog_ui == null:
		return
	var combat_active: bool = _turn_system.active
	var player_turn: bool = combat_active and _turn_system.is_player_turn(player) and not _enemy_turn_running
	var resource_text: String = "Вне боя: кнопка прыжка находится рядом с джойстиком."
	if combat_active:
		resource_text = "Раунд %d · Действие: %s · Доп. действие: %s · Реакция: %s · Перемещение: %d футов" % [
			_turn_system.round_number,
			"готово" if _turn_system.action_available else "использовано",
			"готово" if _turn_system.bonus_action_available else "использовано",
			"готова" if _turn_system.has_reaction(player) else "использована",
			_turn_system.movement_remaining_feet
		]
	var has_plan: bool = _planned_path.size() > 1
	var plan_text: String = "маршрут не выбран" if not has_plan else "маршрут: %d футов" % _planned_cost_feet
	_action_catalog_ui.refresh(
		combat_active,
		player_turn,
		_any_overlay_visible(),
		_build_catalog_entries() if combat_active else {},
		resource_text,
		plan_text,
		has_plan,
		_planned_cost_feet
	)


func _apply_catalog_visibility_rules() -> void:
	if _turn_system.active:
		if _turn_ui != null:
			_turn_ui.hide()
		if _srd_combat_ui != null:
			_srd_combat_ui.hide()
		if _attack_button != null:
			_attack_button.hide()
		if _ability_panel != null:
			_ability_panel.hide()
	else:
		if _attack_button != null:
			_attack_button.visible = _uses_touch_controls() and not _any_overlay_visible()
		if _ability_panel != null and not _any_overlay_visible():
			_ability_panel.show()


func _refresh_reachable_area(force: bool = false) -> void:
	if _movement_plan_overlay == null:
		return
	if not _turn_system.active or not _turn_system.is_player_turn(player) or _enemy_turn_running:
		if not _reachable_signature.is_empty() or force:
			_reachable_signature = ""
			_movement_plan_overlay.clear_reachable_cells()
		return
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return
	var occupied: Dictionary = _occupied_cells(player)
	var occupied_parts: Array[String] = []
	for key: Variant in occupied.keys():
		occupied_parts.append(str(key))
	occupied_parts.sort()
	var signature: String = "|".join([
		str(grid.world_to_cell(player.global_position)),
		str(_turn_system.movement_remaining_feet),
		str(_player_combat_state.has_condition("prone")),
		str(_player_combat_state.has_condition("grappled")),
		str(_player_combat_state.has_condition("restrained")),
		str(_player_combat_state.grappling_target_id),
		",".join(occupied_parts)
	])
	if not force and signature == _reachable_signature:
		return
	_reachable_signature = signature
	var reachable: Dictionary = _movement_planner.calculate_reachable_cells(
		grid,
		grid.world_to_cell(player.global_position),
		occupied,
		_combat_environment,
		_player_combat_state,
		_turn_system.movement_remaining_feet,
		_player_combat_state.grappling_target_id != 0,
		true
	)
	_movement_plan_overlay.set_reachable_cells(reachable, _turn_system.movement_remaining_feet)


func _invalidate_reachable_area() -> void:
	_reachable_signature = ""


func _opportunity_warning_for_path(path: Array[Vector2i]) -> String:
	if _turn_system.disengaged or path.size() < 2:
		return ""
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return ""
	for index: int in range(1, path.size()):
		var from_position: Vector2 = grid.cell_to_world_center(path[index - 1])
		var to_position: Vector2 = grid.cell_to_world_center(path[index])
		if _step_leaves_hostile_reach(from_position, to_position):
			return "Маршрут провоцирует атаку по возможности при выходе из досягаемости."
	return ""


func _step_leaves_hostile_reach(from_position: Vector2, to_position: Vector2) -> bool:
	for entry: Dictionary in _turn_system.entries:
		if bool(entry.get("is_player", false)):
			continue
		var actor: Node = entry.get("node") as Node
		if not is_instance_valid(actor) or not (actor is Node2D) or not _turn_system.has_reaction(actor):
			continue
		if actor.has_method("is_hostile") and not bool(actor.call("is_hostile")):
			continue
		var actor_state: CombatantState = _state_for(actor)
		if not _srd_rules.can_take_reaction(actor_state):
			continue
		if _combat_environment != null and not _combat_environment.has_line_of_sight((actor as Node2D).global_position, from_position):
			continue
		var current_distance: int = DistanceSystem.distance_feet((actor as Node2D).global_position, from_position)
		var future_distance: int = DistanceSystem.distance_feet((actor as Node2D).global_position, to_position)
		if current_distance <= DistanceSystem.MELEE_REACH_FEET and future_distance > DistanceSystem.MELEE_REACH_FEET:
			return true
	return false


func _trigger_enemy_opportunity_attacks(from_position: Vector2, to_position: Vector2) -> void:
	if _turn_system.disengaged:
		return
	for entry: Dictionary in _turn_system.entries:
		if bool(entry.get("is_player", false)):
			continue
		var actor: Node = entry.get("node") as Node
		if not is_instance_valid(actor) or not (actor is Node2D):
			continue
		if actor.has_method("is_hostile") and not bool(actor.call("is_hostile")):
			continue
		if not _turn_system.has_reaction(actor):
			continue
		var actor_state: CombatantState = _state_for(actor)
		if not _srd_rules.can_take_reaction(actor_state):
			continue
		if _combat_environment != null and not _combat_environment.has_line_of_sight((actor as Node2D).global_position, from_position):
			continue
		var current_distance: int = DistanceSystem.distance_feet((actor as Node2D).global_position, from_position)
		var future_distance: int = DistanceSystem.distance_feet((actor as Node2D).global_position, to_position)
		# D&D: перемещение внутри досягаемости не провоцирует реакцию; триггер — именно выход из неё.
		if current_distance <= DistanceSystem.MELEE_REACH_FEET and future_distance > DistanceSystem.MELEE_REACH_FEET:
			_turn_system.consume_reaction(actor)
			if actor.has_method("perform_opportunity_attack"):
				actor.call("perform_opportunity_attack")
				if GameState.player_character.current_health <= 0:
					return


func _can_plan_movement() -> bool:
	return (
		_turn_system.active
		and _turn_system.is_player_turn(player)
		and not _enemy_turn_running
		and not _movement_execution_running
		and not GameState.input_locked
		and not _any_overlay_visible()
		and (_action_catalog_ui == null or not _action_catalog_ui.is_catalog_open())
		and _srd_rules.effective_speed_feet(30, _player_combat_state) > 0
	)
