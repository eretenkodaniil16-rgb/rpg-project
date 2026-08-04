extends "res://scripts/game/game_item_use_runtime.gd"

const CONTROLLABLE_ALLY_SCENE: PackedScene = preload("res://scenes/game/controllable_ally.tscn")
const ALLY_CHARACTER_ID: String = "companion_irna_guard_01"
const ALLY_STABILIZE_ACTION_ID: String = "stabilize_controllable_ally"
const ALLY_INTERACTION_DISTANCE_FEET: int = 5
const GRID_STEP_FEET_ALLY: int = 5
const RESTORE_DELAY_FRAMES: int = 12

var _controllable_ally: ControllableAlly = null
var _ally_death_save_running: bool = false
var _ally_restore_complete: bool = false


func _ready() -> void:
	super._ready()
	_ensure_controllable_ally()
	add_to_group("world_state_serializers")
	call_deferred("_restore_controllable_ally_after_scene_ready")
	_update_status()


func _ensure_controllable_ally() -> void:
	var existing: Node = get_tree().get_first_node_in_group("controllable_allies")
	if existing is ControllableAlly and is_instance_valid(existing as ControllableAlly):
		_controllable_ally = existing as ControllableAlly
		return
	_controllable_ally = CONTROLLABLE_ALLY_SCENE.instantiate() as ControllableAlly
	if _controllable_ally == null:
		push_error("Не удалось создать управляемого союзника.")
		return
	_controllable_ally.name = "ControllableAllyIrna"
	add_child(_controllable_ally)
	var spawn_position: Vector2 = player.global_position + Vector2(-72.0, 0.0) if is_instance_valid(player) else Vector2(360.0, 440.0)
	_controllable_ally.global_position = spawn_position


func _start_turn_based_combat(trigger_target: Node) -> void:
	if _controllable_ally != null and _controllable_ally.is_combat_active():
		_turn_system.set_pending_player_controlled_actors([_controllable_ally])
	else:
		_turn_system.clear_pending_player_controlled_actors()
	super._start_turn_based_combat(trigger_target)
	_turn_system.clear_pending_player_controlled_actors()
	if _turn_system.active and _controllable_ally != null:
		_controllable_ally.set_turn_based_mode(true)


func _stop_turn_based_combat(message: String) -> void:
	super._stop_turn_based_combat(message)
	if _controllable_ally != null:
		_controllable_ally.set_turn_based_mode(false)


func _snap_combatants_to_cells() -> void:
	super._snap_combatants_to_cells()
	if _controllable_ally == null or not _controllable_ally.is_combat_active():
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
	if has_method("_place_actor_in_stable_combat_cell"):
		call("_place_actor_in_stable_combat_cell", _controllable_ally, grid, occupied)
	else:
		var ally_cell: Vector2i = grid.snap_actor_to_free_cell(_controllable_ally, occupied)
		occupied[ally_cell] = _controllable_ally


func _state_for(actor: Node) -> CombatantState:
	if _controllable_ally != null and actor == _controllable_ally:
		return _controllable_ally.get_combatant_state()
	return super._state_for(actor)


func _begin_current_turn() -> void:
	if not _turn_system.active:
		return
	var actor: Node = _turn_system.current_actor()
	if _controllable_ally == null or actor != _controllable_ally:
		super._begin_current_turn()
		return
	var state: CombatantState = _controllable_ally.get_combatant_state()
	state.tick_conditions("start_turn")
	if _controllable_ally.current_health <= 0:
		_resolve_ally_zero_hp_turn()
		return
	if not _srd_rules.can_take_action(state):
		show_combat_message(
			"%s пропускает ход из-за состояния: %s." % [
				_controllable_ally.get_combat_name(),
				_srd_rules.format_conditions(state)
			],
			false
		)
		call_deferred("_advance_combat_turn")
		return
	_begin_controllable_ally_turn()


