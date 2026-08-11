extends "res://scripts/game/game_advanced_party_tactics_v1_runtime.gd"

const COORDINATION_AI_SCRIPT: Script = preload("res://scripts/systems/squad_plan_npc_ai_system.gd")
const SQUAD_PLANS_SCRIPT: Script = preload("res://scripts/systems/squad_tactical_plan_system.gd")
const COORDINATION_FLANK_OFFSET_PIXELS: float = 118.0
const COORDINATION_REAR_OFFSET_PIXELS: float = 176.0
const COORDINATION_SEARCH_OFFSET_PIXELS: float = 132.0

var _coordination_ai: SquadPlanNpcAiSystem
var _coordination_plans: SquadTacticalPlanSystem = SQUAD_PLANS_SCRIPT.new() as SquadTacticalPlanSystem
var _coordination_assignment_by_actor: Dictionary = {}
var _coordination_objective_by_actor: Dictionary = {}
var _coordination_reserved_cells: Dictionary = {}
var _coordination_active_planning_actor_id: String = ""
var _coordination_reservation_round: int = -1
var _coordination_announced_plan_by_squad: Dictionary = {}


func _ready() -> void:
	super._ready()
	_coordination_ai = COORDINATION_AI_SCRIPT.new() as SquadPlanNpcAiSystem
	# The squad-aware system is a strict subclass of the already-approved
	# AdvancedNpcCombatAiSystem. Replacing these facades keeps every existing
	# target/spell/tactical contract while enabling assignment-aware decisions.
	_advanced_ai = _coordination_ai
	_combat_ai = _coordination_ai
	_npc_ai = _coordination_ai


func _process(delta: float) -> void:
	var combat_before: bool = _turn_system.active
	super._process(delta)
	if combat_before and not _turn_system.active:
		_clear_coordination_runtime_v1()


func _build_party_tactical_context_v1(
	actor_node: Node2D,
	actor: Node,
	target: Node,
	profile: Dictionary,
	guard_anchor: Vector2,
	perceived_target_position: Vector2,
	target_visible: bool,
	target_memory: Dictionary,
	casualty_observation: Dictionary
) -> Dictionary:
	var context: Dictionary = super._build_party_tactical_context_v1(
		actor_node,
		actor,
		target,
		profile,
		guard_anchor,
		perceived_target_position,
		target_visible,
		target_memory,
		casualty_observation
	)
	if _coordination_ai == null or _coordination_plans == null:
		return context
	var actor_id: String = actor_id_for_party_tactics_v1(actor)
	var squad_id: String = str(profile.get("squad_id", ""))
	if actor_id.is_empty() or squad_id.is_empty():
		return context

	_reset_coordination_reservations_if_new_round_v1()
	var squad_context: Dictionary = _build_coordination_squad_context_v1(
		actor,
		actor_id,
		profile,
		context,
		perceived_target_position
	)
	var plan: Dictionary = _coordination_plans.evaluate_squad_plan(
		squad_id,
		_turn_system.round_number,
		squad_context
	)
	if plan.is_empty():
		_coordination_assignment_by_actor.erase(actor_id)
		_coordination_objective_by_actor.erase(actor_id)
		return context

	var actor_ids: Array[String] = []
	var member_ids_value: Variant = squad_context.get("member_ids", [])
	if member_ids_value is Array:
		for value: Variant in member_ids_value as Array:
			actor_ids.append(str(value))
	actor_ids.sort()
	var actor_index: int = maxi(actor_ids.find(actor_id), 0)
	var assignment: Dictionary = _coordination_plans.get_actor_assignment(
		squad_id,
		actor_id,
		str(profile.get("role", NpcCombatAiSystem.ROLE_MELEE)),
		actor_index,
		_turn_system.round_number
	)
	if assignment.is_empty():
		return context

	context["squad_plan"] = plan.duplicate(true)
	context["squad_plan_assignment"] = assignment.duplicate(true)
	context["squad_plan_id"] = str(plan.get("plan_id", ""))
	context["squad_plan_phase"] = str(plan.get("phase", ""))
	_coordination_assignment_by_actor[actor_id] = assignment.duplicate(true)
	_announce_coordination_plan_if_needed_v1(squad_id, plan, actor)
	return context


