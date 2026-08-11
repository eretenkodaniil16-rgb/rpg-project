extends "res://scripts/game/game_combat_ai_coordination_v2_runtime.gd"

const PARTY_STEALTH_STATE_SCRIPT_V3: Script = preload("res://scripts/systems/party_stealth_state_system.gd")
const PARTY_STEALTH_STATE_FLAG_V3: String = "party_stealth_v3_state"
const PLAYER_STEALTH_ACTOR_ID_V3: String = "player_character"
const PARTY_STEALTH_TELEPORT_RESET_PIXELS: float = 192.0

var _party_stealth_state_v3: PartyStealthStateSystem = PARTY_STEALTH_STATE_SCRIPT_V3.new() as PartyStealthStateSystem
var _party_last_position_v3: Dictionary = {}
var _party_step_elapsed_v3: Dictionary = {}
var _party_active_search_cooldown_v3: Dictionary = {}
var _last_party_noise_event_v3: Dictionary = {}
var _combat_entry_target_id_v3: String = ""


func _ready() -> void:
	super._ready()
	_restore_party_stealth_state_v3()
	_prime_party_step_tracking_v3()
	_refresh_alert_indicator()


func _build_catalog_entries() -> Dictionary:
	var entries: Dictionary = super._build_catalog_entries()
	if _turn_system.active:
		return entries
	var active_target: Node = get_active_player_controlled_actor()
	if not is_instance_valid(active_target) or not active_target is Node2D:
		return entries
	var values: Variant = entries.get("action", [])
	if not values is Array:
		return entries
	var action_entries: Array = values as Array
	var hidden: bool = _is_party_target_hidden_v3(active_target)
	var visible_observers: Array[Node] = _visible_observers_for_party_target_v3(active_target)
	for index: int in range(action_entries.size()):
		var value: Variant = action_entries[index]
		if not value is Dictionary:
			continue
		var entry: Dictionary = (value as Dictionary).duplicate(true)
		if str(entry.get("id", "")) != "exploration_hide":
			continue
		entry["label"] = "ВЫЙТИ ИЗ УКРЫТИЯ" if hidden else "СКРЫТЬСЯ"
		entry["enabled"] = not GameState.input_locked and (hidden or visible_observers.is_empty())
		if hidden:
			entry["description"] = "%s скрыт: результат Скрытности %d. Обнаружение, громкий шум или явное действие прекращают скрытность только этого персонажа." % [
				_party_target_display_name_v3(active_target),
				_get_party_stealth_total_v3(active_target)
			]
		elif not visible_observers.is_empty():
			entry["description"] = "Нельзя скрыться, пока выбранного персонажа непосредственно видит NPC."
		else:
			entry["description"] = "Скрытность проверяется отдельно для выбранного члена отряда; каждый NPC использует собственное Восприятие."
		action_entries[index] = entry
	entries["action"] = action_entries
	return entries


func _toggle_exploration_hide() -> void:
	var target: Node = get_active_player_controlled_actor()
	if not is_instance_valid(target) or not target is Node2D:
		return
	if _is_party_target_hidden_v3(target):
		_break_party_target_hidden_v3(target, "%s прекращает скрытное перемещение." % _party_target_display_name_v3(target))
		return
	var visible_observers: Array[Node] = _visible_observers_for_party_target_v3(target)
	if not visible_observers.is_empty():
		show_combat_message("%s не может скрыться: сохраняется прямая линия обзора." % _party_target_display_name_v3(target), false)
		return

	var target_position: Vector2 = (target as Node2D).global_position
	var hiding_spot: Dictionary = _stealth_alerts.get_hiding_spot_at(target_position)
	var concealment_bonus: int = int(hiding_spot.get("concealment_bonus", 0))
	var difficulty: int = _stealth_perception.get_hide_entry_dc()
	var overrides: Array[int] = _exploration_hide_roll_overrides.duplicate()
	_exploration_hide_roll_overrides.clear()
	var disadvantage: bool = target == player and _player_has_untrained_armor_d20_disadvantage("dexterity")
	var reroll_one: bool = target == player and GameState.player_character != null and GameState.player_character.reroll_natural_one
	var check: Dictionary = _srd_rules.resolve_d20_test(
		_party_stealth_modifier_v3(target),
		difficulty,
		false,
		disadvantage,
		overrides,
		reroll_one
	)
	var total: int = int(check.get("total", 0)) + concealment_bonus
	if total < difficulty:
		show_combat_message("%s не удалось скрыться: Скрытность %d против СЛ %d." % [_party_target_display_name_v3(target), total, difficulty], false)
		report_party_world_noise_v3(target, "quiet_step", {"source_type": "failed_hide"})
		return
	_set_party_target_stealth_v3(target, true, total)
	show_combat_message("%s скрыт: результат Скрытности %d." % [_party_target_display_name_v3(target), total], true)
	_refresh_action_catalog()
	_refresh_alert_indicator()


