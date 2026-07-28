extends "res://scripts/game/game_encounters_runtime.gd"

const COMBAT_ESCAPE_SYSTEM_SCRIPT: Script = preload("res://scripts/systems/combat_escape_system.gd")
const ESCAPE_ZONE_OVERLAY_SCRIPT: Script = preload("res://scripts/game/escape_zone_overlay.gd")
const DETECTION_AWARE: String = "aware"
const DETECTION_PURSUING: String = "pursuing_last_seen"
const DETECTION_TRACKING: String = "tracking"
const DETECTION_SEARCHING: String = "searching"
const DETECTION_LOST: String = "lost"
const SEARCH_STEP_FEET: int = 5
const MAX_TRACE_CELLS: int = 32

var _combat_escape: CombatEscapeSystem = COMBAT_ESCAPE_SYSTEM_SCRIPT.new() as CombatEscapeSystem
var _escape_zone_overlay: EscapeZoneOverlay
var _escape_mode_active: bool = false
var _escape_completion_running: bool = false
var _escape_route_id: String = ""
var _escape_objective_ready: bool = false
var _escape_room_entered: bool = false
var _hide_confirmed_route_id: String = ""
var _stealth_total: int = 0
var _observer_states: Dictionary = {}
var _movement_trace: Array[Dictionary] = []
var _last_seen_player_position: Vector2 = Vector2.ZERO
var _hide_roll_overrides: Array[int] = []
var _search_roll_overrides: Array[int] = []


func _ready() -> void:
	super._ready()
	_escape_zone_overlay = ESCAPE_ZONE_OVERLAY_SCRIPT.new() as EscapeZoneOverlay
	_escape_zone_overlay.name = "EscapeZoneOverlay"
	_escape_zone_overlay.z_index = 17
	add_child(_escape_zone_overlay)
	_escape_zone_overlay.bind_grid(_get_battle_grid())
	_escape_zone_overlay.hide()


func _process(delta: float) -> void:
	super._process(delta)
	if _turn_system.active and not _player_combat_state.hidden and _player_visible_to_any_observer():
		_last_seen_player_position = player.global_position
	if _escape_mode_active and not _player_combat_state.hidden:
		_cancel_escape_mode(false)
	if _escape_objective_ready and not _player_remains_in_selected_objective():
		_escape_objective_ready = false
		_reset_search_failures()
		show_combat_message("Герой покинул выбранное укрытие — отсчёт потери следа сброшен.", false)


func _start_turn_based_combat(trigger_target: Node) -> void:
	super._start_turn_based_combat(trigger_target)
	_reset_escape_runtime()
	_last_seen_player_position = player.global_position
	for observer: Node in _active_observers():
		_set_observer_state(observer, DETECTION_AWARE, player.global_position)


func _stop_turn_based_combat(message: String) -> void:
	_reset_escape_runtime()
	if _player_combat_state != null:
		_player_combat_state.hidden = false
	super._stop_turn_based_combat(message)


func _reset_escape_runtime() -> void:
	_escape_mode_active = false
	_escape_completion_running = false
	_escape_route_id = ""
	_escape_objective_ready = false
	_escape_room_entered = false
	_hide_confirmed_route_id = ""
	_stealth_total = 0
	_observer_states.clear()
	_movement_trace.clear()
	_hide_roll_overrides.clear()
	_search_roll_overrides.clear()
	if _escape_zone_overlay != null:
		_escape_zone_overlay.clear_escape_cells()