func _objective_for_advanced_intent(
	actor: Node,
	guard_anchor: Vector2,
	target_position: Vector2,
	intent_id: String
) -> Vector2:
	if actor == null or not actor.has_method("get_actor_id") or not actor is Node2D:
		return super._objective_for_advanced_intent(actor, guard_anchor, target_position, intent_id)
	var actor_id: String = str(actor.call("get_actor_id"))
	var assignment_value: Variant = _coordination_assignment_by_actor.get(actor_id, {})
	if not assignment_value is Dictionary or (assignment_value as Dictionary).is_empty():
		return super._objective_for_advanced_intent(actor, guard_anchor, target_position, intent_id)

	var assignment: Dictionary = assignment_value as Dictionary
	var objective_id: String = str(assignment.get("objective", ""))
	var slot: String = str(assignment.get("slot", "front"))
	var actor_node: Node2D = actor as Node2D
	var objective: Vector2 = target_position
	match objective_id:
		"bound_ally":
			objective = _coordination_bound_ally_position_v1(
				str(assignment.get("squad_id", "")),
				target_position
			)
		"fallback_line":
			objective = _coordination_fallback_line_position_v1(
				actor_node.global_position,
				guard_anchor,
				target_position,
				slot
			)
		"target_flank":
			objective = _coordination_target_slot_position_v1(
				actor_node.global_position,
				target_position,
				slot,
				COORDINATION_FLANK_OFFSET_PIXELS
			)
		"target_front":
			objective = _coordination_target_slot_position_v1(
				actor_node.global_position,
				target_position,
				slot,
				58.0
			)
		"target_rear":
			objective = _coordination_target_slot_position_v1(
				actor_node.global_position,
				target_position,
				slot,
				COORDINATION_REAR_OFFSET_PIXELS
			)
		"memory_sector":
			objective = target_position + _coordination_absolute_slot_offset_v1(
				slot,
				COORDINATION_SEARCH_OFFSET_PIXELS
			)
		"memory_rear":
			objective = target_position + _coordination_absolute_slot_offset_v1(
				"rear",
				COORDINATION_SEARCH_OFFSET_PIXELS
			)
		"nearest_ally":
			var ally: Node2D = _nearest_living_ally(actor)
			objective = ally.global_position if ally != null else guard_anchor
		"passage":
			# Environment-reactive passage plans are intentionally not synthesized
			# here. Without a concrete world event, the safe fallback is the anchor.
			objective = guard_anchor
		_:
			return super._objective_for_advanced_intent(actor, guard_anchor, target_position, intent_id)
	_coordination_objective_by_actor[actor_id] = objective
	return objective


func _plan_advanced_party_movement_v1(
	actor_node: Node2D,
	actor: Node,
	target: Node,
	profile: Dictionary,
	guard_anchor: Vector2,
	objective_position: Vector2,
	intent_id: String,
	movement_feet: int
) -> Dictionary:
	_coordination_active_planning_actor_id = actor_id_for_party_tactics_v1(actor)
	var selected: Dictionary = super._plan_advanced_party_movement_v1(
		actor_node,
		actor,
		target,
		profile,
		guard_anchor,
		objective_position,
		intent_id,
		movement_feet
	)
	var planning_actor_id: String = _coordination_active_planning_actor_id
	_coordination_active_planning_actor_id = ""
	if planning_actor_id.is_empty() or selected.is_empty():
		return selected
	var cell_value: Variant = selected.get("cell", null)
	if not cell_value is Vector2i:
		return selected
	var squad_id: String = str(profile.get("squad_id", ""))
	if squad_id.is_empty():
		return selected
	var reservations_value: Variant = _coordination_reserved_cells.get(squad_id, {})
	var reservations: Dictionary = (
		reservations_value as Dictionary
		if reservations_value is Dictionary
		else {}
	)
	reservations[planning_actor_id] = cell_value
	_coordination_reserved_cells[squad_id] = reservations
	return selected


