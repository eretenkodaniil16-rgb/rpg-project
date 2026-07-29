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

var _combat_ai: NpcCombatAiSystem
var _combat_ai_guard_anchors: Dictionary = {}
var _combat_ai_was_active: bool = false


func _ready() -> void:
	_combat_ai = NPC_COMBAT_AI_SYSTEM_SCRIPT.new() as NpcCombatAiSystem
	_npc_ai = _combat_ai
	super._ready()
	_combat_ai_was_active = _turn_system.active


func _process(delta: float) -> void:
	var active_before: bool = _turn_system.active
	super._process(delta)
	var active_after: bool = _turn_system.active
	if active_before and not active_after:
		_combat_ai_guard_anchors.clear()
	_combat_ai_was_active = active_after


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
		var intent: Dictionary = _combat_ai.choose_combat_intent(actor_id, _build_combat_ai_context(actor_node, actor, profile, guard_anchor))
		var intent_id: String = str(intent.get("intent", NpcAiSystem.INTENT_WAIT))
		var movement_feet: int = int(actor.call("get_combat_speed_feet")) if actor.has_method("get_combat_speed_feet") else 30
		var attack_range_feet: int = int(intent.get("attack_range_feet", DistanceSystem.MELEE_REACH_FEET))
		var minimum_range_feet: int = int(intent.get("minimum_range_feet", 0))
		var preferred_range_feet: int = int(intent.get("preferred_range_feet", attack_range_feet))

		match intent_id:
			NpcAiSystem.INTENT_RETREAT:
				while movement_feet >= GRID_STEP_FEET and _move_combat_ai_one_step(actor_node, player.global_position, false):
					movement_feet -= GRID_STEP_FEET
					await get_tree().create_timer(0.12).timeout
			NpcCombatAiSystem.INTENT_REPOSITION:
				while movement_feet >= GRID_STEP_FEET and DistanceSystem.distance_feet(actor_node.global_position, player.global_position) < minimum_range_feet:
					if not _move_combat_ai_one_step(actor_node, player.global_position, false):
						break
					movement_feet -= GRID_STEP_FEET
					await get_tree().create_timer(0.12).timeout
			NpcAiSystem.INTENT_ADVANCE, NpcCombatAiSystem.INTENT_INTERCEPT:
				while movement_feet >= GRID_STEP_FEET:
					var current_distance: int = DistanceSystem.distance_feet(actor_node.global_position, player.global_position)
					var current_visible: bool = _combat_environment == null or _combat_environment.has_line_of_sight(actor_node.global_position, player.global_position)
					if current_distance <= preferred_range_feet and current_visible:
						break
					if not _move_combat_ai_one_step(actor_node, player.global_position, true):
						break
					movement_feet -= GRID_STEP_FEET
					await get_tree().create_timer(0.12).timeout
			NpcCombatAiSystem.INTENT_GUARD:
				while movement_feet >= GRID_STEP_FEET and DistanceSystem.distance_feet(actor_node.global_position, guard_anchor) > int(profile.get("guard_return_tolerance_feet", DistanceSystem.MELEE_REACH_FEET)):
					if not _move_combat_ai_one_step(actor_node, guard_anchor, true):
						break
					movement_feet -= GRID_STEP_FEET
					await get_tree().create_timer(0.12).timeout
			NpcAiSystem.INTENT_WAIT:
				show_combat_message("%s удерживает позицию." % _target_name(actor), true)

		var distance_after_movement: int = DistanceSystem.distance_feet(actor_node.global_position, player.global_position)
		var target_visible_after_movement: bool = _combat_environment == null or _combat_environment.has_line_of_sight(actor_node.global_position, player.global_position)
		if intent_id in [NpcAiSystem.INTENT_ATTACK, NpcAiSystem.INTENT_ADVANCE, NpcCombatAiSystem.INTENT_REPOSITION, NpcCombatAiSystem.INTENT_INTERCEPT] and distance_after_movement <= attack_range_feet and target_visible_after_movement:
			if actor.has_method("perform_combat_turn_attack"):
				actor.call("perform_combat_turn_attack")
				_update_status()
				await get_tree().create_timer(0.4).timeout

	_enemy_turn_running = false
	var character: PlayerCharacter = GameState.player_character as PlayerCharacter
	if character != null and character.current_health > 0:
		_advance_combat_turn()


