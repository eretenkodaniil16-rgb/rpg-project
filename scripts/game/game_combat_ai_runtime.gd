extends "res://scripts/game/game_pursuit_escape_runtime.gd"

const NPC_COMBAT_AI_SYSTEM_SCRIPT: Script = preload("res://scripts/systems/npc_combat_ai_system.gd")
const AI_GRID_DIRECTIONS: Array[Vector2i] = [
	Vector2i(1, 0),
	Vector2i(-1, 0),
	Vector2i(0, 1),
	Vector2i(0, -1),
	Vector2i(1, 1),
	Vector2i(1, -1),
	Vector2i(-1, 1),
	Vector2i(-1, -1)
]
const AI_MOVEMENT_INTENTS: Array[String] = [
	NpcAiSystem.INTENT_ADVANCE,
	NpcAiSystem.INTENT_RETREAT,
	NpcCombatAiSystem.INTENT_REPOSITION,
	NpcCombatAiSystem.INTENT_INTERCEPT,
	NpcCombatAiSystem.INTENT_SEARCH,
	NpcCombatAiSystem.INTENT_GUARD
]

var _combat_ai: NpcCombatAiSystem
var _combat_ai_guard_anchors: Dictionary = {}
var _combat_ai_actor_memory: Dictionary = {}
var _combat_ai_squad_memory: Dictionary = {}


func _ready() -> void:
	_combat_ai = NPC_COMBAT_AI_SYSTEM_SCRIPT.new() as NpcCombatAiSystem
	_npc_ai = _combat_ai
	super._ready()


func _process(delta: float) -> void:
	var active_before: bool = _turn_system.active
	super._process(delta)
	if active_before and not _turn_system.active:
		_clear_combat_ai_runtime_state()


func _run_enemy_turn(actor: Node) -> void:
	if actor == null or not actor.has_method("get_actor_id") or _combat_ai == null or not _combat_ai.has_profile(str(actor.call("get_actor_id"))):
		await super._run_enemy_turn(actor)
		return
	if not (actor is Node2D) or not _turn_system.active or _turn_system.current_actor() != actor:
		return

	_enemy_turn_running = true
	_refresh_turn_interface()
	while _turn_system.active and _any_overlay_visible():
		await get_tree().process_frame
	await get_tree().create_timer(0.35).timeout

	if is_instance_valid(actor) and (not actor.has_method("can_take_combat_turn") or bool(actor.call("can_take_combat_turn"))):
		var actor_node: Node2D = actor as Node2D
		var actor_id: String = str(actor.call("get_actor_id"))
		var profile: Dictionary = _combat_ai.get_profile(actor_id)
		var guard_anchor: Vector2 = _ensure_combat_ai_guard_anchor(actor_id, actor_node.global_position)
		var target_visible: bool = _combat_ai_can_see_player_from(actor_node.global_position)
		if target_visible:
			_record_combat_ai_target_sighting(actor_id, profile, player.global_position)
		var target_memory: Dictionary = _get_combat_ai_target_memory(actor_id, profile)
		var has_target_memory: bool = not target_memory.is_empty()
		var perceived_target_position: Vector2 = player.global_position if target_visible else (target_memory.get("position", guard_anchor) as Vector2 if has_target_memory else guard_anchor)
		var context: Dictionary = _build_combat_ai_context(actor_node, actor, profile, guard_anchor, perceived_target_position, target_visible, target_memory)
		var intent: Dictionary = _combat_ai.choose_combat_intent(actor_id, context)
		var intent_id: String = str(intent.get("intent", NpcAiSystem.INTENT_WAIT))
		var movement_feet: int = int(actor.call("get_combat_speed_feet")) if actor.has_method("get_combat_speed_feet") else 30
		var attack_range_feet: int = int(intent.get("attack_range_feet", DistanceSystem.MELEE_REACH_FEET))

		if intent_id in AI_MOVEMENT_INTENTS and movement_feet >= GRID_STEP_FEET:
			var objective_position: Vector2 = guard_anchor if intent_id == NpcCombatAiSystem.INTENT_GUARD else perceived_target_position
			var plan: Dictionary = _plan_combat_ai_movement(actor_node, actor, profile, guard_anchor, objective_position, intent_id, movement_feet)
			await _execute_combat_ai_path(actor_node, plan.get("path", []) as Array, intent_id)
		elif intent_id == NpcAiSystem.INTENT_WAIT:
			show_combat_message("%s удерживает позицию: подтверждённая цель потеряна." % _target_name(actor), true)

		var visible_after_movement: bool = _combat_ai_can_see_player_from(actor_node.global_position)
		if visible_after_movement:
			_record_combat_ai_target_sighting(actor_id, profile, player.global_position)
		elif intent_id == NpcCombatAiSystem.INTENT_SEARCH and has_target_memory:
			var searched_position: Vector2 = target_memory.get("position", perceived_target_position) as Vector2
			if DistanceSystem.distance_feet(actor_node.global_position, searched_position) <= DistanceSystem.MELEE_REACH_FEET:
				_invalidate_combat_ai_target_memory(actor_id, profile, searched_position)
				show_combat_message("%s проверяет последнюю известную позицию, но не находит цель." % _target_name(actor), true)

		var distance_after_movement: int = DistanceSystem.distance_feet(actor_node.global_position, player.global_position)
		if intent_id not in [NpcAiSystem.INTENT_RETREAT, NpcAiSystem.INTENT_WAIT] and visible_after_movement and distance_after_movement <= attack_range_feet:
			if actor.has_method("perform_combat_turn_attack"):
				actor.call("perform_combat_turn_attack")
				_update_status()
				await get_tree().create_timer(0.4).timeout

	_enemy_turn_running = false
	var character: PlayerCharacter = GameState.player_character as PlayerCharacter
	if character != null and character.current_health > 0:
		_advance_combat_turn()