func _begin_controllable_ally_turn() -> void:
	if _controllable_ally == null or not _turn_system.is_actor_turn(_controllable_ally):
		return
	_set_all_turn_markers(false)
	_controllable_ally.set_turn_active(true)
	var grid: BattleGrid = _get_battle_grid()
	if grid != null:
		grid.set_active_actor(_controllable_ally)
	_refresh_turn_interface()
	_update_combat_controls()
	show_combat_message(
		"Ход Ирны: выберите врага, переместитесь или выполните атаку.",
		true
	)


func _resolve_ally_zero_hp_turn(roll_override: int = -1) -> Dictionary:
	if _ally_death_save_running or _controllable_ally == null:
		return {"resolved": false}
	_ally_death_save_running = true
	var state: CombatantState = _controllable_ally.get_combatant_state()
	if state.dead:
		_controllable_ally.mark_dead()
		_ally_death_save_running = false
		call_deferred("_advance_combat_turn")
		return {"resolved": false, "dead": true}
	if state.stable:
		show_combat_message("Ирна стабильна, но остаётся без сознания.", true)
		_ally_death_save_running = false
		call_deferred("_advance_combat_turn")
		return {"resolved": false, "stable": true}
	var result: Dictionary = _srd_rules.resolve_death_save(state, roll_override)
	if bool(result.get("regained_hit_point", false)):
		_controllable_ally.recover_to_one_hit_point()
		show_combat_message("Натуральная 20: Ирна приходит в сознание с 1 HP.", true)
		_ally_death_save_running = false
		_begin_controllable_ally_turn()
		_update_status()
		return result
	if bool(result.get("dead", false)):
		_controllable_ally.mark_dead()
	show_combat_message(
		"Спасбросок смерти Ирны: %d · успехи %d/3 · провалы %d/3." % [
			int(result.get("natural", 0)),
			int(result.get("successes", 0)),
			int(result.get("failures", 0))
		],
		not bool(result.get("dead", false))
	)
	_ally_death_save_running = false
	_update_status()
	call_deferred("_advance_combat_turn")
	return result


func _request_attack() -> void:
	if _is_controllable_ally_turn():
		await _request_controllable_ally_attack()
		return
	await super._request_attack()


func _request_controllable_ally_attack(roll_override: int = -1) -> void:
	if not _ally_turn_input_available():
		return
	if not _target_is_valid(_selected_target):
		_select_nearest_target()
	if not _target_is_valid(_selected_target):
		show_combat_message("Для атаки Ирны выберите доступного противника.", false)
		return
	var target: Node = _selected_target
	var result: AttackResult = _controllable_ally.build_basic_attack_result(target, roll_override)
	if result.out_of_range:
		if _attack_popup != null:
			_attack_popup.show_result(result)
		show_combat_message(result.note, false)
		return
	if not _turn_system.consume_action():
		show_combat_message("Основное действие Ирны уже использовано.", false)
		return
	_set_combat_busy(true)
	await _controllable_ally.play_attack_animation((target as Node2D).global_position)
	if _target_is_valid(target):
		target.call("receive_player_attack", result, true)
	_set_combat_busy(false)
	_update_status()
	_after_player_action()


func request_combat_move(step: Vector2i) -> void:
	if not _is_controllable_ally_turn():
		super.request_combat_move(step)
		return
	if not _ally_turn_input_available() or step == Vector2i.ZERO:
		return
	var state: CombatantState = _controllable_ally.get_combatant_state()
	if _srd_rules.effective_speed_feet(_controllable_ally.get_combat_speed_feet(), state) <= 0:
		show_combat_message("Состояние Ирны не позволяет перемещаться.", false)
		return
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return
	var current_cell: Vector2i = grid.world_to_cell(_controllable_ally.global_position)
	var destination_cell: Vector2i = current_cell + step
	if not grid.is_cell_valid(destination_cell):
		show_combat_message("Эта клетка находится за пределами поля боя.", false)
		return
	if _occupied_cells(_controllable_ally).has(destination_cell):
		show_combat_message("Клетка занята другим участником.", false)
		return
	if _combat_environment != null:
		if _combat_environment.is_cell_blocked(grid, destination_cell):
			show_combat_message("Клетка перекрыта препятствием.", false)
			return
		if _combat_environment.is_transition_blocked(grid, current_cell, destination_cell):
			show_combat_message("Между клетками находится стена или закрытая дверь.", false)
			return
	var destination: Vector2 = grid.cell_to_world_center(destination_cell)
	var difficult: bool = _combat_environment != null and _combat_environment.is_difficult_position(destination)
	var movement_cost: int = _srd_rules.movement_cost_feet(
		GRID_STEP_FEET_ALLY,
		state,
		difficult,
		state.has_condition("prone")
	)
	if _turn_system.movement_remaining_feet < movement_cost:
		show_combat_message("Ирне не хватает перемещения: требуется %d футов." % movement_cost, false)
		return
	if not _turn_system.disengaged:
		_trigger_enemy_opportunity_attacks_against_ally(
			_controllable_ally.global_position,
			destination
		)
		if _controllable_ally.get_combatant_state().dead:
			return
	if not _turn_system.spend_movement(movement_cost):
		return
	_controllable_ally.global_position = destination
	_controllable_ally.set_facing_direction(Vector2(step))
	_refresh_turn_interface()
	_update_target_label()