func _update_exploration_step_noise(delta: float) -> void:
	for target: Node in _party_stealth_targets_v3():
		if not target is Node2D or not _party_stealth_target_available_v3(target):
			continue
		var actor_id: String = _party_stealth_actor_id_v3(target)
		var current_position: Vector2 = (target as Node2D).global_position
		var previous: Vector2 = _party_last_position_v3.get(actor_id, Vector2.INF) as Vector2
		_party_last_position_v3[actor_id] = current_position
		if target == player:
			_last_exploration_player_position = current_position
		if previous == Vector2.INF:
			_party_step_elapsed_v3[actor_id] = 0.0
			continue
		var distance: float = current_position.distance_to(previous)
		if distance > PARTY_STEALTH_TELEPORT_RESET_PIXELS:
			_party_step_elapsed_v3[actor_id] = 0.0
			continue
		if distance <= 0.75:
			_party_step_elapsed_v3[actor_id] = 0.0
			continue
		var elapsed: float = float(_party_step_elapsed_v3.get(actor_id, 0.0)) + maxf(delta, 0.0)
		_party_step_elapsed_v3[actor_id] = elapsed
		if elapsed < STEP_NOISE_INTERVAL_SECONDS:
			continue
		_party_step_elapsed_v3[actor_id] = 0.0
		var hidden: bool = _is_party_target_hidden_v3(target)
		var noise_type: String = "quiet_step" if hidden else "normal_step"
		var hiding_spot: Dictionary = _stealth_alerts.get_hiding_spot_at(current_position)
		var overrides: Dictionary = {"source_type": "party_movement"}
		if not hiding_spot.is_empty():
			overrides["intensity"] = roundi(
				float(_stealth_alerts.get_noise_profile(noise_type).get("intensity", 10))
				* float(hiding_spot.get("noise_multiplier", 1.0))
			)
		report_party_world_noise_v3(target, noise_type, overrides)


func _update_exploration_alerts(delta: float) -> void:
	_perception_tick_accumulator_v2 += maxf(delta, 0.0)
	var interval: float = _stealth_perception.get_perception_tick_seconds()
	if _perception_tick_accumulator_v2 < interval:
		return
	var tick_delta: float = _perception_tick_accumulator_v2
	_perception_tick_accumulator_v2 = 0.0
	for observer: Node in _exploration_alert_actors():
		_update_party_exploration_observer_v3(observer, tick_delta)


func _update_party_exploration_observer_v3(observer: Node, delta: float) -> void:
	if not is_instance_valid(observer) or not observer is Node2D or not observer.has_method("get_actor_id"):
		return
	var observer_id: String = str(observer.call("get_actor_id"))
	var profile: Dictionary = _stealth_alerts.get_profile(observer_id)
	if profile.is_empty():
		return
	var record: Dictionary = _record_for_actor(observer_id)
	record["step_retarget_cooldown_seconds"] = maxf(float(record.get("step_retarget_cooldown_seconds", 0.0)) - maxf(delta, 0.0), 0.0)
	var detected_target: Node = null
	var detected_distance: int = 999999
	for target: Node in _party_stealth_targets_v3():
		if not _party_stealth_target_available_v3(target):
			continue
		if not _observer_detects_party_target_v3(observer, profile, record, target, delta):
			continue
		if _is_party_target_hidden_v3(target):
			_break_party_target_hidden_v3(target, "%s обнаружил %s." % [_target_name(observer), _party_target_display_name_v3(target)])
		_record_party_sighting_v3(observer, target, (target as Node2D).global_position, 1.0, "visual")
		var distance: int = DistanceSystem.distance_feet((observer as Node2D).global_position, (target as Node2D).global_position)
		if detected_target == null or distance < detected_distance:
			detected_target = target
			detected_distance = distance

	if is_instance_valid(detected_target) and detected_target is Node2D:
		var target_position: Vector2 = (detected_target as Node2D).global_position
		record = _stealth_alerts.apply_visual_observation(record, true, false, target_position, delta, profile)
		if observer.has_method("set_facing_direction"):
			observer.call("set_facing_direction", target_position - (observer as Node2D).global_position)
		record = _advance_visible_actor_behavior(observer, record, profile, delta)
	else:
		var remembered: Dictionary = _party_stealth_state_v3.get_latest_observer_memory(observer_id)
		var remembered_position: Vector2 = _memory_position_v3(remembered, (observer as Node2D).global_position)
		record = _stealth_alerts.apply_visual_observation(record, false, false, remembered_position, delta, profile)
		record = _advance_unseen_actor_behavior(observer, record, profile, delta)
	_alert_records[observer_id] = record
	_apply_record_to_actor(observer, record)
	if str(record.get("state", "")) == StealthAlertSystem.STATE_ALERTED and is_instance_valid(detected_target):
		_begin_combat_from_party_alert_v3(observer, record, detected_target)


