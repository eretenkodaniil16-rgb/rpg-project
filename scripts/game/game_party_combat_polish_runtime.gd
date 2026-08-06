extends "res://scripts/game/game_party_target_runtime.gd"

const PARTY_TARGET_SWITCH_MARGIN_FEET: int = 5

var _enemy_party_target_by_actor_id: Dictionary = {}
var _enemy_attack_range_by_actor_id: Dictionary = {}


func _on_active_party_target_requested() -> void:
	_close_action_catalog_immediately()
	if not _is_controllable_ally_turn():
		super._on_active_party_target_requested()
		return
	# A feedback/status overlay must not turn the target button into a dead control
	# during Irina's own turn. Only real gameplay locks block target selection.
	if GameState.input_locked or _attack_in_progress or _enemy_turn_running:
		return
	_cycle_full_irina_target()
	_refresh_party_menu()


func _update_combat_controls() -> void:
	super._update_combat_controls()
	if _target_button == null or not _is_controllable_ally_turn():
		return
	_target_button.disabled = (
		GameState.input_locked
		or _attack_in_progress
		or _enemy_turn_running
	)


func _run_enemy_turn(actor: Node) -> void:
	if not _enemy_supports_party_targeting(actor):
		await super._run_enemy_turn(actor)
		return
	var target: Node = _select_enemy_party_target(actor)
	if target != _controllable_ally:
		await super._run_enemy_turn(actor)
		return
	await _run_enemy_turn_against_irina(actor)


func _enemy_supports_party_targeting(actor: Node) -> bool:
	return (
		is_instance_valid(actor)
		and actor is Node2D
		and actor.has_method("get_actor_id")
		and _combat_ai != null
		and _combat_ai.has_profile(str(actor.call("get_actor_id")))
	)


func _select_enemy_party_target(actor: Node) -> Node:
	if not actor is Node2D:
		return player
	var actor_node: Node2D = actor as Node2D
	var actor_id: String = str(actor.call("get_actor_id")) if actor.has_method("get_actor_id") else ""
	var profile: Dictionary = _combat_ai.get_profile(actor_id) if _combat_ai != null and not actor_id.is_empty() else {}
	var attack_range_feet: int = maxi(
		int(profile.get("attack_range_feet", DistanceSystem.MELEE_REACH_FEET)),
		DistanceSystem.MELEE_REACH_FEET
	)
	var minimum_range_feet: int = maxi(int(profile.get("minimum_range_feet", 0)), 0)
	var candidates: Array[Node] = []
	if _enemy_party_target_is_available(player) and _enemy_can_see_party_target_from(actor_node.global_position, player):
		candidates.append(player)
	if _enemy_party_target_is_available(_controllable_ally) and _enemy_can_see_party_target_from(actor_node.global_position, _controllable_ally):
		candidates.append(_controllable_ally)
	if candidates.is_empty():
		_enemy_party_target_by_actor_id.erase(actor.get_instance_id())
		return player

	var previous_id: int = int(_enemy_party_target_by_actor_id.get(actor.get_instance_id(), 0))
	var selected: Node = candidates[0]
	var selected_score: float = _enemy_party_target_score(
		actor_node.global_position,
		selected,
		attack_range_feet,
		minimum_range_feet,
		previous_id
	)
	for candidate: Node in candidates.slice(1):
		var score: float = _enemy_party_target_score(
			actor_node.global_position,
			candidate,
			attack_range_feet,
			minimum_range_feet,
			previous_id
		)
		if score > selected_score + 0.0001:
			selected = candidate
			selected_score = score
	_enemy_party_target_by_actor_id[actor.get_instance_id()] = selected.get_instance_id()
	_enemy_attack_range_by_actor_id[actor.get_instance_id()] = attack_range_feet
	return selected


func _enemy_party_target_score(
	origin: Vector2,
	target: Node,
	attack_range_feet: int,
	minimum_range_feet: int,
	previous_id: int
) -> float:
	if not target is Node2D:
		return -100000.0
	var distance: int = DistanceSystem.distance_feet(origin, (target as Node2D).global_position)
	var attack_ready: bool = distance <= attack_range_feet and distance >= minimum_range_feet
	var score: float = -float(distance)
	if attack_ready:
		score += 1000.0
	if target.get_instance_id() == previous_id:
		score += 3.0
	# The hero remains the tie-breaker. Irina becomes the target only when she is
	# actually the more immediate visible threat, not by arbitrary round-robin.
	if target == player:
		score += float(PARTY_TARGET_SWITCH_MARGIN_FEET)
	return score


func _enemy_party_target_is_available(target: Node) -> bool:
	if not is_instance_valid(target) or not target is Node2D:
		return false
	if target == player:
		var character: PlayerCharacter = GameState.player_character as PlayerCharacter
		return character != null and character.current_health > 0
	if target == _controllable_ally:
		return (
			_ally_current_health() > 0
			and _ally_state() != null
			and not _ally_state().dead
			and (
				not _controllable_ally.has_method("can_receive_enemy_attack")
				or bool(_controllable_ally.call("can_receive_enemy_attack"))
			)
		)
	return false


func _enemy_can_see_party_target_from(origin: Vector2, target: Node) -> bool:
	if not target is Node2D:
		return false
	if target == player and _player_combat_state != null and _player_combat_state.hidden:
		return false
	return (
		_combat_environment == null
		or _combat_environment.has_line_of_sight(origin, (target as Node2D).global_position)
	)


