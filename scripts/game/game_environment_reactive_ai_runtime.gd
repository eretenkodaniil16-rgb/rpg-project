extends "res://scripts/game/game_nonlethal_restraints_runtime.gd"

const ENVIRONMENT_AI_SCRIPT: Script = preload("res://scripts/systems/environment_reactive_npc_ai_system.gd")
const ENVIRONMENT_EVENTS_SCRIPT: Script = preload("res://scripts/systems/environment_event_system.gd")
const BODY_MOVEMENT_EVENT_DISTANCE_PIXELS: float = 20.0

var _environment_ai: EnvironmentReactiveNpcAiSystem
var _environment_events: EnvironmentEventSystem = ENVIRONMENT_EVENTS_SCRIPT.new() as EnvironmentEventSystem
var _environment_context_by_actor: Dictionary = {}
var _door_state_snapshot: Dictionary = {}
var _body_environment_snapshot: Dictionary = {}


func _ready() -> void:
	super._ready()
	_environment_ai = ENVIRONMENT_AI_SCRIPT.new() as EnvironmentReactiveNpcAiSystem
	_advanced_ai = _environment_ai
	_combat_ai = _environment_ai
	_npc_ai = _environment_ai
	_snapshot_environment_bodies(false)


func _process(delta: float) -> void:
	var combat_before: bool = _turn_system.active
	super._process(delta)
	_snapshot_environment_bodies(true)
	if combat_before and not _turn_system.active:
		_environment_events.clear_combat_memory()
		_environment_context_by_actor.clear()


func report_environment_change(event_type: String, world_position: Vector2, payload: Dictionary = {}) -> Dictionary:
	var severity: float = float(payload.get("severity", 1.0))
	var audible_radius: int = int(payload.get("audible_radius_feet", _default_environment_audible_radius(event_type)))
	var visible_radius: int = int(payload.get("visible_radius_feet", _default_environment_visible_radius(event_type)))
	var round_number: int = _turn_system.round_number if _turn_system != null and _turn_system.active else 0
	return _environment_events.report_event(
		event_type,
		world_position,
		payload,
		severity,
		audible_radius,
		visible_radius,
		round_number
	)


func on_stealth_door_state_changed(door_id: String, door_state: String) -> void:
	super.on_stealth_door_state_changed(door_id, door_state)
	var previous: String = str(_door_state_snapshot.get(door_id, ""))
	_door_state_snapshot[door_id] = door_state
	if previous.is_empty() or previous == door_state:
		return
	var door: Node2D = _find_environment_door(door_id)
	var position: Vector2 = door.global_position if door != null else Vector2.ZERO
	var event_type: String = ""
	match door_state:
		"open": event_type = EnvironmentEventSystem.EVENT_PASSAGE_OPENED
		"broken": event_type = EnvironmentEventSystem.EVENT_DOOR_BROKEN
		"closed", "locked", "blocked": event_type = EnvironmentEventSystem.EVENT_DOOR_CLOSED
	if event_type.is_empty():
		return
	report_environment_change(event_type, position, {
		"door_id": door_id,
		"previous_state": previous,
		"door_state": door_state,
		"severity": 1.3 if door_state == "broken" else 1.0,
		"audible_radius_feet": 100 if door_state == "broken" else 65,
		"visible_radius_feet": 90
	})


func get_environment_event_system_for_testing() -> EnvironmentEventSystem:
	return _environment_events


func get_environment_decision_for_testing(actor_id: String) -> Dictionary:
	var context_value: Variant = _environment_context_by_actor.get(actor_id, {})
	if not context_value is Dictionary or _environment_ai == null:
		return {}
	return _environment_ai.choose_combat_intent(actor_id, context_value as Dictionary)


