extends "res://scripts/game/game_srd_combat.gd"

const PLANNED_MOVEMENT_SYSTEM_SCRIPT: Script = preload("res://scripts/systems/planned_movement_system.gd")
const MOVEMENT_PLAN_OVERLAY_SCRIPT: Script = preload("res://scripts/game/movement_plan_overlay.gd")
const ACTION_CATALOG_UI_SCRIPT: Script = preload("res://scripts/ui/action_catalog_ui.gd")

var _movement_planner: PlannedMovementSystem = PLANNED_MOVEMENT_SYSTEM_SCRIPT.new() as PlannedMovementSystem
var _movement_plan_overlay: MovementPlanOverlay
var _action_catalog_ui: ActionCatalogUI
var _planned_path: Array[Vector2i] = []
var _planned_cost_feet: int = 0
var _movement_execution_running: bool = false
var _jump_in_progress: bool = false


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
	_refresh_action_catalog()


func _process(delta: float) -> void:
	super._process(delta)
	_apply_catalog_visibility_rules()
	_refresh_action_catalog()


func _unhandled_input(event: InputEvent) -> void:
	if _can_plan_movement():
		var screen_position: Vector2 = Vector2.ZERO
		var pressed: bool = false
		if event is InputEventScreenTouch:
			var touch := event as InputEventScreenTouch
			pressed = touch.pressed
			screen_position = touch.position
		elif event is InputEventMouseButton:
			var mouse := event as InputEventMouseButton
			pressed = mouse.pressed and mouse.button_index == MOUSE_BUTTON_LEFT
			screen_position = mouse.position
		if pressed:
			var world_position: Vector2 = get_viewport().get_canvas_transform().affine_inverse() * screen_position
			_plan_to_world_position(world_position)
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
	_plan_to_cell(base_cell + step)


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
		show_combat_message("Нельзя выбрать клетку препятствия для перемещения.", false)
		return
	var start_cell: Vector2i = grid.world_to_cell(player.global_position)
	var occupied: Dictionary = _occupied_cells(player)
	var result: Dictionary = _movement_planner.build_path(
		grid,
		start_cell,
		destination_cell,
		occupied,
		_combat_environment,
		_player_combat_state,
		_turn_system.movement_remaining_feet,
		_player_combat_state.grappling_target_id != 0
	)
	if not bool(result.get("reachable", false)):
		show_combat_message(str(result.get("reason", "Путь недоступен.")), false)
		return
	_planned_path = result.get("path", []) as Array[Vector2i]
	_planned_cost_feet = int(result.get("cost_feet", 0))
	_movement_plan_overlay.set_plan(_planned_path, _planned_cost_feet, true)
	show_combat_message("Маршрут выбран: %d футов. Подтвердите перемещение во вкладке действий." % _planned_cost_feet, true)
	_refresh_action_catalog()


func _confirm_planned_movement() -> void:
	if _movement_execution_running or not _can_plan_movement() or _planned_path.size() < 2:
		return
	_execute_planned_path()


func _execute_planned_path() -> void:
	_movement_execution_running = true
	if _action_catalog_ui != null:
		_action_catalog_ui.close_catalog()
	var grid: BattleGrid = _get_battle_grid()
	var path_copy: Array[Vector2i] = _planned_path.duplicate()
	for index: int in range(1, path_copy.size()):
		if not _turn_system.active or not _turn_system.is_player_turn(player):
			break
		var destination_cell: Vector2i = path_copy[index]
		if _occupied_cells(player).has(destination_cell) or (_combat_environment != null and _combat_environment.is_cell_blocked(grid, destination_cell)):
			show_combat_message("Маршрут прерван: следующая клетка стала недоступной.", false)
			break
		var movement_cost: int = _movement_planner.movement_cost_for_cell(
			grid,
			destination_cell,
			_combat_environment,
			_player_combat_state,
			_player_combat_state.grappling_target_id != 0
		)
		if _turn_system.movement_remaining_feet < movement_cost:
			show_combat_message("Маршрут прерван: перемещение закончилось.", false)
			break
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
		var tween: Tween = create_tween()
		tween.tween_property(player, "global_position", destination, 0.12)
		await tween.finished
		GameState.player_position = destination
		_drag_grappled_target(previous_position)
	_clear_movement_plan()
	_movement_execution_running = false
	_refresh_turn_interface()
	_refresh_srd_interface()
	_refresh_action_catalog()


func _cancel_planned_movement() -> void:
	_clear_movement_plan()
	show_combat_message("Запланированный маршрут отменён.", true)


func _clear_movement_plan() -> void:
	_planned_path.clear()
	_planned_cost_feet = 0
	if _movement_plan_overlay != null:
		_movement_plan_overlay.clear_plan()


func _begin_current_turn() -> void:
	_clear_movement_plan()
	super._begin_current_turn()


func _advance_combat_turn() -> void:
	_clear_movement_plan()
	if _action_catalog_ui != null:
		_action_catalog_ui.close_catalog()
	super._advance_combat_turn()


func _stop_turn_based_combat(message: String) -> void:
	_clear_movement_plan()
	if _action_catalog_ui != null:
		_action_catalog_ui.close_catalog()
	super._stop_turn_based_combat(message)


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
		show_combat_message("В направлении движения нет подходящего препятствия для прыжка или свободной клетки приземления.", false)
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
	_refresh_action_catalog()


