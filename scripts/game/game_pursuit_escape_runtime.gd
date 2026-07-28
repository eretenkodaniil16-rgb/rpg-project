extends "res://scripts/game/game_exploration_stealth_runtime.gd"

const PATROL_ALERT_GROUP_SYSTEM_AI_SCRIPT: Script = preload("res://scripts/systems/patrol_alert_group_system_ai.gd")
const NPC_AI_SYSTEM_SCRIPT: Script = preload("res://scripts/systems/npc_ai_system.gd")
const NPC_NAVIGATION_SYSTEM_SCRIPT: Script = preload("res://scripts/systems/npc_navigation_system.gd")
const TURN_BASED_COMBAT_SYSTEM_AI_SCRIPT: Script = preload("res://scripts/systems/turn_based_combat_system_ai.gd")

const PLAYER_FEEDBACK_STATE_PRIORITY: Dictionary = {
	StealthAlertSystem.STATE_CALM: 0,
	StealthAlertSystem.STATE_SUSPICIOUS: 1,
	StealthAlertSystem.STATE_INVESTIGATING: 2,
	StealthAlertSystem.STATE_SEARCHING: 3,
	StealthAlertSystem.STATE_ALERTED: 4,
	StealthAlertSystem.STATE_COMBAT: 5
}
const CONTEXT_INTERACTION_DISTANCE_FEET: int = 10

var _patrol_alert_groups: PatrolAlertGroupSystemAi = PATROL_ALERT_GROUP_SYSTEM_AI_SCRIPT.new() as PatrolAlertGroupSystemAi
var _npc_ai: NpcAiSystem = NPC_AI_SYSTEM_SCRIPT.new() as NpcAiSystem
var _npc_navigation: NpcNavigationSystem = NPC_NAVIGATION_SYSTEM_SCRIPT.new() as NpcNavigationSystem
var _alert_broadcasted: Dictionary = {}
var _inspected_target_instance_id: int = 0


func _ready() -> void:
	_turn_system = TURN_BASED_COMBAT_SYSTEM_AI_SCRIPT.new() as TurnBasedCombatSystemAi
	super._ready()
	_refresh_action_catalog()


func _process(delta: float) -> void:
	super._process(delta)
	if _turn_system.active:
		_update_pending_combat_joins()


func _update_exploration_alerts(delta: float) -> void:
	if _any_overlay_visible() or (_action_catalog_ui != null and _action_catalog_ui.is_catalog_open()):
		return
	super._update_exploration_alerts(delta)


func _update_exploration_step_noise(delta: float) -> void:
	if _any_overlay_visible() or (_action_catalog_ui != null and _action_catalog_ui.is_catalog_open()):
		_last_exploration_player_position = player.global_position
		_step_noise_elapsed = 0.0
		return
	super._update_exploration_step_noise(delta)


func _exploration_alert_actors() -> Array[Node]:
	var result: Array[Node] = super._exploration_alert_actors()
	var seen_ids: Dictionary = {}
	for actor: Node in result:
		if is_instance_valid(actor):
			seen_ids[actor.get_instance_id()] = true
	for actor: Node in get_tree().get_nodes_in_group("stealth_alert_actors"):
		if not is_instance_valid(actor) or not (actor is Node2D) or not actor.has_method("get_actor_id"):
			continue
		if seen_ids.has(actor.get_instance_id()):
			continue
		var actor_id: String = str(actor.call("get_actor_id"))
		if actor_id.is_empty() or not _stealth_alerts.has_profile(actor_id):
			continue
		if actor.has_method("is_combat_active") and not bool(actor.call("is_combat_active")):
			continue
		result.append(actor)
		seen_ids[actor.get_instance_id()] = true
	return result


func _context_targets() -> Array[Node]:
	var result: Array[Node] = []
	var seen_ids: Dictionary = {}
	for group_id: String in ["combat_targets", "context_action_targets"]:
		for actor: Node in get_tree().get_nodes_in_group(group_id):
			if not is_instance_valid(actor) or not (actor is Node2D):
				continue
			if actor.has_method("is_combat_active") and not bool(actor.call("is_combat_active")):
				continue
			if seen_ids.has(actor.get_instance_id()):
				continue
			result.append(actor)
			seen_ids[actor.get_instance_id()] = true
	result.sort_custom(func(left: Node, right: Node) -> bool:
		return player.global_position.distance_squared_to((left as Node2D).global_position) < player.global_position.distance_squared_to((right as Node2D).global_position)
	)
	return result


