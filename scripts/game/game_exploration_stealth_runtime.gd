extends "res://scripts/game/game_hidden_escape_runtime.gd"

const STEALTH_ALERT_SYSTEM_SCRIPT: Script = preload("res://scripts/systems/stealth_alert_system.gd")
const ALERT_PERSIST_INTERVAL_SECONDS: float = 0.5
const STEP_NOISE_INTERVAL_SECONDS: float = 0.42
const SEARCH_REACHED_DISTANCE_PIXELS: float = 22.0

var _stealth_alerts: StealthAlertSystem = STEALTH_ALERT_SYSTEM_SCRIPT.new() as StealthAlertSystem
var _exploration_hidden: bool = false
var _alert_records: Dictionary = {}
var _alert_persist_elapsed: float = 0.0
var _step_noise_elapsed: float = 0.0
var _last_exploration_player_position: Vector2 = Vector2.INF
var _exploration_hide_roll_overrides: Array[int] = []
var _alert_indicator: Label
var _last_noise_sequence: int = 0


func _ready() -> void:
	super._ready()
	_build_alert_indicator()
	_restore_exploration_alerts()
	_connect_stealth_alert_signals()
	_last_exploration_player_position = player.global_position
	_refresh_alert_indicator()


func _process(delta: float) -> void:
	super._process(delta)
	if _turn_system.active:
		_sync_combat_alert_records()
		_refresh_alert_indicator()
		return
	_update_exploration_step_noise(delta)
	_update_exploration_alerts(delta)
	_alert_persist_elapsed += maxf(delta, 0.0)
	if _alert_persist_elapsed >= ALERT_PERSIST_INTERVAL_SECONDS:
		_alert_persist_elapsed = 0.0
		_persist_all_alert_records(false)
	_refresh_alert_indicator()


func _active_observers() -> Array[Node]:
	var result: Array[Node] = []
	if _turn_system == null:
		return result
	for entry: Dictionary in _turn_system.entries:
		if bool(entry.get("is_player", false)):
			continue
		var actor: Node = entry.get("node") as Node
		if not is_instance_valid(actor) or not (actor is Node2D):
			continue
		if actor.has_method("can_take_combat_turn") and not bool(actor.call("can_take_combat_turn")):
			continue
		result.append(actor)
	return result


func _on_hide_requested() -> void:
	await super._on_hide_requested()
	if not _player_combat_state.hidden:
		return
	for observer: Node in _active_observers():
		_set_observer_state(observer, DETECTION_PURSUING, _last_seen_player_position)


func force_active_escape_encounter_for_testing(encounter_id: String) -> void:
	_active_combat_encounter_id = encounter_id


func _build_catalog_entries() -> Dictionary:
	var entries: Dictionary = super._build_catalog_entries()
	if _turn_system.active:
		return entries
	var action_entries: Array = entries.get("action", []) as Array
	if not _catalog_contains(action_entries, "exploration_hide"):
		var hiding_spot: Dictionary = _stealth_alerts.get_hiding_spot_at(player.global_position)
		var currently_seen: bool = _player_visible_to_any_exploration_actor()
		var enabled: bool = not GameState.input_locked and not currently_seen
		var label: String = "ВЫЙТИ ИЗ УКРЫТИЯ" if _exploration_hidden else "СКРЫТЬСЯ"
		var description: String
		if _exploration_hidden:
			description = "Прекратить скрытное состояние. Резкое движение и шум также могут выдать героя."
		elif currently_seen:
			description = "Нельзя скрыться, пока NPC сохраняет прямой визуальный контакт."
		elif hiding_spot.is_empty():
			description = "Попытаться скрыться за полным укрытием. Специальное укромное место даст бонус."
		else:
			description = "Спрятаться в «%s» с бонусом маскировки +%d." % [
				str(hiding_spot.get("label", "укрытии")),
				int(hiding_spot.get("concealment_bonus", 0))
			]
		action_entries.append(_entry("exploration_hide", label, enabled, description, "stealth"))
		entries["action"] = action_entries
	return entries


func _on_catalog_action_requested(action_id: String) -> void:
	if action_id == "exploration_hide" and not _turn_system.active:
		_toggle_exploration_hide()
		_refresh_action_catalog()
		return
	super._on_catalog_action_requested(action_id)


func _request_attack() -> void:
	var origin: Vector2 = player.global_position
	await super._request_attack()
	report_world_noise("weapon", origin, {"source_type": "player_attack"})
	_break_exploration_hidden("Атака выдала позицию героя.")