func _trigger_enemy_opportunity_attacks_against_ally(
	from_position: Vector2,
	to_position: Vector2
) -> void:
	for entry: Dictionary in _turn_system.entries:
		if bool(entry.get("is_player", false)):
			continue
		var attacker: Node = entry.get("node") as Node
		if not is_instance_valid(attacker) or not attacker is Node2D:
			continue
		if attacker.has_method("is_hostile") and not bool(attacker.call("is_hostile")):
			continue
		if not _turn_system.has_reaction(attacker):
			continue
		var current_distance: int = DistanceSystem.distance_feet(
			(attacker as Node2D).global_position,
			from_position
		)
		var future_distance: int = DistanceSystem.distance_feet(
			(attacker as Node2D).global_position,
			to_position
		)
		if (
			current_distance <= DistanceSystem.MELEE_REACH_FEET
			and future_distance > DistanceSystem.MELEE_REACH_FEET
		):
			_turn_system.consume_reaction(attacker)
			show_combat_message(
				"%s проводит атаку по возможности против Ирны." % _target_name(attacker),
				false
			)
			_resolve_npc_attack_against_ally(
				attacker,
				int(attacker.get("attack_bonus")),
				int(attacker.get("damage_die")),
				int(attacker.get("damage_bonus")),
				str(attacker.get("damage_type"))
			)
			if _controllable_ally.get_combatant_state().dead:
				return


func resolve_npc_attack(
	attacker: Node,
	attack_bonus: int,
	damage_die: int,
	damage_bonus: int,
	damage_type: String = "slashing"
) -> Dictionary:
	if _enemy_should_attack_ally(attacker):
		return _resolve_npc_attack_against_ally(
			attacker,
			attack_bonus,
			damage_die,
			damage_bonus,
			damage_type
		)
	return super.resolve_npc_attack(
		attacker,
		attack_bonus,
		damage_die,
		damage_bonus,
		damage_type
	)


func _enemy_should_attack_ally(attacker: Node) -> bool:
	if (
		_controllable_ally == null
		or not _controllable_ally.can_receive_enemy_attack()
		or not is_instance_valid(attacker)
		or not attacker is Node2D
	):
		return false
	var ally_distance: int = DistanceSystem.distance_feet(
		(attacker as Node2D).global_position,
		_controllable_ally.global_position
	)
	if ally_distance > DistanceSystem.MELEE_REACH_FEET:
		return false
	var player_distance: int = DistanceSystem.distance_feet(
		(attacker as Node2D).global_position,
		player.global_position
	)
	return GameState.player_character.current_health <= 0 or ally_distance <= player_distance


