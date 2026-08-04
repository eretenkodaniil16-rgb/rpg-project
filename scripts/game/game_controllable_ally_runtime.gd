extends "res://scripts/game/game_item_use_runtime.gd"

const CONTROLLABLE_ALLY_SCENE: PackedScene = preload("res://scenes/game/controllable_ally.tscn")
const ALLY_CHARACTER_ID: String = "companion_irna_guard_01"
const ALLY_STABILIZE_ACTION_ID: String = "stabilize_controllable_ally"
const ALLY_INTERACTION_DISTANCE_FEET: int = 5
const RESTORE_DELAY_FRAMES: int = 12

var _controllable_ally: Node = null
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
	if is_instance_valid(existing):
		_controllable_ally = existing
		return
	_controllable_ally = CONTROLLABLE_ALLY_SCENE.instantiate()
	if _controllable_ally == null:
		push_error("Не удалось создать управляемого союзника.")
		return
	_controllable_ally.name = "ControllableAllyIrna"
	add_child(_controllable_ally)
	if _controllable_ally is Node2D:
		var spawn_position: Vector2 = player.global_position + Vector2(-72.0, 0.0) if is_instance_valid(player) else Vector2(360.0, 440.0)
		(_controllable_ally as Node2D).global_position = spawn_position


func _start_turn_based_combat(trigger_target: Node) -> void:
	if _ally_is_combat_active():
		_turn_system.set_pending_player_controlled_actors([_controllable_ally])
	else:
		_turn_system.clear_pending_player_controlled_actors()
	super._start_turn_based_combat(trigger_target)
	_turn_system.clear_pending_player_controlled_actors()
	if _turn_system.active:
		_call_ally("set_turn_based_mode", [true])


func _stop_turn_based_combat(message: String) -> void:
	super._stop_turn_based_combat(message)
	_call_ally("set_turn_based_mode", [false])


func _state_for(actor: Node) -> CombatantState:
	if actor == _controllable_ally and is_instance_valid(_controllable_ally):
		return _controllable_ally.call("get_combatant_state") as CombatantState
	return super._state_for(actor)


func _begin_current_turn() -> void:
	if not _turn_system.active:
		return
	var actor: Node = _turn_system.current_actor()
	if actor != _controllable_ally:
		super._begin_current_turn()
		return
	var state: CombatantState = _ally_state()
	if state == null:
		call_deferred("_advance_combat_turn")
		return
	state.tick_conditions("start_turn")
	if _ally_current_health() <= 0:
		_resolve_ally_zero_hp_turn()
		return
	if not _srd_rules.can_take_action(state):
		show_combat_message("Ирна пропускает ход из-за состояния: %s." % _srd_rules.format_conditions(state), false)
		call_deferred("_advance_combat_turn")
		return
	_begin_controllable_ally_turn()


func _begin_controllable_ally_turn() -> void:
	if not _turn_system.is_actor_turn(_controllable_ally):
		return
	_set_all_turn_markers(false)
	_call_ally("set_turn_active", [true])
	_refresh_turn_interface()
	_update_combat_controls()
	show_combat_message("Ход Ирны: доступны перемещение, атака и завершение хода.", true)


func _resolve_ally_zero_hp_turn(roll_override: int = -1) -> Dictionary:
	if _ally_death_save_running or not is_instance_valid(_controllable_ally):
		return {"resolved": false}
	_ally_death_save_running = true
	var state: CombatantState = _ally_state()
	if state == null:
		_ally_death_save_running = false
		return {"resolved": false}
	if state.dead:
		_call_ally("mark_dead")
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
		_call_ally("recover_to_one_hit_point")
		show_combat_message("Натуральная 20: Ирна приходит в сознание с 1 HP.", true)
		_ally_death_save_running = false
		_update_status()
		return result
	if bool(result.get("dead", false)):
		_call_ally("mark_dead")
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


func _build_catalog_entries() -> Dictionary:
	var entries: Dictionary = super._build_catalog_entries()
	_append_controllable_ally_stabilization(entries)
	return entries