func _combat_ai_cell_is_available(
	grid: BattleGrid,
	cell: Vector2i,
	occupied: Dictionary
) -> bool:
	if not super._combat_ai_cell_is_available(grid, cell, occupied):
		return false
	if _coordination_active_planning_actor_id.is_empty() or _coordination_ai == null:
		return true
	var profile: Dictionary = _coordination_ai.get_profile(
		_coordination_active_planning_actor_id
	)
	var squad_id: String = str(profile.get("squad_id", ""))
	var reservations_value: Variant = _coordination_reserved_cells.get(squad_id, {})
	if not reservations_value is Dictionary:
		return true
	var reservations: Dictionary = reservations_value as Dictionary
	for actor_key: Variant in reservations.keys():
		var reserved_actor_id: String = str(actor_key)
		if reserved_actor_id == _coordination_active_planning_actor_id:
			continue
		var reserved_cell: Variant = reservations.get(actor_key, null)
		if reserved_cell is Vector2i and reserved_cell == cell:
			return false
	return true


func _execute_party_target_path_v1(
	actor: Node2D,
	target: Node,
	path: Array,
	intent_id: String
) -> void:
	var actor_id: String = actor_id_for_party_tactics_v1(actor)
	var start_position: Vector2 = actor.global_position if actor != null else Vector2.ZERO
	await super._execute_party_target_path_v1(actor, target, path, intent_id)
	if actor_id.is_empty() or _coordination_plans == null or not is_instance_valid(actor):
		return
	var assignment: Dictionary = get_coordination_assignment_v1_for_testing(actor_id)
	if assignment.is_empty():
		return
	var objective_value: Variant = _coordination_objective_by_actor.get(actor_id, null)
	var moved: bool = actor.global_position.distance_to(start_position) >= 8.0
	var reached: bool = (
		objective_value is Vector2
		and DistanceSystem.distance_feet(
			actor.global_position,
			objective_value as Vector2
		) <= 15
	)
	var stationary_success: bool = intent_id in [
		AdvancedNpcCombatAiSystem.INTENT_CAST_SPELL,
		AdvancedNpcCombatAiSystem.INTENT_TAKE_COVER,
		NpcCombatAiSystem.INTENT_GUARD
	]
	_coordination_plans.record_actor_outcome(
		str(assignment.get("squad_id", "")),
		actor_id,
		str(assignment.get("action", "")),
		_turn_system.round_number,
		moved or reached or stationary_success
	)


func _build_coordination_squad_context_v1(
	actor: Node,
	actor_id: String,
	profile: Dictionary,
	actor_context: Dictionary,
	perceived_target_position: Vector2
) -> Dictionary:
	var squad_id: String = str(profile.get("squad_id", ""))
	var members: Array[Node] = _living_coordination_members_v1(squad_id, actor)
	var member_ids: Array[String] = []
	var total_health_ratio: float = 0.0
	var total_morale: float = 0.0
	var has_melee: bool = false
	var has_ranged: bool = false
	var has_defender: bool = false
	var has_caster: bool = false
	for member: Node in members:
		var member_id: String = (
			str(member.call("get_actor_id"))
			if member.has_method("get_actor_id")
			else member.name.to_snake_case()
		)
		member_ids.append(member_id)
		var member_profile: Dictionary = _coordination_ai.get_profile(member_id)
		var role_id: String = str(
			member_profile.get("role", NpcCombatAiSystem.ROLE_MELEE)
		)
		has_melee = has_melee or role_id == NpcCombatAiSystem.ROLE_MELEE
		has_ranged = has_ranged or role_id == NpcCombatAiSystem.ROLE_RANGED
		has_defender = has_defender or role_id == NpcCombatAiSystem.ROLE_DEFENDER
		has_caster = has_caster or role_id == AdvancedNpcCombatAiSystem.ROLE_CASTER
		total_health_ratio += _coordination_actor_health_ratio_v1(member)
		total_morale += clampf(float(member_profile.get("morale", 0.6)), 0.0, 1.0)
	member_ids.sort()
	var member_count: int = maxi(members.size(), 1)
	var bound_ally: Dictionary = (
		_coordination_visible_bound_ally_v1(actor as Node2D, squad_id)
		if actor is Node2D
		else {}
	)
	return {
		"squad_id": squad_id,
		"actor_id": actor_id,
		"member_ids": member_ids,
		"ally_count": members.size(),
		"casualty_count": maxi(
			int(actor_context.get("casualty_count", 0)),
			int(actor_context.get("defeated_ally_count", 0))
		),
		"average_health_ratio": total_health_ratio / float(member_count),
		"average_morale": total_morale / float(member_count),
		"bound_ally_visible": not bound_ally.is_empty(),
		"bound_ally_position": bound_ally.get("position", Vector2.ZERO),
		"passage_relevant": false,
		"target_visible": bool(actor_context.get("target_visible", false)),
		"has_target_memory": bool(actor_context.get("has_target_memory", false)),
		"has_melee": has_melee,
		"has_ranged": has_ranged,
		"has_defender": has_defender,
		"has_caster": has_caster,
		"flank_route_count": maxi(int(actor_context.get("escape_route_count", 0)) - 1, 0),
		"target_position": perceived_target_position
	}


