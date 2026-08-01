extends "res://scripts/game/game_guard_post_encounter_runtime.gd"

const FIRST_ROOM_ENCOUNTER_ID: String = "vault_guard_post_01"
const SECOND_ROOM_ENCOUNTER_ID: String = "vault_inner_watch_01"
const FIRST_ROOM_ACTOR_IDS: Array[String] = ["caretaker", "service_guard"]
const SECOND_ROOM_ACTOR_IDS: Array[String] = ["training_marksman", "training_mage"]

const FIRST_ROOM_APPROACH_X: float = 610.0
const FIRST_ROOM_STEALTH_EXIT_X: float = 813.0
const SECOND_ROOM_ENTRY_X: float = 941.0
const SECOND_ROOM_STEALTH_EXIT_X: float = 1170.0

const ROOM_ONE_OUTCOME_FLAG: String = "vault_guard_post_room1_outcome"
const ROOM_ONE_COMBAT_STARTED_FLAG: String = "vault_guard_post_room1_combat_started"
const ROOM_ONE_HOSTILE_FLAG: String = "vault_inner_watch_hostile"
const INNER_GATE_OPEN_FLAG: String = "vault_inner_gate_open"

var _inner_watch_combat_starting: bool = false
var _two_room_resolution_in_progress: bool = false


func _ready() -> void:
	_ensure_two_room_migration()
	super._ready()
	_sync_room_from_persistent_state()


func _start_turn_based_combat(trigger_target: Node) -> void:
	if _encounter_id_for_actor(trigger_target) == FIRST_ROOM_ENCOUNTER_ID:
		GameState.set_flag(ROOM_ONE_COMBAT_STARTED_FLAG, true)
	super._start_turn_based_combat(trigger_target)


func _encounter_id_for_actor(actor: Node) -> String:
	var actor_id: String = _actor_id(actor)
	if actor_id in FIRST_ROOM_ACTOR_IDS:
		return FIRST_ROOM_ENCOUNTER_ID
	if actor_id in SECOND_ROOM_ACTOR_IDS:
		return SECOND_ROOM_ENCOUNTER_ID
	return super._encounter_id_for_actor(actor)


func _resolve_active_combat_encounter_if_complete() -> void:
	if _active_combat_encounter_id == FIRST_ROOM_ENCOUNTER_ID:
		_resolve_combat_room_if_complete(FIRST_ROOM_ENCOUNTER_ID, FIRST_ROOM_ACTOR_IDS, false)
		return
	if _active_combat_encounter_id == SECOND_ROOM_ENCOUNTER_ID:
		_resolve_combat_room_if_complete(SECOND_ROOM_ENCOUNTER_ID, SECOND_ROOM_ACTOR_IDS, true)
		return
	super._resolve_active_combat_encounter_if_complete()


func _evaluate_guard_post_state() -> void:
	if _two_room_resolution_in_progress or not GameState.has_method("get_encounter_status"):
		return
	_evaluate_first_room()
	_evaluate_second_room()


func get_first_room_encounter_id_for_testing() -> String:
	return FIRST_ROOM_ENCOUNTER_ID


func get_second_room_encounter_id_for_testing() -> String:
	return SECOND_ROOM_ENCOUNTER_ID


func get_first_room_outcome_for_testing() -> String:
	return str(GameState.get_flag(ROOM_ONE_OUTCOME_FLAG, ""))


func resolve_first_room_for_testing(resolution_id: String) -> void:
	if resolution_id in ["guards_subdued", "guards_defeated", "mixed_neutralization"]:
		GameState.set_flag(ROOM_ONE_COMBAT_STARTED_FLAG, true)
	_resolve_room(FIRST_ROOM_ENCOUNTER_ID, resolution_id, {
		"source_type": "test",
		"source_id": "two_room_simulation"
	})
	_sync_room_from_persistent_state()


