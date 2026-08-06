extends "res://scripts/game/game_party_medicine_recovery_runtime.gd"

const FIELD_SUPPORT_STABILIZE_LABEL: String = "МЕДИЦИНА: СТАБИЛИЗИРОВАТЬ ИРИНУ"
const FIELD_SUPPORT_RECOVER_LABEL: String = "МЕДИЦИНА: ПРИВЕСТИ ИРИНУ В СОЗНАНИЕ"
const FIELD_SUPPORT_TRANSACTION_REASON: String = "ally_field_medicine"

const FOLLOW_STOP_DISTANCE_PIXELS: float = 82.0
const FOLLOW_PATH_REFRESH_SECONDS: float = 0.30
const FOLLOW_WAYPOINT_REACHED_PIXELS: float = 10.0
const FOLLOW_STUCK_SECONDS: float = 0.55
const FOLLOW_ROUTE_BUDGET_FEET: int = 300
const FOLLOW_NEIGHBOR_OFFSETS: Array[Vector2i] = [
	Vector2i.LEFT,
	Vector2i.RIGHT,
	Vector2i.UP,
	Vector2i.DOWN,
	Vector2i(-1, -1),
	Vector2i(1, -1),
	Vector2i(-1, 1),
	Vector2i(1, 1)
]

var _field_follow_path: Array[Vector2i] = []
var _field_follow_path_index: int = 0
var _field_follow_refresh_remaining: float = 0.0
var _field_follow_last_leader_cell: Vector2i = Vector2i(-99999, -99999)
var _field_follow_last_position: Vector2 = Vector2.INF
var _field_follow_stuck_elapsed: float = 0.0
var _field_follow_owns_physics: bool = false
var _field_visibility_source_id: int = 0


func _exit_tree() -> void:
	_release_external_follow_control()


func _physics_process(delta: float) -> void:
	_sync_party_visibility_source()
	_process_party_follow_navigation(delta)


func _build_catalog_entries() -> Dictionary:
	var entries: Dictionary = super._build_catalog_entries()
	var action_values: Variant = entries.get("action", [])
	var filtered_actions: Array = []
	if action_values is Array:
		for value: Variant in action_values as Array:
			if not value is Dictionary:
				continue
			var entry: Dictionary = value as Dictionary
			var action_id: String = str(entry.get("id", ""))
			if action_id == ALLY_STABILIZE_ACTION_ID:
				continue
			if (
				action_id == ITEM_USE_ACTION_PREFIX + HEALERS_KIT_ID
				and _selected_target == _controllable_ally
			):
				continue
			filtered_actions.append(entry)

	if _ally_needs_field_support() and GameState.get_item_count(HEALERS_KIT_ID) > 0:
		var stable_at_zero: bool = _ally_is_stable_at_zero()
		var reachable: bool = _ally_distance_from_player() <= ALLY_INTERACTION_DISTANCE_FEET
		var player_can_use: bool = (
			not _turn_system.active
			or (
				_turn_system.is_player_turn(player)
				and _turn_system.action_available
				and not _enemy_turn_running
			)
		)
		filtered_actions.append(_entry(
			ALLY_STABILIZE_ACTION_ID,
			FIELD_SUPPORT_RECOVER_LABEL if stable_at_zero else FIELD_SUPPORT_STABILIZE_LABEL,
			reachable and player_can_use,
			(
				"Проверка Медицины СЛ %d с набором лекаря. При успехе Ирина приходит "
				% ALLY_MEDICINE_DIFFICULTY_CLASS
				+ "в сознание с 1 HP."
				if stable_at_zero
				else (
					"Проверка Медицины СЛ %d с набором лекаря. При успехе Ирина "
					% ALLY_MEDICINE_DIFFICULTY_CLASS
					+ "стабилизируется с 0 HP."
				)
			),
			"item"
		))
	entries["action"] = filtered_actions
	return entries


func _on_feedback_catalog_action_requested(action_id: String) -> void:
	if action_id == ALLY_STABILIZE_ACTION_ID:
		_attempt_controllable_ally_field_support()
		_refresh_action_catalog()
		return
	if (
		action_id == ITEM_USE_ACTION_PREFIX + HEALERS_KIT_ID
		and _ally_needs_field_support()
	):
		_attempt_controllable_ally_field_support()
		_refresh_action_catalog()
		return
	super._on_feedback_catalog_action_requested(action_id)


