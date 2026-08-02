extends "res://scripts/game/game_guard_post_player_feedback_runtime.gd"

const EXPLORATION_MOVEMENT_STATIONARY: String = "stationary"
const EXPLORATION_MOVEMENT_PATROL: String = "patrol"
const STEP_NOISE_TYPES: Array[String] = ["quiet_step", "normal_step", "running_step"]
const VISIBLE_STANDOFF_PIXELS: float = 82.0
const VISIBLE_APPROACH_SPEED_MULTIPLIER: float = 0.72

const PEACEFUL_AUTHORIZATION_BROKEN_FLAG: String = "vault_guard_post_peaceful_authorization_broken"
const INNER_WATCH_BETRAYAL_RESOLVED_FLAG: String = "vault_inner_watch_betrayal_resolved"
const INNER_WATCH_BETRAYAL_RUNTIME_ID: String = "vault_inner_watch_betrayal_consequence"
const FIRST_ROOM_OUTCOME_FLAG_LOCAL: String = "vault_guard_post_room1_outcome"
const FIRST_ROOM_COMBAT_STARTED_FLAG_LOCAL: String = "vault_guard_post_room1_combat_started"
const INNER_GATE_OPEN_FLAG_LOCAL: String = "vault_inner_gate_open"
const FIRST_ROOM_ACTOR_IDS_LOCAL: Array[String] = ["caretaker", "service_guard"]
const SECOND_ROOM_ACTOR_IDS_LOCAL: Array[String] = ["training_marksman", "training_mage"]
const SECOND_ROOM_ENTRY_X_LOCAL: float = 941.0
const SECOND_ROOM_ENCOUNTER_ID_LOCAL: String = "vault_inner_watch_01"

var _inner_watch_betrayal_starting: bool = false
var _inner_watch_betrayal_combat_active: bool = false


func _on_feedback_catalog_action_requested(action_id: String) -> void:
	# Hide opens a blocking d20 result. Remove the catalog first so two modal
	# layers are never visible at the same time on Android.
	if action_id in ["hide", "exploration_hide"]:
		_close_action_catalog_immediately()
	super._on_feedback_catalog_action_requested(action_id)


func _on_feedback_hide_requested() -> void:
	_close_action_catalog_immediately()
	super._on_feedback_hide_requested()


func _evaluate_guard_post_state() -> void:
	_ensure_peaceful_authorization_consequence()
	super._evaluate_guard_post_state()


func _evaluate_second_room() -> void:
	if not _peaceful_authorization_is_broken():
		super._evaluate_second_room()
		return
	if player == null or player.global_position.x < SECOND_ROOM_ENTRY_X_LOCAL:
		return
	if bool(GameState.get_flag(INNER_WATCH_BETRAYAL_RESOLVED_FLAG, false)):
		return
	var states: Dictionary = _room_actor_states(SECOND_ROOM_ACTOR_IDS_LOCAL)
	if not _resolution_for_actor_states(states, true).is_empty():
		GameState.set_flag(INNER_WATCH_BETRAYAL_RESOLVED_FLAG, true)
		GameState.save_game()
		return
	var second_status: String = str(GameState.get_encounter_status(SECOND_ROOM_ENCOUNTER_ID_LOCAL))
	if second_status == EncounterSystem.STATUS_AVAILABLE:
		_begin_encounter(SECOND_ROOM_ENCOUNTER_ID_LOCAL, "inner_watch_betrayal")
		second_status = str(GameState.get_encounter_status(SECOND_ROOM_ENCOUNTER_ID_LOCAL))
	if second_status == EncounterSystem.STATUS_ACTIVE:
		_start_inner_watch_combat()
		return
	# The original inner encounter may already be resolved as authorized_passage.
	# Do not reopen or reward it again; run a separate consequence combat instead.
	if second_status in [EncounterSystem.STATUS_RESOLVED, EncounterSystem.STATUS_REWARDED]:
		_start_authorized_betrayal_combat()