func _living_coordination_members_v1(
	squad_id: String,
	include_actor: Node
) -> Array[Node]:
	var result: Array[Node] = []
	var seen: Dictionary = {}
	if is_instance_valid(include_actor):
		_add_coordination_member_v1(result, seen, include_actor, squad_id)
	if _turn_system != null:
		for entry: Dictionary in _turn_system.entries:
			var participant: Node = entry.get("node") as Node
			_add_coordination_member_v1(result, seen, participant, squad_id)
	for target: Node in get_tree().get_nodes_in_group("combat_targets"):
		_add_coordination_member_v1(result, seen, target, squad_id)
	return result


func _add_coordination_member_v1(
	result: Array[Node],
	seen: Dictionary,
	participant: Node,
	squad_id: String
) -> void:
	if (
		not is_instance_valid(participant)
		or seen.has(participant.get_instance_id())
		or not participant.has_method("get_actor_id")
	):
		return
	if participant.has_method("is_combat_active") and not bool(participant.call("is_combat_active")):
		return
	var participant_id: String = str(participant.call("get_actor_id"))
	if str(_coordination_ai.get_profile(participant_id).get("squad_id", "")) != squad_id:
		return
	seen[participant.get_instance_id()] = true
	result.append(participant)


func _coordination_visible_bound_ally_v1(
	observer: Node2D,
	squad_id: String
) -> Dictionary:
	if observer == null:
		return {}
	for body: Node in get_tree().get_nodes_in_group("bound_bodies"):
		if (
			not is_instance_valid(body)
			or not body is Node2D
			or body == observer
			or not body.has_method("get_body_actor_id")
		):
			continue
		var body_id: String = str(body.call("get_body_actor_id"))
		if str(_coordination_ai.get_profile(body_id).get("squad_id", "")) != squad_id:
			continue
		var position: Vector2 = (body as Node2D).global_position
		if _combat_environment != null and not _combat_environment.has_line_of_sight(
			observer.global_position,
			position
		):
			continue
		return {"actor_id": body_id, "position": position}
	return {}


func _coordination_bound_ally_position_v1(
	squad_id: String,
	fallback: Vector2
) -> Vector2:
	for body: Node in get_tree().get_nodes_in_group("bound_bodies"):
		if (
			not is_instance_valid(body)
			or not body is Node2D
			or not body.has_method("get_body_actor_id")
		):
			continue
		var body_id: String = str(body.call("get_body_actor_id"))
		if str(_coordination_ai.get_profile(body_id).get("squad_id", "")) == squad_id:
			return (body as Node2D).global_position
	return fallback


func _coordination_actor_health_ratio_v1(actor: Node) -> float:
	if actor == null:
		return 0.0
	var current: int = (
		int(actor.call("get_current_health"))
		if actor.has_method("get_current_health")
		else int(actor.get("current_health"))
	)
	var maximum: int = (
		int(actor.call("get_maximum_health"))
		if actor.has_method("get_maximum_health")
		else int(actor.get("maximum_health"))
	)
	return clampf(float(current) / float(maxi(maximum, 1)), 0.0, 1.0)


func _coordination_fallback_line_position_v1(
	actor_position: Vector2,
	guard_anchor: Vector2,
	target_position: Vector2,
	slot: String
) -> Vector2:
	var away: Vector2 = guard_anchor - target_position
	if away.length_squared() <= 0.0001:
		away = actor_position - target_position
	if away.length_squared() <= 0.0001:
		away = Vector2.LEFT
	var base: Vector2 = guard_anchor + away.normalized() * 128.0
	return base + _coordination_absolute_slot_offset_v1(slot, 54.0)


func _coordination_target_slot_position_v1(
	actor_position: Vector2,
	target_position: Vector2,
	slot: String,
	distance_pixels: float
) -> Vector2:
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