func _enrich_advanced_context(
	context: Dictionary,
	actor_node: Node2D,
	actor: Node,
	actor_id: String,
	profile: Dictionary,
	observation: Dictionary
) -> void:
	super._enrich_advanced_context(context, actor_node, actor, actor_id, profile, observation)
	if _environment_ai == null:
		return
	var environment_profile: Dictionary = _environment_ai.get_environment_profile(actor_id, profile)
	var visibility_check := func(position: Vector2) -> bool:
		return _combat_environment == null or _combat_environment.has_line_of_sight(actor_node.global_position, position)
	var event: Dictionary = _environment_events.latest_perceived_event(
		actor_id,
		actor_node.global_position,
		_turn_system.round_number,
		maxi(int(environment_profile.get("event_memory_rounds", 3)), 0),
		visibility_check,
		maxi(int(environment_profile.get("perception_feet", 60)), 0),
		maxi(int(environment_profile.get("hearing_feet", 70)), 0)
	)
	if event.is_empty():
		_environment_context_by_actor[actor_id] = context.duplicate(true)
		return
	var payload: Dictionary = event.get("payload", {}) as Dictionary if event.get("payload", {}) is Dictionary else {}
	var distance_feet: int = maxi(int(event.get("distance_feet", 0)), 0)
	var event_position: Vector2 = event.get("position", actor_node.global_position) as Vector2
	var event_type: String = str(event.get("type", ""))
	var actor_squad: String = str(profile.get("squad_id", ""))
	var event_squad: String = str(payload.get("squad_id", ""))
	context["environment_event"] = event
	context["environment_relevance"] = clampf(1.0 - float(distance_feet) / 120.0, 0.2, 1.0)
	context["actor_in_environment_hazard"] = _combat_environment != null and _combat_environment.has_method("is_hazardous_position") and bool(_combat_environment.call("is_hazardous_position", actor_node.global_position))
	context["environment_cover_compromised"] = event_type == EnvironmentEventSystem.EVENT_COVER_DESTROYED and distance_feet <= 30
	context["environment_passage_relevant"] = event_type in [EnvironmentEventSystem.EVENT_PASSAGE_OPENED, EnvironmentEventSystem.EVENT_DOOR_BROKEN, EnvironmentEventSystem.EVENT_DOOR_CLOSED] and distance_feet <= 40
	context["environment_same_squad"] = not actor_squad.is_empty() and actor_squad == event_squad
	context["environment_event_position"] = event_position
	_environment_context_by_actor[actor_id] = context.duplicate(true)
	_environment_events.acknowledge(actor_id, str(event.get("event_id", "")))
	show_combat_message("%s замечает изменение окружения: %s." % [_target_name(actor), _environment_event_label(event_type)], false)


func _objective_for_advanced_intent(actor: Node, guard_anchor: Vector2, target_position: Vector2, intent_id: String) -> Vector2:
	var actor_id: String = str(actor.call("get_actor_id")) if actor != null and actor.has_method("get_actor_id") else ""
	var context_value: Variant = _environment_context_by_actor.get(actor_id, {})
	if not actor_id.is_empty() and context_value is Dictionary and _environment_ai != null:
		var decision: Dictionary = _environment_ai.choose_combat_intent(actor_id, context_value as Dictionary)
		var action: String = str(decision.get("environment_action", ""))
		var event_position: Vector2 = decision.get("environment_event_position", target_position) as Vector2
		if action == EnvironmentReactiveNpcAiSystem.ACTION_AVOID_HAZARD and actor is Node2D:
			var away: Vector2 = (actor as Node2D).global_position - event_position
			if away.length_squared() <= 0.0001:
				away = Vector2.RIGHT
			return (actor as Node2D).global_position + away.normalized() * 192.0
		if action in [
			EnvironmentReactiveNpcAiSystem.ACTION_EXPLOIT_OPENING,
			EnvironmentReactiveNpcAiSystem.ACTION_SECURE_PASSAGE,
			EnvironmentReactiveNpcAiSystem.ACTION_HOLD_BREACH,
			EnvironmentReactiveNpcAiSystem.ACTION_INVESTIGATE_CHANGE,
			EnvironmentReactiveNpcAiSystem.ACTION_RESCUE_ALLY,
			EnvironmentReactiveNpcAiSystem.ACTION_GUARD_PASSAGE
		]:
			return event_position
	return super._objective_for_advanced_intent(actor, guard_anchor, target_position, intent_id)


func _execute_combat_ai_path(actor: Node2D, path: Array, intent_id: String) -> void:
	await super._execute_combat_ai_path(actor, path, intent_id)
	if actor == null or not actor.has_method("get_actor_id") or _environment_ai == null:
		return
	var actor_id: String = str(actor.call("get_actor_id"))
	var context_value: Variant = _environment_context_by_actor.get(actor_id, {})
	if not context_value is Dictionary:
		return
	var decision: Dictionary = _environment_ai.choose_combat_intent(actor_id, context_value as Dictionary)
	if str(decision.get("environment_action", "")) != EnvironmentReactiveNpcAiSystem.ACTION_SECURE_PASSAGE:
		return
	var context: Dictionary = context_value as Dictionary
	var event: Dictionary = context.get("environment_event", {}) as Dictionary if context.get("environment_event", {}) is Dictionary else {}
	var payload: Dictionary = event.get("payload", {}) as Dictionary if event.get("payload", {}) is Dictionary else {}
	var door_id: String = str(payload.get("door_id", ""))
	var door: Node2D = _find_environment_door(door_id)
	if door == null or DistanceSystem.distance_feet(actor.global_position, door.global_position) > 10:
		return
	if door.has_method("get_door_state") and str(door.call("get_door_state")) == "open" and door.has_method("set_door_state"):
		door.call("set_door_state", "closed", true)
		show_combat_message("%s закрывает проход, восстанавливая оборонительную линию." % _target_name(actor), true)


