extends "res://scripts/game/game_guard_post_two_room_runtime.gd"

const FIRST_ROOM_PARLEY_ACTOR_IDS: Array[String] = ["caretaker", "service_guard"]
const SERVICE_GUARD_NOTICED_FLAG: String = "vault_guard_post_service_guard_noticed"
const INNER_AI_WATCHDOG_SECONDS: float = 0.8

var _inner_ai_watchdog_elapsed: float = 0.0
var _inner_ai_watchdog_actor_id: String = ""
var _inner_ai_turn_started: Dictionary = {}
var _inner_ai_turn_completed: Dictionary = {}
var _peaceful_cleanup_applied: bool = false


func _ready() -> void:
	super._ready()
	_settle_pending_peaceful_outcome()


func _process(delta: float) -> void:
	# Dialogue choices set their flags before the dialogue panel closes. Resolve
	# and clean the peaceful route before exploration detection receives a frame.
	_settle_pending_peaceful_outcome()
	super._process(delta)
	_maintain_inner_watch_ai(delta)


func _broadcast_actor_alert(actor: Node, record: Dictionary) -> void:
	if _first_room_actor_should_remain_neutral(actor):
		return
	super._broadcast_actor_alert(actor, record)


func _begin_combat_from_alert(actor: Node, record: Dictionary) -> void:
	if _first_room_actor_should_remain_neutral(actor):
		_handle_neutral_first_room_detection(actor, record)
		return
	super._begin_combat_from_alert(actor, record)


func _start_inner_watch_combat() -> void:
	if _turn_system.active:
		return
	_prepare_inner_watch_combatants()
	_enemy_turn_running = false
	_inner_ai_watchdog_elapsed = 0.0
	_inner_ai_watchdog_actor_id = ""
	super._start_inner_watch_combat()


func _run_enemy_turn(actor: Node) -> void:
	var actor_id: String = _actor_id(actor)
	if actor_id in SECOND_ROOM_ACTOR_IDS:
		_inner_ai_turn_started[actor_id] = int(_inner_ai_turn_started.get(actor_id, 0)) + 1
	await super._run_enemy_turn(actor)
	if actor_id in SECOND_ROOM_ACTOR_IDS:
		_inner_ai_turn_completed[actor_id] = int(_inner_ai_turn_completed.get(actor_id, 0)) + 1


func _resolve_room(encounter_id: String, resolution_id: String, context: Dictionary) -> void:
	super._resolve_room(encounter_id, resolution_id, context)
	if encounter_id == FIRST_ROOM_ENCOUNTER_ID and resolution_id == "peaceful_passage":
		_apply_peaceful_guard_post_state()


func get_inner_watch_ai_turn_started_for_testing(actor_id: String) -> int:
	return int(_inner_ai_turn_started.get(actor_id, 0))


func get_inner_watch_ai_turn_completed_for_testing(actor_id: String) -> int:
	return int(_inner_ai_turn_completed.get(actor_id, 0))


func prepare_inner_watch_combatants_for_testing() -> void:
	_prepare_inner_watch_combatants()


func _first_room_actor_should_remain_neutral(actor: Node) -> bool:
	var actor_id: String = _actor_id(actor)
	if actor_id not in FIRST_ROOM_PARLEY_ACTOR_IDS:
		return false
	if bool(GameState.get_flag(ROOM_ONE_COMBAT_STARTED_FLAG, false)):
		return false
	if actor.has_method("is_hostile") and bool(actor.call("is_hostile")):
		return false
	var outcome: String = str(GameState.get_flag(ROOM_ONE_OUTCOME_FLAG, ""))
	if outcome == "peaceful":
		return true
	var status: String = str(GameState.get_encounter_status(FIRST_ROOM_ENCOUNTER_ID))
	return status not in [EncounterSystem.STATUS_RESOLVED, EncounterSystem.STATUS_REWARDED]


func _handle_neutral_first_room_detection(actor: Node, record: Dictionary) -> void:
	var actor_id: String = _actor_id(actor)
	if actor_id.is_empty():
		return
	var noticed_flag: String = CARETAKER_NOTICED_FLAG if actor_id == CARETAKER_ACTOR_ID else SERVICE_GUARD_NOTICED_FLAG
	var first_contact: bool = not bool(GameState.get_flag(noticed_flag, false))
	record["state"] = StealthAlertSystem.STATE_SUSPICIOUS
	record["suspicion"] = StealthAlertSystem.SUSPICION_SUSPICIOUS
	record["search_seconds_remaining"] = 0.0
	record["alert_cooldown_seconds"] = 0.0
	_alert_records[actor_id] = record
	if actor.has_method("set_exploration_alert_state"):
		actor.call(
			"set_exploration_alert_state",
			StealthAlertSystem.STATE_SUSPICIOUS,
			StealthAlertSystem.SUSPICION_SUSPICIOUS,
			_stealth_alerts.vector_from_value(record.get("last_known_position", []))
		)
	actor.set("hostile", false)
	GameState.set_flag(noticed_flag, true)
	_persist_alert_record(actor_id, first_contact)
	if not first_contact:
		return
	if actor_id == CARETAKER_ACTOR_ID:
		show_combat_message("Смотритель замечает героя, но не нападает. С ним можно поговорить через ДЕЙСТВИЯ.", true)
	else:
		show_combat_message("Служебный дозорный замечает героя, но ждёт решения Смотрителя.", true)