func _on_ability_requested(ability_id: String) -> void:
	var origin: Vector2 = player.global_position
	await super._on_ability_requested(ability_id)
	report_world_noise("spell", origin, {"source_type": "player_ability", "ability_id": ability_id})
	_break_exploration_hidden("Применение способности выдало позицию героя.")


func report_world_noise(noise_type: String, world_position: Vector2, overrides: Dictionary = {}) -> Dictionary:
	if not GameState.has_method("report_stealth_noise"):
		return {}
	return GameState.call("report_stealth_noise", noise_type, world_position, overrides, false, true) as Dictionary


func on_stealth_door_state_changed(_door_id: String, _door_state: String) -> void:
	_refresh_action_catalog()


func _toggle_exploration_hide() -> void:
	if _exploration_hidden:
		_break_exploration_hidden("Герой вышел из укрытия.")
		return
	var visible_observers: Array[Node] = _visible_exploration_observers()
	if not visible_observers.is_empty():
		show_combat_message(_line_of_sight_failure_message(visible_observers), false)
		return
	var hiding_spot: Dictionary = _stealth_alerts.get_hiding_spot_at(player.global_position)
	var concealment_bonus: int = int(hiding_spot.get("concealment_bonus", 0))
	var difficulty: int = 10
	for actor: Node in _exploration_alert_actors():
		var actor_id: String = str(actor.call("get_actor_id"))
		var profile: Dictionary = _stealth_alerts.get_profile(actor_id)
		difficulty = maxi(difficulty, int(profile.get("passive_perception", 10)))
	var overrides: Array[int] = _exploration_hide_roll_overrides.duplicate()
	_exploration_hide_roll_overrides.clear()
	var check: Dictionary = _srd_rules.resolve_d20_test(
		GameState.player_character.get_skill_modifier("stealth"),
		difficulty,
		false,
		_player_has_untrained_armor_d20_disadvantage("dexterity"),
		overrides,
		GameState.player_character.reroll_natural_one
	)
	var total: int = int(check.get("total", 0)) + concealment_bonus
	if total < difficulty:
		show_combat_message("Скрыться не удалось: %d против пассивного Восприятия %d." % [total, difficulty], false)
		report_world_noise("quiet_step", player.global_position, {"source_type": "failed_hide"})
		return
	_exploration_hidden = true
	GameState.player_character.active_effects["exploration_hidden"] = true
	var spot_label: String = str(hiding_spot.get("label", "полным укрытием"))
	show_combat_message("Герой скрылся в «%s»: Скрытность %d против %d." % [spot_label, total, difficulty], true)
	_refresh_action_catalog()


func _break_exploration_hidden(message: String = "") -> void:
	if not _exploration_hidden:
		return
	_exploration_hidden = false
	GameState.player_character.active_effects.erase("exploration_hidden")
	if not message.is_empty():
		show_combat_message(message, false)
	_refresh_action_catalog()


func _update_exploration_step_noise(delta: float) -> void:
	var current_position: Vector2 = player.global_position
	if _last_exploration_player_position == Vector2.INF:
		_last_exploration_player_position = current_position
		return
	var distance: float = current_position.distance_to(_last_exploration_player_position)
	_last_exploration_player_position = current_position
	if distance <= 0.75:
		_step_noise_elapsed = 0.0
		return
	_step_noise_elapsed += maxf(delta, 0.0)
	if _step_noise_elapsed < STEP_NOISE_INTERVAL_SECONDS:
		return
	_step_noise_elapsed = 0.0
	var hiding_spot: Dictionary = _stealth_alerts.get_hiding_spot_at(current_position)
	var noise_type: String = "quiet_step" if _exploration_hidden else "normal_step"
	var overrides: Dictionary = {"source_type": "player_movement"}
	if not hiding_spot.is_empty():
		overrides["intensity"] = roundi(float(_stealth_alerts.get_noise_profile(noise_type).get("intensity", 10)) * float(hiding_spot.get("noise_multiplier", 1.0)))
	report_world_noise(noise_type, current_position, overrides)
	if _exploration_hidden and hiding_spot.is_empty():
		_break_exploration_hidden("Герой покинул укромное место и оставил заметный след.")


func _update_exploration_alerts(delta: float) -> void:
	for actor: Node in _exploration_alert_actors():
		_update_exploration_actor(actor, delta)