func _sync_room_from_persistent_state() -> void:
	if not _peaceful_authorization_is_broken():
		super._sync_room_from_persistent_state()
		return
	var room: Node = _two_room_node()
	if room == null:
		return
	var gate_state: String = ""
	if room.has_method("get_inner_gate"):
		var gate: Node = room.call("get_inner_gate") as Node
		if is_instance_valid(gate) and gate.has_method("get_door_state"):
			gate_state = str(gate.call("get_door_state"))
	if gate_state in ["", "locked"] and room.has_method("open_inner_gate"):
		room.call("open_inner_gate", "peaceful_authorization_broken")
	# Never restore MODE_AUTHORIZED after the player has attacked the authorized
	# outer guard. Once the inner squad has been activated, preserve that mode.
	if (
		_inner_watch_betrayal_combat_active
		or (_turn_system.active and _active_combat_encounter_id == INNER_WATCH_BETRAYAL_RUNTIME_ID)
		or (player != null and player.global_position.x >= SECOND_ROOM_ENTRY_X_LOCAL)
	):
		_set_inner_watch_mode("hostile")


func _resolve_active_combat_encounter_if_complete() -> void:
	if (
		_inner_watch_betrayal_combat_active
		or _active_combat_encounter_id == INNER_WATCH_BETRAYAL_RUNTIME_ID
	):
		if not _combat_should_end():
			return
		_inner_watch_betrayal_combat_active = false
		_inner_watch_betrayal_starting = false
		_active_combat_encounter_id = ""
		GameState.set_flag(INNER_WATCH_BETRAYAL_RESOLVED_FLAG, true)
		GameState.save_game()
		_stop_turn_based_combat(
			"Внутренний дозор уничтожен после нарушения мирной договорённости. Повторная награда за проход не начисляется."
		)
		return
	super._resolve_active_combat_encounter_if_complete()


func is_peaceful_authorization_broken_for_testing() -> bool:
	return _peaceful_authorization_is_broken()


func get_inner_watch_betrayal_runtime_id_for_testing() -> String:
	return INNER_WATCH_BETRAYAL_RUNTIME_ID


func _ensure_peaceful_authorization_consequence() -> void:
	if _peaceful_authorization_is_broken():
		return
	if str(GameState.get_flag(FIRST_ROOM_OUTCOME_FLAG_LOCAL, "")) != "peaceful":
		return
	var authorization_broken: bool = bool(
		GameState.get_flag(FIRST_ROOM_COMBAT_STARTED_FLAG_LOCAL, false)
	)
	if not authorization_broken:
		var states: Dictionary = _room_actor_states(FIRST_ROOM_ACTOR_IDS_LOCAL)
		for actor_id: String in FIRST_ROOM_ACTOR_IDS_LOCAL:
			if str(states.get(actor_id, "active")) in ["dead", "unconscious"]:
				authorization_broken = true
				break
	if not authorization_broken:
		return
	GameState.set_flag(PEACEFUL_AUTHORIZATION_BROKEN_FLAG, true)
	GameState.set_flag("vault_inner_watch_hostile", true)
	GameState.set_flag(INNER_GATE_OPEN_FLAG_LOCAL, true)
	GameState.save_game()


func _peaceful_authorization_is_broken() -> bool:
	return bool(GameState.get_flag(PEACEFUL_AUTHORIZATION_BROKEN_FLAG, false))


func _start_authorized_betrayal_combat() -> void:
	if (
		_inner_watch_betrayal_starting
		or _inner_watch_betrayal_combat_active
		or _turn_system.active
	):
		return
	var room: Node = _two_room_node()
	if room == null:
		return
	var marksman: Node = room.call("get_training_marksman") if room.has_method("get_training_marksman") else null
	var mage: Node = room.call("get_training_mage") if room.has_method("get_training_mage") else null
	if not is_instance_valid(marksman) or not is_instance_valid(mage):
		return
	_inner_watch_betrayal_starting = true
	if room.has_method("activate_inner_watch_combat"):
		room.call("activate_inner_watch_combat")
	_prepare_inner_watch_combatants()
	show_combat_message(
		"Стрелок и Рунный тактик узнают о нападении после мирного прохода и отзывают разрешение.",
		false
	)
	_inner_watch_betrayal_combat_active = true
	_start_turn_based_combat(marksman)
	if _turn_system.active:
		_active_combat_encounter_id = INNER_WATCH_BETRAYAL_RUNTIME_ID
	else:
		_inner_watch_betrayal_combat_active = false
	_inner_watch_betrayal_starting = false