func _cycle_target() -> void:
	if _turn_system.active:
		super._cycle_target()
		return
	if GameState.input_locked or _attack_in_progress or _any_overlay_visible():
		return
	var targets: Array[Node] = _context_targets()
	if targets.is_empty():
		_set_selected_target(null)
		show_combat_message("Рядом нет доступных целей или объектов.", false)
		return
	var current_index: int = targets.find(_selected_target)
	if current_index < 0:
		_set_selected_target(targets[0])
	elif current_index + 1 < targets.size():
		_set_selected_target(targets[current_index + 1])
	else:
		_set_selected_target(null)
	_refresh_action_catalog()


func _set_selected_target(target: Node) -> void:
	var previous_id: int = _selected_target.get_instance_id() if is_instance_valid(_selected_target) else 0
	super._set_selected_target(target)
	var current_id: int = _selected_target.get_instance_id() if is_instance_valid(_selected_target) else 0
	if previous_id != current_id:
		_inspected_target_instance_id = 0
	_refresh_action_catalog()


func _update_target_label() -> void:
	if _target_label == null:
		return
	var has_target: bool = _target_is_valid(_selected_target)
	_target_label.visible = has_target and not _any_overlay_visible()
	if _target_button != null:
		_target_button.text = "СЛЕД. ЦЕЛЬ" if has_target else "ЦЕЛЬ"
	if not has_target:
		_target_label.text = ""
		return
	var target_position: Vector2 = (_selected_target as Node2D).global_position
	var distance: int = DistanceSystem.distance_feet(player.global_position, target_position)
	var base_text: String = "Цель: %s · %d футов" % [_target_name(_selected_target), distance]
	if not _selected_target_is_inspected():
		_target_label.text = "%s · состояние неизвестно — откройте ДЕЙСТВИЯ" % base_text
		return
	var status_text: String = str(_selected_target.call("get_context_status_text")) if _selected_target.has_method("get_context_status_text") else "Внешнее состояние не удалось определить."
	_target_label.text = "%s · %s" % [base_text, status_text]


func _selected_target_is_inspected() -> bool:
	return is_instance_valid(_selected_target) and _selected_target.get_instance_id() == _inspected_target_instance_id


func _build_catalog_entries() -> Dictionary:
	if _turn_system.active:
		var combat_entries: Dictionary = super._build_catalog_entries()
		var action_entries: Array = combat_entries.get("action", []) as Array
		action_entries.append(_entry(
			"inspect_target",
			"ОСМОТРЕТЬ ЦЕЛЬ",
			_target_is_valid(_selected_target),
			"Оценить наблюдаемое поведение, отношение и тяжесть ранений выбранного существа. Не раскрывает скрытые числовые характеристики.",
			"target"
		))
		combat_entries["action"] = action_entries
		return combat_entries

	var inherited: Dictionary = super._build_catalog_entries()
	var selected: bool = _target_is_valid(_selected_target)
	var interaction_ready: bool = selected and _selected_target.has_method("interact") and DistanceSystem.distance_feet(player.global_position, (_selected_target as Node2D).global_position) <= CONTEXT_INTERACTION_DISTANCE_FEET
	var action_entries: Array[Dictionary] = [
		_entry("inspect_target", "ОСМОТРЕТЬ", selected, "Оценить только внешне наблюдаемое состояние выбранного NPC.", "target"),
		_entry("context_interact", "ВЗАИМОДЕЙСТВОВАТЬ", interaction_ready, "Поговорить или применить основное взаимодействие к выбранной цели. Требуется приблизиться.", "target"),
		_entry("attack", "АТАКОВАТЬ", selected and _selected_target.has_method("receive_player_attack"), "Совершить обычную атаку по выбранной цели. Это может начать бой.", "target"),
		_entry("clear_target", "СНЯТЬ ВЫБОР", selected, "Отменить выбор текущей цели.", "target")
	]
	var inherited_actions: Array = inherited.get("action", []) as Array
	for entry_value: Variant in inherited_actions:
		if not entry_value is Dictionary:
			continue
		var entry: Dictionary = entry_value as Dictionary
		if str(entry.get("id", "")) == "exploration_hide":
			action_entries.append(entry.duplicate(true))
	return {"action": action_entries, "bonus": [], "reaction": []}