func _build_catalog_entries() -> Dictionary:
	var entries: Dictionary = super._build_catalog_entries()
	var action_entries: Array = entries.get("action", []) as Array
	if not _catalog_contains(action_entries, "escape"):
		var definition: Dictionary = _active_encounter_definition()
		var allowed: bool = _combat_escape.is_escape_allowed(definition)
		var player_turn: bool = (
			_turn_system.active
			and _turn_system.is_player_turn(player)
			and not _enemy_turn_running
		)
		var hidden: bool = _player_combat_state.hidden
		var movement_allowed: bool = (
			not _player_combat_state.dead
			and not _player_combat_state.has_condition("grappled")
			and not _player_combat_state.has_condition("restrained")
		)
		var enabled: bool = player_turn and allowed and hidden and movement_allowed
		var description: String = "Сначала разорвите линию обзора и успешно используйте «Скрыться»."
		if not allowed:
			description = "В этом столкновении нет пригодного маршрута отхода."
		elif _escape_objective_ready:
			description = "Оставайтесь в укрытии, пока каждый противник не потеряет след нужное число раз."
		elif _escape_room_entered:
			description = "Вы в другой комнате. Найдите отмеченное место и снова используйте «Скрыться»."
		elif hidden:
			description = "Подсветить укромные места и переходы в соседние комнаты. Простого выхода к краю поля недостаточно."
		action_entries.append(_entry(
			"escape",
			_escape_action_label(),
			enabled,
			description,
			"movement"
		))
		entries["action"] = action_entries
	if _escape_mode_active:
		var reaction_entries: Array = entries.get("reaction", []) as Array
		reaction_entries.append(_entry(
			"escape_progress",
			_escape_progress_label(),
			false,
			_escape_progress_description(),
			"tactic"
		))
		entries["reaction"] = reaction_entries
	return entries


func _escape_action_label() -> String:
	if _escape_objective_ready:
		return "БЕГСТВО: ПЕРЕЖДАТЬ ПОИСК"
	if _escape_room_entered:
		return "БЕГСТВО: СПРЯТАТЬСЯ В КОМНАТЕ"
	return "БЕГСТВО: МАРШРУТЫ" if _escape_mode_active else "БЕГСТВО"


func _escape_progress_label() -> String:
	var route: Dictionary = _selected_escape_route()
	if route.is_empty():
		return "ПУТЬ ОТХОДА НЕ ВЫБРАН"
	var required: int = _combat_escape.get_required_search_sweeps(route, _active_encounter_definition())
	return "ПОИСК: %d/%d" % [_minimum_failed_searches(), required]


func _escape_progress_description() -> String:
	var route: Dictionary = _selected_escape_route()
	if route.is_empty():
		return "Выберите укромное место или незаметно перейдите в другую комнату."
	return "%s. Враги идут к последней известной позиции и пытаются восстановить путь по следам." % _combat_escape.get_route_label(route)


func _on_catalog_action_requested(action_id: String) -> void:
	if action_id == "escape":
		_arm_escape_mode()
		_invalidate_reachable_area()
		_refresh_action_catalog()
		return
	super._on_catalog_action_requested(action_id)


