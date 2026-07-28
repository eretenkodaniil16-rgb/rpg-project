extends "res://scripts/game/game_encounters_runtime.gd"

const COMBAT_ESCAPE_SYSTEM_SCRIPT: Script = preload("res://scripts/systems/combat_escape_system.gd")
const ESCAPE_ZONE_OVERLAY_SCRIPT: Script = preload("res://scripts/game/escape_zone_overlay.gd")
const DETECTION_AWARE: String = "aware"
const DETECTION_SEARCHING: String = "searching"
const SEARCH_STEP_FEET: int = 5

var _combat_escape: CombatEscapeSystem = COMBAT_ESCAPE_SYSTEM_SCRIPT.new() as CombatEscapeSystem
var _escape_zone_overlay: EscapeZoneOverlay
var _escape_mode_active: bool = false
var _escape_completion_running: bool = false
var _stealth_total: int = 0
var _observer_states: Dictionary = {}
var _hide_roll_overrides: Array[int] = []


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
	if _escape_mode_active and not _player_combat_state.hidden:
		_cancel_escape_mode(false)


func _start_turn_based_combat(trigger_target: Node) -> void:
	super._start_turn_based_combat(trigger_target)
	_escape_mode_active = false
	_stealth_total = 0
	_observer_states.clear()
	for observer: Node in _active_observers():
		_set_observer_state(observer, DETECTION_AWARE, player.global_position)
	if _escape_zone_overlay != null:
		_escape_zone_overlay.clear_escape_cells()


func _stop_turn_based_combat(message: String) -> void:
	_escape_mode_active = false
	_escape_completion_running = false
	_stealth_total = 0
	_observer_states.clear()
	if _player_combat_state != null:
		_player_combat_state.hidden = false
	if _escape_zone_overlay != null:
		_escape_zone_overlay.clear_escape_cells()
	super._stop_turn_based_combat(message)


func _build_catalog_entries() -> Dictionary:
	var entries: Dictionary = super._build_catalog_entries()
	var action_entries: Array = entries.get("action", []) as Array
	if _catalog_contains(action_entries, "escape"):
		return entries
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
		description = "В этом столкновении путь бегства не определён или перекрыт."
	elif hidden:
		description = "Подсветить разрешённые выходы. Бой завершится только при достижении выхода без повторного обнаружения."
	action_entries.append(_entry(
		"escape",
		"БЕГСТВО: ВЫХОД" if _escape_mode_active else "БЕГСТВО",
		enabled,
		description,
		"movement"
	))
	entries["action"] = action_entries
	return entries


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
	_cancel_escape_mode(false)
	_player_combat_state.hidden = false
	_stealth_total = 0
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
	var total: int = int(check.get("total", 0))
	var success: bool = observers.is_empty() or _combat_escape.stealth_succeeds(total, observers)
	if success:
		_player_combat_state.hidden = true
		_stealth_total = total
		for observer: Node in observers:
			_set_observer_state(observer, DETECTION_SEARCHING, player.global_position)
		show_combat_message(
			"Герой скрыт: Скрытность %d против пассивного Восприятия %d. Противники ищут последнюю известную позицию." % [total, difficulty],
			true
		)
	else:
		for observer: Node in observers:
			_set_observer_state(observer, DETECTION_AWARE, player.global_position)
		show_combat_message(
			"Скрыться не удалось: Скрытность %d против пассивного Восприятия %d." % [total, difficulty],
			false
		)
	_refresh_turn_interface()
	_refresh_action_catalog()