func _on_catalog_action_requested(action_id: String) -> void:
	match action_id:
		"inspect_target":
			_inspect_selected_target()
		"context_interact":
			_context_interact_selected_target()
		"clear_target":
			_set_selected_target(null)
			show_combat_message("Выбор цели снят.", true)
		_:
			super._on_catalog_action_requested(action_id)
	_refresh_action_catalog()


func _inspect_selected_target() -> void:
	if not _target_is_valid(_selected_target):
		show_combat_message("Сначала выберите цель.", false)
		return
	_inspected_target_instance_id = _selected_target.get_instance_id()
	_update_target_label()
	var status_text: String = str(_selected_target.call("get_context_status_text")) if _selected_target.has_method("get_context_status_text") else "Можно оценить только положение цели."
	show_combat_message("%s: %s" % [_target_name(_selected_target), status_text], true)


func _context_interact_selected_target() -> void:
	if not _target_is_valid(_selected_target) or not _selected_target.has_method("interact"):
		show_combat_message("У выбранной цели нет доступного взаимодействия.", false)
		return
	var distance: int = DistanceSystem.distance_feet(player.global_position, (_selected_target as Node2D).global_position)
	if distance > CONTEXT_INTERACTION_DISTANCE_FEET:
		show_combat_message("Для взаимодействия нужно приблизиться.", false)
		return
	_selected_target.call("interact")


func _refresh_action_catalog() -> void:
	if _action_catalog_ui == null:
		return
	if _turn_system.active:
		super._refresh_action_catalog()
		return
	var target_text: String = "Цель не выбрана. Выберите NPC кнопкой ЦЕЛЬ."
	if _target_is_valid(_selected_target):
		target_text = "Выбрано: %s. Состояние раскрывается только действием ОСМОТРЕТЬ." % _target_name(_selected_target)
	_action_catalog_ui.refresh(
		false,
		true,
		_any_overlay_visible(),
		_build_catalog_entries(),
		target_text,
		"исследование",
		false,
		0
	)


func _update_exploration_actor(actor: Node, delta: float) -> void:
	if actor == null or not is_instance_valid(actor) or not (actor is Node2D):
		return
	var actor_id: String = str(actor.call("get_actor_id"))
	var profile: Dictionary = _stealth_alerts.get_profile(actor_id)
	if profile.is_empty():
		return
	var record: Dictionary = _record_for_actor(actor_id)
	var previous_state: String = str(record.get("state", StealthAlertSystem.STATE_CALM))
	var visible: bool = _exploration_actor_can_see_player(actor, profile)
	var hiding_spot: Dictionary = _stealth_alerts.get_hiding_spot_at(player.global_position)
	var target_hidden: bool = _exploration_hidden and not hiding_spot.is_empty()
	record = _stealth_alerts.apply_visual_observation(record, visible, target_hidden, player.global_position, delta, profile)
	if visible:
		if _exploration_hidden and hiding_spot.is_empty():
			_break_exploration_hidden("NPC заметил героя вне укромного места.")
		if actor.has_method("set_facing_direction"):
			actor.call("set_facing_direction", player.global_position - (actor as Node2D).global_position)
	else:
		if previous_state in [
			StealthAlertSystem.STATE_INVESTIGATING,
			StealthAlertSystem.STATE_SEARCHING,
			StealthAlertSystem.STATE_ALERTED
		]:
			record["state"] = previous_state
			record = _advance_actor_investigation(actor, record, profile, delta)
		elif str(record.get("state", StealthAlertSystem.STATE_CALM)) == StealthAlertSystem.STATE_CALM:
			record = _advance_actor_patrol(actor, record, delta)
	_alert_records[actor_id] = record
	_apply_record_to_actor(actor, record)
	var current_state: String = str(record.get("state", StealthAlertSystem.STATE_CALM))
	if previous_state not in [StealthAlertSystem.STATE_ALERTED, StealthAlertSystem.STATE_COMBAT] and current_state in [StealthAlertSystem.STATE_ALERTED, StealthAlertSystem.STATE_COMBAT]:
		_broadcast_actor_alert(actor, record)
	elif current_state not in [StealthAlertSystem.STATE_ALERTED, StealthAlertSystem.STATE_COMBAT]:
		_alert_broadcasted.erase(actor_id)
	if current_state == StealthAlertSystem.STATE_ALERTED and visible and _patrol_alert_groups.can_start_combat(actor_id):
		_begin_combat_from_alert(actor, record)