func _coordination_absolute_slot_offset_v1(
	slot: String,
	distance_pixels: float
) -> Vector2:
	match slot:
		"left": return Vector2(-distance_pixels, 0.0)
		"right": return Vector2(distance_pixels, 0.0)
		"rear_left": return Vector2(-distance_pixels * 0.7, distance_pixels * 0.7)
		"rear_right": return Vector2(distance_pixels * 0.7, distance_pixels * 0.7)
		"rear": return Vector2(0.0, distance_pixels)
		"front_left": return Vector2(-distance_pixels * 0.7, -distance_pixels * 0.45)
		"front_right": return Vector2(distance_pixels * 0.7, -distance_pixels * 0.45)
		_: return Vector2(0.0, -distance_pixels)


func _reset_coordination_reservations_if_new_round_v1() -> void:
	if _coordination_reservation_round == _turn_system.round_number:
		return
	_coordination_reservation_round = _turn_system.round_number
	_coordination_reserved_cells.clear()


func _announce_coordination_plan_if_needed_v1(
	squad_id: String,
	plan: Dictionary,
	actor: Node
) -> void:
	var plan_id: String = str(plan.get("plan_id", ""))
	if plan_id.is_empty() or str(_coordination_announced_plan_by_squad.get(squad_id, "")) == plan_id:
		return
	_coordination_announced_plan_by_squad[squad_id] = plan_id
	show_combat_message(
		"%s задаёт отряду тактический план: %s." % [
			_target_name(actor),
			_coordination_plan_label_v1(plan_id)
		],
		false
	)


func _coordination_plan_label_v1(plan_id: String) -> String:
	return {
		SquadTacticalPlanSystem.PLAN_RESCUE_BOUND_ALLY: "освободить союзника",
		SquadTacticalPlanSystem.PLAN_ORDERLY_WITHDRAWAL: "организованный отход",
		SquadTacticalPlanSystem.PLAN_HOLD_CHOKEPOINT: "удержать проход",
		SquadTacticalPlanSystem.PLAN_SUPPRESS_AND_FLANK: "подавление и обход",
		SquadTacticalPlanSystem.PLAN_SECTOR_SEARCH: "разделить область поиска",
		SquadTacticalPlanSystem.PLAN_COORDINATED_ASSAULT: "согласованное наступление"
	}.get(plan_id, plan_id)


func _clear_coordination_runtime_v1() -> void:
	if _coordination_plans != null:
		_coordination_plans.clear()
	_coordination_assignment_by_actor.clear()
	_coordination_objective_by_actor.clear()
	_coordination_reserved_cells.clear()
	_coordination_announced_plan_by_squad.clear()
	_coordination_active_planning_actor_id = ""
	_coordination_reservation_round = -1


func get_coordination_plan_v1_for_testing(squad_id: String) -> Dictionary:
	return (
		_coordination_plans.get_active_plan(squad_id)
		if _coordination_plans != null
		else {}
	)


func get_coordination_assignment_v1_for_testing(actor_id: String) -> Dictionary:
	var value: Variant = _coordination_assignment_by_actor.get(actor_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func get_coordination_objective_v1_for_testing(actor_id: String) -> Vector2:
	var value: Variant = _coordination_objective_by_actor.get(actor_id, Vector2.INF)
	return value as Vector2 if value is Vector2 else Vector2.INF


func get_coordination_reserved_cells_v1_for_testing(squad_id: String) -> Dictionary:
	var value: Variant = _coordination_reserved_cells.get(squad_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func build_coordination_context_v1_for_testing(
	actor: Node,
	target: Node,
	overrides: Dictionary = {}
) -> Dictionary:
	var context: Dictionary = get_party_tactical_context_v1_for_testing(
		actor,
		target,
		overrides
	)
	return context


func choose_coordination_intent_v1_for_testing(
	actor: Node,
	target: Node,
	overrides: Dictionary = {}
) -> Dictionary:
	if _coordination_ai == null:
		return {}
	var actor_id: String = actor_id_for_party_tactics_v1(actor)
	if actor_id.is_empty():
		return {}
	var context: Dictionary = build_coordination_context_v1_for_testing(
		actor,
		target,
		overrides
	)
	return _coordination_ai.choose_combat_intent(actor_id, context)


func clear_coordination_runtime_v1_for_testing() -> void:
	_clear_coordination_runtime_v1()