func _on_hide_requested() -> void:
	if not _player_turn_available():
		return
	if not _turn_system.consume_action():
		show_combat_message("Для попытки скрыться требуется действие.", false)
		return
	_player_combat_state.hidden = false
	_stealth_total = 0
	_escape_objective_ready = false
	_reset_search_failures()
	var definition: Dictionary = _active_encounter_definition()
	var grid: BattleGrid = _get_battle_grid()
	var current_cell: Vector2i = grid.world_to_cell(player.global_position) if grid != null else Vector2i(-99999, -99999)
	var candidate_route: Dictionary = _combat_escape.find_hide_route(definition, current_cell)
	var candidate_type: String = _combat_escape.get_route_type(candidate_route)
	var route_bonus_allowed: bool = (
		candidate_type == CombatEscapeSystem.ROUTE_HIDEOUT
		or (candidate_type == CombatEscapeSystem.ROUTE_ROOM_TRANSITION and _escape_room_entered)
	)
	var concealment_bonus: int = _combat_escape.get_concealment_bonus(candidate_route) if route_bonus_allowed else 0
	var observers: Array[Node] = _active_observers()
	var visible_observers: Array[Node] = []
	for observer: Node in observers:
		if not _observer_can_see_position(observer, player.global_position):
			continue
		if GameState.player_character.naturally_stealthy and _has_larger_creature_cover(observer):
			continue
		visible_observers.append(observer)
	if not visible_observers.is_empty():
		for observer: Node in observers:
			_set_observer_state(observer, DETECTION_AWARE, player.global_position)
		show_combat_message("Скрыться не удалось: хотя бы один противник сохраняет прямую линию обзора.", false)
		_refresh_turn_interface()
		_refresh_action_catalog()
		return

	var difficulty: int = _combat_escape.highest_passive_perception(observers)
	var modifier: int = GameState.player_character.get_skill_modifier("stealth")
	var disadvantage: bool = _player_has_untrained_armor_d20_disadvantage("dexterity")
	var overrides: Array[int] = _hide_roll_overrides.duplicate()
	_hide_roll_overrides.clear()
	var check: Dictionary = _srd_rules.resolve_d20_test(
		modifier,
		difficulty,
		false,
		disadvantage,
		overrides,
		GameState.player_character.reroll_natural_one
	)
	var raw_total: int = int(check.get("total", 0))
	var effective_total: int = raw_total + concealment_bonus
	var success: bool = observers.is_empty() or _combat_escape.stealth_succeeds(effective_total, observers)
	if success:
		_player_combat_state.hidden = true
		_stealth_total = effective_total
		if route_bonus_allowed and not candidate_route.is_empty():
			_hide_confirmed_route_id = str(candidate_route.get("id", ""))
			_select_escape_route(candidate_route)
		else:
			_hide_confirmed_route_id = ""
		for observer: Node in observers:
			_set_observer_state(observer, DETECTION_PURSUING, _last_seen_player_position)
		var bonus_text: String = ""
		if concealment_bonus > 0:
			bonus_text = " + %d за укромное место" % concealment_bonus
		show_combat_message(
			"Герой скрыт: Скрытность %d%s против пассивного Восприятия %d. Враги идут к последнему месту контакта." % [raw_total, bonus_text, difficulty],
			true
		)
		if _escape_mode_active and route_bonus_allowed and not candidate_route.is_empty():
			_activate_escape_objective(candidate_route)
	else:
		_hide_confirmed_route_id = ""
		for observer: Node in observers:
			_set_observer_state(observer, DETECTION_AWARE, player.global_position)
		show_combat_message(
			"Скрыться не удалось: Скрытность %d против пассивного Восприятия %d." % [effective_total, difficulty],
			false
		)
	_refresh_escape_overlay()
	_refresh_turn_interface()
	_refresh_action_catalog()


func _execute_planned_path() -> void:
	var path_copy: Array[Vector2i] = _planned_path.duplicate()
	var was_hidden: bool = _player_combat_state.hidden
	var exposed_during_route: bool = was_hidden and _path_exposes_player(path_copy)
	await super._execute_planned_path()
	if exposed_during_route and _player_combat_state.hidden:
		_break_hidden("Маршрут прошёл через поле зрения противника — герой обнаружен.")
		return
	if was_hidden and _player_combat_state.hidden and path_copy.size() > 1:
		_record_hidden_path(path_copy)
		var transition_route: Dictionary = _combat_escape.find_room_transition_route(_active_encounter_definition(), path_copy)
		if not transition_route.is_empty():
			_select_escape_route(transition_route)
			_escape_room_entered = true
			_escape_objective_ready = false
			_hide_confirmed_route_id = ""
			_reset_search_failures()
			show_combat_message(
				"Герой незаметно прошёл в «%s». Враги продолжают путь к последнему месту контакта; теперь нужно снова спрятаться в отмеченной точке." % _combat_escape.get_route_label(transition_route),
				true
			)
	_refresh_escape_overlay()
	_refresh_action_catalog()


func apply_damage_to_player(amount: int, damage_type: String, critical_hit: bool = false, source: Node = null) -> Dictionary:
	var result: Dictionary = super.apply_damage_to_player(amount, damage_type, critical_hit, source)
	if int(result.get("applied", 0)) > 0 and _player_combat_state.hidden:
		_break_hidden("Полученный урон выдал позицию героя.")
	return result


func _on_ability_requested(ability_id: String) -> void:
	var was_hidden: bool = _player_combat_state.hidden
	await super._on_ability_requested(ability_id)
	if was_hidden and _player_combat_state.hidden:
		_break_hidden("Применение способности выдало позицию героя.")


