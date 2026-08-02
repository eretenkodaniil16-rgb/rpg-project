class_name HidePursuitTransitionController
extends Node

var _game: Node
var _state: Node
var _transition_running: bool = false


func _ready() -> void:
	_game = get_parent()
	_state = get_tree().root.get_node_or_null("GameState")


func _process(_delta: float) -> void:
	if not is_instance_valid(_game):
		return
	_close_catalog_outside_player_turn()
	if _transition_running:
		return
	var turn_system: TurnBasedCombatSystem = _turn_system()
	var combat_state: CombatantState = _combat_state()
	if turn_system == null or combat_state == null:
		return
	if not turn_system.active or not combat_state.hidden:
		return
	_transition_running = true
	call_deferred("_suspend_detected_hidden_combat")


func is_player_combat_turn() -> bool:
	var turn_system: TurnBasedCombatSystem = _turn_system()
	var player: Node = _player()
	return (
		turn_system != null
		and turn_system.active
		and is_instance_valid(player)
		and turn_system.is_player_turn(player)
		and not bool(_game.get("_enemy_turn_running"))
	)


func suspend_combat_for_hidden_pursuit_for_testing(
	observers: Array[Node],
	last_known_position: Vector2
) -> void:
	if _transition_running:
		return
	_transition_running = true
	_suspend_combat_for_hidden_pursuit(observers, last_known_position)


func _suspend_detected_hidden_combat() -> void:
	var turn_system: TurnBasedCombatSystem = _turn_system()
	if turn_system == null or not turn_system.active:
		_transition_running = false
		return
	var last_known_position: Vector2 = _game.get("_last_seen_player_position") as Vector2
	var player: Node2D = _player() as Node2D
	if last_known_position == Vector2.ZERO and is_instance_valid(player):
		last_known_position = player.global_position
	_suspend_combat_for_hidden_pursuit(_combat_search_observers(turn_system), last_known_position)


func _suspend_combat_for_hidden_pursuit(
	observers: Array[Node],
	last_known_position: Vector2
) -> void:
	_close_action_catalog()
	_game.call(
		"_stop_turn_based_combat",
		"Герой скрылся. Инициатива завершена; противники идут к последней известной позиции и начинают поиск."
	)

	if not is_instance_valid(_state):
		_state = get_tree().root.get_node_or_null("GameState")
	_game.set("_exploration_hidden", true)
	if is_instance_valid(_state):
		var character: PlayerCharacter = _state.get("player_character") as PlayerCharacter
		if character != null:
			character.active_effects["exploration_hidden"] = true

	var runtime_records: Dictionary = _game.get("_alert_records") as Dictionary
	var stealth_system := StealthAlertSystem.new()
	for actor: Node in observers:
		if not is_instance_valid(actor):
			continue
		var actor_id: String = _actor_id(actor)
		if actor_id.is_empty():
			continue
		actor.set("hostile", false)
		if actor.has_method("set_turn_active"):
			actor.call("set_turn_active", false)
		var profile: Dictionary = stealth_system.get_profile(actor_id)
		var record: Dictionary = (
			_state.call("get_stealth_alert_record", actor_id) as Dictionary
			if is_instance_valid(_state) and _state.has_method("get_stealth_alert_record")
			else {}
		)
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
		runtime_records[actor_id] = record
		if actor.has_method("set_exploration_alert_state"):
			actor.call(
				"set_exploration_alert_state",
				StealthAlertSystem.STATE_INVESTIGATING,
				float(record["suspicion"]),
				last_known_position
			)
		if is_instance_valid(_state) and _state.has_method("set_stealth_alert_record"):
			_state.call("set_stealth_alert_record", actor_id, record, false, false)
		if _game.has_method("_persist_alert_record"):
			_game.call("_persist_alert_record", actor_id, false)
	_game.set("_alert_records", runtime_records)

	if _game.has_method("_refresh_alert_indicator"):
		_game.call("_refresh_alert_indicator")
	if _game.has_method("_refresh_action_catalog"):
		_game.call("_refresh_action_catalog")
	if is_instance_valid(_state) and _state.has_method("save_game"):
		_state.call("save_game")
	_transition_running = false


func _combat_search_observers(turn_system: TurnBasedCombatSystem) -> Array[Node]:
	var result: Array[Node] = []
	for entry: Dictionary in turn_system.entries:
		if bool(entry.get("is_player", false)):
			continue
		var actor: Node = entry.get("node") as Node
		if not is_instance_valid(actor) or not actor is Node2D:
			continue
		if actor.has_method("is_combat_active") and not bool(actor.call("is_combat_active")):
			continue
		result.append(actor)
	return result


func _close_catalog_outside_player_turn() -> void:
	var turn_system: TurnBasedCombatSystem = _turn_system()
	if turn_system == null or not turn_system.active:
		return
	if _transition_running or not is_player_combat_turn():
		_close_action_catalog()


func _close_action_catalog() -> void:
	var catalog: Node = _game.get_node_or_null("Interface/ActionCatalogUI")
	if catalog != null and catalog.has_method("close_catalog"):
		catalog.call("close_catalog")


func _turn_system() -> TurnBasedCombatSystem:
	return _game.get("_turn_system") as TurnBasedCombatSystem if is_instance_valid(_game) else null


func _combat_state() -> CombatantState:
	return _game.get("_player_combat_state") as CombatantState if is_instance_valid(_game) else null


func _player() -> Node:
	return _game.get_node_or_null("Player") if is_instance_valid(_game) else null


func _actor_id(actor: Node) -> String:
	if actor.has_method("get_actor_id"):
		return str(actor.call("get_actor_id"))
	if _game.has_method("_actor_id"):
		return str(_game.call("_actor_id", actor))
	return ""