func _settle_pending_peaceful_outcome() -> void:
	if bool(GameState.get_flag(ROOM_ONE_COMBAT_STARTED_FLAG, false)):
		return
	var outcome: String = str(GameState.get_flag(ROOM_ONE_OUTCOME_FLAG, ""))
	if outcome == "peaceful":
		_apply_peaceful_guard_post_state()
		return
	if not bool(GameState.get_flag("caretaker_convinced", false)) or _turn_system.active:
		return
	var status: String = str(GameState.get_encounter_status(FIRST_ROOM_ENCOUNTER_ID))
	if status == EncounterSystem.STATUS_AVAILABLE and player != null and player.global_position.x >= FIRST_ROOM_APPROACH_X:
		_begin_encounter(FIRST_ROOM_ENCOUNTER_ID, "caretaker_dialogue")
		status = str(GameState.get_encounter_status(FIRST_ROOM_ENCOUNTER_ID))
	if status == EncounterSystem.STATUS_ACTIVE:
		_resolve_room(FIRST_ROOM_ENCOUNTER_ID, "peaceful_passage", {
			"source_type": "dialogue",
			"source_id": "caretaker_convinced_pre_alert"
		})
		_sync_room_from_persistent_state()


func _apply_peaceful_guard_post_state() -> void:
	if _peaceful_cleanup_applied and str(GameState.get_flag(ROOM_ONE_OUTCOME_FLAG, "")) == "peaceful":
		return
	if str(GameState.get_flag(ROOM_ONE_OUTCOME_FLAG, "")) != "peaceful":
		return
	_peaceful_cleanup_applied = true
	for actor_id: String in FIRST_ROOM_PARLEY_ACTOR_IDS:
		var actor: Node = _find_guard_post_actor(actor_id)
		if is_instance_valid(actor):
			actor.set("hostile", false)
			if actor.has_method("set_exploration_alert_state"):
				actor.call("set_exploration_alert_state", StealthAlertSystem.STATE_CALM, 0.0, Vector2.ZERO)
		var record: Dictionary = GameState.get_stealth_alert_record(actor_id)
		record["state"] = StealthAlertSystem.STATE_CALM
		record["suspicion"] = 0.0
		record["last_known_position"] = []
		record["search_seconds_remaining"] = 0.0
		record["alert_cooldown_seconds"] = 0.0
		_alert_records[actor_id] = record
		_alert_broadcasted.erase(actor_id)
		_persist_alert_record(actor_id, false)
	GameState.save_game()


func _find_guard_post_actor(actor_id: String) -> Node:
	for actor: Node in _guard_post_candidate_nodes():
		if is_instance_valid(actor) and _actor_id(actor) == actor_id:
			return actor
	return null


func _prepare_inner_watch_combatants() -> void:
	var room: Node = _two_room_node()
	if room == null:
		return
	if room.has_method("activate_inner_watch_combat"):
		room.call("activate_inner_watch_combat")
	for method_name: String in ["get_training_marksman", "get_training_mage"]:
		if not room.has_method(method_name):
			continue
		var actor: Node = room.call(method_name) as Node
		if not is_instance_valid(actor):
			continue
		if not actor.is_in_group("combat_targets"):
			actor.add_to_group("combat_targets")
		if not actor.is_in_group("stealth_alert_actors"):
			actor.add_to_group("stealth_alert_actors")
		if actor.has_method("activate_combat_participant"):
			actor.call("activate_combat_participant")
		elif actor.has_method("enter_combat_hostile"):
			actor.call("enter_combat_hostile")
		if actor.has_method("set_facing_direction") and player != null:
			actor.call("set_facing_direction", player.global_position - (actor as Node2D).global_position)


func _maintain_inner_watch_ai(delta: float) -> void:
	if not _turn_system.active or _enemy_turn_running:
		_reset_inner_ai_watchdog()
		return
	var actor: Node = _turn_system.current_actor()
	if not is_instance_valid(actor) or actor == player:
		_reset_inner_ai_watchdog()
		return
	var actor_id: String = _actor_id(actor)
	if actor_id not in SECOND_ROOM_ACTOR_IDS:
		_reset_inner_ai_watchdog()
		return
	if _any_overlay_visible():
		return
	if actor_id != _inner_ai_watchdog_actor_id:
		_inner_ai_watchdog_actor_id = actor_id
		_inner_ai_watchdog_elapsed = 0.0
	_inner_ai_watchdog_elapsed += maxf(delta, 0.0)
	if _inner_ai_watchdog_elapsed < INNER_AI_WATCHDOG_SECONDS:
		return
	_inner_ai_watchdog_elapsed = 0.0
	call_deferred("_run_enemy_turn", actor)


func _reset_inner_ai_watchdog() -> void:
	_inner_ai_watchdog_elapsed = 0.0
	_inner_ai_watchdog_actor_id = ""