func _observer_detects_party_target_v3(
	observer: Node,
	profile: Dictionary,
	record: Dictionary,
	target: Node,
	delta: float
) -> bool:
	var observation: Dictionary = _geometric_party_observation_v3(observer, profile, target)
	if not bool(observation.get("geometric_visible", false)):
		return false
	if not _is_party_target_hidden_v3(target):
		return true
	var passive: Dictionary = _stealth_perception.resolve_passive_detection(
		_get_party_stealth_total_v3(target),
		int(profile.get("passive_perception", 10)),
		int(observation.get("distance_feet", 0)),
		true,
		bool(observation.get("fully_concealed", false))
	)
	if bool(passive.get("detected", false)):
		return true
	return _active_search_finds_hidden_party_target_v3(observer, profile, record, target, observation, delta)


func _active_search_finds_hidden_party_target_v3(
	observer: Node,
	profile: Dictionary,
	record: Dictionary,
	target: Node,
	observation: Dictionary,
	delta: float
) -> bool:
	if not _is_party_target_hidden_v3(target) or _get_party_stealth_total_v3(target) <= 0:
		return false
	if not _stealth_perception.is_active_search_state(str(record.get("state", StealthAlertSystem.STATE_CALM))):
		return false
	var observer_id: String = str(observer.call("get_actor_id"))
	var target_id: String = _party_stealth_actor_id_v3(target)
	var combat_profile: Dictionary = _party_observer_combat_profile_v3(observer_id)
	var squad_id: String = str(combat_profile.get("squad_id", ""))
	if (
		_party_stealth_state_v3.get_observer_memory(observer_id, target_id).is_empty()
		and _party_stealth_state_v3.get_squad_memory(squad_id, target_id).is_empty()
	):
		return false
	var cooldown_key: String = "%s|%s" % [observer_id, target_id]
	var cooldown: float = maxf(float(_party_active_search_cooldown_v3.get(cooldown_key, 0.0)) - maxf(delta, 0.0), 0.0)
	_party_active_search_cooldown_v3[cooldown_key] = cooldown
	if cooldown > 0.0:
		return false
	if not bool(observation.get("geometric_visible", false)):
		return false
	if int(observation.get("distance_feet", 9999)) > _stealth_perception.get_active_search_max_distance_feet():
		return false
	_party_active_search_cooldown_v3[cooldown_key] = _stealth_perception.get_active_search_interval_seconds()
	var natural: int
	if not _active_search_roll_overrides_v2.is_empty():
		natural = clampi(_active_search_roll_overrides_v2.pop_front(), 1, 20)
	else:
		natural = int(_srd_rules.roll_d20(0).get("natural", 1))
	var search: Dictionary = _stealth_perception.resolve_active_search(
		_get_party_stealth_total_v3(target),
		int(profile.get("perception_modifier", 0)),
		natural
	)
	if bool(search.get("success", false)):
		show_combat_message("%s проводит активный поиск и обнаруживает %s: %d против Скрытности %d." % [
			_target_name(observer),
			_party_target_display_name_v3(target),
			int(search.get("total", 0)),
			_get_party_stealth_total_v3(target)
		], false)
		return true
	return false


