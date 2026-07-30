extends "res://scripts/game/game_environment_reactive_ai_runtime.gd"

const SQUAD_AI_SCRIPT: Script = preload("res://scripts/systems/squad_plan_npc_ai_system.gd")
const SQUAD_PLANS_SCRIPT: Script = preload("res://scripts/systems/squad_tactical_plan_system.gd")
const SQUAD_FLANK_OFFSET_PIXELS: float = 118.0
const SQUAD_REAR_OFFSET_PIXELS: float = 176.0
const SQUAD_SEARCH_OFFSET_PIXELS: float = 132.0

var _squad_ai: SquadPlanNpcAiSystem
var _squad_plans: SquadTacticalPlanSystem = SQUAD_PLANS_SCRIPT.new() as SquadTacticalPlanSystem
var _squad_assignment_by_actor: Dictionary = {}
var _squad_objective_by_actor: Dictionary = {}
var _squad_reserved_cells: Dictionary = {}
var _active_planning_actor_id: String = ""
var _reservation_round: int = -1
var _announced_plan_by_squad: Dictionary = {}


func _ready() -> void:
	super._ready()
	_squad_ai = SQUAD_AI_SCRIPT.new() as SquadPlanNpcAiSystem
	_environment_ai = _squad_ai
	_advanced_ai = _squad_ai
	_combat_ai = _squad_ai
	_npc_ai = _squad_ai


func _process(delta: float) -> void:
	var combat_before: bool = _turn_system.active
	super._process(delta)
	if combat_before and not _turn_system.active:
		_clear_squad_plan_runtime()


func _enrich_advanced_context(
	context: Dictionary,
	actor_node: Node2D,
	actor: Node,
	actor_id: String,
	profile: Dictionary,
	observation: Dictionary
) -> void:
	super._enrich_advanced_context(context, actor_node, actor, actor_id, profile, observation)
	if _squad_ai == null or _squad_plans == null:
		return
	var squad_id: String = str(profile.get("squad_id", ""))
	if squad_id.is_empty():
		return
	_reset_reservations_if_new_round()
	var squad_context: Dictionary = _build_squad_plan_context(actor, actor_id, profile, context)
	var plan: Dictionary = _squad_plans.evaluate_squad_plan(squad_id, _turn_system.round_number, squad_context)
	if plan.is_empty():
		_squad_assignment_by_actor.erase(actor_id)
		return
	var actor_ids: Array[String] = []
for member_id_value: Variant in squad_context.get("member_ids", []) as Array:
    actor_ids.append(str(member_id_value))
	var actor_index: int = maxi(actor_ids.find(actor_id), 0)
	var assignment: Dictionary = _squad_plans.get_actor_assignment(
		squad_id,
		actor_id,
		str(profile.get("role", NpcCombatAiSystem.ROLE_MELEE)),
		actor_index,
		_turn_system.round_number
	)
	if assignment.is_empty():
		return
	context["squad_plan"] = plan
	context["squad_plan_assignment"] = assignment
	context["squad_plan_id"] = str(plan.get("plan_id", ""))
	context["squad_plan_phase"] = str(plan.get("phase", ""))
	_squad_assignment_by_actor[actor_id] = assignment.duplicate(true)
	_environment_context_by_actor[actor_id] = context.duplicate(true)
	_announce_squad_plan_if_needed(squad_id, plan, actor)


func get_squad_plan_for_testing(squad_id: String) -> Dictionary:
	return _squad_plans.get_active_plan(squad_id) if _squad_plans != null else {}