func _run_enemy_turn(actor: Node) -> void:
	if _player_combat_state.hidden and actor in _active_observers():
		await _run_enemy_search_turn(actor)
		return
	await super._run_enemy_turn(actor)


func _run_enemy_search_turn(actor: Node) -> void:
	if not _turn_system.active or _turn_system.current_actor() != actor:
		return
	_enemy_turn_running = true
	_refresh_turn_interface()
	while _turn_system.active and _any_overlay_visible():
		await get_tree().process_frame
	await get_tree().create_timer(0.2).timeout
	if _observer_can_see_position(actor, player.global_position):
		_break_hidden("%s восстановил визуальный контакт с героем." % _target_name(actor))
		_enemy_turn_running = false
		await super._run_enemy_turn(actor)
		return

	var record: Dictionary = _observer_record(actor)
	var last_known: Vector2 = record.get("last_known_position", _last_seen_player_position) as Vector2
	await _move_searching_observer(actor, last_known)
	if _player_combat_state.hidden and _observer_can_see_position(actor, player.global_position):
		_break_hidden("%s обошёл укрытие и обнаружил героя." % _target_name(actor))
	elif _player_combat_state.hidden:
		var distance_to_search: int = DistanceSystem.distance_feet((actor as Node2D).global_position, last_known)
		if distance_to_search > DistanceSystem.MELEE_REACH_FEET:
			show_combat_message("%s преследует героя до последней известной позиции." % _target_name(actor), true)
		else:
			_resolve_search_at_last_known(actor)
	_enemy_turn_running = false
	if _turn_system.active and not _player_combat_state.dead:
		_advance_combat_turn()


func _resolve_search_at_last_known(actor: Node) -> bool:
	if actor == null or not is_instance_valid(actor) or not _player_combat_state.hidden:
		return false
	var route: Dictionary = _selected_escape_route()
	var record: Dictionary = _observer_record(actor)
	var trace_cursor: int = maxi(int(record.get("trace_cursor", 0)), 0)
	var next_trace: Dictionary = _trace_at(trace_cursor)
	if not next_trace.is_empty():
		var tracking_dc: int = _combat_escape.get_tracking_dc(_stealth_total, route)
		var tracking_roll: Dictionary = _resolve_search_roll(_combat_escape.tracking_modifier(actor), tracking_dc)
		if bool(tracking_roll.get("success", false)):
			record["state"] = DETECTION_TRACKING
			record["last_known_position"] = next_trace.get("position", _last_seen_player_position)
			record["trace_cursor"] = trace_cursor + 1
			record["failed_searches"] = 0
			_store_observer_record(actor, record)
			show_combat_message(
				"%s находит продолжение следа: %d против Сл %d и меняет направление поиска." % [_target_name(actor), int(tracking_roll.get("total", 0)), tracking_dc],
				false
			)
			return false
		record["state"] = DETECTION_SEARCHING
		_store_observer_record(actor, record)
		show_combat_message(
			"%s теряет след: %d против Сл %d." % [_target_name(actor), int(tracking_roll.get("total", 0)), tracking_dc],
			true
		)
		_register_failed_search(actor)
		return _try_complete_escape()

	var search_dc: int = _combat_escape.get_search_dc(_stealth_total, route)
	var perception_roll: Dictionary = _resolve_search_roll(_combat_escape.perception_modifier(actor), search_dc)
	if bool(perception_roll.get("success", false)):
		_break_hidden(
			"%s находит героя по шуму, следам и деталям укрытия: %d против Сл %d." % [_target_name(actor), int(perception_roll.get("total", 0)), search_dc]
		)
		return false
	show_combat_message(
		"%s обыскивает последнюю известную область, но ничего не находит: %d против Сл %d." % [_target_name(actor), int(perception_roll.get("total", 0)), search_dc],
		true
	)
	_register_failed_search(actor)
	return _try_complete_escape()


