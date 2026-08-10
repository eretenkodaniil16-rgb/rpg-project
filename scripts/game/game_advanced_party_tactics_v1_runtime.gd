extends "res://scripts/game/game_combat_ai_targeting_v3_runtime.gd"

const PARTY_TACTICS_MOVEMENT_INTENTS_V1: Array[String] = [
	NpcAiSystem.INTENT_ADVANCE,
	NpcAiSystem.INTENT_RETREAT,
	NpcCombatAiSystem.INTENT_REPOSITION,
	NpcCombatAiSystem.INTENT_INTERCEPT,
	NpcCombatAiSystem.INTENT_SEARCH,
	NpcCombatAiSystem.INTENT_GUARD,
	AdvancedNpcCombatAiSystem.INTENT_CAST_SPELL,
	AdvancedNpcCombatAiSystem.INTENT_TAKE_COVER,
	AdvancedNpcCombatAiSystem.INTENT_REGROUP
]
const PARTY_TACTICS_ACTION_INTENTS_V1: Array[String] = [
	AdvancedNpcCombatAiSystem.INTENT_CAST_SPELL,
	AdvancedNpcCombatAiSystem.INTENT_RALLY,
	AdvancedNpcCombatAiSystem.INTENT_DODGE,
	AdvancedNpcCombatAiSystem.INTENT_SHOVE
]

var _party_target_memory_by_actor_v1: Dictionary = {}
var _party_target_memory_by_squad_v1: Dictionary = {}


func _process(delta: float) -> void:
	var combat_before: bool = _turn_system.active
	super._process(delta)
	if combat_before and not _turn_system.active:
		_clear_party_target_memory_v1()


func _select_enemy_party_target(actor: Node) -> Node:
	var selected: Node = super._select_enemy_party_target(actor)
	if not actor is Node2D:
		return selected
	var actor_node: Node2D = actor as Node2D
	var actor_id: String = str(actor.call("get_actor_id")) if actor.has_method("get_actor_id") else ""
	var profile: Dictionary = _advanced_ai.get_profile(actor_id) if _advanced_ai != null and not actor_id.is_empty() else {}
	if is_instance_valid(selected) and _enemy_party_target_is_available(selected) and _enemy_can_see_party_target_from(actor_node.global_position, selected):
		_record_party_target_sighting_v1(actor, profile, selected)
		return selected

	var memory: Dictionary = _get_party_target_memory_v1(actor, profile)
	var remembered_target: Node = memory.get("target") as Node
	if not is_instance_valid(remembered_target) or remembered_target == player:
		return selected
	var actor_instance_id: int = actor.get_instance_id()
	_assign_actor_target_claim_v2(actor_instance_id, remembered_target.get_instance_id())
	_enemy_party_target_by_actor_id[actor_instance_id] = remembered_target.get_instance_id()
	_enemy_attack_range_by_actor_id[actor_instance_id] = maxi(
		int(profile.get("attack_range_feet", DistanceSystem.MELEE_REACH_FEET)),
		DistanceSystem.MELEE_REACH_FEET
	)
	_last_targeting_diagnostics_v2 = {
		"actor_id": actor_id,
		"selected_target_id": remembered_target.get_instance_id(),
		"selected_target_name": _party_target_name_v3(remembered_target),
		"selected_score": 0.0,
		"candidate_count": 0,
		"round": _turn_system.round_number,
		"targeting_version": "advanced_party_tactics_v1_memory"
	}
	return remembered_target