func _update_exploration_actor(actor: Node, delta: float) -> void:
	if actor == null or not is_instance_valid(actor) or not (actor is Node2D):
		return
	var actor_id: String = str(actor.call("get_actor_id"))
	var profile: Dictionary = _stealth_alerts.get_profile(actor_id)
	if profile.is_empty():
		return
	var record: Dictionary = _record_for_actor(actor_id)
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
		record = _advance_actor_investigation(actor, record, profile, delta)
	_alert_records[actor_id] = record
	_apply_record_to_actor(actor, record)
	if str(record.get("state", "")) == StealthAlertSystem.STATE_ALERTED and visible:
		_begin_combat_from_alert(actor, record)


func _advance_actor_investigation(actor: Node, record: Dictionary, profile: Dictionary, delta: float) -> Dictionary:
	var state: String = str(record.get("state", StealthAlertSystem.STATE_CALM))
	if state not in [
		StealthAlertSystem.STATE_INVESTIGATING,
		StealthAlertSystem.STATE_SEARCHING,
		StealthAlertSystem.STATE_ALERTED
	]:
		return record
	var target_position: Vector2 = _stealth_alerts.vector_from_value(record.get("last_known_position", []))
	var actor_position: Vector2 = (actor as Node2D).global_position
	var distance: float = actor_position.distance_to(target_position)
	var reached: bool = distance <= SEARCH_REACHED_DISTANCE_PIXELS
	if not reached:
		var speed: float = maxf(float(profile.get("investigation_speed_pixels", 90.0)), 0.0)
		var next_position: Vector2 = actor_position.move_toward(target_position, speed * maxf(delta, 0.0))
		(actor as Node2D).global_position = next_position
		if actor.has_method("set_facing_direction"):
			actor.call("set_facing_direction", target_position - actor_position)
		reached = next_position.distance_to(target_position) <= SEARCH_REACHED_DISTANCE_PIXELS
	return _stealth_alerts.advance_search(record, delta, reached, profile)


func _exploration_actor_can_see_player(actor: Node, profile: Dictionary) -> bool:
	if actor == null or not is_instance_valid(actor) or not (actor is Node2D):
		return false
	var actor_position: Vector2 = (actor as Node2D).global_position
	var facing: Vector2 = actor.call("get_facing_direction") as Vector2 if actor.has_method("get_facing_direction") else Vector2.LEFT
	var line_of_sight_clear: bool = not _stealth_alerts.door_blocks_line_of_sight(GameState, actor_position, player.global_position)
	if line_of_sight_clear and _combat_environment != null:
		line_of_sight_clear = _combat_environment.has_line_of_sight(actor_position, player.global_position)
	var hiding_spot: Dictionary = _stealth_alerts.get_hiding_spot_at(player.global_position)
	var fully_concealed: bool = _exploration_hidden and not hiding_spot.is_empty()
	return _stealth_alerts.can_see_target(actor_position, facing, player.global_position, profile, line_of_sight_clear, fully_concealed)


func _visible_exploration_observers() -> Array[Node]:
	var result: Array[Node] = []
	for actor: Node in _exploration_alert_actors():
		var actor_id: String = str(actor.call("get_actor_id"))
		if _exploration_actor_can_see_player(actor, _stealth_alerts.get_profile(actor_id)):
			result.append(actor)
	return result


func _player_visible_to_any_exploration_actor() -> bool:
	return not _visible_exploration_observers().is_empty()


func _exploration_alert_actors() -> Array[Node]:
	var result: Array[Node] = []
	for actor: Node in get_tree().get_nodes_in_group("combat_targets"):
		if not is_instance_valid(actor) or not (actor is Node2D) or not actor.has_method("get_actor_id"):
			continue
		var actor_id: String = str(actor.call("get_actor_id"))
		if actor_id.is_empty() or not _stealth_alerts.has_profile(actor_id):
			continue
		if actor.has_method("is_combat_active") and not bool(actor.call("is_combat_active")):
			continue
		result.append(actor)
	return result


func _begin_combat_from_alert(actor: Node, record: Dictionary) -> void:
	if _turn_system.active or actor == null or not is_instance_valid(actor):
		return
	_break_exploration_hidden()
	record["state"] = StealthAlertSystem.STATE_COMBAT
	record["suspicion"] = StealthAlertSystem.SUSPICION_ALERTED
	var actor_id: String = str(actor.call("get_actor_id"))
	_alert_records[actor_id] = record
	_persist_alert_record(actor_id, true)
	if actor.has_method("enter_combat_hostile"):
		actor.call("enter_combat_hostile")
	show_combat_message("%s обнаружил героя и поднимает тревогу." % _target_name(actor), false)
	_start_turn_based_combat(actor)