func _geometric_party_observation_v3(observer: Node, profile: Dictionary, target: Node) -> Dictionary:
	if not is_instance_valid(observer) or not observer is Node2D or not is_instance_valid(target) or not target is Node2D:
		return {"geometric_visible": false, "distance_feet": 9999, "fully_concealed": false}
	var observer_position: Vector2 = (observer as Node2D).global_position
	var target_position: Vector2 = (target as Node2D).global_position
	var facing: Vector2 = observer.call("get_facing_direction") as Vector2 if observer.has_method("get_facing_direction") else Vector2.LEFT
	var line_of_sight_clear: bool = not _stealth_alerts.door_blocks_line_of_sight(GameState, observer_position, target_position)
	if line_of_sight_clear and _combat_environment != null:
		line_of_sight_clear = _combat_environment.has_line_of_sight(observer_position, target_position)
	var geometric_visible: bool = _stealth_alerts.can_see_target(
		observer_position,
		facing,
		target_position,
		profile,
		line_of_sight_clear,
		false
	)
	return {
		"geometric_visible": geometric_visible,
		"distance_feet": DistanceSystem.distance_feet(observer_position, target_position),
		"fully_concealed": _is_party_target_hidden_v3(target) and not _stealth_alerts.get_hiding_spot_at(target_position).is_empty()
	}


func _visible_observers_for_party_target_v3(target: Node) -> Array[Node]:
	var result: Array[Node] = []
	for observer: Node in _exploration_alert_actors():
		if not observer.has_method("get_actor_id"):
			continue
		var profile: Dictionary = _stealth_alerts.get_profile(str(observer.call("get_actor_id")))
		if bool(_geometric_party_observation_v3(observer, profile, target).get("geometric_visible", false)):
			result.append(observer)
	return result


func report_party_world_noise_v3(target: Node, noise_type: String, overrides: Dictionary = {}) -> Dictionary:
	if not is_instance_valid(target) or not target is Node2D:
		return {}
	var payload: Dictionary = overrides.duplicate(true)
	payload["source_actor_id"] = _party_stealth_actor_id_v3(target)
	var event: Dictionary = report_world_noise(noise_type, (target as Node2D).global_position, payload)
	_last_party_noise_event_v3 = event.duplicate(true)
	return event


func _on_stealth_noise_reported(noise_event: Dictionary) -> void:
	super._on_stealth_noise_reported(noise_event)
	var source_actor_id: String = str(noise_event.get("source_actor_id", ""))
	if source_actor_id.is_empty() or not _party_stealth_actor_ids_v3().has(source_actor_id):
		return
	var source_position: Vector2 = _stealth_alerts.vector_from_value(noise_event.get("position", []))
	for observer: Node in _exploration_alert_actors():
		if not observer is Node2D or not observer.has_method("get_actor_id"):
			continue
		var observer_id: String = str(observer.call("get_actor_id"))
		var stealth_profile: Dictionary = _stealth_alerts.get_profile(observer_id)
		var room_id: String = _stealth_alerts.get_room_id_at((observer as Node2D).global_position)
		if not _stealth_alerts.actor_hears_noise(GameState, (observer as Node2D).global_position, room_id, noise_event, stealth_profile):
			continue
		var combat_profile: Dictionary = _party_observer_combat_profile_v3(observer_id)
		_party_stealth_state_v3.record_sighting(
			observer_id,
			str(combat_profile.get("squad_id", "")),
			source_actor_id,
			source_position,
			0.55,
			"noise",
			bool(combat_profile.get("shares_target_information", true))
		)
	_persist_party_stealth_state_v3()


func _record_party_sighting_v3(
	observer: Node,
	target: Node,
	position: Vector2,
	confidence: float,
	source: String
) -> Dictionary:
	if not is_instance_valid(observer) or not observer.has_method("get_actor_id"):
		return {}
	var observer_id: String = str(observer.call("get_actor_id"))
	var target_id: String = _party_stealth_actor_id_v3(target)
	var combat_profile: Dictionary = _party_observer_combat_profile_v3(observer_id)
	var memory: Dictionary = _party_stealth_state_v3.record_sighting(
		observer_id,
		str(combat_profile.get("squad_id", "")),
		target_id,
		position,
		confidence,
		source,
		bool(combat_profile.get("shares_target_information", true))
	)
	_persist_party_stealth_state_v3()
	return memory