func _update_exploration_actor(actor: Node, delta: float) -> void:
	if actor == null or not is_instance_valid(actor) or not (actor is Node2D):
		return
	var actor_id: String = str(actor.call("get_actor_id"))
	var profile: Dictionary = _stealth_alerts.get_profile(actor_id)
	if profile.is_empty():
		return
	var record: Dictionary = _record_for_actor(actor_id)
	record["step_retarget_cooldown_seconds"] = maxf(
		float(record.get("step_retarget_cooldown_seconds", 0.0)) - maxf(delta, 0.0),
		0.0
	)
	var visible: bool = _exploration_actor_can_see_player(actor, profile)
	var hiding_spot: Dictionary = _stealth_alerts.get_hiding_spot_at(player.global_position)
	var target_hidden: bool = _exploration_hidden and not hiding_spot.is_empty()
	record = _stealth_alerts.apply_visual_observation(
		record,
		visible,
		target_hidden,
		player.global_position,
		delta,
		profile
	)
	if visible:
		if _exploration_hidden and hiding_spot.is_empty():
			_break_exploration_hidden("NPC заметил героя вне укромного места.")
		record = _advance_visible_actor_behavior(actor, record, profile, delta)
	else:
		record = _advance_unseen_actor_behavior(actor, record, profile, delta)
	_alert_records[actor_id] = record
	_apply_record_to_actor(actor, record)
	if str(record.get("state", "")) == StealthAlertSystem.STATE_ALERTED and visible:
		_begin_combat_from_alert(actor, record)


func _advance_visible_actor_behavior(
	actor: Node,
	record: Dictionary,
	profile: Dictionary,
	delta: float
) -> Dictionary:
	var movement_mode: String = str(profile.get("movement_mode", EXPLORATION_MOVEMENT_PATROL))
	if movement_mode == EXPLORATION_MOVEMENT_STATIONARY:
		_face_actor_toward(actor, player.global_position)
		return record
	var state_name: String = str(record.get("state", StealthAlertSystem.STATE_CALM))
	# A calm or merely suspicious patrol does not freeze because the hero entered
	# its cone. It keeps its authored route until a real investigation begins.
	if state_name in [StealthAlertSystem.STATE_CALM, StealthAlertSystem.STATE_SUSPICIOUS]:
		return _advance_actor_patrol(actor, record, delta)
	return _move_actor_to_visible_standoff(actor, record, profile, delta)


func _advance_unseen_actor_behavior(
	actor: Node,
	record: Dictionary,
	profile: Dictionary,
	delta: float
) -> Dictionary:
	var movement_mode: String = str(profile.get("movement_mode", EXPLORATION_MOVEMENT_PATROL))
	var state_name: String = str(record.get("state", StealthAlertSystem.STATE_CALM))
	if movement_mode == EXPLORATION_MOVEMENT_STATIONARY:
		if state_name in [
			StealthAlertSystem.STATE_INVESTIGATING,
			StealthAlertSystem.STATE_SEARCHING,
			StealthAlertSystem.STATE_ALERTED
		]:
			_face_actor_toward(
				actor,
				_stealth_alerts.vector_from_value(record.get("last_known_position", []))
			)
			# A stationary post searches by watching and listening; it never abandons
			# its authored position to walk after the player.
			return _stealth_alerts.advance_search(record, delta, true, profile)
		return record
	if state_name in [StealthAlertSystem.STATE_CALM, StealthAlertSystem.STATE_SUSPICIOUS]:
		return _advance_actor_patrol(actor, record, delta)
	return _advance_actor_investigation(actor, record, profile, delta)


func _advance_actor_investigation(
	actor: Node,
	record: Dictionary,
	profile: Dictionary,
	delta: float
) -> Dictionary:
	var state_name: String = str(record.get("state", StealthAlertSystem.STATE_CALM))
	if state_name not in [
		StealthAlertSystem.STATE_INVESTIGATING,
		StealthAlertSystem.STATE_SEARCHING,
		StealthAlertSystem.STATE_ALERTED
	]:
		return record
	var target_position: Vector2 = _stealth_alerts.vector_from_value(
		record.get("last_known_position", [])
	)
	var actor_node: Node2D = actor as Node2D
	if str(profile.get("movement_mode", EXPLORATION_MOVEMENT_PATROL)) == EXPLORATION_MOVEMENT_STATIONARY:
		_face_actor_toward(actor, target_position)
		return _stealth_alerts.advance_search(record, delta, true, profile)
	var updated: Dictionary = record.duplicate(true)
	if _npc_navigation == null:
		updated["navigation_used"] = false
		updated["navigation_blocked"] = true
		return updated
	var movement: Dictionary = _npc_navigation.move_actor(
		actor_node,
		target_position,
		maxf(float(profile.get("investigation_speed_pixels", 90.0)), 0.0),
		delta
	)
	updated["navigation_used"] = true
	updated["navigation_blocked"] = bool(movement.get("blocked", false))
	var direction: Vector2 = movement.get("direction", Vector2.ZERO) as Vector2
	if direction.length_squared() > 0.0001 and actor.has_method("set_facing_direction"):
		actor.call("set_facing_direction", direction)
	var reached: bool = (
		bool(movement.get("reached", false))
		or actor_node.global_position.distance_to(target_position) <= SEARCH_REACHED_DISTANCE_PIXELS
	)
	return _stealth_alerts.advance_search(updated, delta, reached, profile)