func _run_enemy_turn_against_party_target_v3(actor: Node, target: Node) -> void:
	if _advanced_ai == null or not actor is Node2D or not target is Node2D:
		await super._run_enemy_turn_against_party_target_v3(actor, target)
		return
	if not _turn_system.active or _turn_system.current_actor() != actor:
		return

	_enemy_turn_running = true
	_refresh_turn_interface()
	while _turn_system.active and _any_overlay_visible():
		await get_tree().process_frame
	await get_tree().create_timer(0.28).timeout

	if is_instance_valid(actor) and is_instance_valid(target) and (
		not actor.has_method("can_take_combat_turn") or bool(actor.call("can_take_combat_turn"))
	):
		var actor_node: Node2D = actor as Node2D
		var actor_id: String = str(actor.call("get_actor_id"))
		var profile: Dictionary = _advanced_ai.get_profile(actor_id)
		if profile.is_empty():
			_enemy_turn_running = false
			await super._run_enemy_turn_against_party_target_v3(actor, target)
			return
		var guard_anchor: Vector2 = _ensure_combat_ai_guard_anchor(actor_id, actor_node.global_position)
		var casualty_observation: Dictionary = _observe_allied_bodies(actor_node, actor_id, profile)
		var target_visible: bool = _enemy_can_see_party_target_from(actor_node.global_position, target)
		if target_visible:
			_record_party_target_sighting_v1(actor, profile, target)
		var target_memory: Dictionary = _get_party_target_memory_v1(actor, profile)
		var has_target_memory: bool = not target_memory.is_empty()
		var perceived_target_position: Vector2 = (
			(target as Node2D).global_position
			if target_visible
			else target_memory.get("position", guard_anchor) as Vector2
			if has_target_memory
			else guard_anchor
		)
		var context: Dictionary = _build_party_tactical_context_v1(
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

		var movement_feet: int = int(actor.call("get_combat_speed_feet")) if actor.has_method("get_combat_speed_feet") else 30
		var preplan: Dictionary = {}
		if str(profile.get("role", "")) == AdvancedNpcCombatAiSystem.ROLE_CASTER and movement_feet >= GRID_STEP_FEET:
			preplan = _plan_advanced_party_movement_v1(
				actor_node,
				actor,
				target,
				profile,
				guard_anchor,
				perceived_target_position,
				AdvancedNpcCombatAiSystem.INTENT_CAST_SPELL,
				movement_feet
			)
			if not preplan.is_empty():
				context["spell_plan_score"] = maxf(
					float(context.get("spell_plan_score", NpcCombatAiSystem.BLOCKED_SCORE)),
					float(preplan.get("score", NpcCombatAiSystem.BLOCKED_SCORE))
				)
				context["no_useful_attack"] = false

		var intent: Dictionary = _advanced_ai.choose_combat_intent(actor_id, context)
		var intent_id: String = str(intent.get("intent", NpcAiSystem.INTENT_WAIT))
		var attack_range_feet: int = maxi(int(intent.get("attack_range_feet", DistanceSystem.MELEE_REACH_FEET)), DistanceSystem.MELEE_REACH_FEET)
		var minimum_range_feet: int = maxi(int(intent.get("minimum_range_feet", 0)), 0)
		var selected_plan: Dictionary = preplan if intent_id == AdvancedNpcCombatAiSystem.INTENT_CAST_SPELL and not preplan.is_empty() else {}

		if intent_id in PARTY_TACTICS_MOVEMENT_INTENTS_V1 and movement_feet >= GRID_STEP_FEET:
			var objective_position: Vector2 = _objective_for_advanced_intent(actor, guard_anchor, perceived_target_position, intent_id)
			if selected_plan.is_empty():
				selected_plan = _plan_advanced_party_movement_v1(
					actor_node,
					actor,
					target,
					profile,
					guard_anchor,
					objective_position,
					intent_id,
					movement_feet
				)
			await _execute_party_target_path_v1(actor_node, target, selected_plan.get("path", []) as Array, intent_id)

		match intent_id:
			AdvancedNpcCombatAiSystem.INTENT_RALLY:
				_resolve_ai_rally(actor, profile)
			AdvancedNpcCombatAiSystem.INTENT_DODGE:
				_ai_dodge_until_round[actor.get_instance_id()] = _turn_system.round_number
				show_combat_message("%s принимает защитную стойку и затрудняет атаки до своего следующего хода." % _target_name(actor), true)
			AdvancedNpcCombatAiSystem.INTENT_SHOVE:
				_resolve_ai_shove_against_target_v3(actor_node, actor, target)
			AdvancedNpcCombatAiSystem.INTENT_CAST_SPELL:
				var spell_plan: Dictionary = (
					selected_plan.get("spell_plan", {}) as Dictionary
					if selected_plan.get("spell_plan", {}) is Dictionary
					else {}
				)
				if spell_plan.is_empty():
					spell_plan = _evaluate_spell_plan_for_target_v3(actor, profile, actor_node.global_position, target)
				if not spell_plan.is_empty() and actor.has_method("set_selected_combat_spell_id"):
					actor.call("set_selected_combat_spell_id", str(spell_plan.get("spell_id", "")))
					await _cast_enemy_spell_at_party_target_v3(actor, target, spell_plan)
			NpcAiSystem.INTENT_WAIT:
				show_combat_message("%s удерживает позицию и оценивает бой." % _target_name(actor), true)

		var visible_after: bool = _enemy_can_see_party_target_from(actor_node.global_position, target)
		if visible_after:
			_record_party_target_sighting_v1(actor, profile, target)
		elif intent_id == NpcCombatAiSystem.INTENT_SEARCH and has_target_memory:
			var searched_position: Vector2 = target_memory.get("position", perceived_target_position) as Vector2
			if DistanceSystem.distance_feet(actor_node.global_position, searched_position) <= DistanceSystem.MELEE_REACH_FEET:
				_invalidate_party_target_memory_v1(actor, profile, searched_position)
				show_combat_message("%s проверяет последнюю известную позицию %s, но не находит цель." % [_target_name(actor), _party_target_name_v3(target)], true)

		var distance_after: int = DistanceSystem.distance_feet(actor_node.global_position, (target as Node2D).global_position)
		var attack_ready_after: bool = (
			visible_after
			and distance_after <= attack_range_feet
			and distance_after >= minimum_range_feet
		)
		if (
			intent_id not in PARTY_TACTICS_ACTION_INTENTS_V1
			and intent_id not in [NpcAiSystem.INTENT_RETREAT, NpcAiSystem.INTENT_WAIT, NpcCombatAiSystem.INTENT_GUARD]
			and attack_ready_after
			and actor.has_method("perform_combat_turn_attack")
		):
			_enemy_party_target_by_actor_id[actor.get_instance_id()] = target.get_instance_id()
			_enemy_attack_range_by_actor_id[actor.get_instance_id()] = attack_range_feet
			actor.call("perform_combat_turn_attack")
			_update_status()
			await get_tree().create_timer(0.35).timeout

	_enemy_turn_running = false
	if _party_has_living_combatant():
		_advance_combat_turn()


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
	var context: Dictionary = _build_combat_ai_context(
		actor_node,
		actor,
		profile,
		guard_anchor,
		perceived_target_position,
		target_visible,
		target_memory
	)
	var distance: int = DistanceSystem.distance_feet(actor_node.global_position, perceived_target_position)
	var attack_range: int = maxi(int(profile.get("attack_range_feet", DistanceSystem.MELEE_REACH_FEET)), DistanceSystem.MELEE_REACH_FEET)
	var minimum_range: int = maxi(int(profile.get("minimum_range_feet", 0)), 0)
	var squad_id: String = str(profile.get("squad_id", ""))
	var casualty_context: Dictionary = _casualty_ai.get_context(actor_id_for_party_tactics_v1(actor), squad_id, _turn_system.round_number)
	var rally_active: bool = bool(casualty_context.get("rally_active", false))
	var target_state: CombatantState = _party_target_state_v3(target)
	var movement_feet: int = int(actor.call("get_combat_speed_feet")) if actor.has_method("get_combat_speed_feet") else 30

	context["distance_feet"] = distance
	context["target_visible"] = target_visible
	context["has_target_memory"] = not target_memory.is_empty()
	context["memory_confidence"] = float(target_memory.get("confidence", 0.0))
	context["can_attack"] = target_visible and distance <= attack_range and distance >= minimum_range
	context["can_move"] = movement_feet > 0
	context["target_health_ratio"] = _party_target_health_ratio_v3(target)
	context["hostile_count"] = _living_party_target_count_v1()
	context["new_casualty_seen"] = bool(casualty_observation.get("new", false))
	context["casualty_count"] = int(casualty_context.get("casualty_count", 0))
	context["rally_active"] = rally_active
	context["defeated_ally_count"] = maxi(int(context.get("defeated_ally_count", 0)) - (1 if rally_active else 0), 0)
	context["nearest_ally_distance_feet"] = _nearest_combat_ai_ally_distance(actor, actor_node.global_position)
	context["can_shove"] = target_visible and distance <= DistanceSystem.MELEE_REACH_FEET
	context["target_prone"] = target_state != null and target_state.has_condition("prone")
	context["can_dodge"] = true
	context["no_safe_retreat"] = int(context.get("escape_route_count", 0)) <= 1
	context["better_cover_available"] = _better_cover_available_against_party_target_v1(actor_node, actor, perceived_target_position)
	context["target_near_hazard"] = _position_near_blocked_edge_v1(perceived_target_position)
	context["no_useful_attack"] = not bool(context.get("can_attack", false)) and target_memory.is_empty()
	if str(profile.get("role", "")) == AdvancedNpcCombatAiSystem.ROLE_CASTER:
		var spell_plan: Dictionary = _evaluate_spell_plan_for_target_v3(actor, profile, actor_node.global_position, target)
		context["spell_plan_score"] = float(spell_plan.get("score", NpcCombatAiSystem.BLOCKED_SCORE))
		if not spell_plan.is_empty():
			context["no_useful_attack"] = false
	return context


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
	if not target is Node2D:
		return {"path": [], "score": NpcCombatAiSystem.BLOCKED_SCORE}
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return {"path": [], "score": NpcCombatAiSystem.BLOCKED_SCORE}
	var target_position: Vector2 = (target as Node2D).global_position
	var candidates: Array[Dictionary] = _build_combat_ai_reachable_candidates(actor_node, movement_feet)
	var selected: Dictionary = {}
	var selected_score: float = NpcCombatAiSystem.BLOCKED_SCORE
	var attack_range: int = maxi(int(profile.get("attack_range_feet", DistanceSystem.MELEE_REACH_FEET)), DistanceSystem.MELEE_REACH_FEET)
	var minimum_range: int = maxi(int(profile.get("minimum_range_feet", 0)), 0)
	for candidate: Dictionary in candidates:
		var cell: Vector2i = candidate.get("cell", grid.world_to_cell(actor_node.global_position)) as Vector2i
		var position: Vector2 = grid.cell_to_world_center(cell)
		var target_visible: bool = _enemy_can_see_party_target_from(position, target)
		var distance_to_target: int = DistanceSystem.distance_feet(position, target_position)
		var cover: Dictionary = _combat_environment.get_cover(target_position, position) if _combat_environment != null else {"bonus": 0, "total_cover": false}
		var spell_plan: Dictionary = (
			_evaluate_spell_plan_for_target_v3(actor, profile, position, target)
			if str(profile.get("role", "")) == AdvancedNpcCombatAiSystem.ROLE_CASTER
			else {}
		)
		var candidate_context: Dictionary = {
			"valid": not bool(cover.get("total_cover", false)) or intent_id in [NpcAiSystem.INTENT_RETREAT, AdvancedNpcCombatAiSystem.INTENT_TAKE_COVER],
			"distance_feet": distance_to_target if target_visible else DistanceSystem.distance_feet(position, objective_position),
			"distance_to_objective_feet": DistanceSystem.distance_feet(position, objective_position),
			"distance_from_guard_anchor_feet": DistanceSystem.distance_feet(position, guard_anchor),
			"nearest_ally_distance_feet": _nearest_combat_ai_ally_distance(actor, position),
			"mobility": _combat_ai_mobility_from(actor_node, position),
			"path_cost_feet": int(candidate.get("cost_feet", 0)),
			"target_visible": target_visible,
			"attack_ready": target_visible and distance_to_target <= attack_range and distance_to_target >= minimum_range,
			"cover_bonus": int(cover.get("bonus", 0)),
			"spell_plan_score": float(spell_plan.get("score", NpcCombatAiSystem.BLOCKED_SCORE))
		}
		var score: float = _advanced_ai.score_candidate_position(intent_id, profile, {}, candidate_context)
		candidate["score"] = score
		candidate["world_position"] = position
		candidate["target_visible"] = target_visible
		candidate["spell_plan"] = spell_plan
		if _combat_ai_candidate_is_better(candidate, score, selected, selected_score):
			selected = candidate.duplicate(true)
			selected_score = score
	if selected.is_empty():
		return {"path": [], "score": NpcCombatAiSystem.BLOCKED_SCORE}
	selected["score"] = selected_score
	return selected


func _execute_party_target_path_v1(actor: Node2D, target: Node, path: Array, intent_id: String) -> void:
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return
	for value: Variant in path:
		if not value is Vector2i:
			continue
		var cell: Vector2i = value as Vector2i
		var current_cell: Vector2i = grid.world_to_cell(actor.global_position)
		if not _combat_ai_cell_is_available(grid, cell, _occupied_cells(actor)):
			break
		if _combat_ai_transition_is_blocked(grid, current_cell, cell):
			break
		actor.global_position = grid.cell_to_world_center(cell)
		await get_tree().create_timer(0.1).timeout
		if intent_id == NpcCombatAiSystem.INTENT_SEARCH and _enemy_can_see_party_target_from(actor.global_position, target):
			break


func _better_cover_available_against_party_target_v1(actor_node: Node2D, actor: Node, threat_position: Vector2) -> bool:
	if _combat_environment == null:
		return false
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return false
	var current: Dictionary = _combat_environment.get_cover(threat_position, actor_node.global_position)
	var current_bonus: int = int(current.get("bonus", 0))
	var movement_feet: int = int(actor.call("get_combat_speed_feet")) if actor.has_method("get_combat_speed_feet") else 30
	for candidate: Dictionary in _build_combat_ai_reachable_candidates(actor_node, movement_feet):
		var cell: Vector2i = candidate.get("cell", Vector2i.ZERO) as Vector2i
		var cover: Dictionary = _combat_environment.get_cover(threat_position, grid.cell_to_world_center(cell))
		if not bool(cover.get("total_cover", false)) and int(cover.get("bonus", 0)) > current_bonus:
			return true
	return false


func _position_near_blocked_edge_v1(world_position: Vector2) -> bool:
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return false
	var cell: Vector2i = grid.world_to_cell(world_position)
	var blocked: int = 0
	for step: Vector2i in [Vector2i.LEFT, Vector2i.RIGHT, Vector2i.UP, Vector2i.DOWN]:
		var neighbour: Vector2i = cell + step
		if not grid.is_cell_valid(neighbour) or (_combat_environment != null and _combat_environment.is_cell_blocked(grid, neighbour)):
			blocked += 1
	return blocked >= 2


func _record_party_target_sighting_v1(actor: Node, profile: Dictionary, target: Node) -> void:
	if not is_instance_valid(actor) or not target is Node2D:
		return
	var target_actor_id: String = _party_target_adapter_v3.get_actor_id(target, player)
	if target_actor_id.is_empty():
		return
	var actor_id: String = actor_id_for_party_tactics_v1(actor)
	var record: Dictionary = {
		"target_actor_id": target_actor_id,
		"target_instance_id": target.get_instance_id(),
		"position": (target as Node2D).global_position,
		"round": _turn_system.round_number,
		"source_actor_id": actor_id
	}
	_party_target_memory_by_actor_v1[actor_id] = record.duplicate(true)
	var squad_id: String = str(profile.get("squad_id", ""))
	if not squad_id.is_empty() and bool(profile.get("shares_target_information", true)):
		_party_target_memory_by_squad_v1[squad_id] = record.duplicate(true)


func _get_party_target_memory_v1(actor: Node, profile: Dictionary) -> Dictionary:
	var actor_id: String = actor_id_for_party_tactics_v1(actor)
	var memory_rounds: int = maxi(int(profile.get("memory_rounds", 2)), 0)
	var actor_value: Variant = _party_target_memory_by_actor_v1.get(actor_id, {})
	var actor_record: Dictionary = actor_value as Dictionary if actor_value is Dictionary else {}
	var valid: Dictionary = _validated_party_target_memory_v1(actor_record, memory_rounds)
	if not valid.is_empty():
		return valid
	if not bool(profile.get("shares_target_information", true)):
		return {}
	var squad_id: String = str(profile.get("squad_id", ""))
	var squad_value: Variant = _party_target_memory_by_squad_v1.get(squad_id, {})
	var squad_record: Dictionary = squad_value as Dictionary if squad_value is Dictionary else {}
	return _validated_party_target_memory_v1(squad_record, memory_rounds)


func _validated_party_target_memory_v1(record: Dictionary, memory_rounds: int) -> Dictionary:
	if record.is_empty() or not record.get("position", null) is Vector2:
		return {}
	var target_actor_id: String = str(record.get("target_actor_id", ""))
	if target_actor_id.is_empty():
		return {}
	var target: Node = _party_target_by_actor_id_v1(target_actor_id)
	if not is_instance_valid(target) or not _enemy_party_target_is_available(target):
		return {}
	var age: int = maxi(_turn_system.round_number - int(record.get("round", _turn_system.round_number)), 0)
	if age > memory_rounds:
		return {}
	var result: Dictionary = record.duplicate(true)
	result["target"] = target
	result["age_rounds"] = age
	result["confidence"] = 1.0 if memory_rounds <= 0 else clampf(1.0 - float(age) / float(memory_rounds + 1), 0.0, 1.0)
	return result


func _invalidate_party_target_memory_v1(actor: Node, profile: Dictionary, searched_position: Vector2) -> void:
	var actor_id: String = actor_id_for_party_tactics_v1(actor)
	var actor_value: Variant = _party_target_memory_by_actor_v1.get(actor_id, {})
	var actor_record: Dictionary = actor_value as Dictionary if actor_value is Dictionary else {}
	_party_target_memory_by_actor_v1.erase(actor_id)
	var squad_id: String = str(profile.get("squad_id", ""))
	if squad_id.is_empty():
		return
	var squad_value: Variant = _party_target_memory_by_squad_v1.get(squad_id, {})
	var squad_record: Dictionary = squad_value as Dictionary if squad_value is Dictionary else {}
	if squad_record.get("position", null) is Vector2 and DistanceSystem.distance_feet(squad_record.get("position", searched_position) as Vector2, searched_position) <= DistanceSystem.MELEE_REACH_FEET:
		_party_target_memory_by_squad_v1.erase(squad_id)
	if actor_record.is_empty():
		return


func _party_target_by_actor_id_v1(target_actor_id: String) -> Node:
	for target: Node in _party_combat_targets_v3():
		if _party_target_adapter_v3.get_actor_id(target, player) == target_actor_id:
			return target
	return null


func _living_party_target_count_v1() -> int:
	var count: int = 0
	for target: Node in _party_combat_targets_v3():
		if _enemy_party_target_is_available(target):
			count += 1
	return count


func _clear_party_target_memory_v1() -> void:
	_party_target_memory_by_actor_v1.clear()
	_party_target_memory_by_squad_v1.clear()


func actor_id_for_party_tactics_v1(actor: Node) -> String:
	if is_instance_valid(actor) and actor.has_method("get_actor_id"):
		return str(actor.call("get_actor_id"))
	return ""


func record_party_target_sighting_v1_for_testing(actor: Node, target: Node) -> void:
	var actor_id: String = actor_id_for_party_tactics_v1(actor)
	var profile: Dictionary = _advanced_ai.get_profile(actor_id) if _advanced_ai != null and not actor_id.is_empty() else {}
	_record_party_target_sighting_v1(actor, profile, target)


func get_party_target_memory_v1_for_testing(actor: Node) -> Dictionary:
	var actor_id: String = actor_id_for_party_tactics_v1(actor)
	var profile: Dictionary = _advanced_ai.get_profile(actor_id) if _advanced_ai != null and not actor_id.is_empty() else {}
	var memory: Dictionary = _get_party_target_memory_v1(actor, profile)
	memory.erase("target")
	return memory


func get_party_tactical_context_v1_for_testing(actor: Node, target: Node, overrides: Dictionary = {}) -> Dictionary:
	if _advanced_ai == null or not actor is Node2D or not target is Node2D:
		return {}
	var actor_id: String = actor_id_for_party_tactics_v1(actor)
	var profile: Dictionary = _advanced_ai.get_profile(actor_id)
	if profile.is_empty():
		return {}
	var actor_node: Node2D = actor as Node2D
	var guard_anchor: Vector2 = _ensure_combat_ai_guard_anchor(actor_id, actor_node.global_position)
	var visible: bool = _enemy_can_see_party_target_from(actor_node.global_position, target)
	if visible:
		_record_party_target_sighting_v1(actor, profile, target)
	var memory: Dictionary = _get_party_target_memory_v1(actor, profile)
	var perceived_position: Vector2 = (target as Node2D).global_position if visible else memory.get("position", guard_anchor) as Vector2
	var context: Dictionary = _build_party_tactical_context_v1(
		actor_node,
		actor,
		target,
		profile,
		guard_anchor,
		perceived_position,
		visible,
		memory,
		{"new": false}
	)
	context.merge(overrides, true)
	return context


func choose_party_tactical_intent_v1_for_testing(actor: Node, target: Node, overrides: Dictionary = {}) -> Dictionary:
	if _advanced_ai == null:
		return {}
	var actor_id: String = actor_id_for_party_tactics_v1(actor)
	if actor_id.is_empty():
		return {}
	var context: Dictionary = get_party_tactical_context_v1_for_testing(actor, target, overrides)
	return _advanced_ai.choose_combat_intent(actor_id, context) if not context.is_empty() else {}