func _sync_combat_alert_records() -> void:
	for actor: Node in _exploration_alert_actors():
		var actor_id: String = str(actor.call("get_actor_id"))
		var record: Dictionary = _record_for_actor(actor_id)
		record["state"] = StealthAlertSystem.STATE_COMBAT
		record["suspicion"] = StealthAlertSystem.SUSPICION_ALERTED
		record["last_known_position"] = _stealth_alerts.vector_to_value(player.global_position)
		_alert_records[actor_id] = record
		_apply_record_to_actor(actor, record)


func _connect_stealth_alert_signals() -> void:
	if GameState.has_signal("stealth_noise_reported") and not GameState.stealth_noise_reported.is_connected(_on_stealth_noise_reported):
		GameState.stealth_noise_reported.connect(_on_stealth_noise_reported)
	if GameState.has_signal("encounter_abandoned") and not GameState.encounter_abandoned.is_connected(_on_encounter_abandoned_for_alerts):
		GameState.encounter_abandoned.connect(_on_encounter_abandoned_for_alerts)


func _on_stealth_noise_reported(noise_event: Dictionary) -> void:
	_last_noise_sequence = maxi(_last_noise_sequence, int(noise_event.get("sequence", 0)))
	for actor: Node in _exploration_alert_actors():
		var actor_id: String = str(actor.call("get_actor_id"))
		var profile: Dictionary = _stealth_alerts.get_profile(actor_id)
		var actor_room_id: String = _stealth_alerts.get_room_id_at((actor as Node2D).global_position)
		if not _stealth_alerts.actor_hears_noise(GameState, (actor as Node2D).global_position, actor_room_id, noise_event, profile):
			continue
		var record: Dictionary = _stealth_alerts.apply_noise(_record_for_actor(actor_id), noise_event, profile)
		_alert_records[actor_id] = record
		_apply_record_to_actor(actor, record)
		_persist_alert_record(actor_id, false)


func _on_encounter_abandoned_for_alerts(_encounter_id: String, _reason_id: String, state: Dictionary) -> void:
	var context: Dictionary = state.get("close_context", {}) as Dictionary if state.get("close_context", {}) is Dictionary else {}
	if not bool(context.get("enemies_alerted", false)):
		return
	for actor: Node in _exploration_alert_actors():
		var actor_id: String = str(actor.call("get_actor_id"))
		var profile: Dictionary = _stealth_alerts.get_profile(actor_id)
		var record: Dictionary = _record_for_actor(actor_id)
		record["state"] = StealthAlertSystem.STATE_SEARCHING
		record["suspicion"] = 82.0
		record["last_known_position"] = _stealth_alerts.vector_to_value(_last_seen_player_position)
		record["search_seconds_remaining"] = float(profile.get("search_duration_seconds", 12.0))
		record["alert_cooldown_seconds"] = float(profile.get("alert_cooldown_seconds", 24.0))
		_alert_records[actor_id] = record
		_apply_record_to_actor(actor, record)
		_persist_alert_record(actor_id, true)


func _restore_exploration_alerts() -> void:
	_alert_records.clear()
	if not GameState.has_method("get_all_stealth_alert_records"):
		return
	var stored: Dictionary = GameState.call("get_all_stealth_alert_records") as Dictionary
	for actor_id_value: Variant in stored.keys():
		_alert_records[str(actor_id_value)] = (stored[actor_id_value] as Dictionary).duplicate(true)
	for actor: Node in _exploration_alert_actors():
		var actor_id: String = str(actor.call("get_actor_id"))
		var record: Dictionary = _record_for_actor(actor_id)
		if str(record.get("state", "")) == StealthAlertSystem.STATE_COMBAT:
			record["state"] = StealthAlertSystem.STATE_SEARCHING
			record["suspicion"] = 82.0
			record["search_seconds_remaining"] = float(_stealth_alerts.get_profile(actor_id).get("search_duration_seconds", 12.0))
			_alert_records[actor_id] = record
		_apply_record_to_actor(actor, record)


func _record_for_actor(actor_id: String) -> Dictionary:
	var value: Variant = _alert_records.get(actor_id, {})
	if value is Dictionary and not (value as Dictionary).is_empty():
		return (value as Dictionary).duplicate(true)
	var record: Dictionary = GameState.call("get_stealth_alert_record", actor_id) as Dictionary if GameState.has_method("get_stealth_alert_record") else {}
	_alert_records[actor_id] = record.duplicate(true)
	return record