func _execute_planned_path() -> void:
	var path_copy: Array[Vector2i] = _planned_path.duplicate()
	var exposed_during_route: bool = _player_combat_state.hidden and _path_exposes_player(path_copy)
	await super._execute_planned_path()
	if exposed_during_route and _player_combat_state.hidden:
		_break_hidden("Маршрут прошёл через поле зрения противника — герой обнаружен.")
	if _player_combat_state.hidden and _escape_mode_active:
		_try_complete_escape()


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

	var state: Dictionary = _observer_record(actor)
	var last_known: Vector2 = state.get("last_known_position", player.global_position) as Vector2
	await _move_searching_observer(actor, last_known)
	if _player_combat_state.hidden and _observer_can_see_position(actor, player.global_position):
		_break_hidden("%s обошёл укрытие и обнаружил героя." % _target_name(actor))
	elif _player_combat_state.hidden:
		var modifier: int = _combat_escape.perception_modifier(actor)
		var check: Dictionary = _srd_rules.resolve_d20_test(modifier, maxi(_stealth_total, 1))
		if bool(check.get("success", false)):
			_break_hidden("%s обнаружил следы героя проверкой Восприятия." % _target_name(actor))
		else:
			show_combat_message(
				"%s ищет героя у последней известной позиции: %d против Скрытности %d." % [
					_target_name(actor),
					int(check.get("total", 0)),
					_stealth_total
				],
				true
			)
	_enemy_turn_running = false
	if _turn_system.active and not _player_combat_state.dead:
		_advance_combat_turn()


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
		show_combat_message("Пути отхода в этом столкновении перекрыты.", false)
		return
	if not _player_combat_state.hidden:
		show_combat_message("Сначала разорвите линию обзора и успешно скройтесь от всех противников.", false)
		return
	if _player_combat_state.has_condition("grappled") or _player_combat_state.has_condition("restrained"):
		show_combat_message("Нельзя бежать, пока герой схвачен или обездвижен.", false)
		return
	_escape_mode_active = true
	var cells: Array[Vector2i] = _escape_cells()
	if _escape_zone_overlay != null:
		_escape_zone_overlay.set_escape_cells(cells)
	show_combat_message("Бегство подготовлено. Доберитесь до подсвеченного выхода, не попавшись противникам.", true)
	_try_complete_escape()


func _try_complete_escape() -> bool:
	if _escape_completion_running or not _escape_mode_active or not _player_combat_state.hidden:
		return false
	if _active_combat_encounter_id.is_empty() or not GameState.has_method("abandon_encounter"):
		return false
	if _player_combat_state.dead or _player_combat_state.has_condition("grappled") or _player_combat_state.has_condition("restrained"):
		return false
	if _player_visible_to_any_observer():
		_break_hidden("Противник видит героя у выхода — бегство сорвано.")
		return false
	var grid: BattleGrid = _get_battle_grid()
	if grid == null or grid.world_to_cell(player.global_position) not in _escape_cells():
		return false

	_escape_completion_running = true
	var definition: Dictionary = _active_encounter_definition()
	var encounter_id: String = _active_combat_encounter_id
	var reason_id: String = _combat_escape.get_reason_id(definition)
	var result: Dictionary = GameState.call(
		"abandon_encounter",
		encounter_id,
		reason_id,
		{
			"source_type": "combat_escape",
			"escape_cell": [grid.world_to_cell(player.global_position).x, grid.world_to_cell(player.global_position).y],
			"combat_round": _turn_system.round_number,
			"stealth_total": _stealth_total,
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
	var safe_anchor: Vector2 = _combat_escape.get_safe_anchor(definition, GameState.player_position)
	player.global_position = safe_anchor
	GameState.player_position = safe_anchor
	_player_combat_state.hidden = false
	_escape_mode_active = false
	_stealth_total = 0
	_active_combat_encounter_id = ""
	GameState.save_game()
	_stop_turn_based_combat("Герой скрылся от противников и покинул столкновение.")
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
	if _escape_zone_overlay != null:
		_escape_zone_overlay.clear_escape_cells()
	if show_message:
		show_combat_message("Подготовка к бегству отменена.", false)


func _break_hidden(message: String) -> void:
	if not _player_combat_state.hidden and not _escape_mode_active:
		return
	_player_combat_state.hidden = false
	_stealth_total = 0
	_cancel_escape_mode(false)
	for observer: Node in _active_observers():
		_set_observer_state(observer, DETECTION_AWARE, player.global_position)
	show_combat_message(message, false)
	_refresh_turn_interface()
	_refresh_action_catalog()


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
	_observer_states[observer.get_instance_id()] = {
		"actor": observer,
		"state": detection_state,
		"last_known_position": last_known_position
	}
	if observer.has_method("set_detection_state"):
		observer.call("set_detection_state", detection_state, last_known_position)


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


func set_hide_roll_overrides_for_testing(values: Array[int]) -> void:
	_hide_roll_overrides = values.duplicate()


func force_hidden_escape_state_for_testing(stealth_total: int, armed: bool = true) -> void:
	_player_combat_state.hidden = true
	_stealth_total = maxi(stealth_total, 1)
	_escape_mode_active = armed
	if armed and _escape_zone_overlay != null:
		_escape_zone_overlay.set_escape_cells(_escape_cells())


func get_escape_cells_for_testing() -> Array[Vector2i]:
	return _escape_cells()


func get_detection_state_for_testing(observer: Node) -> String:
	return str(_observer_record(observer).get("state", ""))


func try_complete_escape_for_testing() -> bool:
	return _try_complete_escape()