func _resolve_search_roll(modifier: int, difficulty: int) -> Dictionary:
	var overrides: Array[int] = []
	if not _search_roll_overrides.is_empty():
		overrides.append(_search_roll_overrides.pop_front())
	return _srd_rules.resolve_d20_test(modifier, difficulty, false, false, overrides)


func _register_failed_search(observer: Node) -> void:
	var record: Dictionary = _observer_record(observer)
	record["state"] = DETECTION_SEARCHING
	if _escape_objective_ready:
		record["failed_searches"] = maxi(int(record.get("failed_searches", 0)), 0) + 1
		var route: Dictionary = _selected_escape_route()
		var required: int = _combat_escape.get_required_search_sweeps(route, _active_encounter_definition())
		if int(record.get("failed_searches", 0)) >= required:
			record["state"] = DETECTION_LOST
	_store_observer_record(observer, record)
	_refresh_action_catalog()


func _move_searching_observer(actor: Node, target_position: Vector2) -> void:
	if actor == null or not is_instance_valid(actor) or not (actor is Node2D):
		return
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return
	var movement_feet: int = maxi(
		int(actor.call("get_combat_speed_feet")) if actor.has_method("get_combat_speed_feet") else 30,
		0
	)
	while movement_feet >= SEARCH_STEP_FEET and _player_combat_state.hidden:
		var current_cell: Vector2i = grid.world_to_cell((actor as Node2D).global_position)
		var target_cell: Vector2i = grid.world_to_cell(target_position)
		if current_cell == target_cell:
			break
		var best_cell: Vector2i = current_cell
		var best_distance: float = grid.cell_to_world_center(current_cell).distance_squared_to(target_position)
		for offset: Vector2i in [
			Vector2i.LEFT, Vector2i.RIGHT, Vector2i.UP, Vector2i.DOWN,
			Vector2i(-1, -1), Vector2i(1, -1), Vector2i(-1, 1), Vector2i(1, 1)
		]:
			var candidate: Vector2i = current_cell + offset
			if not grid.is_cell_valid(candidate):
				continue
			if _combat_environment != null and _combat_environment.is_cell_blocked(grid, candidate):
				continue
			if _occupied_cells(actor).has(candidate):
				continue
			var distance: float = grid.cell_to_world_center(candidate).distance_squared_to(target_position)
			if distance < best_distance:
				best_distance = distance
				best_cell = candidate
		if best_cell == current_cell:
			break
		var destination: Vector2 = grid.cell_to_world_center(best_cell)
		var tween: Tween = create_tween()
		tween.tween_property(actor as Node2D, "global_position", destination, 0.12)
		await tween.finished
		movement_feet -= SEARCH_STEP_FEET
		if _observer_can_see_position(actor, player.global_position):
			break


func _arm_escape_mode() -> void:
	if not _turn_system.active or _active_combat_encounter_id.is_empty():
		show_combat_message("Нет активного столкновения, из которого можно бежать.", false)
		return
	var definition: Dictionary = _active_encounter_definition()
	if not _combat_escape.is_escape_allowed(definition):
		show_combat_message("В этом столкновении нет пригодного пути отхода.", false)
		return
	if not _player_combat_state.hidden:
		show_combat_message("Сначала разорвите линию обзора и успешно скройтесь от всех противников.", false)
		return
	if _player_combat_state.has_condition("grappled") or _player_combat_state.has_condition("restrained"):
		show_combat_message("Нельзя бежать, пока герой схвачен или обездвижен.", false)
		return
	_escape_mode_active = true
	_refresh_escape_overlay()
	var grid: BattleGrid = _get_battle_grid()
	var current_cell: Vector2i = grid.world_to_cell(player.global_position) if grid != null else Vector2i(-99999, -99999)
	var hide_route: Dictionary = _combat_escape.find_hide_route(definition, current_cell)
	if not hide_route.is_empty() and _hide_confirmed_route_id == str(hide_route.get("id", "")):
		_select_escape_route(hide_route)
		_activate_escape_objective(hide_route)
		return
	var destination_route: Dictionary = _combat_escape.find_destination_route(definition, current_cell)
	if not destination_route.is_empty() and _escape_room_entered:
		_select_escape_route(destination_route)
		show_combat_message("Вы вошли в соседнюю комнату. Переместитесь в отмеченную точку и снова используйте «Скрыться».", true)
		return
	show_combat_message(
		"Пути отхода отмечены: фиолетовый — глубокое укрытие, синий — переход, зелёный — место повторного скрытия в соседней комнате.",
		true
	)