func _combat_ai_cell_is_available(grid: BattleGrid, cell: Vector2i, occupied: Dictionary) -> bool:
	if not super._combat_ai_cell_is_available(grid, cell, occupied):
		return false
	return _combat_environment == null or not _combat_environment.has_method("is_hazardous_cell") or not bool(_combat_environment.call("is_hazardous_cell", grid, cell))


func _snapshot_environment_bodies(report_changes: bool) -> void:
	var current_ids: Dictionary = {}
	for body: Node in get_tree().get_nodes_in_group("visible_bodies"):
		if not is_instance_valid(body) or not body is Node2D or not body.has_method("get_body_actor_id"):
			continue
		var actor_id: String = str(body.call("get_body_actor_id"))
		if actor_id.is_empty():
			continue
		var position: Vector2 = (body as Node2D).global_position
		var bound: bool = body.has_method("is_bound_body") and bool(body.call("is_bound_body"))
		var previous_value: Variant = _body_environment_snapshot.get(actor_id, {})
		var previous: Dictionary = previous_value as Dictionary if previous_value is Dictionary else {}
		if report_changes and not previous.is_empty():
			var previous_position: Vector2 = previous.get("position", position) as Vector2
			if previous_position.distance_to(position) >= BODY_MOVEMENT_EVENT_DISTANCE_PIXELS:
				report_environment_change(EnvironmentEventSystem.EVENT_BODY_MOVED, position, {
					"actor_id": actor_id,
					"squad_id": _environment_actor_squad(actor_id),
					"audible_radius_feet": 35,
					"visible_radius_feet": 70
				})
			if bound and not bool(previous.get("bound", false)):
				report_environment_change(EnvironmentEventSystem.EVENT_ALLY_BOUND, position, {
					"actor_id": actor_id,
					"squad_id": _environment_actor_squad(actor_id),
					"audible_radius_feet": 20,
					"visible_radius_feet": 80,
					"severity": 1.4
				})
		_body_environment_snapshot[actor_id] = {"position": position, "bound": bound}
		current_ids[actor_id] = true
	for actor_key: Variant in _body_environment_snapshot.keys():
		if not current_ids.has(str(actor_key)):
			_body_environment_snapshot.erase(actor_key)


func _environment_actor_squad(actor_id: String) -> String:
	if _environment_ai == null:
		return ""
	return str(_environment_ai.get_profile(actor_id).get("squad_id", ""))


func _find_environment_door(door_id: String) -> Node2D:
	if door_id.is_empty():
		return null
	for door: Node in get_tree().get_nodes_in_group("stealth_doors"):
		if door is Node2D and door.has_method("get_door_id") and str(door.call("get_door_id")) == door_id:
			return door as Node2D
	return null


func _default_environment_audible_radius(event_type: String) -> int:
	match event_type:
		EnvironmentEventSystem.EVENT_DOOR_BROKEN: return 100
		EnvironmentEventSystem.EVENT_COVER_DESTROYED: return 90
		EnvironmentEventSystem.EVENT_PASSAGE_OPENED, EnvironmentEventSystem.EVENT_DOOR_CLOSED: return 60
		EnvironmentEventSystem.EVENT_HAZARD_ADDED: return 35
		EnvironmentEventSystem.EVENT_BODY_MOVED: return 30
		_: return 0


func _default_environment_visible_radius(event_type: String) -> int:
	match event_type:
		EnvironmentEventSystem.EVENT_HAZARD_ADDED, EnvironmentEventSystem.EVENT_COVER_DESTROYED: return 100
		EnvironmentEventSystem.EVENT_DOOR_BROKEN, EnvironmentEventSystem.EVENT_PASSAGE_OPENED: return 90
		EnvironmentEventSystem.EVENT_BODY_MOVED, EnvironmentEventSystem.EVENT_ALLY_BOUND: return 80
		_: return 65


func _environment_event_label(event_type: String) -> String:
	return {
		EnvironmentEventSystem.EVENT_HAZARD_ADDED: "появилась опасная зона",
		EnvironmentEventSystem.EVENT_HAZARD_REMOVED: "опасная зона исчезла",
		EnvironmentEventSystem.EVENT_COVER_DESTROYED: "укрытие разрушено",
		EnvironmentEventSystem.EVENT_COVER_RESTORED: "укрытие восстановлено",
		EnvironmentEventSystem.EVENT_PASSAGE_OPENED: "проход открыт",
		EnvironmentEventSystem.EVENT_DOOR_CLOSED: "проход закрыт",
		EnvironmentEventSystem.EVENT_DOOR_BROKEN: "дверь разрушена",
		EnvironmentEventSystem.EVENT_BODY_MOVED: "тело перемещено",
		EnvironmentEventSystem.EVENT_ALLY_BOUND: "союзник связан"
	}.get(event_type, event_type)