func _begin_combat_from_party_alert_v3(observer: Node, record: Dictionary, detected_target: Node) -> void:
	if _turn_system.active or not is_instance_valid(observer) or not is_instance_valid(detected_target):
		return
	var observer_id: String = str(observer.call("get_actor_id")) if observer.has_method("get_actor_id") else ""
	_record_party_sighting_v3(observer, detected_target, (detected_target as Node2D).global_position, 1.0, "combat_alert")
	record["state"] = StealthAlertSystem.STATE_COMBAT
	record["suspicion"] = StealthAlertSystem.SUSPICION_ALERTED
	_alert_records[observer_id] = record
	_persist_alert_record(observer_id, true)
	if observer.has_method("enter_combat_hostile"):
		observer.call("enter_combat_hostile")
	_combat_entry_target_id_v3 = _party_stealth_actor_id_v3(detected_target)
	show_combat_message("%s обнаружил %s и поднимает тревогу." % [_target_name(observer), _party_target_display_name_v3(detected_target)], false)
	_start_turn_based_combat(observer)


func _start_turn_based_combat(trigger_target: Node) -> void:
	var hero_was_hidden: bool = is_instance_valid(player) and _is_party_target_hidden_v3(player)
	super._start_turn_based_combat(trigger_target)
	if hero_was_hidden and _player_combat_state != null:
		_player_combat_state.hidden = true
	for observer: Node in _active_observers():
		if not observer.has_method("get_actor_id"):
			continue
		var memory: Dictionary = _party_stealth_state_v3.get_latest_observer_memory(str(observer.call("get_actor_id")))
		if memory.is_empty():
			continue
		_set_observer_state(observer, DETECTION_AWARE, _memory_position_v3(memory, (observer as Node2D).global_position))


func _sync_combat_alert_records() -> void:
	for observer: Node in _exploration_alert_actors():
		if not observer.has_method("get_actor_id"):
			continue
		var observer_id: String = str(observer.call("get_actor_id"))
		var record: Dictionary = _record_for_actor(observer_id)
		record["state"] = StealthAlertSystem.STATE_COMBAT
		record["suspicion"] = StealthAlertSystem.SUSPICION_ALERTED
		var memory: Dictionary = _party_stealth_state_v3.get_latest_observer_memory(observer_id)
		if not memory.is_empty():
			record["last_known_position"] = _stealth_alerts.vector_to_value(_memory_position_v3(memory, (observer as Node2D).global_position))
		_alert_records[observer_id] = record
		_apply_record_to_actor(observer, record)


func _resolve_party_follow_target(ally: CharacterBody2D, leader: Node2D) -> Dictionary:
	var resolution: Dictionary = super._resolve_party_follow_target(ally, leader)
	if not bool(resolution.get("reachable", true)):
		return resolution
	if not _is_party_target_hidden_v3(leader) or _is_party_target_hidden_v3(ally):
		return resolution
	var desired: Vector2 = resolution.get("target", leader.global_position) as Vector2
	if not _party_follow_position_exposed_v3(desired):
		return resolution
	return {
		"reachable": false,
		"target": ally.global_position,
		"reason": "stealth_exposure",
		"stealth_hold": true
	}


func _party_follow_position_exposed_v3(position: Vector2) -> bool:
	for observer: Node in _exploration_alert_actors():
		if not observer is Node2D or not observer.has_method("get_actor_id"):
			continue
		var profile: Dictionary = _stealth_alerts.get_profile(str(observer.call("get_actor_id")))
		if profile.is_empty():
			continue
		var observer_position: Vector2 = (observer as Node2D).global_position
		var facing: Vector2 = observer.call("get_facing_direction") as Vector2 if observer.has_method("get_facing_direction") else Vector2.LEFT
		var clear: bool = not _stealth_alerts.door_blocks_line_of_sight(GameState, observer_position, position)
		if clear and _combat_environment != null:
			clear = _combat_environment.has_line_of_sight(observer_position, position)
		if _stealth_alerts.can_see_target(observer_position, facing, position, profile, clear, false):
			return true
	return false


func _restore_party_stealth_state_v3() -> void:
	_party_stealth_state_v3.restore_persistent_state(GameState.get_flag(PARTY_STEALTH_STATE_FLAG_V3, {}))
	for target: Node in _party_stealth_targets_v3():
		var actor_id: String = _party_stealth_actor_id_v3(target)
		if _party_stealth_state_v3.has_target_state(actor_id):
			continue
		if target == player:
			_party_stealth_state_v3.set_target_state(actor_id, _exploration_hidden, _exploration_stealth_total_v2)
		elif target.has_method("is_exploration_hidden") and target.has_method("get_exploration_stealth_total"):
			_party_stealth_state_v3.set_target_state(actor_id, bool(target.call("is_exploration_hidden")), int(target.call("get_exploration_stealth_total")))
		else:
			_party_stealth_state_v3.set_target_state(actor_id, false, 0)
	_sync_legacy_hero_stealth_v3()
	_persist_party_stealth_state_v3()