func _build_combat_ai_context(
	actor_node: Node2D,
	actor: Node,
	profile: Dictionary,
	guard_anchor: Vector2,
	perceived_target_position: Vector2,
	target_visible: bool,
	target_memory: Dictionary
) -> Dictionary:
	var distance: int = DistanceSystem.distance_feet(actor_node.global_position, perceived_target_position)
	var current_health: int = int(actor.call("get_current_health")) if actor.has_method("get_current_health") else 1
	var maximum_health: int = int(actor.call("get_maximum_health")) if actor.has_method("get_maximum_health") else maxi(current_health, 1)
	var attack_range_feet: int = maxi(int(profile.get("attack_range_feet", DistanceSystem.MELEE_REACH_FEET)), DistanceSystem.MELEE_REACH_FEET)
	var team_state: Dictionary = _combat_ai_team_state(actor)
	return {
		"distance_feet": distance,
		"actor_health_ratio": float(current_health) / float(maxi(maximum_health, 1)),
		"target_visible": target_visible,
		"has_target_memory": not target_memory.is_empty(),
		"memory_confidence": float(target_memory.get("confidence", 0.0)),
		"can_attack": target_visible and distance <= attack_range_feet,
		"can_move": int(actor.call("get_combat_speed_feet")) > 0 if actor.has_method("get_combat_speed_feet") else true,
		"distance_from_guard_anchor_feet": DistanceSystem.distance_feet(actor_node.global_position, guard_anchor),
		"target_distance_from_guard_anchor_feet": DistanceSystem.distance_feet(perceived_target_position, guard_anchor),
		"ally_count": int(team_state.get("ally_count", 1)),
		"hostile_count": int(team_state.get("hostile_count", 1)),
		"defeated_ally_count": int(team_state.get("defeated_ally_count", 0)),
		"escape_route_count": _combat_ai_mobility_from(actor_node, actor_node.global_position),
		"target_health_ratio": _combat_ai_player_health_ratio()
	}