func _evaluate_first_room() -> void:
	var status: String = str(GameState.get_encounter_status(FIRST_ROOM_ENCOUNTER_ID))
	if status == EncounterSystem.STATUS_AVAILABLE and player.global_position.x >= FIRST_ROOM_APPROACH_X:
		_begin_encounter(FIRST_ROOM_ENCOUNTER_ID, "outer_guard_room")
		status = str(GameState.get_encounter_status(FIRST_ROOM_ENCOUNTER_ID))
	if status in [EncounterSystem.STATUS_RESOLVED, EncounterSystem.STATUS_REWARDED]:
		_sync_room_from_persistent_state()
		return
	if status != EncounterSystem.STATUS_ACTIVE:
		return
	var combat_started: bool = bool(GameState.get_flag(ROOM_ONE_COMBAT_STARTED_FLAG, false))
	if (
		not combat_started
		and not _turn_system.active
		and bool(GameState.get_flag("caretaker_convinced", false))
	):
		_resolve_room(FIRST_ROOM_ENCOUNTER_ID, "peaceful_passage", {
			"source_type": "dialogue",
			"source_id": "caretaker_convinced"
		})
		_sync_room_from_persistent_state()
		return
	if (
		not combat_started
		and not _turn_system.active
		and player.global_position.x >= FIRST_ROOM_STEALTH_EXIT_X
		and _actors_calm(FIRST_ROOM_ACTOR_IDS)
	):
		_resolve_room(FIRST_ROOM_ENCOUNTER_ID, "stealth_bypass", {
			"source_type": "stealth",
			"source_id": "inner_gate_approach"
		})
		_sync_room_from_persistent_state()
		return
	var states: Dictionary = _room_actor_states(FIRST_ROOM_ACTOR_IDS)
	var resolution_id: String = _resolution_for_actor_states(states, false)
	if not resolution_id.is_empty():
		_resolve_room(FIRST_ROOM_ENCOUNTER_ID, resolution_id, {
			"source_type": "combat",
			"combat_round": _turn_system.round_number,
			"actor_states": states
		})
		_sync_room_from_persistent_state()


func _evaluate_second_room() -> void:
	var first_status: String = str(GameState.get_encounter_status(FIRST_ROOM_ENCOUNTER_ID))
	if first_status not in [EncounterSystem.STATUS_RESOLVED, EncounterSystem.STATUS_REWARDED]:
		return
	if player.global_position.x < SECOND_ROOM_ENTRY_X:
		return
	var second_status: String = str(GameState.get_encounter_status(SECOND_ROOM_ENCOUNTER_ID))
	if second_status == EncounterSystem.STATUS_AVAILABLE:
		_begin_encounter(SECOND_ROOM_ENCOUNTER_ID, "inner_watch_room")
		second_status = str(GameState.get_encounter_status(SECOND_ROOM_ENCOUNTER_ID))
	if second_status in [EncounterSystem.STATUS_RESOLVED, EncounterSystem.STATUS_REWARDED]:
		return
	if second_status != EncounterSystem.STATUS_ACTIVE:
		return
	var first_outcome: String = str(GameState.get_flag(ROOM_ONE_OUTCOME_FLAG, ""))
	match first_outcome:
		"peaceful":
			_set_inner_watch_mode("authorized")
			_resolve_room(SECOND_ROOM_ENCOUNTER_ID, "authorized_passage", {
				"source_type": "consequence",
				"source_id": "caretaker_authorization"
			})
		"combat":
			_start_inner_watch_combat()
		"stealth":
			_set_inner_watch_mode("watching")
			if (
				not _turn_system.active
				and player.global_position.x >= SECOND_ROOM_STEALTH_EXIT_X
				and _actors_calm(SECOND_ROOM_ACTOR_IDS)
			):
				_resolve_room(SECOND_ROOM_ENCOUNTER_ID, "stealth_bypass", {
					"source_type": "stealth",
					"source_id": "inner_watch_exit"
				})


func _start_inner_watch_combat() -> void:
	if _inner_watch_combat_starting or _turn_system.active:
		return
	var room: Node = _two_room_node()
	if room == null:
		return
	_inner_watch_combat_starting = true
	GameState.set_flag("vault_inner_watch_entered", true)
	if room.has_method("activate_inner_watch_combat"):
		room.call("activate_inner_watch_combat")
	var marksman: Node = room.call("get_training_marksman") if room.has_method("get_training_marksman") else null
	if is_instance_valid(marksman):
		show_combat_message("Стрелок и Рунный тактик знают о нападении на внешний караул и немедленно атакуют.", false)
		_start_turn_based_combat(marksman)
	_inner_watch_combat_starting = false


func _resolve_combat_room_if_complete(
	encounter_id: String,
	actor_ids: Array[String],
	inner_room: bool
) -> void:
	if not _combat_should_end():
		return
	var states: Dictionary = _room_actor_states(actor_ids)
	var resolution_id: String = _resolution_for_actor_states(states, inner_room)
	if resolution_id.is_empty():
		return
	_resolve_room(encounter_id, resolution_id, {
		"source_type": "combat",
		"source_id": "two_room_runtime",
		"combat_round": _turn_system.round_number,
		"actor_states": states
	})
	if encounter_id == FIRST_ROOM_ENCOUNTER_ID:
		_sync_room_from_persistent_state()