func _activate_escape_objective(route: Dictionary) -> void:
	if route.is_empty() or _hide_confirmed_route_id != str(route.get("id", "")):
		return
	if _combat_escape.get_route_type(route) == CombatEscapeSystem.ROUTE_ROOM_TRANSITION and not _escape_room_entered:
		return
	_escape_objective_ready = true
	_reset_search_failures()
	show_combat_message(
		"Герой затаился в «%s». Бегство завершится только после %d неудачных поисковых циклов каждого противника." % [
			_combat_escape.get_route_label(route),
			_combat_escape.get_required_search_sweeps(route, _active_encounter_definition())
		],
		true
	)
	_try_complete_escape()


func _try_complete_escape() -> bool:
	if _escape_completion_running or not _escape_mode_active or not _escape_objective_ready or not _player_combat_state.hidden:
		return false
	if _active_combat_encounter_id.is_empty() or not GameState.has_method("abandon_encounter"):
		return false
	if _player_combat_state.dead or _player_combat_state.has_condition("grappled") or _player_combat_state.has_condition("restrained"):
		return false
	if not _player_remains_in_selected_objective():
		return false
	if _player_visible_to_any_observer():
		_break_hidden("Противник восстановил контакт с героем — бегство сорвано.")
		return false
	var route: Dictionary = _selected_escape_route()
	if route.is_empty():
		return false
	var required: int = _combat_escape.get_required_search_sweeps(route, _active_encounter_definition())
	for observer: Node in _active_observers():
		if int(_observer_record(observer).get("failed_searches", 0)) < required:
			return false

	_escape_completion_running = true
	var definition: Dictionary = _active_encounter_definition()
	var encounter_id: String = _active_combat_encounter_id
	var reason_id: String = _combat_escape.get_reason_id(definition, route)
	var grid: BattleGrid = _get_battle_grid()
	var cell: Vector2i = grid.world_to_cell(player.global_position) if grid != null else Vector2i.ZERO
	var result: Dictionary = GameState.call(
		"abandon_encounter",
		encounter_id,
		reason_id,
		{
			"source_type": "combat_escape",
			"escape_route_id": _escape_route_id,
			"escape_route_type": _combat_escape.get_route_type(route),
			"escape_cell": [cell.x, cell.y],
			"combat_round": _turn_system.round_number,
			"stealth_total": _stealth_total,
			"minimum_failed_searches": _minimum_failed_searches(),
			"trace_cells_left": _movement_trace.size(),
			"enemies_alerted": true
		},
		false,
		true
	) as Dictionary
	if not bool(result.get("success", false)):
		_escape_completion_running = false
		show_combat_message(str(result.get("message", "Не удалось завершить бегство.")), false)
		return false

	var alert_flag: String = _combat_escape.get_alert_flag(definition)
	if not alert_flag.is_empty():
		GameState.set_flag(alert_flag, true)
	if _combat_escape.should_restore_participants(definition):
		_restore_encounter_participants()
	var safe_anchor: Vector2 = _combat_escape.get_safe_anchor(definition, GameState.player_position, route)
	player.global_position = safe_anchor
	GameState.player_position = safe_anchor
	_player_combat_state.hidden = false
	_active_combat_encounter_id = ""
	GameState.save_game()
	_stop_turn_based_combat("Противники потеряли след. Герой покинул столкновение через «%s»." % _combat_escape.get_route_label(route))
	_escape_completion_running = false
	return true


func _restore_encounter_participants() -> void:
	for entry: Dictionary in _turn_system.entries:
		if bool(entry.get("is_player", false)):
			continue
		var actor: Node = entry.get("node") as Node
		if is_instance_valid(actor) and actor.has_method("reset_combat_state"):
			actor.call("reset_combat_state", true)