func _plan_combat_ai_movement(
	actor_node: Node2D,
	actor: Node,
	profile: Dictionary,
	guard_anchor: Vector2,
	objective_position: Vector2,
	intent_id: String,
	movement_feet: int
) -> Dictionary:
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return {"path": [], "score": NpcCombatAiSystem.BLOCKED_SCORE}
	var candidates: Array[Dictionary] = _build_combat_ai_reachable_candidates(actor_node, movement_feet)
	var selected: Dictionary = {}
	var selected_score: float = NpcCombatAiSystem.BLOCKED_SCORE
	for candidate: Dictionary in candidates:
		var cell: Vector2i = candidate.get("cell", grid.world_to_cell(actor_node.global_position)) as Vector2i
		var position: Vector2 = grid.cell_to_world_center(cell)
		var target_visible: bool = _combat_ai_can_see_player_from(position)
		var distance_to_player: int = DistanceSystem.distance_feet(position, player.global_position)
		var attack_range_feet: int = maxi(int(profile.get("attack_range_feet", DistanceSystem.MELEE_REACH_FEET)), DistanceSystem.MELEE_REACH_FEET)
		var candidate_context: Dictionary = {
			"valid": true,
			"distance_feet": distance_to_player if target_visible else DistanceSystem.distance_feet(position, objective_position),
			"distance_to_objective_feet": DistanceSystem.distance_feet(position, objective_position),
			"distance_from_guard_anchor_feet": DistanceSystem.distance_feet(position, guard_anchor),
			"nearest_ally_distance_feet": _nearest_combat_ai_ally_distance(actor, position),
			"mobility": _combat_ai_mobility_from(actor_node, position),
			"path_cost_feet": int(candidate.get("cost_feet", 0)),
			"target_visible": target_visible,
			"attack_ready": target_visible and distance_to_player <= attack_range_feet
		}
		var score: float = _combat_ai.score_candidate_position(intent_id, profile, {}, candidate_context)
		candidate["score"] = score
		candidate["world_position"] = position
		candidate["target_visible"] = target_visible
		if _combat_ai_candidate_is_better(candidate, score, selected, selected_score):
			selected = candidate.duplicate(true)
			selected_score = score
	if selected.is_empty():
		return {"path": [], "score": NpcCombatAiSystem.BLOCKED_SCORE}
	selected["score"] = selected_score
	return selected


func _build_combat_ai_reachable_candidates(actor: Node2D, movement_feet: int) -> Array[Dictionary]:
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return []
	var start_cell: Vector2i = grid.world_to_cell(actor.global_position)
	var maximum_cost: int = maxi(movement_feet, 0)
	var occupied: Dictionary = _occupied_cells(actor)
	var frontier: Array[Vector2i] = [start_cell]
	var costs: Dictionary = {start_cell: 0}
	var paths: Dictionary = {start_cell: []}
	var candidates: Array[Dictionary] = []

	while not frontier.is_empty():
		var current_cell: Vector2i = frontier.pop_front()
		var current_cost: int = int(costs.get(current_cell, 0))
		var current_path: Array = paths.get(current_cell, []) as Array
		candidates.append({"cell": current_cell, "cost_feet": current_cost, "path": current_path.duplicate()})
		for step: Vector2i in AI_GRID_DIRECTIONS:
			var destination_cell: Vector2i = current_cell + step
			var next_cost: int = current_cost + GRID_STEP_FEET
			if next_cost > maximum_cost or not _combat_ai_cell_is_available(grid, destination_cell, occupied):
				continue
			if abs(step.x) == 1 and abs(step.y) == 1 and not _combat_ai_diagonal_step_allowed(grid, current_cell, step, occupied):
				continue
			if costs.has(destination_cell) and int(costs[destination_cell]) <= next_cost:
				continue
			var next_path: Array = current_path.duplicate()
			next_path.append(destination_cell)
			costs[destination_cell] = next_cost
			paths[destination_cell] = next_path
			frontier.append(destination_cell)
	return candidates


func _combat_ai_cell_is_available(grid: BattleGrid, cell: Vector2i, occupied: Dictionary) -> bool:
	if not grid.is_cell_valid(cell) or occupied.has(cell):
		return false
	return _combat_environment == null or not _combat_environment.is_cell_blocked(grid, cell)


func _combat_ai_diagonal_step_allowed(grid: BattleGrid, origin: Vector2i, step: Vector2i, occupied: Dictionary) -> bool:
	var horizontal: Vector2i = origin + Vector2i(step.x, 0)
	var vertical: Vector2i = origin + Vector2i(0, step.y)
	return _combat_ai_cell_is_available(grid, horizontal, occupied) and _combat_ai_cell_is_available(grid, vertical, occupied)