func _run_enemy_turn_against_irina(actor: Node) -> void:
	if not actor is Node2D or not _turn_system.active or _turn_system.current_actor() != actor:
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
		var attack_range_feet: int = maxi(
			int(profile.get("attack_range_feet", DistanceSystem.MELEE_REACH_FEET)),
			DistanceSystem.MELEE_REACH_FEET
		)
		var minimum_range_feet: int = maxi(int(profile.get("minimum_range_feet", 0)), 0)
		var preferred_range_feet: int = clampi(
			int(profile.get("preferred_range_feet", attack_range_feet)),
			minimum_range_feet,
			attack_range_feet
		)
		var movement_feet: int = int(actor.call("get_combat_speed_feet")) if actor.has_method("get_combat_speed_feet") else 30
		var target_visible: bool = _enemy_can_see_party_target_from(actor_node.global_position, _controllable_ally)
		var distance: int = DistanceSystem.distance_feet(actor_node.global_position, (_controllable_ally as Node2D).global_position)
		var attack_ready: bool = target_visible and distance <= attack_range_feet and distance >= minimum_range_feet

		if not attack_ready and movement_feet >= GRID_STEP_FEET:
			var plan: Dictionary = _plan_enemy_movement_to_party_target(
				actor_node,
				actor,
				_controllable_ally,
				movement_feet,
				attack_range_feet,
				minimum_range_feet,
				preferred_range_feet
			)
			await _execute_combat_ai_path(
				actor_node,
				plan.get("path", []) as Array,
				NpcAiSystem.INTENT_ADVANCE
			)

		target_visible = _enemy_can_see_party_target_from(actor_node.global_position, _controllable_ally)
		distance = DistanceSystem.distance_feet(actor_node.global_position, (_controllable_ally as Node2D).global_position)
		attack_ready = target_visible and distance <= attack_range_feet and distance >= minimum_range_feet
		if attack_ready and actor.has_method("perform_combat_turn_attack"):
			_enemy_party_target_by_actor_id[actor.get_instance_id()] = _controllable_ally.get_instance_id()
			_enemy_attack_range_by_actor_id[actor.get_instance_id()] = attack_range_feet
			actor.call("perform_combat_turn_attack")
			_update_status()
			await get_tree().create_timer(0.4).timeout

	_enemy_turn_running = false
	if _party_has_living_combatant():
		_advance_combat_turn()


func _plan_enemy_movement_to_party_target(
	actor_node: Node2D,
	actor: Node,
	target: Node,
	movement_feet: int,
	attack_range_feet: int,
	minimum_range_feet: int,
	preferred_range_feet: int
) -> Dictionary:
	if not target is Node2D:
		return {"path": [], "score": -100000.0}
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return {"path": [], "score": -100000.0}
	var selected: Dictionary = {}
	var selected_score: float = -100000.0
	var target_position: Vector2 = (target as Node2D).global_position
	for candidate: Dictionary in _build_combat_ai_reachable_candidates(actor_node, movement_feet):
		var cell: Vector2i = candidate.get("cell", grid.world_to_cell(actor_node.global_position)) as Vector2i
		var position: Vector2 = grid.cell_to_world_center(cell)
		var visible: bool = _enemy_can_see_party_target_from(position, target)
		var distance: int = DistanceSystem.distance_feet(position, target_position)
		var attack_ready: bool = visible and distance <= attack_range_feet and distance >= minimum_range_feet
		var range_error: int = absi(distance - preferred_range_feet)
		var score: float = -float(range_error * 5 + int(candidate.get("cost_feet", 0)))
		if visible:
			score += 100.0
		if attack_ready:
			score += 10000.0
		candidate["score"] = score
		candidate["world_position"] = position
		candidate["target_visible"] = visible
		if selected.is_empty() or score > selected_score + 0.0001:
			selected = candidate.duplicate(true)
			selected_score = score
	if selected.is_empty():
		return {"path": [], "score": -100000.0}
	selected["score"] = selected_score
	return selected


func _enemy_should_attack_controllable_ally(attacker: Node) -> bool:
	if is_instance_valid(attacker) and is_instance_valid(_controllable_ally):
		var selected_id: int = int(_enemy_party_target_by_actor_id.get(attacker.get_instance_id(), 0))
		if selected_id == _controllable_ally.get_instance_id():
			var attack_range_feet: int = int(_enemy_attack_range_by_actor_id.get(
				attacker.get_instance_id(),
				DistanceSystem.MELEE_REACH_FEET
			))
			if attacker is Node2D and _controllable_ally is Node2D:
				var distance: int = DistanceSystem.distance_feet(
					(attacker as Node2D).global_position,
					(_controllable_ally as Node2D).global_position
				)
				return (
					distance <= attack_range_feet
					and _enemy_can_see_party_target_from((attacker as Node2D).global_position, _controllable_ally)
				)
	return super._enemy_should_attack_controllable_ally(attacker)


func _party_has_living_combatant() -> bool:
	var character: PlayerCharacter = GameState.player_character as PlayerCharacter
	return (
		(character != null and character.current_health > 0)
		or _ally_current_health() > 0
	)


func select_enemy_party_target_for_testing(actor: Node) -> Node:
	return _select_enemy_party_target(actor)


func get_enemy_party_target_instance_id_for_testing(actor: Node) -> int:
	return int(_enemy_party_target_by_actor_id.get(actor.get_instance_id(), 0)) if is_instance_valid(actor) else 0