func _persist_party_stealth_state_v3() -> void:
	GameState.set_flag(PARTY_STEALTH_STATE_FLAG_V3, _party_stealth_state_v3.serialize_persistent_state())


func _sync_legacy_hero_stealth_v3() -> void:
	if not is_instance_valid(player):
		return
	var actor_id: String = _party_stealth_actor_id_v3(player)
	_exploration_hidden = _party_stealth_state_v3.is_hidden(actor_id)
	_exploration_stealth_total_v2 = _party_stealth_state_v3.get_stealth_total(actor_id)
	if GameState.player_character == null:
		return
	if _exploration_hidden:
		GameState.player_character.active_effects["exploration_hidden"] = true
		GameState.player_character.active_effects["exploration_stealth_total"] = _exploration_stealth_total_v2
	else:
		GameState.player_character.active_effects.erase("exploration_hidden")
		GameState.player_character.active_effects.erase("exploration_stealth_total")


func _set_party_target_stealth_v3(target: Node, hidden: bool, stealth_total: int) -> void:
	var actor_id: String = _party_stealth_actor_id_v3(target)
	if actor_id.is_empty():
		return
	_party_stealth_state_v3.set_target_state(actor_id, hidden, stealth_total)
	if target.has_method("set_exploration_stealth_state"):
		target.call("set_exploration_stealth_state", hidden, stealth_total)
	if target == player:
		_sync_legacy_hero_stealth_v3()
	_persist_party_stealth_state_v3()


func _break_party_target_hidden_v3(target: Node, message: String = "") -> void:
	if not _is_party_target_hidden_v3(target):
		return
	_set_party_target_stealth_v3(target, false, 0)
	if not message.is_empty():
		show_combat_message(message, false)
	_refresh_action_catalog()
	_refresh_alert_indicator()


func _is_party_target_hidden_v3(target: Node) -> bool:
	return _party_stealth_state_v3.is_hidden(_party_stealth_actor_id_v3(target))


func _get_party_stealth_total_v3(target: Node) -> int:
	return _party_stealth_state_v3.get_stealth_total(_party_stealth_actor_id_v3(target))


func _party_stealth_modifier_v3(target: Node) -> int:
	if target == player and GameState.player_character != null:
		return GameState.player_character.get_skill_modifier("stealth")
	if target.has_method("get_exploration_stealth_modifier"):
		return int(target.call("get_exploration_stealth_modifier"))
	if target.has_method("get_saving_throw_modifier"):
		return int(target.call("get_saving_throw_modifier", "dexterity"))
	return 0


func _party_stealth_targets_v3() -> Array[Node]:
	var result: Array[Node] = []
	var seen: Dictionary = {}
	if is_instance_valid(player):
		result.append(player)
		seen[player.get_instance_id()] = true
	for target: Node in get_tree().get_nodes_in_group("controllable_allies"):
		if not is_instance_valid(target) or not target is Node2D or seen.has(target.get_instance_id()):
			continue
		result.append(target)
		seen[target.get_instance_id()] = true
	return result


func _party_stealth_actor_ids_v3() -> Array[String]:
	var result: Array[String] = []
	for target: Node in _party_stealth_targets_v3():
		var actor_id: String = _party_stealth_actor_id_v3(target)
		if not actor_id.is_empty():
			result.append(actor_id)
	result.sort()
	return result


func _party_stealth_actor_id_v3(target: Node) -> String:
	if not is_instance_valid(target):
		return ""
	if target == player:
		return PLAYER_STEALTH_ACTOR_ID_V3
	if target.has_method("get_actor_id"):
		return str(target.call("get_actor_id"))
	return "party_actor_%d" % target.get_instance_id()


func _party_target_display_name_v3(target: Node) -> String:
	if target == player and GameState.player_character != null and not GameState.player_character.character_name.is_empty():
		return GameState.player_character.character_name
	if target.has_method("get_combat_name"):
		return str(target.call("get_combat_name"))
	return str(target.name) if is_instance_valid(target) else "цель"