func _request_item_use(item_id: String) -> void:
	if item_id == HEALERS_KIT_ID and _ally_needs_field_support():
		_attempt_controllable_ally_field_support()
		_update_status()
		_refresh_turn_interface()
		_refresh_action_catalog()
		_sync_exploration_hud_visibility()
		return
	super._request_item_use(item_id)


func _attempt_controllable_ally_field_support(roll_override: int = -1) -> Dictionary:
	if _ally_medicine_running:
		return _medicine_failure("Помощь уже оказывается.")
	if not is_instance_valid(_controllable_ally):
		return _medicine_failure("Союзник недоступен.")
	if not _ally_needs_field_support():
		return _medicine_failure("Ирина не нуждается в полевой помощи.")
	if _ally_distance_from_player() > ALLY_INTERACTION_DISTANCE_FEET:
		return _medicine_failure("Чтобы оказать помощь Ирине, нужно стоять в соседней клетке.")
	if GameState.get_item_count(HEALERS_KIT_ID) <= 0:
		return _medicine_failure("Для проверки нужен набор лекаря.")
	if _turn_system.active:
		if not _turn_system.is_player_turn(player) or _enemy_turn_running:
			return _medicine_failure("Помощь можно оказать только на ходу главного героя.")
		if not _turn_system.action_available:
			return _medicine_failure("Основное действие на этом ходу уже использовано.")

	_ally_medicine_running = true
	var stable_before: bool = _ally_is_stable_at_zero()
	var context: Dictionary = {
		"source": FIELD_SUPPORT_TRANSACTION_REASON,
		"target_id": str(_controllable_ally.call("get_actor_id")),
		"difficulty_class": ALLY_MEDICINE_DIFFICULTY_CLASS,
		"recovery_stage": "consciousness" if stable_before else "stabilization"
	}
	var reservation_value: Variant = GameState.reserve_inventory_item(
		HEALERS_KIT_ID,
		1,
		FIELD_SUPPORT_TRANSACTION_REASON,
		context
	)
	if not reservation_value is Dictionary:
		_ally_medicine_running = false
		return _medicine_failure("Не удалось подготовить набор лекаря.")
	var reservation: Dictionary = reservation_value as Dictionary
	if not bool(reservation.get("success", false)):
		_ally_medicine_running = false
		return _medicine_failure("Набор лекаря закончился или уже используется.")

	if _turn_system.active and not _turn_system.consume_action():
		GameState.rollback_inventory_transaction(str(reservation.get("transaction_id", "")))
		_ally_medicine_running = false
		return _medicine_failure("Основное действие на этом ходу уже использовано.")

	var check: SkillCheckResult = _ally_skill_checks.perform_skill_check(
		GameState.player_character,
		ALLY_MEDICINE_SKILL_ID,
		ALLY_MEDICINE_DIFFICULTY_CLASS,
		0,
		roll_override
	)
	var committed: bool = _commit_medicine_supplies(reservation)
	if not committed:
		_ally_medicine_running = false
		return _medicine_failure("Не удалось списать применение набора лекаря.")

	var result: Dictionary = {
		"success": false,
		"consumed": true,
		"natural_roll": check.natural_roll,
		"total": check.total,
		"difficulty": check.difficulty,
		"medicine_success": check.success,
		"recovery_stage": "consciousness" if stable_before else "stabilization"
	}
	if check.success:
		if stable_before:
			_call_ally("recover_to_one_hit_point")
			result["success"] = _ally_current_health() == 1
			result["message"] = (
				"Медицина: d20 %d, итог %d против СЛ %d — успех. "
				% [check.natural_roll, check.total, check.difficulty]
				+ "Ирина приходит в сознание с 1 HP."
			)
		else:
			var stabilize_value: Variant = _call_ally("stabilize_with_healers_kit")
			result["success"] = (
				stabilize_value is Dictionary
				and bool((stabilize_value as Dictionary).get("success", false))
			)
			result["message"] = (
				"Медицина: d20 %d, итог %d против СЛ %d — успех. "
				% [check.natural_roll, check.total, check.difficulty]
				+ "Ирина стабильна, но остаётся без сознания с 0 HP."
			)
	else:
		result["message"] = (
			"Медицина: d20 %d, итог %d против СЛ %d — неудача. "
			% [check.natural_roll, check.total, check.difficulty]
			+ (
				"Ирина остаётся стабильной, но без сознания; применение набора израсходовано."
				if stable_before
				else "Ирина продолжает умирать; применение набора израсходовано."
			)
		)

	if not _turn_system.active:
		GameState.save_game()
	_ally_medicine_running = false
	show_combat_message(
		str(result.get("message", "Проверка Медицины завершена.")),
		bool(result.get("success", false))
	)
	_update_status()
	_refresh_turn_interface()
	return result