func _advance_actor_patrol(actor: Node, record: Dictionary, delta: float) -> Dictionary:
	if GameState.input_locked or actor == null or not (actor is Node2D):
		return record
	var actor_id: String = str(actor.call("get_actor_id"))
	var waypoint: Dictionary = _patrol_alert_groups.get_current_patrol_waypoint(actor_id, record)
	if waypoint.is_empty():
		return record
	var target_position: Vector2 = _patrol_alert_groups.get_current_patrol_target(actor_id, record)
	var config: Dictionary = _patrol_alert_groups.get_actor_config(actor_id)
	var route: Dictionary = _patrol_alert_groups.get_patrol_route(str(config.get("patrol_id", "")))
	var reached_distance: float = maxf(float(route.get("waypoint_reached_distance_pixels", 10.0)), 1.0)
	var actor_node: Node2D = actor as Node2D
	if actor_node.global_position.distance_to(target_position) > reached_distance:
		var movement: Dictionary = _npc_navigation.move_actor(actor_node, target_position, float(config.get("patrol_speed_pixels", 70.0)), delta)
		var updated_record: Dictionary = record.duplicate(true)
		updated_record["patrol_wait_remaining"] = 0.0
		updated_record["patrol_wait_initialized"] = false
		updated_record["navigation_used"] = bool(movement.get("used_navigation", false))
		var direction: Vector2 = movement.get("direction", Vector2.ZERO) as Vector2
		if direction.length_squared() > 0.0001 and actor.has_method("set_facing_direction"):
			actor.call("set_facing_direction", direction)
		return updated_record
	var patrol_result: Dictionary = _patrol_alert_groups.advance_patrol(actor_id, record, actor_node.global_position, delta)
	var result_record: Dictionary = patrol_result.get("record", record) as Dictionary
	var facing: Vector2 = patrol_result.get("facing", Vector2.ZERO) as Vector2
	if facing.length_squared() > 0.0001 and actor.has_method("set_facing_direction"):
		actor.call("set_facing_direction", facing)
	return result_record


func _advance_actor_investigation(actor: Node, record: Dictionary, profile: Dictionary, delta: float) -> Dictionary:
	var state: String = str(record.get("state", StealthAlertSystem.STATE_CALM))
	if state not in [StealthAlertSystem.STATE_INVESTIGATING, StealthAlertSystem.STATE_SEARCHING, StealthAlertSystem.STATE_ALERTED]:
		return record
	if actor == null or not (actor is Node2D):
		return record
	var target_position: Vector2 = _stealth_alerts.vector_from_value(record.get("last_known_position", []))
	var actor_node: Node2D = actor as Node2D
	var reached: bool = actor_node.global_position.distance_to(target_position) <= SEARCH_REACHED_DISTANCE_PIXELS
	var updated_record: Dictionary = record.duplicate(true)
	if not reached:
		var movement: Dictionary = _npc_navigation.move_actor(actor_node, target_position, float(profile.get("investigation_speed_pixels", 90.0)), delta)
		reached = bool(movement.get("reached", false))
		updated_record["navigation_used"] = bool(movement.get("used_navigation", false))
		var direction: Vector2 = movement.get("direction", Vector2.ZERO) as Vector2
		if direction.length_squared() > 0.0001 and actor.has_method("set_facing_direction"):
			actor.call("set_facing_direction", direction)
	return _stealth_alerts.advance_search(updated_record, delta, reached, profile)