func _apply_record_to_actor(actor: Node, record: Dictionary) -> void:
	if actor.has_method("set_exploration_alert_state"):
		actor.call(
			"set_exploration_alert_state",
			str(record.get("state", StealthAlertSystem.STATE_CALM)),
			float(record.get("suspicion", 0.0)),
			_stealth_alerts.vector_from_value(record.get("last_known_position", []))
		)


func _persist_alert_record(actor_id: String, save_after: bool) -> void:
	if actor_id.is_empty() or not _alert_records.has(actor_id) or not GameState.has_method("set_stealth_alert_record"):
		return
	GameState.call("set_stealth_alert_record", actor_id, (_alert_records[actor_id] as Dictionary), save_after, false)


func _persist_all_alert_records(save_after: bool) -> void:
	for actor_id_value: Variant in _alert_records.keys():
		_persist_alert_record(str(actor_id_value), false)
	if save_after:
		GameState.save_game()


func _build_alert_indicator() -> void:
	_alert_indicator = Label.new()
	_alert_indicator.name = "ExplorationStealthAlertIndicator"
	_alert_indicator.set_anchors_preset(Control.PRESET_TOP_LEFT)
	_alert_indicator.offset_left = 22.0
	_alert_indicator.offset_top = 108.0
	_alert_indicator.offset_right = 520.0
	_alert_indicator.offset_bottom = 144.0
	_alert_indicator.add_theme_font_size_override("font_size", 17)
	_alert_indicator.z_index = 30
	$Interface.add_child(_alert_indicator)
	_add_exploration_hud_node(_alert_indicator)


func _refresh_alert_indicator() -> void:
	if _alert_indicator == null:
		return
	var highest_suspicion: float = 0.0
	var highest_state: String = StealthAlertSystem.STATE_CALM
	for value: Variant in _alert_records.values():
		if not value is Dictionary:
			continue
		var record: Dictionary = value as Dictionary
		if float(record.get("suspicion", 0.0)) >= highest_suspicion:
			highest_suspicion = float(record.get("suspicion", 0.0))
			highest_state = str(record.get("state", StealthAlertSystem.STATE_CALM))
	var hidden_label: String = "СКРЫТ" if (_exploration_hidden or _player_combat_state.hidden) else "ВИДИМ"
	_alert_indicator.text = "%s · %s · ПОДОЗРЕНИЕ %d%%" % [hidden_label, highest_state.to_upper(), roundi(highest_suspicion)]
	_alert_indicator.add_theme_color_override(
		"font_color",
		Color(1.0, 0.42, 0.34, 1.0) if highest_suspicion >= StealthAlertSystem.SUSPICION_INVESTIGATING else Color(0.86, 0.82, 0.5, 1.0)
	)


func set_exploration_hide_roll_overrides_for_testing(values: Array) -> void:
	_exploration_hide_roll_overrides.clear()
	for value: Variant in values:
		_exploration_hide_roll_overrides.append(int(value))


func force_exploration_alert_tick_for_testing(delta: float) -> void:
	_update_exploration_alerts(delta)
	_refresh_alert_indicator()


func get_exploration_alert_record_for_testing(actor: Node) -> Dictionary:
	if actor == null or not actor.has_method("get_actor_id"):
		return {}
	return _record_for_actor(str(actor.call("get_actor_id")))


func force_post_escape_search_for_testing(actor: Node, last_known_position: Vector2) -> void:
	if actor == null or not actor.has_method("get_actor_id"):
		return
	var actor_id: String = str(actor.call("get_actor_id"))
	var profile: Dictionary = _stealth_alerts.get_profile(actor_id)
	var record: Dictionary = _record_for_actor(actor_id)
	record["state"] = StealthAlertSystem.STATE_SEARCHING
	record["suspicion"] = 82.0
	record["last_known_position"] = _stealth_alerts.vector_to_value(last_known_position)
	record["search_seconds_remaining"] = float(profile.get("search_duration_seconds", 12.0))
	record["alert_cooldown_seconds"] = float(profile.get("alert_cooldown_seconds", 24.0))
	_alert_records[actor_id] = record
	_apply_record_to_actor(actor, record)
	_persist_alert_record(actor_id, false)


func is_exploration_hidden_for_testing() -> bool:
	return _exploration_hidden


func get_alert_indicator_text_for_testing() -> String:
	return _alert_indicator.text if _alert_indicator != null else ""