func _move_actor_to_visible_standoff(
	actor: Node,
	record: Dictionary,
	profile: Dictionary,
	delta: float
) -> Dictionary:
	var actor_node: Node2D = actor as Node2D
	var away: Vector2 = actor_node.global_position - player.global_position
	if away.length_squared() <= 0.0001:
		away = Vector2.LEFT
	var target_position: Vector2 = (
		player.global_position
		+ away.normalized() * float(profile.get("visible_standoff_pixels", VISIBLE_STANDOFF_PIXELS))
	)
	var updated: Dictionary = record.duplicate(true)
	if _npc_navigation == null:
		_face_actor_toward(actor, player.global_position)
		updated["navigation_used"] = false
		updated["navigation_blocked"] = true
		return updated
	var movement: Dictionary = _npc_navigation.move_actor(
		actor_node,
		target_position,
		maxf(float(profile.get("investigation_speed_pixels", 90.0)), 0.0)
			* float(profile.get("visible_speed_multiplier", VISIBLE_APPROACH_SPEED_MULTIPLIER)),
		delta
	)
	updated["navigation_used"] = true
	updated["navigation_blocked"] = bool(movement.get("blocked", false))
	var direction: Vector2 = movement.get("direction", Vector2.ZERO) as Vector2
	if direction.length_squared() > 0.0001:
		actor.call("set_facing_direction", direction)
	else:
		_face_actor_toward(actor, player.global_position)
	return updated


func _on_stealth_noise_reported(noise_event: Dictionary) -> void:
	_last_noise_sequence = maxi(_last_noise_sequence, int(noise_event.get("sequence", 0)))
	for actor: Node in _exploration_alert_actors():
		var actor_id: String = str(actor.call("get_actor_id"))
		var profile: Dictionary = _stealth_alerts.get_profile(actor_id)
		var actor_position: Vector2 = (actor as Node2D).global_position
		var actor_room_id: String = _stealth_alerts.get_room_id_at(actor_position)
		if not _stealth_alerts.actor_hears_noise(
			GameState,
			actor_position,
			actor_room_id,
			noise_event,
			profile
		):
			continue
		var current: Dictionary = _record_for_actor(actor_id)
		var previous_target: Vector2 = _stealth_alerts.vector_from_value(
			current.get("last_known_position", [])
		)
		var state_name: String = str(current.get("state", StealthAlertSystem.STATE_CALM))
		var noise_type: String = str(noise_event.get("noise_type", "unknown"))
		var is_step_noise: bool = noise_type in STEP_NOISE_TYPES
		var target_is_active: bool = (
			state_name in [StealthAlertSystem.STATE_INVESTIGATING, StealthAlertSystem.STATE_ALERTED]
			and previous_target != Vector2.ZERO
			and actor_position.distance_to(previous_target) > SEARCH_REACHED_DISTANCE_PIXELS
		)
		var retarget_cooldown: float = float(
			current.get("step_retarget_cooldown_seconds", 0.0)
		)
		var preserve_target: bool = is_step_noise and (
			target_is_active or retarget_cooldown > 0.0
		)
		var updated: Dictionary = _stealth_alerts.apply_noise(current, noise_event, profile)
		if preserve_target:
			updated["last_known_position"] = _stealth_alerts.vector_to_value(previous_target)
		else:
			updated["step_retarget_cooldown_seconds"] = float(
				profile.get("step_retarget_cooldown_seconds", 1.5)
			) if is_step_noise else 0.0
		updated["stimulus_kind"] = "step" if is_step_noise else "noise"
		_alert_records[actor_id] = updated
		_apply_record_to_actor(actor, updated)
		_persist_alert_record(actor_id, false)


func _face_actor_toward(actor: Node, target_position: Vector2) -> void:
	if actor == null or not is_instance_valid(actor) or not actor is Node2D:
		return
	var direction: Vector2 = target_position - (actor as Node2D).global_position
	if direction.length_squared() > 0.0001 and actor.has_method("set_facing_direction"):
		actor.call("set_facing_direction", direction)