func _party_stealth_target_available_v3(target: Node) -> bool:
	if not is_instance_valid(target) or not target is Node2D:
		return false
	if target == player:
		return GameState.player_character != null and GameState.player_character.current_health > 0 and not _player_combat_state.dead
	if target.has_method("get_current_health") and int(target.call("get_current_health")) <= 0:
		return false
	if target.has_method("get_combatant_state"):
		var state: CombatantState = target.call("get_combatant_state") as CombatantState
		if state != null and state.dead:
			return false
	return true


func _party_observer_combat_profile_v3(observer_id: String) -> Dictionary:
	if observer_id.is_empty() or _combat_ai == null:
		return {}
	return _combat_ai.get_profile(observer_id)


func _prime_party_step_tracking_v3() -> void:
	_party_last_position_v3.clear()
	_party_step_elapsed_v3.clear()
	for target: Node in _party_stealth_targets_v3():
		if target is Node2D:
			var actor_id: String = _party_stealth_actor_id_v3(target)
			_party_last_position_v3[actor_id] = (target as Node2D).global_position
			_party_step_elapsed_v3[actor_id] = 0.0


func _memory_position_v3(memory: Dictionary, fallback: Vector2 = Vector2.ZERO) -> Vector2:
	var value: Variant = memory.get("position", fallback)
	return value as Vector2 if value is Vector2 else fallback


func set_party_stealth_total_v3_for_testing(target: Node, total: int) -> void:
	_set_party_target_stealth_v3(target, total > 0, maxi(total, 0))


func get_party_stealth_snapshot_v3_for_testing(target: Node) -> Dictionary:
	return _party_stealth_state_v3.get_target_state(_party_stealth_actor_id_v3(target))


func get_party_stealth_actor_ids_v3_for_testing() -> Array[String]:
	return _party_stealth_actor_ids_v3()


func resolve_party_passive_detection_v3_for_testing(
	observer: Node,
	target: Node,
	distance_feet: int,
	fully_concealed: bool = false
) -> Dictionary:
	var profile: Dictionary = _stealth_alerts.get_profile(str(observer.call("get_actor_id"))) if is_instance_valid(observer) and observer.has_method("get_actor_id") else {}
	return _stealth_perception.resolve_passive_detection(
		_get_party_stealth_total_v3(target),
		int(profile.get("passive_perception", 10)),
		distance_feet,
		true,
		fully_concealed
	)


func force_party_target_detection_v3_for_testing(observer: Node, target: Node) -> Dictionary:
	if not is_instance_valid(observer) or not is_instance_valid(target) or not target is Node2D:
		return {}
	if _is_party_target_hidden_v3(target):
		_break_party_target_hidden_v3(target)
	return _record_party_sighting_v3(observer, target, (target as Node2D).global_position, 1.0, "test_detection")


func get_party_sighting_memory_v3_for_testing(observer: Node, target: Node) -> Dictionary:
	if not is_instance_valid(observer) or not observer.has_method("get_actor_id"):
		return {}
	return _party_stealth_state_v3.get_observer_memory(str(observer.call("get_actor_id")), _party_stealth_actor_id_v3(target))


func get_squad_sighting_memory_v3_for_testing(observer: Node, target: Node) -> Dictionary:
	if not is_instance_valid(observer) or not observer.has_method("get_actor_id"):
		return {}
	var observer_id: String = str(observer.call("get_actor_id"))
	var profile: Dictionary = _party_observer_combat_profile_v3(observer_id)
	return _party_stealth_state_v3.get_squad_memory(str(profile.get("squad_id", "")), _party_stealth_actor_id_v3(target))


func report_party_noise_v3_for_testing(target: Node, noise_type: String = "quiet_step") -> Dictionary:
	return report_party_world_noise_v3(target, noise_type, {"source_type": "test_party_noise"})


func get_last_party_noise_event_v3_for_testing() -> Dictionary:
	return _last_party_noise_event_v3.duplicate(true)


func get_persisted_party_stealth_state_v3_for_testing() -> Dictionary:
	var value: Variant = GameState.get_flag(PARTY_STEALTH_STATE_FLAG_V3, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func is_party_follow_position_exposed_v3_for_testing(position: Vector2) -> bool:
	return _party_follow_position_exposed_v3(position)