func attempt_controllable_ally_medicine_for_testing(natural_roll: int) -> Dictionary:
	return _attempt_controllable_ally_field_support(natural_roll)


func _ally_needs_field_support() -> bool:
	var state: CombatantState = _ally_state()
	return (
		is_instance_valid(_controllable_ally)
		and state != null
		and _ally_current_health() <= 0
		and not state.dead
	)


func _ally_is_stable_at_zero() -> bool:
	var state: CombatantState = _ally_state()
	return state != null and _ally_current_health() <= 0 and state.stable and not state.dead


func _sync_party_visibility_source() -> void:
	var source: Node = get_active_player_controlled_actor()
	if not is_instance_valid(source) or not source is Node2D:
		source = player
	if not is_instance_valid(source) or not source is Node2D:
		return
	var source_id: int = source.get_instance_id()
	if source_id == _field_visibility_source_id:
		return
	var updated: bool = false
	for visibility_node: Node in get_tree().get_nodes_in_group("player_visibility"):
		if visibility_node.has_method("set_vision_source"):
			visibility_node.call("set_vision_source", source as Node2D)
			updated = true
	if updated:
		_field_visibility_source_id = source_id


func _process_party_follow_navigation(delta: float) -> void:
	if not is_instance_valid(_controllable_ally) or not _controllable_ally is CharacterBody2D:
		_release_external_follow_control()
		return
	var should_follow: bool = (
		not is_party_combat_active()
		and _exploration_mode_id == EXPLORATION_MODE_PARTY
		and _ally_current_health() > 0
		and not bool(_ally_state().dead if _ally_state() != null else false)
		and is_instance_valid(player)
	)
	if not should_follow:
		_release_external_follow_control()
		return

	_claim_external_follow_control()
	var ally: CharacterBody2D = _controllable_ally as CharacterBody2D
	var distance_to_leader: float = ally.global_position.distance_to(player.global_position)
	if distance_to_leader <= FOLLOW_STOP_DISTANCE_PIXELS:
		_stop_external_follow_motion(ally)
		return

	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		_stop_external_follow_motion(ally)
		return
	var leader_cell: Vector2i = grid.world_to_cell(player.global_position)
	_field_follow_refresh_remaining = maxf(_field_follow_refresh_remaining - delta, 0.0)
	if (
		_field_follow_path.is_empty()
		or leader_cell != _field_follow_last_leader_cell
		or _field_follow_refresh_remaining <= 0.0
	):
		_rebuild_follow_path(grid, leader_cell)

	if _field_follow_path.is_empty() or _field_follow_path_index >= _field_follow_path.size():
		_stop_external_follow_motion(ally)
		return

	var waypoint: Vector2 = grid.cell_to_world_center(_field_follow_path[_field_follow_path_index])
	var offset: Vector2 = waypoint - ally.global_position
	if offset.length() <= FOLLOW_WAYPOINT_REACHED_PIXELS:
		_field_follow_path_index += 1
		if _field_follow_path_index >= _field_follow_path.size():
			_stop_external_follow_motion(ally)
			return
		waypoint = grid.cell_to_world_center(_field_follow_path[_field_follow_path_index])
		offset = waypoint - ally.global_position

	if offset.length_squared() <= 0.001:
		_stop_external_follow_motion(ally)
		return
	var direction: Vector2 = offset.normalized()
	var follow_speed: float = maxf(float(ally.get("follow_speed_pixels")), 1.0)
	ally.call("set_facing_direction", direction)
	ally.velocity = direction * follow_speed
	ally.move_and_slide()
	_update_follow_stuck_state(ally, delta)


func _claim_external_follow_control() -> void:
	if _field_follow_owns_physics or not is_instance_valid(_controllable_ally):
		return
	_controllable_ally.call("set_manual_control_enabled", false)
	_controllable_ally.set_physics_process(false)
	_field_follow_owns_physics = true
	_clear_follow_path()