func _cancel_escape_mode(show_message: bool = true) -> void:
	if not _escape_mode_active:
		return
	_escape_mode_active = false
	_escape_objective_ready = false
	if _escape_zone_overlay != null:
		_escape_zone_overlay.clear_escape_cells()
	if show_message:
		show_combat_message("Подготовка к бегству отменена.", false)


func _break_hidden(message: String) -> void:
	if not _player_combat_state.hidden and not _escape_mode_active:
		return
	_player_combat_state.hidden = false
	_stealth_total = 0
	_hide_confirmed_route_id = ""
	_escape_objective_ready = false
	_cancel_escape_mode(false)
	_last_seen_player_position = player.global_position
	for observer: Node in _active_observers():
		_set_observer_state(observer, DETECTION_AWARE, player.global_position)
	show_combat_message(message, false)
	_refresh_turn_interface()
	_refresh_action_catalog()


func _record_hidden_path(path: Array[Vector2i]) -> void:
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return
	for index: int in range(1, path.size()):
		var cell: Vector2i = path[index]
		_movement_trace.append({
			"cell": cell,
			"position": grid.cell_to_world_center(cell),
			"round": _turn_system.round_number
		})
	while _movement_trace.size() > MAX_TRACE_CELLS:
		_movement_trace.pop_front()


func _trace_at(index: int) -> Dictionary:
	if index < 0 or index >= _movement_trace.size():
		return {}
	return _movement_trace[index].duplicate(true)


func _reset_search_failures() -> void:
	for observer: Node in _active_observers():
		var record: Dictionary = _observer_record(observer)
		record["failed_searches"] = 0
		_store_observer_record(observer, record)


func _minimum_failed_searches() -> int:
	var observers: Array[Node] = _active_observers()
	if observers.is_empty():
		return 0
	var result: int = 999999
	for observer: Node in observers:
		result = mini(result, maxi(int(_observer_record(observer).get("failed_searches", 0)), 0))
	return 0 if result == 999999 else result


func _player_remains_in_selected_objective() -> bool:
	var route: Dictionary = _selected_escape_route()
	var grid: BattleGrid = _get_battle_grid()
	if route.is_empty() or grid == null:
		return false
	return grid.world_to_cell(player.global_position) in _combat_escape.route_hide_cells(route)


func _select_escape_route(route: Dictionary) -> void:
	if route.is_empty():
		return
	var route_id: String = str(route.get("id", ""))
	if route_id.is_empty():
		return
	if _escape_route_id != route_id:
		_escape_route_id = route_id
		_escape_objective_ready = false
		_reset_search_failures()


func _selected_escape_route() -> Dictionary:
	if _escape_route_id.is_empty():
		return {}
	return _combat_escape.get_route(_active_encounter_definition(), _escape_route_id)


func _refresh_escape_overlay() -> void:
	if _escape_zone_overlay == null:
		return
	if not _escape_mode_active:
		_escape_zone_overlay.clear_escape_cells()
		return
	_escape_zone_overlay.set_route_cells(_combat_escape.overlay_cells(_active_encounter_definition()))


func _active_observers() -> Array[Node]:
	var result: Array[Node] = []
	if _turn_system == null:
		return result
	for entry: Dictionary in _turn_system.entries:
		if bool(entry.get("is_player", false)):
			continue
		var actor: Node = entry.get("node") as Node
		if not is_instance_valid(actor) or not (actor is Node2D) or not _target_is_valid(actor):
			continue
		var hostile: bool = bool(actor.call("is_hostile")) if actor.has_method("is_hostile") else true
		if hostile:
			result.append(actor)
	return result


func _observer_can_see_position(observer: Node, world_position: Vector2) -> bool:
	if observer == null or not is_instance_valid(observer) or not (observer is Node2D):
		return false
	var grid: BattleGrid = _get_battle_grid()
	if _combat_escape.blocks_cross_room_line_of_sight(
		grid,
		_active_encounter_definition(),
		(observer as Node2D).global_position,
		world_position
	):
		return false
	if _combat_environment == null:
		return true
	return _combat_environment.has_line_of_sight((observer as Node2D).global_position, world_position)