func _resolve_npc_attack_against_ally(
	attacker: Node,
	attack_bonus: int,
	damage_die: int,
	damage_bonus: int,
	damage_type: String
) -> Dictionary:
	if _controllable_ally == null or not _controllable_ally.can_receive_enemy_attack():
		return {"hit": false}
	var attacker_position: Vector2 = (attacker as Node2D).global_position if attacker is Node2D else Vector2.ZERO
	var distance: int = DistanceSystem.distance_feet(
		attacker_position,
		_controllable_ally.global_position
	)
	var cover: Dictionary = (
		_combat_environment.get_cover(attacker_position, _controllable_ally.global_position)
		if _combat_environment != null
		else {"bonus": 0, "total_cover": false}
	)
	if bool(cover.get("total_cover", false)):
		show_combat_message("%s не видит Ирну за полным укрытием." % _target_name(attacker), false)
		return {"hit": false, "total_cover": true}
	var attacker_state: CombatantState = _state_for(attacker)
	var defender_state: CombatantState = _controllable_ally.get_combatant_state()
	var adjustments: Dictionary = _srd_rules.attack_roll_adjustments(
		attacker_state,
		defender_state,
		distance,
		true,
		true
	)
	if bool(adjustments.get("blocked", false)):
		return {"hit": false, "blocked": true}
	var roll: Dictionary = _srd_rules.roll_d20(
		attack_bonus,
		bool(adjustments.get("advantage", false)),
		bool(adjustments.get("disadvantage", false)) or _controllable_ally.is_dodging()
	)
	var natural: int = int(roll.get("natural", 1))
	var target_ac: int = _controllable_ally.get_armor_class() + int(cover.get("bonus", 0))
	var hit: bool = natural != 1 and (
		natural == 20 or int(roll.get("total", 0)) >= target_ac
	)
	if not hit:
		show_combat_message(
			"%s промахивается по Ирне: %d против КД %d." % [
				_target_name(attacker),
				int(roll.get("total", 0)),
				target_ac
			],
			false
		)
		return {
			"hit": false,
			"natural": natural,
			"total": int(roll.get("total", 0))
		}
	var critical: bool = natural == 20 or bool(adjustments.get("automatic_critical", false))
	var damage: int = damage_bonus
	for _index: int in range(2 if critical else 1):
		damage += _srd_dice.roll_die(maxi(damage_die, 2))
	return _apply_damage_to_ally(damage, damage_type, critical, attacker)


func _apply_damage_to_ally(
	amount: int,
	damage_type: String,
	critical_hit: bool = false,
	source: Node = null
) -> Dictionary:
	if _controllable_ally == null:
		return {"hit": false, "applied": 0}
	var state: CombatantState = _controllable_ally.get_combatant_state()
	if state.dead:
		return {"hit": true, "applied": 0, "dead": true}
	if _controllable_ally.current_health <= 0:
		var zero_result: Dictionary = _srd_rules.damage_at_zero_hit_points(state, critical_hit)
		show_combat_message(
			"Урон по Ирне при 0 HP: %d провала спасброска смерти." % int(
				zero_result.get("failures_added", 0)
			),
			false
		)
		if bool(zero_result.get("dead", false)):
			_controllable_ally.mark_dead()
		_update_status()
		return zero_result
	var mitigation: Dictionary = _srd_rules.resolve_damage(amount, damage_type, state)
	var applied: int = int(mitigation.get("applied", 0))
	var before: int = _controllable_ally.current_health
	_controllable_ally.current_health = maxi(0, before - applied)
	var remaining_damage: int = maxi(applied - before, 0)
	show_combat_message(
		"%s наносит Ирне %d урона. HP: %d/%d." % [
			_target_name(source) if source != null else "Источник",
			applied,
			_controllable_ally.current_health,
			_controllable_ally.maximum_health
		],
		false
	)
	if _controllable_ally.current_health <= 0:
		if remaining_damage >= _controllable_ally.maximum_health:
			_controllable_ally.mark_dead()
			show_combat_message("Ирна погибает от массивного урона.", false)
		else:
			_controllable_ally.enter_dying()
			show_combat_message(
				"Ирна без сознания и начинает совершать спасброски смерти.",
				false
			)
	else:
		_controllable_ally.call("_update_combat_visuals")
	_update_status()
	return {
		"hit": true,
		"applied": applied,
		"critical": critical_hit,
		"dead": state.dead
	}


func _build_catalog_entries() -> Dictionary:
	var entries: Dictionary = super._build_catalog_entries()
	_append_controllable_ally_stabilization(entries)
	return entries