func _broadcast_actor_alert(source_actor: Node, source_record: Dictionary) -> void:
	if source_actor == null or not is_instance_valid(source_actor) or not (source_actor is Node2D) or not source_actor.has_method("get_actor_id"):
		return
	var source_actor_id: String = str(source_actor.call("get_actor_id"))
	if source_actor_id.is_empty() or bool(_alert_broadcasted.get(source_actor_id, false)):
		return
	_alert_broadcasted[source_actor_id] = true
	var source_position: Vector2 = (source_actor as Node2D).global_position
	var source_room_id: String = _stealth_alerts.get_room_id_at(source_position)
	var relayed_count: int = 0
	for listener: Node in _exploration_alert_actors():
		if listener == source_actor or not (listener is Node2D) or not listener.has_method("get_actor_id"):
			continue
		var listener_actor_id: String = str(listener.call("get_actor_id"))
		var listener_position: Vector2 = (listener as Node2D).global_position
		var listener_room_id: String = _stealth_alerts.get_room_id_at(listener_position)
		var audibility: float = _stealth_alerts.noise_multiplier_between_rooms(GameState, source_room_id, listener_room_id)
		if not _patrol_alert_groups.can_relay_alert(source_actor_id, listener_actor_id, source_position, listener_position, audibility):
			continue
		var listener_profile: Dictionary = _stealth_alerts.get_profile(listener_actor_id)
		var listener_record: Dictionary = _record_for_actor(listener_actor_id)
		var relayed_record: Dictionary = _patrol_alert_groups.apply_alert_relay(
			listener_actor_id,
			listener_record,
			source_actor_id,
			source_record,
			listener_profile
		)
		if relayed_record == listener_record:
			continue
		_alert_records[listener_actor_id] = relayed_record
		_apply_record_to_actor(listener, relayed_record)
		_persist_alert_record(listener_actor_id, false)
		if listener.has_method("set_facing_direction"):
			listener.call("set_facing_direction", source_position - listener_position)
		relayed_count += 1
	if relayed_count > 0:
		show_combat_message("Сигнал тревоги передан ближайшему дозору.", false)


func _sync_combat_alert_records() -> void:
	var ai_turn_system: TurnBasedCombatSystemAi = _turn_system as TurnBasedCombatSystemAi
	for actor: Node in _exploration_alert_actors():
		if ai_turn_system == null or not ai_turn_system.has_combatant(actor):
			continue
		var actor_id: String = str(actor.call("get_actor_id"))
		var record: Dictionary = _record_for_actor(actor_id)
		record["state"] = StealthAlertSystem.STATE_COMBAT
		record["suspicion"] = StealthAlertSystem.SUSPICION_ALERTED
		record["last_known_position"] = _stealth_alerts.vector_to_value(player.global_position)
		_alert_records[actor_id] = record
		_apply_record_to_actor(actor, record)


func _update_pending_combat_joins() -> void:
	var ai_turn_system: TurnBasedCombatSystemAi = _turn_system as TurnBasedCombatSystemAi
	if ai_turn_system == null or not ai_turn_system.active:
		return
	for actor: Node in _exploration_alert_actors():
		if actor == player or ai_turn_system.has_combatant(actor) or not actor.has_method("get_actor_id") or not (actor is Node2D):
			continue
		var actor_id: String = str(actor.call("get_actor_id"))
		if not _patrol_alert_groups.can_join_active_combat(actor_id):
			continue
		var record: Dictionary = _record_for_actor(actor_id)
		var distance: int = DistanceSystem.distance_feet((actor as Node2D).global_position, player.global_position)
		if not _npc_ai.should_join_combat(actor_id, distance, str(record.get("state", StealthAlertSystem.STATE_CALM))):
			continue
		if not actor.has_method("activate_combat_participant") or not bool(actor.call("activate_combat_participant")):
			continue
		var initiative_modifier: int = int(actor.call("get_initiative_modifier")) if actor.has_method("get_initiative_modifier") else 0
		if not ai_turn_system.add_combatant(actor, initiative_modifier):
			continue
		record["state"] = StealthAlertSystem.STATE_COMBAT
		record["suspicion"] = StealthAlertSystem.SUSPICION_ALERTED
		record["last_known_position"] = _stealth_alerts.vector_to_value(player.global_position)
		record["joined_combat_round"] = ai_turn_system.round_number
		_alert_records[actor_id] = record
		_apply_record_to_actor(actor, record)
		_persist_alert_record(actor_id, true)
		show_combat_message("%s присоединяется к бою в конце текущего порядка инициативы." % _target_name(actor), false)


