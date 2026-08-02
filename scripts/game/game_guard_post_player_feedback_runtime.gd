extends "res://scripts/game/game_guard_post_polish_base_runtime.gd"

var _hide_transition_running: bool = false


func _ready() -> void:
	super._ready()
	# Base scenes connect signals while their own scripts are active. Replace only
	# those inherited handlers with explicit leaf-runtime dispatchers so the real
	# UI path and direct method calls execute the same Hide transition.
	_replace_bound_handler(
		_action_catalog_ui,
		&"action_requested",
		&"_on_catalog_action_requested",
		Callable(self, "_on_feedback_catalog_action_requested")
	)
	_replace_bound_handler(
		_srd_combat_ui,
		&"hide_requested",
		&"_on_hide_requested",
		Callable(self, "_on_feedback_hide_requested")
	)


func _process(delta: float) -> void:
	super._process(delta)
	if _turn_system.active and not is_player_combat_turn():
		_close_action_catalog_immediately()


func is_player_combat_turn() -> bool:
	return (
		_turn_system.active
		and _turn_system.is_player_turn(player)
		and not _enemy_turn_running
	)


func _advance_combat_turn() -> void:
	_close_action_catalog_immediately()
	super._advance_combat_turn()


func _on_feedback_catalog_action_requested(action_id: String) -> void:
	if action_id == "hide":
		_on_hide_requested()
		_invalidate_reachable_area()
		_refresh_action_catalog()
		return
	super._on_catalog_action_requested(action_id)


func _on_feedback_hide_requested() -> void:
	_on_hide_requested()


func _on_hide_requested() -> void:
	if _hide_transition_running:
		return
	_hide_transition_running = true
	var combat_was_active: bool = _turn_system.active
	var observers: Array[Node] = _combat_search_observers()
	var last_known_position: Vector2 = _last_seen_player_position
	if last_known_position == Vector2.ZERO:
		last_known_position = player.global_position
	# The inherited Hide resolution is synchronous. Running it directly ensures
	# the success flag is available before deciding whether initiative must stop.
	super._on_hide_requested()
	if (
		not combat_was_active
		or not _turn_system.active
		or not _player_combat_state.hidden
	):
		_hide_transition_running = false
		return
	_suspend_combat_for_hidden_pursuit(observers, last_known_position)


func _suspend_combat_for_hidden_pursuit(observers: Array[Node], last_known_position: Vector2) -> void:
	_close_action_catalog_immediately()
	_stop_turn_based_combat(
		"Герой скрылся. Инициатива завершена; противники идут к последней известной позиции и начинают поиск."
	)

	_exploration_hidden = true
	GameState.player_character.active_effects["exploration_hidden"] = true
	for actor: Node in observers:
		if not is_instance_valid(actor) or not actor.has_method("get_actor_id"):
			continue
		var actor_id: String = str(actor.call("get_actor_id"))
		if actor_id.is_empty():
			continue
		actor.set("hostile", false)
		if actor.has_method("set_turn_active"):
			actor.call("set_turn_active", false)
		var profile: Dictionary = _stealth_alerts.get_profile(actor_id)
		var record: Dictionary = GameState.get_stealth_alert_record(actor_id)
		record["state"] = StealthAlertSystem.STATE_INVESTIGATING
		record["suspicion"] = maxf(
			float(record.get("suspicion", 0.0)),
			StealthAlertSystem.SUSPICION_INVESTIGATING
		)
		record["last_known_position"] = [last_known_position.x, last_known_position.y]
		record["search_seconds_remaining"] = maxf(
			float(record.get("search_seconds_remaining", 0.0)),
			float(profile.get("search_duration_seconds", 10.0))
		)
		record["alert_cooldown_seconds"] = maxf(
			float(record.get("alert_cooldown_seconds", 0.0)),
			float(profile.get("alert_cooldown_seconds", 20.0))
		)
		_alert_records[actor_id] = record
		if actor.has_method("set_exploration_alert_state"):
			actor.call(
				"set_exploration_alert_state",
				StealthAlertSystem.STATE_INVESTIGATING,
				float(record["suspicion"]),
				last_known_position
			)
		_persist_alert_record(actor_id, false)

	_refresh_alert_indicator()
	_refresh_action_catalog()
	GameState.save_game()
	_hide_transition_running = false


func _combat_search_observers() -> Array[Node]:
	var result: Array[Node] = []
	for entry: Dictionary in _turn_system.entries:
		if bool(entry.get("is_player", false)):
			continue
		var actor: Node = entry.get("node") as Node
		if not is_instance_valid(actor) or not actor is Node2D:
			continue
		if actor.has_method("is_combat_active") and not bool(actor.call("is_combat_active")):
			continue
		result.append(actor)
	return result


func _close_action_catalog_immediately() -> void:
	var catalog: Node = get_node_or_null("Interface/ActionCatalogUI")
	if catalog != null and catalog.has_method("close_catalog"):
		catalog.call("close_catalog")


func _replace_bound_handler(
	emitter: Object,
	signal_name: StringName,
	inherited_method: StringName,
	replacement: Callable
) -> void:
	if emitter == null:
		return
	for connection_value: Variant in emitter.get_signal_connection_list(signal_name):
		if not connection_value is Dictionary:
			continue
		var callable_value: Variant = (connection_value as Dictionary).get("callable")
		if not callable_value is Callable:
			continue
		var existing: Callable = callable_value as Callable
		if existing.get_object() == self and existing.get_method() == inherited_method:
			emitter.disconnect(signal_name, existing)
	if not emitter.is_connected(signal_name, replacement):
		emitter.connect(signal_name, replacement)