func _append_controllable_ally_stabilization(entries: Dictionary) -> void:
	if (
		_controllable_ally == null
		or GameState.get_item_count(HEALERS_KIT_ID) <= 0
		or not _controllable_ally.can_be_stabilized_with_healers_kit()
	):
		return
	var definition: Dictionary = GameState.get_item_definition(HEALERS_KIT_ID)
	var reachable: bool = DistanceSystem.distance_feet(
		player.global_position,
		_controllable_ally.global_position
	) <= ALLY_INTERACTION_DISTANCE_FEET
	var player_can_use: bool = (
		not _turn_system.active
		or (
			_turn_system.is_player_turn(player)
			and _turn_system.action_available
			and not _enemy_turn_running
		)
	)
	var action_entries: Array = entries.get("action", []) as Array
	action_entries.append(_entry(
		ALLY_STABILIZE_ACTION_ID,
		_item_use_system.build_action_label(
			definition,
			_controllable_ally.get_combat_name()
		),
		reachable and player_can_use,
		"Стабилизировать Ирну набором лекаря. HP не восстанавливаются.",
		"item"
	))
	entries["action"] = action_entries


func _on_feedback_catalog_action_requested(action_id: String) -> void:
	if action_id == ALLY_STABILIZE_ACTION_ID:
		_stabilize_controllable_ally()
		_refresh_action_catalog()
		return
	super._on_feedback_catalog_action_requested(action_id)


func _stabilize_controllable_ally() -> Dictionary:
	if _controllable_ally == null:
		return {"success": false, "message": "Союзник недоступен."}
	if DistanceSystem.distance_feet(
		player.global_position,
		_controllable_ally.global_position
	) > ALLY_INTERACTION_DISTANCE_FEET:
		var distant: Dictionary = {
			"success": false,
			"message": "Чтобы стабилизировать Ирну, нужно стоять в соседней клетке."
		}
		show_combat_message(str(distant["message"]), false)
		return distant
	var result: Dictionary = _execute_item_use(
		HEALERS_KIT_ID,
		_controllable_ally,
		{}
	)
	show_combat_message(
		str(result.get("message", "Набор лекаря использован.")),
		bool(result.get("success", false))
	)
	_update_status()
	_refresh_turn_interface()
	return result


func _on_ability_requested(ability_id: String) -> void:
	if _is_controllable_ally_turn():
		if _ability_panel != null:
			_ability_panel.set_message(
				"В текущем этапе Ирна использует только обычную атаку.",
				false
			)
		return
	await super._on_ability_requested(ability_id)


func _on_dash_requested() -> void:
	if not _is_controllable_ally_turn():
		super._on_dash_requested()
		return
	if not _ally_turn_input_available():
		return
	if _turn_system.use_dash(_controllable_ally.get_combat_speed_feet()):
		show_combat_message("Ирна выполняет Рывок.", true)
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
		_controllable_ally.set_dodging(true)
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
		_on_feedback_target_requested()
		return
	super._cycle_target()


func _select_nearest_target() -> void:
	if not _is_controllable_ally_turn():
		super._select_nearest_target()
		return
	var targets: Array[Node] = _available_targets()
	if targets.is_empty():
		_set_selected_target(null)
		return
	var nearest: Node = targets[0]
	var nearest_distance: float = _controllable_ally.global_position.distance_squared_to(
		(nearest as Node2D).global_position
	)
	for target: Node in targets:
		var candidate: float = _controllable_ally.global_position.distance_squared_to(
			(target as Node2D).global_position
		)
		if candidate < nearest_distance:
			nearest = target
			nearest_distance = candidate
	_set_selected_target(nearest)


func _update_target_label() -> void:
	super._update_target_label()
	if (
		_target_label == null
		or not _is_controllable_ally_turn()
		or not _target_is_valid(_selected_target)
	):
		return
	var distance: int = DistanceSystem.distance_feet(
		_controllable_ally.global_position,
		(_selected_target as Node2D).global_position
	)
	_target_label.text = "Ирна → %s · %d футов · КД %d" % [
		_target_name(_selected_target),
		distance,
		int(_selected_target.call("get_armor_class"))
	]