func _append_controllable_ally_stabilization(entries: Dictionary) -> void:
	if not is_instance_valid(_controllable_ally):
		return
	if GameState.get_item_count(HEALERS_KIT_ID) <= 0:
		return
	if not _controllable_ally.has_method("can_be_stabilized_with_healers_kit"):
		return
	if not bool(_controllable_ally.call("can_be_stabilized_with_healers_kit")):
		return
	var definition: Dictionary = GameState.get_item_definition(HEALERS_KIT_ID)
	var reachable: bool = _ally_distance_from_player() <= ALLY_INTERACTION_DISTANCE_FEET
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
		_item_use_system.build_action_label(definition, _ally_name()),
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
	if not is_instance_valid(_controllable_ally):
		return {"success": false, "message": "Союзник недоступен."}
	if _ally_distance_from_player() > ALLY_INTERACTION_DISTANCE_FEET:
		var distant: Dictionary = {
			"success": false,
			"message": "Чтобы стабилизировать Ирну, нужно стоять в соседней клетке."
		}
		show_combat_message(str(distant.get("message", "")), false)
		return distant
	var result: Dictionary = _execute_item_use(HEALERS_KIT_ID, _controllable_ally, {})
	show_combat_message(
		str(result.get("message", "Набор лекаря использован.")),
		bool(result.get("success", false))
	)
	_update_status()
	_refresh_turn_interface()
	return result


func _refresh_turn_interface() -> void:
	if _turn_ui == null:
		return
	var controlled_actor: Node = player
	if _turn_system.active and _turn_system.is_player_controlled_turn():
		controlled_actor = _turn_system.current_actor()
	_turn_ui.refresh(_turn_system, controlled_actor, _any_overlay_visible(), _enemy_turn_running)


func _set_all_turn_markers(value: bool) -> void:
	super._set_all_turn_markers(value)
	_call_ally("set_turn_active", [value])


func _update_status() -> void:
	super._update_status()
	if status_label == null or not is_instance_valid(_controllable_ally):
		return
	var state: CombatantState = _ally_state()
	var state_label: String = "в строю"
	if state != null and state.dead:
		state_label = "погибла"
	elif _ally_current_health() <= 0 and state != null and state.stable:
		state_label = "стабильна"
	elif _ally_current_health() <= 0:
		state_label = "умирает"
	status_label.text += "\nСоюзник: Ирна · %s · HP %d/%d" % [
		state_label,
		_ally_current_health(),
		_ally_maximum_health()
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
	if not is_instance_valid(_controllable_ally) or not _controllable_ally.has_method("capture_world_state"):
		return {}
	return {
		"revision": 1,
		"location_id": "guard_post",
		"entities": {
			ALLY_CHARACTER_ID: _controllable_ally.call("capture_world_state") as Dictionary
		}
	}


func _restore_controllable_ally_after_scene_ready() -> void:
	for _frame: int in range(RESTORE_DELAY_FRAMES):
		await get_tree().process_frame
	if not is_instance_valid(_controllable_ally):
		_ally_restore_complete = true
		return
	var stored: Dictionary = GameState.get_world_entity_state(ALLY_CHARACTER_ID)
	if not stored.is_empty() and _controllable_ally.has_method("restore_world_state"):
		_controllable_ally.call("restore_world_state", stored)
	_ally_restore_complete = true
	_update_status()


func get_controllable_ally_for_testing() -> Node:
	return _controllable_ally


func resolve_controllable_ally_death_save_for_testing(natural: int) -> Dictionary:
	return _resolve_ally_zero_hp_turn(natural)


func _ally_is_combat_active() -> bool:
	return (
		is_instance_valid(_controllable_ally)
		and (
			not _controllable_ally.has_method("is_combat_active")
			or bool(_controllable_ally.call("is_combat_active"))
		)
	)


func _ally_state() -> CombatantState:
	if not is_instance_valid(_controllable_ally) or not _controllable_ally.has_method("get_combatant_state"):
		return null
	return _controllable_ally.call("get_combatant_state") as CombatantState


func _ally_current_health() -> int:
	return int(_controllable_ally.call("get_current_health")) if is_instance_valid(_controllable_ally) and _controllable_ally.has_method("get_current_health") else 0


func _ally_maximum_health() -> int:
	return int(_controllable_ally.call("get_maximum_health")) if is_instance_valid(_controllable_ally) and _controllable_ally.has_method("get_maximum_health") else 1


func _ally_name() -> String:
	return str(_controllable_ally.call("get_combat_name")) if is_instance_valid(_controllable_ally) and _controllable_ally.has_method("get_combat_name") else "Ирна"


func _ally_distance_from_player() -> int:
	if not is_instance_valid(_controllable_ally) or not _controllable_ally is Node2D or not is_instance_valid(player):
		return 9999
	return DistanceSystem.distance_feet(player.global_position, (_controllable_ally as Node2D).global_position)


func _call_ally(method_name: String, arguments: Array = []) -> Variant:
	if not is_instance_valid(_controllable_ally) or not _controllable_ally.has_method(method_name):
		return null
	return _controllable_ally.callv(method_name, arguments)