func _player_visible_to_any_observer() -> bool:
	for observer: Node in _active_observers():
		if _observer_can_see_position(observer, player.global_position):
			return true
	return false


func _path_exposes_player(path: Array[Vector2i]) -> bool:
	if path.size() < 2:
		return false
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return true
	for index: int in range(1, path.size()):
		var position: Vector2 = grid.cell_to_world_center(path[index])
		for observer: Node in _active_observers():
			if _observer_can_see_position(observer, position):
				return true
	return false


func _set_observer_state(observer: Node, detection_state: String, last_known_position: Vector2) -> void:
	if observer == null or not is_instance_valid(observer):
		return
	var record: Dictionary = _observer_record(observer)
	record["actor"] = observer
	record["state"] = detection_state
	record["last_known_position"] = last_known_position
	if not record.has("trace_cursor"):
		record["trace_cursor"] = 0
	if not record.has("failed_searches"):
		record["failed_searches"] = 0
	_store_observer_record(observer, record)


func _store_observer_record(observer: Node, record: Dictionary) -> void:
	if observer == null or not is_instance_valid(observer):
		return
	_observer_states[observer.get_instance_id()] = record.duplicate(true)
	if observer.has_method("set_detection_state"):
		observer.call(
			"set_detection_state",
			str(record.get("state", DETECTION_AWARE)),
			record.get("last_known_position", Vector2.ZERO)
		)


func _observer_record(observer: Node) -> Dictionary:
	if observer == null or not is_instance_valid(observer):
		return {}
	var value: Variant = _observer_states.get(observer.get_instance_id(), {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func _active_encounter_definition() -> Dictionary:
	if _active_combat_encounter_id.is_empty() or not GameState.has_method("get_encounter_definition"):
		return {}
	return GameState.call("get_encounter_definition", _active_combat_encounter_id) as Dictionary


func _escape_cells() -> Array[Vector2i]:
	return _combat_escape.escape_cells(_get_battle_grid(), _active_encounter_definition())


func set_hide_roll_overrides_for_testing(values: Array) -> void:
	_hide_roll_overrides.clear()
	for value: Variant in values:
		_hide_roll_overrides.append(int(value))


func set_search_roll_overrides_for_testing(values: Array) -> void:
	_search_roll_overrides.clear()
	for value: Variant in values:
		_search_roll_overrides.append(int(value))


func force_hidden_escape_state_for_testing(
	stealth_total: int,
	armed: bool = true,
	route_id: String = "",
	objective_ready: bool = false
) -> void:
	_player_combat_state.hidden = true
	_stealth_total = maxi(stealth_total, 1)
	_escape_mode_active = armed
	_escape_route_id = route_id
	_hide_confirmed_route_id = route_id
	_escape_objective_ready = objective_ready
	if armed:
		_refresh_escape_overlay()


func apply_hidden_path_for_testing(path: Array[Vector2i]) -> void:
	_record_hidden_path(path)
	var route: Dictionary = _combat_escape.find_room_transition_route(_active_encounter_definition(), path)
	if not route.is_empty():
		_select_escape_route(route)
		_escape_room_entered = true
		_hide_confirmed_route_id = ""
		_escape_objective_ready = false


func resolve_search_for_testing(observer: Node, roll: int) -> bool:
	_search_roll_overrides.append(roll)
	return _resolve_search_at_last_known(observer)


func get_escape_cells_for_testing() -> Array[Vector2i]:
	return _escape_cells()


func get_detection_state_for_testing(observer: Node) -> String:
	return str(_observer_record(observer).get("state", ""))


func get_escape_progress_for_testing() -> Dictionary:
	return {
		"route_id": _escape_route_id,
		"objective_ready": _escape_objective_ready,
		"room_entered": _escape_room_entered,
		"minimum_failed_searches": _minimum_failed_searches(),
		"trace_count": _movement_trace.size()
	}


func try_complete_escape_for_testing() -> bool:
	return _try_complete_escape()