func _combat_ai_candidate_is_better(candidate: Dictionary, score: float, selected: Dictionary, selected_score: float) -> bool:
	if selected.is_empty() or score > selected_score + 0.0001:
		return true
	if not is_equal_approx(score, selected_score):
		return false
	var candidate_cost: int = int(candidate.get("cost_feet", 0))
	var selected_cost: int = int(selected.get("cost_feet", 0))
	if candidate_cost != selected_cost:
		return candidate_cost < selected_cost
	var candidate_cell: Vector2i = candidate.get("cell", Vector2i.ZERO) as Vector2i
	var selected_cell: Vector2i = selected.get("cell", Vector2i.ZERO) as Vector2i
	return candidate_cell.x < selected_cell.x or (candidate_cell.x == selected_cell.x and candidate_cell.y < selected_cell.y)


func _execute_combat_ai_path(actor: Node2D, path: Array, intent_id: String) -> void:
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return
	for value: Variant in path:
		if not value is Vector2i:
			continue
		var cell: Vector2i = value as Vector2i
		actor.global_position = grid.cell_to_world_center(cell)
		await get_tree().create_timer(0.1).timeout
		if intent_id == NpcCombatAiSystem.INTENT_SEARCH and _combat_ai_can_see_player_from(actor.global_position):
			break


func _combat_ai_can_see_player_from(position: Vector2) -> bool:
	if player == null:
		return false
	if _player_combat_state != null and _player_combat_state.hidden:
		return false
	return _combat_environment == null or _combat_environment.has_line_of_sight(position, player.global_position)


func _record_combat_ai_target_sighting(actor_id: String, profile: Dictionary, target_position: Vector2) -> void:
	var record: Dictionary = {
		"position": target_position,
		"round": _turn_system.round_number,
		"source_actor_id": actor_id
	}
	_combat_ai_actor_memory[actor_id] = record.duplicate(true)
	var squad_id: String = str(profile.get("squad_id", ""))
	if not squad_id.is_empty() and bool(profile.get("shares_target_information", true)):
		_combat_ai_squad_memory[squad_id] = record.duplicate(true)


func _get_combat_ai_target_memory(actor_id: String, profile: Dictionary) -> Dictionary:
	var memory_rounds: int = maxi(int(profile.get("memory_rounds", 2)), 0)
	var actor_record: Dictionary = _combat_ai_actor_memory.get(actor_id, {}) as Dictionary if _combat_ai_actor_memory.get(actor_id, {}) is Dictionary else {}
	var valid_actor_record: Dictionary = _validated_combat_ai_memory(actor_record, memory_rounds)
	if not valid_actor_record.is_empty():
		return valid_actor_record
	if not bool(profile.get("shares_target_information", true)):
		return {}
	var squad_id: String = str(profile.get("squad_id", ""))
	var squad_record: Dictionary = _combat_ai_squad_memory.get(squad_id, {}) as Dictionary if _combat_ai_squad_memory.get(squad_id, {}) is Dictionary else {}
	return _validated_combat_ai_memory(squad_record, memory_rounds)


func _validated_combat_ai_memory(record: Dictionary, memory_rounds: int) -> Dictionary:
	if record.is_empty() or not record.get("position", null) is Vector2:
		return {}
	var age: int = maxi(_turn_system.round_number - int(record.get("round", _turn_system.round_number)), 0)
	if age > memory_rounds:
		return {}
	var result: Dictionary = record.duplicate(true)
	result["age_rounds"] = age
	result["confidence"] = 1.0 if memory_rounds <= 0 else clampf(1.0 - float(age) / float(memory_rounds + 1), 0.0, 1.0)
	return result


func _invalidate_combat_ai_target_memory(actor_id: String, profile: Dictionary, searched_position: Vector2) -> void:
	_combat_ai_actor_memory.erase(actor_id)
	var squad_id: String = str(profile.get("squad_id", ""))
	if squad_id.is_empty():
		return
	var squad_record: Dictionary = _combat_ai_squad_memory.get(squad_id, {}) as Dictionary if _combat_ai_squad_memory.get(squad_id, {}) is Dictionary else {}
	if squad_record.get("position", null) is Vector2 and DistanceSystem.distance_feet(squad_record.get("position", searched_position) as Vector2, searched_position) <= DistanceSystem.MELEE_REACH_FEET:
		_combat_ai_squad_memory.erase(squad_id)