func _refresh_turn_interface() -> void:
	if _turn_ui == null:
		return
	var controlled_actor: Node = player
	if _turn_system.active and _turn_system.is_player_controlled_turn():
		controlled_actor = _turn_system.current_actor()
	_turn_ui.refresh(
		_turn_system,
		controlled_actor,
		_any_overlay_visible(),
		_enemy_turn_running
	)


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


func _occupied_cells(excluded_actor: Node = null) -> Dictionary:
	var occupied: Dictionary = super._occupied_cells(excluded_actor)
	if (
		_controllable_ally != null
		and _controllable_ally != excluded_actor
		and _controllable_ally.is_combat_active()
	):
		var grid: BattleGrid = _get_battle_grid()
		if grid != null:
			occupied[grid.world_to_cell(_controllable_ally.global_position)] = _controllable_ally
	return occupied


func _set_all_turn_markers(value: bool) -> void:
	super._set_all_turn_markers(value)
	if _controllable_ally != null:
		_controllable_ally.set_turn_active(value)


func _is_controllable_ally_turn() -> bool:
	return (
		_turn_system.active
		and _controllable_ally != null
		and _turn_system.is_actor_turn(_controllable_ally)
		and not _enemy_turn_running
	)


func _ally_turn_input_available() -> bool:
	if not _is_controllable_ally_turn():
		show_combat_message("Сейчас не ход Ирны.", false)
		return false
	if GameState.input_locked or _any_overlay_visible() or _attack_in_progress:
		return false
	return true


func _update_status() -> void:
	super._update_status()
	if status_label == null or _controllable_ally == null:
		return
	var state: CombatantState = _controllable_ally.get_combatant_state()
	var state_label: String = "в строю"
	if state.dead:
		state_label = "погибла"
	elif _controllable_ally.current_health <= 0 and state.stable:
		state_label = "стабильна"
	elif _controllable_ally.current_health <= 0:
		state_label = "умирает"
	status_label.text += "\nСоюзник: Ирна · %s · HP %d/%d" % [
		state_label,
		_controllable_ally.current_health,
		_controllable_ally.maximum_health
	]


func can_capture_stable_world_state() -> bool:
	return (
		not _turn_system.active
		and not _attack_in_progress
		and not _enemy_turn_running
		and _ally_restore_complete
	)


func prepare_world_state_for_save() -> void:
	pass


func capture_world_state_for_save() -> Dictionary:
	if _controllable_ally == null:
		return {}
	return {
		"revision": 1,
		"location_id": "guard_post",
		"entities": {
			ALLY_CHARACTER_ID: _controllable_ally.capture_world_state()
		}
	}


func _restore_controllable_ally_after_scene_ready() -> void:
	for _frame: int in range(RESTORE_DELAY_FRAMES):
		await get_tree().process_frame
	if _controllable_ally == null:
		_ally_restore_complete = true
		return
	var stored: Dictionary = GameState.get_world_entity_state(ALLY_CHARACTER_ID)
	if not stored.is_empty():
		_controllable_ally.restore_world_state(stored)
	_ally_restore_complete = true
	_update_status()


func get_controllable_ally_for_testing() -> ControllableAlly:
	return _controllable_ally


func force_controllable_ally_turn_for_testing() -> void:
	if _turn_system.active and _controllable_ally != null:
		_turn_system.force_current_actor_for_testing(_controllable_ally)
		_begin_current_turn()


func resolve_controllable_ally_death_save_for_testing(natural: int) -> Dictionary:
	if _controllable_ally == null:
		return {"resolved": false}
	return _resolve_ally_zero_hp_turn(natural)


func apply_damage_to_controllable_ally_for_testing(
	amount: int,
	critical_hit: bool = false
) -> Dictionary:
	return _apply_damage_to_ally(amount, "slashing", critical_hit, null)


func perform_controllable_ally_attack_for_testing(roll_override: int) -> void:
	await _request_controllable_ally_attack(roll_override)