func _run_enemy_turn(actor: Node) -> void:
	if actor == null or not actor.has_method("get_actor_id") or not _npc_ai.has_profile(str(actor.call("get_actor_id"))):
		await super._run_enemy_turn(actor)
		return
	if not _turn_system.active or _turn_system.current_actor() != actor:
		return
	_enemy_turn_running = true
	_refresh_turn_interface()
	while _turn_system.active and _any_overlay_visible():
		await get_tree().process_frame
	await get_tree().create_timer(0.35).timeout
	if is_instance_valid(actor) and (not actor.has_method("can_take_combat_turn") or bool(actor.call("can_take_combat_turn"))):
		var actor_node: Node2D = actor as Node2D
		var actor_id: String = str(actor.call("get_actor_id"))
		var distance: int = DistanceSystem.distance_feet(actor_node.global_position, player.global_position)
		var current_health: int = int(actor.call("get_current_health")) if actor.has_method("get_current_health") else 1
		var maximum_health: int = int(actor.call("get_maximum_health")) if actor.has_method("get_maximum_health") else maxi(current_health, 1)
		var target_visible: bool = _combat_environment == null or _combat_environment.has_line_of_sight(actor_node.global_position, player.global_position)
		var intent: Dictionary = _npc_ai.choose_combat_intent(actor_id, {
			"distance_feet": distance,
			"actor_health_ratio": float(current_health) / float(maxi(maximum_health, 1)),
			"target_visible": target_visible,
			"can_attack": distance <= DistanceSystem.MELEE_REACH_FEET,
			"can_move": true
		})
		var intent_id: String = str(intent.get("intent", NpcAiSystem.INTENT_WAIT))
		var movement_feet: int = int(actor.call("get_combat_speed_feet")) if actor.has_method("get_combat_speed_feet") else 30
		if intent_id == NpcAiSystem.INTENT_RETREAT:
			while movement_feet >= GRID_STEP_FEET and _move_enemy_away_one_step(actor_node):
				movement_feet -= GRID_STEP_FEET
				await get_tree().create_timer(0.12).timeout
		elif intent_id == NpcAiSystem.INTENT_ADVANCE:
			while movement_feet >= GRID_STEP_FEET and DistanceSystem.distance_feet(actor_node.global_position, player.global_position) > DistanceSystem.MELEE_REACH_FEET:
				if not _move_enemy_one_step(actor_node):
					break
				movement_feet -= GRID_STEP_FEET
				await get_tree().create_timer(0.12).timeout
		if intent_id in [NpcAiSystem.INTENT_ATTACK, NpcAiSystem.INTENT_ADVANCE] and is_instance_valid(actor) and DistanceSystem.distance_feet(actor_node.global_position, player.global_position) <= DistanceSystem.MELEE_REACH_FEET:
			if actor.has_method("perform_combat_turn_attack"):
				actor.call("perform_combat_turn_attack")
				_update_status()
				await get_tree().create_timer(0.4).timeout
	_enemy_turn_running = false
	if GameState.player_character.current_health > 0:
		_advance_combat_turn()