func _combat_ai_team_state(actor: Node) -> Dictionary:
	var ally_count: int = 0
	var defeated_ally_count: int = 0
	for entry: Dictionary in _turn_system.entries:
		var participant: Node = entry.get("node") as Node
		if not is_instance_valid(participant) or participant == player or bool(entry.get("is_player", false)):
			continue
		if participant.has_method("is_combat_active") and not bool(participant.call("is_combat_active")):
			defeated_ally_count += 1
		else:
			ally_count += 1
	if ally_count <= 0 and actor != null:
		ally_count = 1
	var character: PlayerCharacter = GameState.player_character as PlayerCharacter
	return {
		"ally_count": ally_count,
		"defeated_ally_count": defeated_ally_count,
		"hostile_count": 1 if character != null and character.current_health > 0 else 0
	}


func _nearest_combat_ai_ally_distance(actor: Node, position: Vector2) -> int:
	var nearest: int = 9999
	for entry: Dictionary in _turn_system.entries:
		var participant: Node = entry.get("node") as Node
		if not is_instance_valid(participant) or participant == actor or participant == player or bool(entry.get("is_player", false)) or not (participant is Node2D):
			continue
		if participant.has_method("is_combat_active") and not bool(participant.call("is_combat_active")):
			continue
		nearest = mini(nearest, DistanceSystem.distance_feet(position, (participant as Node2D).global_position))
	return nearest


func _combat_ai_mobility_from(actor: Node2D, position: Vector2) -> int:
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return 0
	var origin: Vector2i = grid.world_to_cell(position)
	var occupied: Dictionary = _occupied_cells(actor)
	var count: int = 0
	for step: Vector2i in AI_GRID_DIRECTIONS:
		var destination: Vector2i = origin + step
		if _combat_ai_cell_is_available(grid, destination, occupied):
			count += 1
	return count


func _combat_ai_player_health_ratio() -> float:
	var character: PlayerCharacter = GameState.player_character as PlayerCharacter
	if character == null:
		return 0.0
	return float(character.current_health) / float(maxi(character.maximum_health, 1))


func _ensure_combat_ai_guard_anchor(actor_id: String, current_position: Vector2) -> Vector2:
	if not _combat_ai_guard_anchors.has(actor_id):
		_combat_ai_guard_anchors[actor_id] = current_position
	return _combat_ai_guard_anchors.get(actor_id, current_position) as Vector2


func _clear_combat_ai_runtime_state() -> void:
	_combat_ai_guard_anchors.clear()
	_combat_ai_actor_memory.clear()
	_combat_ai_squad_memory.clear()


func get_combat_ai_role_profile_for_testing(role_id: String) -> Dictionary:
	return _combat_ai.get_role_profile(role_id) if _combat_ai != null else {}


func get_combat_ai_profile_for_testing(actor_id: String) -> Dictionary:
	return _combat_ai.get_profile(actor_id) if _combat_ai != null else {}


func get_combat_ai_anchor_for_testing(actor_id: String) -> Vector2:
	return _combat_ai_guard_anchors.get(actor_id, Vector2.ZERO) as Vector2


func record_combat_ai_sighting_for_testing(actor_id: String, target_position: Vector2) -> void:
	if _combat_ai == null:
		return
	_record_combat_ai_target_sighting(actor_id, _combat_ai.get_profile(actor_id), target_position)


func get_combat_ai_memory_for_testing(actor_id: String) -> Dictionary:
	return _get_combat_ai_target_memory(actor_id, _combat_ai.get_profile(actor_id)) if _combat_ai != null else {}


func plan_combat_ai_movement_for_testing(actor: Node2D, actor_id: String, objective_position: Vector2, intent_id: String, movement_feet: int) -> Dictionary:
	if _combat_ai == null or actor == null:
		return {}
	var profile: Dictionary = _combat_ai.get_profile(actor_id)
	var anchor: Vector2 = _ensure_combat_ai_guard_anchor(actor_id, actor.global_position)
	return _plan_combat_ai_movement(actor, actor, profile, anchor, objective_position, intent_id, movement_feet)