func get_squad_assignment_for_testing(actor_id: String) -> Dictionary:
	var value: Variant = _squad_assignment_by_actor.get(actor_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func get_squad_plan_decision_for_testing(actor_id: String) -> Dictionary:
	var context_value: Variant = _environment_context_by_actor.get(actor_id, {})
	if _squad_ai == null or not context_value is Dictionary:
		return {}
	return _squad_ai.choose_combat_intent(actor_id, context_value as Dictionary)


func record_squad_plan_outcome_for_testing(actor_id: String, success: bool) -> void:
	var assignment: Dictionary = get_squad_assignment_for_testing(actor_id)
	if assignment.is_empty() or _squad_plans == null:
		return
	_squad_plans.record_actor_outcome(
		str(assignment.get("squad_id", "")),
		actor_id,
		str(assignment.get("action", "")),
		_turn_system.round_number,
		success
	)


func _objective_for_advanced_intent(actor: Node, guard_anchor: Vector2, target_position: Vector2, intent_id: String) -> Vector2:
	if actor == null or not actor.has_method("get_actor_id") or not actor is Node2D:
		return super._objective_for_advanced_intent(actor, guard_anchor, target_position, intent_id)
	var actor_id: String = str(actor.call("get_actor_id"))
	var assignment_value: Variant = _squad_assignment_by_actor.get(actor_id, {})
	if not assignment_value is Dictionary or (assignment_value as Dictionary).is_empty():
		return super._objective_for_advanced_intent(actor, guard_anchor, target_position, intent_id)
	var assignment: Dictionary = assignment_value as Dictionary
	var objective_id: String = str(assignment.get("objective", ""))
	var slot: String = str(assignment.get("slot", "front"))
	var actor_node: Node2D = actor as Node2D
	var objective: Vector2 = target_position
	match objective_id:
		"bound_ally":
			objective = _bound_ally_position(str(assignment.get("squad_id", "")), target_position)
		"passage":
			objective = _squad_environment_event_position(actor_id, guard_anchor)
		"fallback_line":
			objective = _fallback_line_position(actor_node.global_position, guard_anchor, target_position, slot)
		"target_flank":
			objective = _target_slot_position(actor_node.global_position, target_position, slot, SQUAD_FLANK_OFFSET_PIXELS)
		"target_front":
			objective = _target_slot_position(actor_node.global_position, target_position, slot, 58.0)
		"target_rear":
			objective = _target_slot_position(actor_node.global_position, target_position, slot, SQUAD_REAR_OFFSET_PIXELS)
		"memory_sector":
			objective = target_position + _absolute_slot_offset(slot, SQUAD_SEARCH_OFFSET_PIXELS)
		"memory_rear":
			objective = target_position + _absolute_slot_offset("rear", SQUAD_SEARCH_OFFSET_PIXELS)
		"nearest_ally":
			var ally: Node2D = _nearest_living_ally(actor)
			objective = ally.global_position if ally != null else guard_anchor
		_:
			return super._objective_for_advanced_intent(actor, guard_anchor, target_position, intent_id)
	_squad_objective_by_actor[actor_id] = objective
	return objective


func _plan_combat_ai_movement(
	actor_node: Node2D,
	actor: Node,
	profile: Dictionary,
	guard_anchor: Vector2,
	objective_position: Vector2,
	intent_id: String,
	movement_feet: int
) -> Dictionary:
	_active_planning_actor_id = str(actor.call("get_actor_id")) if actor != null and actor.has_method("get_actor_id") else ""
	var selected: Dictionary = super._plan_combat_ai_movement(actor_node, actor, profile, guard_anchor, objective_position, intent_id, movement_feet)
	var planning_actor_id: String = _active_planning_actor_id
	_active_planning_actor_id = ""
	if planning_actor_id.is_empty() or selected.is_empty():
		return selected
	var cell_value: Variant = selected.get("cell", null)
	if not cell_value is Vector2i:
		return selected
	var squad_id: String = str(profile.get("squad_id", ""))
	if squad_id.is_empty():
		return selected
	var reservations_value: Variant = _squad_reserved_cells.get(squad_id, {})
	var reservations: Dictionary = reservations_value as Dictionary if reservations_value is Dictionary else {}
	reservations[planning_actor_id] = cell_value
	_squad_reserved_cells[squad_id] = reservations
	return selected


func _combat_ai_cell_is_available(grid: BattleGrid, cell: Vector2i, occupied: Dictionary) -> bool:
	if not super._combat_ai_cell_is_available(grid, cell, occupied):
		return false
	if _active_planning_actor_id.is_empty() or _squad_ai == null:
		return true
	var profile: Dictionary = _squad_ai.get_profile(_active_planning_actor_id)
	var squad_id: String = str(profile.get("squad_id", ""))
	var reservations_value: Variant = _squad_reserved_cells.get(squad_id, {})
	if not reservations_value is Dictionary:
		return true
	var reservations: Dictionary = reservations_value as Dictionary
	for reserved_actor_value: Variant in reservations.keys():
		var reserved_actor_id: String = str(reserved_actor_value)
		if reserved_actor_id == _active_planning_actor_id:
			continue
		var reserved_cell: Variant = reservations.get(reserved_actor_value, null)
		if reserved_cell is Vector2i and reserved_cell == cell:
			return false
	return true


func _execute_combat_ai_path(actor: Node2D, path: Array, intent_id: String) -> void:
	var actor_id: String = str(actor.call("get_actor_id")) if actor != null and actor.has_method("get_actor_id") else ""
	var start_position: Vector2 = actor.global_position if actor != null else Vector2.ZERO
	await super._execute_combat_ai_path(actor, path, intent_id)
	if actor_id.is_empty() or _squad_plans == null or not is_instance_valid(actor):
		return
	var assignment: Dictionary = get_squad_assignment_for_testing(actor_id)
	if assignment.is_empty():
		return
	var objective_value: Variant = _squad_objective_by_actor.get(actor_id, null)
	var moved: bool = actor.global_position.distance_to(start_position) >= 8.0
	var reached: bool = objective_value is Vector2 and DistanceSystem.distance_feet(actor.global_position, objective_value as Vector2) <= 15
	var stationary_role_action: bool = intent_id in [
		AdvancedNpcCombatAiSystem.INTENT_CAST_SPELL,
		AdvancedNpcCombatAiSystem.INTENT_TAKE_COVER,
		NpcCombatAiSystem.INTENT_GUARD
	]
	_squad_plans.record_actor_outcome(
		str(assignment.get("squad_id", "")),
		actor_id,
		str(assignment.get("action", "")),
		_turn_system.round_number,
		moved or reached or stationary_role_action
	)


func _build_squad_plan_context(actor: Node, actor_id: String, profile: Dictionary, actor_context: Dictionary) -> Dictionary:
	var squad_id: String = str(profile.get("squad_id", ""))
	var members: Array[Node] = _living_squad_members(squad_id, actor)
	var member_ids: Array[String] = []
	var total_health_ratio: float = 0.0
	var total_morale: float = 0.0
	var has_melee: bool = false
	var has_ranged: bool = false
	var has_defender: bool = false
	var has_caster: bool = false
	for member: Node in members:
		var member_id: String = str(member.call("get_actor_id")) if member.has_method("get_actor_id") else member.name.to_snake_case()
		member_ids.append(member_id)
		var member_profile: Dictionary = _squad_ai.get_profile(member_id)
		var role_id: String = str(member_profile.get("role", NpcCombatAiSystem.ROLE_MELEE))
		has_melee = has_melee or role_id == NpcCombatAiSystem.ROLE_MELEE
		has_ranged = has_ranged or role_id == NpcCombatAiSystem.ROLE_RANGED
		has_defender = has_defender or role_id == NpcCombatAiSystem.ROLE_DEFENDER
		has_caster = has_caster or role_id == AdvancedNpcCombatAiSystem.ROLE_CASTER
		total_health_ratio += _actor_health_ratio(member)
		total_morale += clampf(float(member_profile.get("morale", 0.6)), 0.0, 1.0)
	member_ids.sort()
	var member_count: int = maxi(members.size(), 1)
	var bound_ally: Dictionary = _visible_bound_ally(actor as Node2D, squad_id)
	var event_value: Variant = actor_context.get("environment_event", {})
	var event: Dictionary = event_value as Dictionary if event_value is Dictionary else {}
	return {
		"squad_id": squad_id,
		"actor_id": actor_id,
		"member_ids": member_ids,
		"ally_count": members.size(),
		"casualty_count": maxi(int(actor_context.get("casualty_count", 0)), int(actor_context.get("defeated_ally_count", 0))),
		"average_health_ratio": total_health_ratio / float(member_count),
		"average_morale": total_morale / float(member_count),
		"bound_ally_visible": not bound_ally.is_empty(),
		"bound_ally_position": bound_ally.get("position", Vector2.ZERO),
		"passage_relevant": bool(actor_context.get("environment_passage_relevant", false)),
		"target_visible": bool(actor_context.get("target_visible", false)),
		"has_target_memory": bool(actor_context.get("has_target_memory", false)),
		"has_melee": has_melee,
		"has_ranged": has_ranged,
		"has_defender": has_defender,
		"has_caster": has_caster,
		"flank_route_count": maxi(int(actor_context.get("escape_route_count", 0)) - 1, 0),
		"environment_event_id": str(event.get("event_id", ""))
	}


func _living_squad_members(squad_id: String, include_actor: Node) -> Array[Node]:
	var result: Array[Node] = []
	var seen: Dictionary = {}
	if is_instance_valid(include_actor):
		result.append(include_actor)
		seen[include_actor.get_instance_id()] = true
	if _turn_system != null:
		for entry: Dictionary in _turn_system.entries:
			var participant: Node = entry.get("node") as Node
			_add_squad_member(result, seen, participant, squad_id)
	for target: Node in get_tree().get_nodes_in_group("combat_targets"):
		_add_squad_member(result, seen, target, squad_id)
	return result


func _add_squad_member(result: Array[Node], seen: Dictionary, participant: Node, squad_id: String) -> void:
	if not is_instance_valid(participant) or seen.has(participant.get_instance_id()) or not participant.has_method("get_actor_id"):
		return
	if participant.has_method("is_combat_active") and not bool(participant.call("is_combat_active")):
		return
	var participant_id: String = str(participant.call("get_actor_id"))
	if str(_squad_ai.get_profile(participant_id).get("squad_id", "")) != squad_id:
		return
	seen[participant.get_instance_id()] = true
	result.append(participant)


func _visible_bound_ally(observer: Node2D, squad_id: String) -> Dictionary:
	if observer == null:
		return {}
	for body: Node in get_tree().get_nodes_in_group("bound_bodies"):
		if not is_instance_valid(body) or not body is Node2D or body == observer or not body.has_method("get_body_actor_id"):
			continue
		var body_id: String = str(body.call("get_body_actor_id"))
		if str(_squad_ai.get_profile(body_id).get("squad_id", "")) != squad_id:
			continue
		var position: Vector2 = (body as Node2D).global_position
		if _combat_environment != null and not _combat_environment.has_line_of_sight(observer.global_position, position):
			continue
		return {"actor_id": body_id, "position": position}
	return {}


func _bound_ally_position(squad_id: String, fallback: Vector2) -> Vector2:
	for body: Node in get_tree().get_nodes_in_group("bound_bodies"):
		if not is_instance_valid(body) or not body is Node2D or not body.has_method("get_body_actor_id"):
			continue
		var body_id: String = str(body.call("get_body_actor_id"))
		if str(_squad_ai.get_profile(body_id).get("squad_id", "")) == squad_id:
			return (body as Node2D).global_position
	return fallback


func _actor_health_ratio(actor: Node) -> float:
	if actor == null:
		return 0.0
	var current: int = int(actor.call("get_current_health")) if actor.has_method("get_current_health") else int(actor.get("current_health"))
	var maximum: int = int(actor.call("get_maximum_health")) if actor.has_method("get_maximum_health") else int(actor.get("maximum_health"))
	return clampf(float(current) / float(maxi(maximum, 1)), 0.0, 1.0)


func _squad_environment_event_position(actor_id: String, fallback: Vector2) -> Vector2:
	var context_value: Variant = _environment_context_by_actor.get(actor_id, {})
	if context_value is Dictionary:
		var context: Dictionary = context_value as Dictionary
		var position_value: Variant = context.get("environment_event_position", null)
		if position_value is Vector2:
			return position_value as Vector2
	return fallback


func _fallback_line_position(actor_position: Vector2, guard_anchor: Vector2, target_position: Vector2, slot: String) -> Vector2:
	var away: Vector2 = guard_anchor - target_position
	if away.length_squared() <= 0.0001:
		away = actor_position - target_position
	if away.length_squared() <= 0.0001:
		away = Vector2.LEFT
	var base: Vector2 = guard_anchor + away.normalized() * 128.0
	return base + _absolute_slot_offset(slot, 54.0)


func _target_slot_position(actor_position: Vector2, target_position: Vector2, slot: String, distance_pixels: float) -> Vector2:
	var forward: Vector2 = actor_position - target_position
	if forward.length_squared() <= 0.0001:
		forward = Vector2.DOWN
	forward = forward.normalized()
	var lateral := Vector2(-forward.y, forward.x)
	match slot:
		"left": return target_position + lateral * distance_pixels
		"right": return target_position - lateral * distance_pixels
		"rear_left": return target_position + forward * distance_pixels + lateral * 72.0
		"rear_right": return target_position + forward * distance_pixels - lateral * 72.0
		"rear": return target_position + forward * distance_pixels
		"front_left": return target_position + forward * distance_pixels * 0.45 + lateral * 58.0
		"front_right": return target_position + forward * distance_pixels * 0.45 - lateral * 58.0
		_: return target_position + forward * distance_pixels


func _absolute_slot_offset(slot: String, distance_pixels: float) -> Vector2:
	match slot:
		"left": return Vector2(-distance_pixels, 0.0)
		"right": return Vector2(distance_pixels, 0.0)
		"rear_left": return Vector2(-distance_pixels * 0.7, distance_pixels * 0.7)
		"rear_right": return Vector2(distance_pixels * 0.7, distance_pixels * 0.7)
		"rear": return Vector2(0.0, distance_pixels)
		"front_left": return Vector2(-distance_pixels * 0.7, -distance_pixels * 0.45)
		"front_right": return Vector2(distance_pixels * 0.7, -distance_pixels * 0.45)
		_: return Vector2(0.0, -distance_pixels)


func _reset_reservations_if_new_round() -> void:
	if _reservation_round == _turn_system.round_number:
		return
	_reservation_round = _turn_system.round_number
	_squad_reserved_cells.clear()


func _announce_squad_plan_if_needed(squad_id: String, plan: Dictionary, actor: Node) -> void:
	var plan_id: String = str(plan.get("plan_id", ""))
	if str(_announced_plan_by_squad.get(squad_id, "")) == plan_id:
		return
	_announced_plan_by_squad[squad_id] = plan_id
	show_combat_message("%s задаёт отряду новый тактический план: %s." % [_target_name(actor), _squad_plan_label(plan_id)], false)


func _squad_plan_label(plan_id: String) -> String:
	return {
		SquadTacticalPlanSystem.PLAN_RESCUE_BOUND_ALLY: "освободить пленника",
		SquadTacticalPlanSystem.PLAN_ORDERLY_WITHDRAWAL: "организованный отход",
		SquadTacticalPlanSystem.PLAN_HOLD_CHOKEPOINT: "удержать проход",
		SquadTacticalPlanSystem.PLAN_SUPPRESS_AND_FLANK: "подавление и обход",
		SquadTacticalPlanSystem.PLAN_SECTOR_SEARCH: "разделить область поиска",
		SquadTacticalPlanSystem.PLAN_COORDINATED_ASSAULT: "согласованное наступление"
	}.get(plan_id, plan_id)


func _clear_squad_plan_runtime() -> void:
	if _squad_plans != null:
		_squad_plans.clear()
	_squad_assignment_by_actor.clear()
	_squad_objective_by_actor.clear()
	_squad_reserved_cells.clear()
	_announced_plan_by_squad.clear()
	_active_planning_actor_id = ""
	_reservation_round = -1