func _build_combat_ai_context(actor_node: Node2D, actor: Node, profile: Dictionary, guard_anchor: Vector2) -> Dictionary:
	var distance: int = DistanceSystem.distance_feet(actor_node.global_position, player.global_position)
	var current_health: int = int(actor.call("get_current_health")) if actor.has_method("get_current_health") else 1
	var maximum_health: int = int(actor.call("get_maximum_health")) if actor.has_method("get_maximum_health") else maxi(current_health, 1)
	var target_visible: bool = _combat_environment == null or _combat_environment.has_line_of_sight(actor_node.global_position, player.global_position)
	var attack_range_feet: int = maxi(int(profile.get("attack_range_feet", DistanceSystem.MELEE_REACH_FEET)), DistanceSystem.MELEE_REACH_FEET)
	return {
		"distance_feet": distance,
		"actor_health_ratio": float(current_health) / float(maxi(maximum_health, 1)),
		"target_visible": target_visible,
		"can_attack": distance <= attack_range_feet,
		"can_move": int(actor.call("get_combat_speed_feet")) > 0 if actor.has_method("get_combat_speed_feet") else true,
		"distance_from_guard_anchor_feet": DistanceSystem.distance_feet(actor_node.global_position, guard_anchor),
		"target_distance_from_guard_anchor_feet": DistanceSystem.distance_feet(player.global_position, guard_anchor)
	}


func _ensure_combat_ai_guard_anchor(actor_id: String, current_position: Vector2) -> Vector2:
	if not _combat_ai_guard_anchors.has(actor_id):
		_combat_ai_guard_anchors[actor_id] = current_position
	return _combat_ai_guard_anchors.get(actor_id, current_position) as Vector2


func _move_combat_ai_one_step(actor: Node2D, target_position: Vector2, toward_target: bool) -> bool:
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return false
	var actor_cell: Vector2i = grid.world_to_cell(actor.global_position)
	var occupied: Dictionary = _occupied_cells(actor)
	var candidate_steps: Array[Vector2i] = []
	candidate_steps.assign(AI_GRID_DIRECTIONS)
	candidate_steps.sort_custom(func(left: Vector2i, right: Vector2i) -> bool:
		var left_position: Vector2 = grid.cell_to_world_center(actor_cell + left)
		var right_position: Vector2 = grid.cell_to_world_center(actor_cell + right)
		var left_distance: float = left_position.distance_squared_to(target_position)
		var right_distance: float = right_position.distance_squared_to(target_position)
		if not toward_target:
			left_distance = -left_distance
			right_distance = -right_distance
		if not is_equal_approx(left_distance, right_distance):
			return left_distance < right_distance
		return left.x < right.x or (left.x == right.x and left.y < right.y)
	)
	for step: Vector2i in candidate_steps:
		var destination_cell: Vector2i = actor_cell + step
		if not grid.is_cell_valid(destination_cell) or occupied.has(destination_cell):
			continue
		if _combat_environment != null and _combat_environment.is_cell_blocked(grid, destination_cell):
			continue
		actor.global_position = grid.cell_to_world_center(destination_cell)
		return true
	return false


func get_combat_ai_role_profile_for_testing(role_id: String) -> Dictionary:
	return _combat_ai.get_role_profile(role_id) if _combat_ai != null else {}


func get_combat_ai_profile_for_testing(actor_id: String) -> Dictionary:
	return _combat_ai.get_profile(actor_id) if _combat_ai != null else {}


func get_combat_ai_anchor_for_testing(actor_id: String) -> Vector2:
	return _combat_ai_guard_anchors.get(actor_id, Vector2.ZERO) as Vector2