func _release_external_follow_control() -> void:
	if is_instance_valid(_controllable_ally) and _controllable_ally is CharacterBody2D:
		var ally: CharacterBody2D = _controllable_ally as CharacterBody2D
		ally.velocity = Vector2.ZERO
		if _field_follow_owns_physics:
			ally.set_physics_process(true)
	_field_follow_owns_physics = false
	_clear_follow_path()


func _stop_external_follow_motion(ally: CharacterBody2D) -> void:
	ally.velocity = Vector2.ZERO
	_field_follow_last_position = ally.global_position
	_field_follow_stuck_elapsed = 0.0


func _clear_follow_path() -> void:
	_field_follow_path.clear()
	_field_follow_path_index = 0
	_field_follow_refresh_remaining = 0.0
	_field_follow_last_leader_cell = Vector2i(-99999, -99999)
	_field_follow_last_position = Vector2.INF
	_field_follow_stuck_elapsed = 0.0


func _rebuild_follow_path(grid: BattleGrid, leader_cell: Vector2i) -> void:
	_field_follow_path.clear()
	_field_follow_path_index = 0
	_field_follow_last_leader_cell = leader_cell
	_field_follow_refresh_remaining = FOLLOW_PATH_REFRESH_SECONDS
	if not _controllable_ally is Node2D:
		return
	var start_cell: Vector2i = grid.world_to_cell((_controllable_ally as Node2D).global_position)
	var occupied: Dictionary = _field_follow_occupied_cells(grid)
	var state: CombatantState = _ally_state()
	var best_cost: int = 2147483647
	var best_path: Array[Vector2i] = []
	for offset: Vector2i in FOLLOW_NEIGHBOR_OFFSETS:
		var destination: Vector2i = leader_cell + offset
		if not grid.is_cell_valid(destination) or occupied.has(destination):
			continue
		if _combat_environment != null and _combat_environment.is_cell_blocked(grid, destination):
			continue
		var path_result: Dictionary = _movement_planner.build_path(
			grid,
			start_cell,
			destination,
			occupied,
			_combat_environment,
			state,
			FOLLOW_ROUTE_BUDGET_FEET,
			false,
			false
		)
		if not bool(path_result.get("reachable", false)):
			continue
		var cost: int = int(path_result.get("cost_feet", 2147483647))
		var path: Array[Vector2i] = _typed_cell_path(path_result.get("path", []))
		if path.size() <= 1:
			continue
		if cost < best_cost:
			best_cost = cost
			best_path = path
	if not best_path.is_empty():
		_field_follow_path = best_path
		_field_follow_path_index = 1


func _field_follow_occupied_cells(grid: BattleGrid) -> Dictionary:
	var occupied: Dictionary = {}
	for group_name: String in ["player", "controllable_allies", "combat_targets"]:
		for node: Node in get_tree().get_nodes_in_group(group_name):
			if not is_instance_valid(node) or node == _controllable_ally or not node is Node2D:
				continue
			occupied[grid.world_to_cell((node as Node2D).global_position)] = node
	return occupied


func _typed_cell_path(value: Variant) -> Array[Vector2i]:
	var result: Array[Vector2i] = []
	if not value is Array:
		return result
	for cell_value: Variant in value as Array:
		if cell_value is Vector2i:
			result.append(cell_value as Vector2i)
	return result


func _update_follow_stuck_state(ally: CharacterBody2D, delta: float) -> void:
	if _field_follow_last_position == Vector2.INF:
		_field_follow_last_position = ally.global_position
		return
	if ally.global_position.distance_to(_field_follow_last_position) <= 0.75:
		_field_follow_stuck_elapsed += delta
	else:
		_field_follow_stuck_elapsed = 0.0
		_field_follow_last_position = ally.global_position
	if _field_follow_stuck_elapsed < FOLLOW_STUCK_SECONDS:
		return
	_field_follow_path.clear()
	_field_follow_path_index = 0
	_field_follow_refresh_remaining = 0.0
	_field_follow_stuck_elapsed = 0.0
	_field_follow_last_position = ally.global_position


func get_field_visibility_source_for_testing() -> Node:
	var source: Node = get_active_player_controlled_actor()
	return source if is_instance_valid(source) else player


func get_field_follow_path_for_testing() -> Array[Vector2i]:
	return _field_follow_path.duplicate()