func _resolution_for_actor_states(actor_states: Dictionary, inner_room: bool) -> String:
	var actor_ids: Array[String] = SECOND_ROOM_ACTOR_IDS if inner_room else FIRST_ROOM_ACTOR_IDS
	if actor_states.size() != actor_ids.size():
		return ""
	var dead_count: int = 0
	var unconscious_count: int = 0
	for actor_id: String in actor_ids:
		var actor_state: String = str(actor_states.get(actor_id, "missing"))
		if actor_state not in ["dead", "unconscious"]:
			return ""
		dead_count += 1 if actor_state == "dead" else 0
		unconscious_count += 1 if actor_state == "unconscious" else 0
	if inner_room:
		if unconscious_count == actor_ids.size():
			return "inner_watch_subdued"
		if dead_count == actor_ids.size():
			return "inner_watch_defeated"
		return "inner_watch_mixed"
	if unconscious_count == actor_ids.size():
		return "guards_subdued"
	if dead_count == actor_ids.size():
		return "guards_defeated"
	return "mixed_neutralization"


func _resolve_room(encounter_id: String, resolution_id: String, context: Dictionary) -> void:
	if _two_room_resolution_in_progress:
		return
	_two_room_resolution_in_progress = true
	var result: Dictionary = GameState.resolve_encounter(
		encounter_id,
		resolution_id,
		context,
		true,
		true
	)
	if bool(result.get("success", false)):
		show_combat_message(str(result.get("message", "Этап караульного поста завершён.")), true)
		if _active_combat_encounter_id == encounter_id:
			_active_combat_encounter_id = ""
	_two_room_resolution_in_progress = false


func _begin_encounter(encounter_id: String, source_id: String) -> void:
	GameState.begin_encounter(encounter_id, {
		"source_type": "exploration",
		"source_id": source_id
	}, true, true)


func _room_actor_states(actor_ids: Array[String]) -> Dictionary:
	var result: Dictionary = {}
	for actor_id: String in actor_ids:
		result[actor_id] = _guard_post_actor_state(actor_id)
	return result


func _actors_calm(actor_ids: Array[String]) -> bool:
	for actor_id: String in actor_ids:
		var record: Dictionary = GameState.get_stealth_alert_record(actor_id)
		if str(record.get("state", StealthAlertSystem.STATE_CALM)) != StealthAlertSystem.STATE_CALM:
			return false
	return true


func _sync_room_from_persistent_state() -> void:
	var room: Node = _two_room_node()
	if room == null:
		return
	var outcome: String = str(GameState.get_flag(ROOM_ONE_OUTCOME_FLAG, ""))
	if not outcome.is_empty() and room.has_method("open_inner_gate"):
		room.call("open_inner_gate", outcome)
	match outcome:
		"peaceful": _set_inner_watch_mode("authorized")
		"stealth": _set_inner_watch_mode("watching")
		_: _set_inner_watch_mode("sealed")


func _set_inner_watch_mode(mode: String) -> void:
	var room: Node = _two_room_node()
	if room != null and room.has_method("set_inner_watch_mode"):
		room.call("set_inner_watch_mode", mode)


func _two_room_node() -> Node:
	return get_node_or_null("StealthTestRoom")


func _ensure_two_room_migration() -> void:
	if not bool(GameState.get_flag("vault_guard_post_resolved", false)):
		return
	if not str(GameState.get_flag(ROOM_ONE_OUTCOME_FLAG, "")).is_empty():
		return
	var migrated_outcome: String = "peaceful" if bool(GameState.get_flag("vault_guard_post_peaceful", false)) else "combat"
	if bool(GameState.get_flag("vault_guard_post_stealth", false)):
		migrated_outcome = "stealth"
	GameState.set_flag(ROOM_ONE_OUTCOME_FLAG, migrated_outcome)
	GameState.set_flag(ROOM_ONE_COMBAT_STARTED_FLAG, migrated_outcome == "combat")
	GameState.set_flag(INNER_GATE_OPEN_FLAG, true)
	GameState.set_flag(ROOM_ONE_HOSTILE_FLAG, migrated_outcome == "combat")