func _move_enemy_away_one_step(actor: Node2D) -> bool:
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return false
	var actor_cell: Vector2i = grid.world_to_cell(actor.global_position)
	var player_cell: Vector2i = grid.world_to_cell(player.global_position)
	var delta: Vector2i = actor_cell - player_cell
	var horizontal: int = 0 if delta.x == 0 else (1 if delta.x > 0 else -1)
	var vertical: int = 0 if delta.y == 0 else (1 if delta.y > 0 else -1)
	var candidates: Array[Vector2i] = [
		Vector2i(horizontal, vertical),
		Vector2i(horizontal, 0),
		Vector2i(0, vertical)
	]
	var occupied: Dictionary = _occupied_cells(actor)
	for candidate_step: Vector2i in candidates:
		if candidate_step == Vector2i.ZERO:
			continue
		var destination_cell: Vector2i = actor_cell + candidate_step
		if not grid.is_cell_valid(destination_cell) or occupied.has(destination_cell):
			continue
		if _combat_environment != null and _combat_environment.is_cell_blocked(grid, destination_cell):
			continue
		actor.global_position = grid.cell_to_world_center(destination_cell)
		return true
	return false


func _refresh_alert_indicator() -> void:
	if _alert_indicator == null:
		return
	var hidden: bool = _exploration_hidden or _player_combat_state.hidden
	_alert_indicator.visible = hidden
	_alert_indicator.text = "СКРЫТ" if hidden else ""
	_alert_indicator.add_theme_color_override("font_color", Color(0.62, 0.86, 0.64, 1.0))


func _highest_player_feedback_state() -> String:
	var highest_state: String = StealthAlertSystem.STATE_CALM
	var highest_priority: int = 0
	for value: Variant in _alert_records.values():
		if not value is Dictionary:
			continue
		var state: String = str((value as Dictionary).get("state", StealthAlertSystem.STATE_CALM))
		var priority: int = int(PLAYER_FEEDBACK_STATE_PRIORITY.get(state, 0))
		if priority > highest_priority:
			highest_priority = priority
			highest_state = state
	return highest_state


func get_patrol_actor_for_testing(actor_id: String) -> Node:
	for actor: Node in _exploration_alert_actors():
		if actor.has_method("get_actor_id") and str(actor.call("get_actor_id")) == actor_id:
			return actor
	return null


func force_patrol_tick_for_testing(actor: Node, delta: float) -> void:
	if actor == null or not actor.has_method("get_actor_id"):
		return
	var actor_id: String = str(actor.call("get_actor_id"))
	var record: Dictionary = _record_for_actor(actor_id)
	record["state"] = StealthAlertSystem.STATE_CALM
	record["suspicion"] = 0.0
	record = _advance_actor_patrol(actor, record, delta)
	_alert_records[actor_id] = record
	_apply_record_to_actor(actor, record)


func force_alert_broadcast_for_testing(source_actor: Node, last_known_position: Vector2) -> void:
	if source_actor == null or not source_actor.has_method("get_actor_id"):
		return
	var source_actor_id: String = str(source_actor.call("get_actor_id"))
	_alert_broadcasted.erase(source_actor_id)
	var record: Dictionary = _record_for_actor(source_actor_id)
	record["state"] = StealthAlertSystem.STATE_ALERTED
	record["suspicion"] = StealthAlertSystem.SUSPICION_ALERTED
	record["last_known_position"] = _stealth_alerts.vector_to_value(last_known_position)
	_alert_records[source_actor_id] = record
	_apply_record_to_actor(source_actor, record)
	_broadcast_actor_alert(source_actor, record)


func select_context_target_for_testing(actor: Node) -> void:
	_set_selected_target(actor)


func inspect_selected_target_for_testing() -> void:
	_inspect_selected_target()


func get_target_label_text_for_testing() -> String:
	return _target_label.text if _target_label != null else ""


func get_action_catalog_entries_for_testing() -> Dictionary:
	return _build_catalog_entries()


func force_combat_join_check_for_testing() -> void:
	_update_pending_combat_joins()


func turn_system_has_actor_for_testing(actor: Node) -> bool:
	var ai_turn_system: TurnBasedCombatSystemAi = _turn_system as TurnBasedCombatSystemAi
	return ai_turn_system != null and ai_turn_system.has_combatant(actor)


func get_ai_intent_for_testing(actor_id: String, context: Dictionary) -> Dictionary:
	return _npc_ai.choose_combat_intent(actor_id, context)