func _build_catalog_entries() -> Dictionary:
	var player_turn: bool = _turn_system.active and _turn_system.is_player_turn(player) and not _enemy_turn_running
	var can_act: bool = player_turn and _turn_system.action_available and _srd_rules.can_take_action(_player_combat_state)
	var can_bonus: bool = player_turn and _turn_system.bonus_action_available and _srd_rules.can_take_action(_player_combat_state)
	var target_melee: bool = _target_is_valid(_selected_target) and DistanceSystem.distance_feet(player.global_position, (_selected_target as Node2D).global_position) <= 5
	var movement_entries: Array[Dictionary] = [
		_entry("confirm_move", "ПЕРЕМЕСТИТЬСЯ", _planned_path.size() > 1 and player_turn, "Подтвердить выбранный маршрут и последовательно пройти по нему."),
		_entry("cancel_move", "ОТМЕНИТЬ ПУТЬ", not _planned_path.is_empty() and player_turn, "Удалить текущий маршрут без расхода перемещения."),
		_entry("prone_toggle", "ВСТАТЬ" if _player_combat_state.has_condition("prone") else "ЛЕЧЬ", player_turn and not _player_combat_state.has_condition("grappled") and (not _player_combat_state.has_condition("prone") or _turn_system.movement_remaining_feet >= 15), "Лечь бесплатно или встать, потратив половину базовой скорости.")
	]
	var action_entries: Array[Dictionary] = [
		_entry("attack", "АТАКА", can_act, "Обычная атака экипированным оружием. Расходует действие."),
		_entry("dash", "РЫВОК", can_act, "Добавить к перемещению значение скорости. Расходует действие."),
		_entry("disengage", "ОТХОД", can_act, "До конца хода перемещение не вызывает атак по возможности."),
		_entry("dodge", "УКЛОНЕНИЕ", can_act, "Атаки видимых противников получают помеху до начала следующего хода."),
		_entry("grapple", "ЗАХВАТ", can_act and target_melee, "Попытаться захватить выбранную соседнюю цель."),
		_entry("shove_prone", "СБИТЬ", can_act and target_melee, "Попытаться сбить выбранную соседнюю цель с ног."),
		_entry("shove_push", "ТОЛКНУТЬ", can_act and target_melee, "Попытаться оттолкнуть цель на одну клетку."),
		_entry("escape_grapple", "ВЫРВАТЬСЯ", can_act and _player_combat_state.has_condition("grappled"), "Попытаться освободиться из захвата."),
		_entry("ready_attack", "ПОДГОТОВИТЬ АТАКУ", can_act, "Потратить действие и атаковать реакцией при выполнении условия."),
		_entry("hide", "СКРЫТЬСЯ", can_act, "Попытаться скрыться от противников. Расходует действие."),
		_entry("end_turn", "ЗАВЕРШИТЬ ХОД", player_turn, "Передать ход следующему участнику.")
	]
	var bonus_entries: Array[Dictionary] = []
	var signature: Dictionary = _class_data.get_signature_ability(GameState.player_character)
	if not signature.is_empty():
		var ability_id: String = str(signature.get("id", GameState.player_character.signature_ability_id))
		var label: String = str(signature.get("name", "Классовая способность"))
		var kind: String = _ability_action_kind(ability_id, signature)
		var enabled: bool = (can_bonus if kind == "bonus" else can_act) and _ability_attempt_is_valid(signature)
		var ability_entry: Dictionary = _entry("ability:%s" % ability_id, label, enabled, "%s. Ресурс: %s." % ["Дополнительное действие" if kind == "bonus" else "Действие", _class_data.get_resource_text(GameState.player_character, signature)])
		if kind == "bonus":
			bonus_entries.append(ability_entry)
		else:
			action_entries.append(ability_entry)
	var reaction_entries: Array[Dictionary] = [
		_entry("reaction_status", "РЕАКЦИЯ ГОТОВА" if _turn_system.has_reaction(player) else "РЕАКЦИЯ ИСПОЛЬЗОВАНА", false, "Реакция расходуется атаками по возможности и подготовленными действиями."),
		_entry("ready_status", "АТАКА ПОДГОТОВЛЕНА" if _player_combat_state.readied_attack else "НЕТ ПОДГОТОВЛЕННОЙ АТАКИ", false, "Подготовленная атака срабатывает автоматически при выполнении условия.")
	]
	return {
		"movement": movement_entries,
		"action": action_entries,
		"bonus": bonus_entries,
		"reaction": reaction_entries
	}


func _entry(action_id: String, label: String, enabled: bool, description: String) -> Dictionary:
	return {"id": action_id, "label": label, "enabled": enabled, "description": description}


func _refresh_action_catalog() -> void:
	if _action_catalog_ui == null:
		return
	var combat_active: bool = _turn_system.active
	var player_turn: bool = combat_active and _turn_system.is_player_turn(player) and not _enemy_turn_running
	var resource_text: String = "Вне боя: прыжок доступен через отдельную кнопку."
	if combat_active:
		resource_text = "Раунд %d · Действие: %s · Доп. действие: %s · Реакция: %s · Перемещение: %d футов" % [
			_turn_system.round_number,
			"готово" if _turn_system.action_available else "использовано",
			"готово" if _turn_system.bonus_action_available else "использовано",
			"готова" if _turn_system.has_reaction(player) else "использована",
			_turn_system.movement_remaining_feet
		]
	var plan_text: String = "маршрут не выбран" if _planned_path.size() < 2 else "маршрут: %d футов" % _planned_cost_feet
	_action_catalog_ui.refresh(combat_active, player_turn, _any_overlay_visible(), _build_catalog_entries() if combat_active else {}, resource_text, plan_text)


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


func _can_plan_movement() -> bool:
	return (
		_turn_system.active
		and _turn_system.is_player_turn(player)
		and not _enemy_turn_running
		and not _movement_execution_running
		and not GameState.input_locked
		and not _any_overlay_visible()
		and _srd_rules.effective_speed_feet(30, _player_combat_state) > 0
	)
