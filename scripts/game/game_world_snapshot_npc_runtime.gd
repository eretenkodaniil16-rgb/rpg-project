extends "res://scripts/game/game_guard_post_polish_runtime.gd"

const WORLD_LOCATION_ID: String = "guard_post"
const WORLD_RESTORE_DELAY_FRAMES: int = 8
const NPC_COLLISION_RADIUS_PIXELS: float = 22.0
const NPC_VISIBLE_APPROACH_DISTANCE_PIXELS: float = 82.0
const NPC_VISIBLE_APPROACH_SPEED_MULTIPLIER: float = 0.72
const NPC_PATH_NODE_LIMIT: int = 512
const WORLD_ENTITY_GROUPS: Array[String] = [
	"combat_targets",
	"stealth_alert_actors",
	"context_action_targets",
	"corpse_targets"
]
const PERSISTED_GROUPS: Array[String] = [
	"combat_targets",
	"stealth_alert_actors",
	"context_action_targets",
	"corpse_targets",
	"visible_bodies",
	"bound_bodies"
]
const GRID_DIRECTIONS: Array[Vector2i] = [
	Vector2i(1, 0),
	Vector2i(-1, 0),
	Vector2i(0, 1),
	Vector2i(0, -1),
	Vector2i(1, 1),
	Vector2i(1, -1),
	Vector2i(-1, 1),
	Vector2i(-1, -1)
]

var _world_snapshot_restored: bool = false
var _world_restore_running: bool = false


func _ready() -> void:
	super._ready()
	add_to_group("world_state_serializers")
	call_deferred("_restore_world_snapshot_after_scene_ready")


func capture_world_state_for_save() -> Dictionary:
	var entities: Dictionary = {}
	for actor: Node in _persistent_world_actors():
		var entity_id: String = _persistent_entity_id(actor)
		if entity_id.is_empty():
			continue
		entities[entity_id] = _capture_actor_state(actor)
	var doors: Dictionary = {}
	for door: Node in get_tree().get_nodes_in_group("stealth_doors"):
		if not is_instance_valid(door) or not door.has_method("get_door_id") or not door.has_method("get_door_state"):
			continue
		var door_id: String = str(door.call("get_door_id"))
		if not door_id.is_empty():
			doors[door_id] = {"state": str(door.call("get_door_state"))}
	var player_facing: Vector2 = Vector2.RIGHT
	if player != null and player.has_method("get_facing_direction"):
		var facing_value: Variant = player.call("get_facing_direction")
		if facing_value is Vector2 and (facing_value as Vector2).length_squared() > 0.0001:
			player_facing = (facing_value as Vector2).normalized()
	return {
		"revision": 1,
		"location_id": WORLD_LOCATION_ID,
		"captured_at_unix": int(Time.get_unix_time_from_system()),
		"player_facing": _vector_to_value(player_facing),
		"entities": entities,
		"doors": doors,
		"environment": _capture_environment_state()
	}


func get_world_entity_state_for_testing(entity_id: String) -> Dictionary:
	var snapshot: Dictionary = capture_world_state_for_save()
	var entities_value: Variant = snapshot.get("entities", {})
	return ((entities_value as Dictionary).get(entity_id, {}) as Dictionary).duplicate(true) if entities_value is Dictionary and (entities_value as Dictionary).get(entity_id, {}) is Dictionary else {}


func restore_world_snapshot_for_testing() -> void:
	await _restore_world_snapshot()


func find_safe_world_position_for_testing(actor: Node2D, requested_position: Vector2) -> Vector2:
	return _resolve_safe_actor_position(actor, requested_position)


func _restore_world_snapshot_after_scene_ready() -> void:
	if _world_restore_running or _world_snapshot_restored:
		return
	_world_restore_running = true
	for _frame: int in range(WORLD_RESTORE_DELAY_FRAMES):
		await get_tree().process_frame
	await _restore_world_snapshot()
	_world_restore_running = false


func _restore_world_snapshot() -> void:
	if _world_snapshot_restored or not GameState.has_method("get_world_snapshot"):
		return
	var snapshot: Dictionary = GameState.call("get_world_snapshot") as Dictionary
	if snapshot.is_empty() or str(snapshot.get("location_id", "")) != WORLD_LOCATION_ID:
		_world_snapshot_restored = true
		return
	_restore_environment_state(snapshot.get("environment", {}) as Dictionary if snapshot.get("environment", {}) is Dictionary else {})
	_restore_door_states(snapshot.get("doors", {}) as Dictionary if snapshot.get("doors", {}) is Dictionary else {})
	var actors_by_id: Dictionary = {}
	for actor: Node in _persistent_world_actors():
		var entity_id: String = _persistent_entity_id(actor)
		if not entity_id.is_empty():
			actors_by_id[entity_id] = actor
	var entities_value: Variant = snapshot.get("entities", {})
	if entities_value is Dictionary:
		for entity_key: Variant in (entities_value as Dictionary).keys():
			var entity_id: String = str(entity_key)
			var actor: Node = actors_by_id.get(entity_id, null) as Node
			var state_value: Variant = (entities_value as Dictionary).get(entity_key, {})
			if is_instance_valid(actor) and state_value is Dictionary:
				_restore_actor_state(actor, state_value as Dictionary)
	var facing: Vector2 = _vector_from_value(snapshot.get("player_facing", []), Vector2.RIGHT)
	if player != null and player.has_method("set_facing_direction"):
		player.call("set_facing_direction", facing)
	_world_snapshot_restored = true
	_update_status()
	_refresh_action_catalog()


func _persistent_world_actors() -> Array[Node]:
	var result: Array[Node] = []
	var seen: Dictionary = {}
	for group_id: String in WORLD_ENTITY_GROUPS:
		for actor: Node in get_tree().get_nodes_in_group(group_id):
			if not is_instance_valid(actor) or not actor is Node2D or actor == player:
				continue
			var instance_id: int = actor.get_instance_id()
			if seen.has(instance_id) or _persistent_entity_id(actor).is_empty():
				continue
			seen[instance_id] = true
			result.append(actor)
	result.sort_custom(func(left: Node, right: Node) -> bool:
		return _persistent_entity_id(left) < _persistent_entity_id(right)
	)
	return result


func _persistent_entity_id(actor: Node) -> String:
	if not is_instance_valid(actor):
		return ""
	if actor.has_method("get_actor_id"):
		var actor_id: String = str(actor.call("get_actor_id"))
		if not actor_id.is_empty():
			return actor_id
	if actor.has_method("get_body_actor_id"):
		var body_id: String = str(actor.call("get_body_actor_id"))
		if not body_id.is_empty():
			return body_id
	return ""


func _capture_actor_state(actor: Node) -> Dictionary:
	var actor_node: Node2D = actor as Node2D
	var entity_id: String = _persistent_entity_id(actor)
	var facing: Vector2 = Vector2.DOWN
	if actor.has_method("get_facing_direction"):
		facing = actor.call("get_facing_direction") as Vector2
	var groups: Array[String] = []
	for group_id: String in PERSISTED_GROUPS:
		if actor.is_in_group(group_id):
			groups.append(group_id)
	var record: Dictionary = {}
	if not entity_id.is_empty():
		var record_value: Variant = _alert_records.get(entity_id, {})
		if record_value is Dictionary:
			record = (record_value as Dictionary).duplicate(true)
		elif GameState.has_method("get_stealth_alert_record"):
			record = GameState.call("get_stealth_alert_record", entity_id) as Dictionary
	var state: Dictionary = {
		"position": _vector_to_value(actor_node.global_position),
		"facing": _vector_to_value(facing),
		"groups": groups,
		"hostile": bool(actor.get("hostile")),
		"defeated": bool(actor.get("defeated")),
		"current_health": int(actor.call("get_current_health")) if actor.has_method("get_current_health") else 0,
		"maximum_health": int(actor.call("get_maximum_health")) if actor.has_method("get_maximum_health") else int(actor.get("maximum_health")),
		"alert_record": record
	}
	if actor.has_method("get_body_state"):
		state["body_state"] = str(actor.call("get_body_state"))
	if actor.has_method("get_detection_state"):
		state["detection_state"] = str(actor.call("get_detection_state"))
	if actor.has_method("get_suspicion"):
		state["suspicion"] = float(actor.call("get_suspicion"))
	if actor.has_method("get_last_known_position"):
		state["last_known_position"] = _vector_to_value(actor.call("get_last_known_position") as Vector2)
	return state


func _restore_actor_state(actor: Node, state: Dictionary) -> void:
	if not actor is Node2D:
		return
	var actor_node: Node2D = actor as Node2D
	var requested_position: Vector2 = _vector_from_value(state.get("position", []), actor_node.global_position)
	actor_node.global_position = _resolve_safe_actor_position(actor_node, requested_position)
	var facing: Vector2 = _vector_from_value(state.get("facing", []), Vector2.DOWN)
	if actor.has_method("set_facing_direction"):
		actor.call("set_facing_direction", facing)
	actor.set("maximum_health", maxi(int(state.get("maximum_health", actor.get("maximum_health"))), 1))
	actor.set("current_health", clampi(int(state.get("current_health", actor.get("current_health"))), 0, int(actor.get("maximum_health"))))
	actor.set("defeated", bool(state.get("defeated", false)))
	actor.set("hostile", bool(state.get("hostile", false)) and not bool(state.get("defeated", false)))
	_restore_actor_groups(actor, state.get("groups", []) as Array if state.get("groups", []) is Array else [])
	var alert_value: Variant = state.get("alert_record", {})
	var actor_id: String = _persistent_entity_id(actor)
	if alert_value is Dictionary and not actor_id.is_empty():
		var alert_record: Dictionary = (alert_value as Dictionary).duplicate(true)
		_alert_records[actor_id] = alert_record
		if actor.has_method("set_exploration_alert_state"):
			actor.call(
				"set_exploration_alert_state",
				str(alert_record.get("state", StealthAlertSystem.STATE_CALM)),
				float(alert_record.get("suspicion", 0.0)),
				_stealth_alerts.vector_from_value(alert_record.get("last_known_position", []))
			)
		_persist_alert_record(actor_id, false)
	elif actor.has_method("set_exploration_alert_state"):
		actor.call(
			"set_exploration_alert_state",
			str(state.get("detection_state", StealthAlertSystem.STATE_CALM)),
			float(state.get("suspicion", 0.0)),
			_vector_from_value(state.get("last_known_position", []), Vector2.ZERO)
		)
	if actor.has_method("_apply_body_groups") and bool(state.get("defeated", false)):
		actor.call("_apply_body_groups")
	if actor.has_method("_update_combat_visuals"):
		actor.call("_update_combat_visuals")


func _restore_actor_groups(actor: Node, stored_groups: Array) -> void:
	var membership: Dictionary = {}
	for group_value: Variant in stored_groups:
		membership[str(group_value)] = true
	for group_id: String in PERSISTED_GROUPS:
		if membership.has(group_id):
			if not actor.is_in_group(group_id):
				actor.add_to_group(group_id)
		elif actor.is_in_group(group_id):
			actor.remove_from_group(group_id)


func _capture_environment_state() -> Dictionary:
	if _combat_environment == null:
		return {}
	var cover_states: Dictionary = {}
	for obstacle: Dictionary in _combat_environment.cover_objects:
		var object_id: String = str(obstacle.get("id", ""))
		if not object_id.is_empty():
			cover_states[object_id] = bool(obstacle.get("active", true))
	var hazards: Dictionary = {}
	for hazard_key: Variant in _combat_environment.dynamic_hazards.keys():
		var value: Variant = _combat_environment.dynamic_hazards.get(hazard_key, {})
		if not value is Dictionary:
			continue
		var hazard: Dictionary = value as Dictionary
		var local_rect: Rect2 = hazard.get("rect", Rect2()) as Rect2
		var world_position: Vector2 = _combat_environment.to_global(local_rect.position)
		hazards[str(hazard_key)] = {
			"rect": [world_position.x, world_position.y, local_rect.size.x, local_rect.size.y],
			"hazard_type": str(hazard.get("hazard_type", "hazard")),
			"severity": float(hazard.get("severity", 1.0)),
			"blocks_movement": bool(hazard.get("blocks_movement", false))
		}
	return {"cover_states": cover_states, "hazards": hazards}


func _restore_environment_state(environment_state: Dictionary) -> void:
	if _combat_environment == null:
		return
	var covers_value: Variant = environment_state.get("cover_states", {})
	if covers_value is Dictionary:
		for object_key: Variant in (covers_value as Dictionary).keys():
			_combat_environment.set_cover_object_active(str(object_key), bool((covers_value as Dictionary)[object_key]), false)
	var hazards_value: Variant = environment_state.get("hazards", {})
	if hazards_value is Dictionary:
		_combat_environment.dynamic_hazards.clear()
		for hazard_key: Variant in (hazards_value as Dictionary).keys():
			var hazard_value: Variant = (hazards_value as Dictionary).get(hazard_key, {})
			if not hazard_value is Dictionary:
				continue
			var hazard: Dictionary = hazard_value as Dictionary
			var rect_value: Variant = hazard.get("rect", [])
			if not rect_value is Array or (rect_value as Array).size() < 4:
				continue
			var world_rect := Rect2(
				Vector2(float((rect_value as Array)[0]), float((rect_value as Array)[1])),
				Vector2(float((rect_value as Array)[2]), float((rect_value as Array)[3]))
			)
			_combat_environment.dynamic_hazards[str(hazard_key)] = {
				"id": str(hazard_key),
				"rect": Rect2(_combat_environment.to_local(world_rect.position), world_rect.size),
				"hazard_type": str(hazard.get("hazard_type", "hazard")),
				"severity": float(hazard.get("severity", 1.0)),
				"blocks_movement": bool(hazard.get("blocks_movement", false))
			}
		_combat_environment.call("_rebuild_collision_bodies")
		_combat_environment.queue_redraw()


func _restore_door_states(doors: Dictionary) -> void:
	for door: Node in get_tree().get_nodes_in_group("stealth_doors"):
		if not is_instance_valid(door) or not door.has_method("get_door_id") or not door.has_method("set_door_state"):
			continue
		var door_id: String = str(door.call("get_door_id"))
		var state_value: Variant = doors.get(door_id, {})
		if state_value is Dictionary:
			door.call("set_door_state", str((state_value as Dictionary).get("state", "closed")), false)


func _update_exploration_actor(actor: Node, delta: float) -> void:
	super._update_exploration_actor(actor, delta)
	if _turn_system.active or GameState.input_locked or actor == null or not is_instance_valid(actor) or not actor is Node2D:
		return
	if actor.has_method("is_combat_active") and not bool(actor.call("is_combat_active")):
		return
	var actor_id: String = str(actor.call("get_actor_id")) if actor.has_method("get_actor_id") else ""
	if actor_id.is_empty():
		return
	var profile: Dictionary = _stealth_alerts.get_profile(actor_id)
	if profile.is_empty() or not _exploration_actor_can_see_player(actor, profile):
		return
	var record: Dictionary = _record_for_actor(actor_id)
	var state: String = str(record.get("state", StealthAlertSystem.STATE_CALM))
	var updated_record: Dictionary = record
	if state == StealthAlertSystem.STATE_CALM:
		updated_record = _advance_actor_patrol(actor, record, delta)
	elif state in [StealthAlertSystem.STATE_SUSPICIOUS, StealthAlertSystem.STATE_INVESTIGATING, StealthAlertSystem.STATE_SEARCHING] and actor_id != CARETAKER_ACTOR_ID:
		var actor_node: Node2D = actor as Node2D
		var away_from_player: Vector2 = actor_node.global_position - player.global_position
		if away_from_player.length_squared() <= 0.0001:
			away_from_player = Vector2.LEFT
		var standoff_position: Vector2 = player.global_position + away_from_player.normalized() * NPC_VISIBLE_APPROACH_DISTANCE_PIXELS
		var speed: float = float(profile.get("investigation_speed_pixels", 90.0)) * NPC_VISIBLE_APPROACH_SPEED_MULTIPLIER
		var movement: Dictionary = _move_actor_safely(actor_node, standoff_position, speed, delta)
		updated_record = record.duplicate(true)
		updated_record["last_known_position"] = _stealth_alerts.vector_to_value(player.global_position)
		updated_record["navigation_used"] = bool(movement.get("used_navigation", false))
		var direction: Vector2 = movement.get("direction", Vector2.ZERO) as Vector2
		if direction.length_squared() > 0.0001 and actor.has_method("set_facing_direction"):
			actor.call("set_facing_direction", direction)
	_alert_records[actor_id] = updated_record
	_apply_record_to_actor(actor, updated_record)


func _advance_actor_patrol(actor: Node, record: Dictionary, delta: float) -> Dictionary:
	if GameState.input_locked or actor == null or not actor is Node2D:
		return record
	var actor_id: String = str(actor.call("get_actor_id"))
	var waypoint: Dictionary = _patrol_alert_groups.get_current_patrol_waypoint(actor_id, record)
	if waypoint.is_empty():
		return record
	var target_position: Vector2 = _patrol_alert_groups.get_current_patrol_target(actor_id, record)
	var config: Dictionary = _patrol_alert_groups.get_actor_config(actor_id)
	var route: Dictionary = _patrol_alert_groups.get_patrol_route(str(config.get("patrol_id", "")))
	var reached_distance: float = maxf(float(route.get("waypoint_reached_distance_pixels", 10.0)), 1.0)
	var actor_node: Node2D = actor as Node2D
	if actor_node.global_position.distance_to(target_position) > reached_distance:
		var movement: Dictionary = _move_actor_safely(actor_node, target_position, float(config.get("patrol_speed_pixels", 70.0)), delta)
		var updated_record: Dictionary = record.duplicate(true)
		updated_record["patrol_wait_remaining"] = 0.0
		updated_record["patrol_wait_initialized"] = false
		updated_record["navigation_used"] = bool(movement.get("used_navigation", false))
		updated_record["navigation_blocked"] = bool(movement.get("blocked", false))
		var direction: Vector2 = movement.get("direction", Vector2.ZERO) as Vector2
		if direction.length_squared() > 0.0001 and actor.has_method("set_facing_direction"):
			actor.call("set_facing_direction", direction)
		return updated_record
	var patrol_result: Dictionary = _patrol_alert_groups.advance_patrol(actor_id, record, actor_node.global_position, delta)
	var result_record: Dictionary = patrol_result.get("record", record) as Dictionary
	var facing: Vector2 = patrol_result.get("facing", Vector2.ZERO) as Vector2
	if facing.length_squared() > 0.0001 and actor.has_method("set_facing_direction"):
		actor.call("set_facing_direction", facing)
	return result_record


func _advance_actor_investigation(actor: Node, record: Dictionary, profile: Dictionary, delta: float) -> Dictionary:
	var state: String = str(record.get("state", StealthAlertSystem.STATE_CALM))
	if state not in [StealthAlertSystem.STATE_INVESTIGATING, StealthAlertSystem.STATE_SEARCHING, StealthAlertSystem.STATE_ALERTED]:
		return record
	if actor == null or not actor is Node2D:
		return record
	var target_position: Vector2 = _stealth_alerts.vector_from_value(record.get("last_known_position", []))
	var actor_node: Node2D = actor as Node2D
	var reached: bool = actor_node.global_position.distance_to(target_position) <= SEARCH_REACHED_DISTANCE_PIXELS
	var updated_record: Dictionary = record.duplicate(true)
	if not reached:
		var movement: Dictionary = _move_actor_safely(actor_node, target_position, float(profile.get("investigation_speed_pixels", 90.0)), delta)
		reached = bool(movement.get("reached", false))
		updated_record["navigation_used"] = bool(movement.get("used_navigation", false))
		updated_record["navigation_blocked"] = bool(movement.get("blocked", false))
		var direction: Vector2 = movement.get("direction", Vector2.ZERO) as Vector2
		if direction.length_squared() > 0.0001 and actor.has_method("set_facing_direction"):
			actor.call("set_facing_direction", direction)
	return _stealth_alerts.advance_search(updated_record, delta, reached, profile)


func _move_actor_safely(actor: Node2D, target_position: Vector2, speed_pixels: float, delta: float) -> Dictionary:
	if actor == null or not is_instance_valid(actor):
		return {"moved": false, "reached": false, "blocked": true, "used_navigation": false, "direction": Vector2.ZERO}
	_repair_actor_position_if_needed(actor)
	var grid: BattleGrid = _get_battle_grid()
	if grid == null or _combat_environment == null:
		return {"moved": false, "reached": false, "blocked": true, "used_navigation": false, "direction": Vector2.ZERO}
	var start_cell: Vector2i = grid.world_to_cell(actor.global_position)
	var requested_cell: Vector2i = grid.world_to_cell(target_position)
	var occupied: Dictionary = _occupied_cells(actor)
	var target_cell: Vector2i = _nearest_safe_cell(grid, requested_cell, occupied)
	if not grid.is_cell_valid(start_cell) or not grid.is_cell_valid(target_cell):
		return {"moved": false, "reached": false, "blocked": true, "used_navigation": false, "direction": Vector2.ZERO}
	var path: Array[Vector2i] = _find_safe_cell_path(grid, start_cell, target_cell, occupied)
	if path.is_empty():
		return {"moved": false, "reached": false, "blocked": true, "used_navigation": true, "direction": Vector2.ZERO}
	var next_position: Vector2 = target_position if path.size() <= 1 else grid.cell_to_world_center(path[1])
	if path.size() <= 1 and _combat_environment.is_position_blocked(next_position, NPC_COLLISION_RADIUS_PIXELS):
		next_position = grid.cell_to_world_center(start_cell)
	var direction: Vector2 = next_position - actor.global_position
	var previous_position: Vector2 = actor.global_position
	if direction.length_squared() > 0.0001:
		var intended: Vector2 = actor.global_position.move_toward(next_position, maxf(speed_pixels, 0.0) * maxf(delta, 0.0))
		if not _combat_environment.is_position_blocked(intended, NPC_COLLISION_RADIUS_PIXELS):
			actor.global_position = intended
	var moved: bool = actor.global_position.distance_squared_to(previous_position) > 0.0001
	var reached: bool = actor.global_position.distance_to(target_position) <= 10.0
	return {
		"moved": moved,
		"reached": reached,
		"blocked": not moved and not reached,
		"used_navigation": true,
		"direction": direction.normalized() if direction.length_squared() > 0.0001 else Vector2.ZERO,
		"next_position": next_position
	}


func _find_safe_cell_path(grid: BattleGrid, start: Vector2i, target: Vector2i, occupied: Dictionary) -> Array[Vector2i]:
	if start == target:
		return [start]
	var frontier: Array[Vector2i] = [start]
	var came_from: Dictionary = {start: start}
	var visited_count: int = 0
	while not frontier.is_empty() and visited_count < NPC_PATH_NODE_LIMIT:
		var current: Vector2i = frontier.pop_front()
		visited_count += 1
		for step: Vector2i in GRID_DIRECTIONS:
			var next: Vector2i = current + step
			if came_from.has(next) or not _cell_is_safe(grid, next, occupied):
				continue
			if _combat_environment.is_transition_blocked(grid, current, next):
				continue
			if step.x != 0 and step.y != 0 and not _diagonal_transition_is_safe(grid, current, step, occupied):
				continue
			came_from[next] = current
			if next == target:
				return _reconstruct_cell_path(came_from, start, target)
			frontier.append(next)
	return []


func _reconstruct_cell_path(came_from: Dictionary, start: Vector2i, target: Vector2i) -> Array[Vector2i]:
	var reversed: Array[Vector2i] = [target]
	var current: Vector2i = target
	while current != start and came_from.has(current):
		current = came_from[current] as Vector2i
		reversed.append(current)
	if reversed[reversed.size() - 1] != start:
		return []
	reversed.reverse()
	return reversed


func _diagonal_transition_is_safe(grid: BattleGrid, origin: Vector2i, step: Vector2i, occupied: Dictionary) -> bool:
	var horizontal: Vector2i = origin + Vector2i(step.x, 0)
	var vertical: Vector2i = origin + Vector2i(0, step.y)
	return (
		_cell_is_safe(grid, horizontal, occupied)
		and _cell_is_safe(grid, vertical, occupied)
		and not _combat_environment.is_transition_blocked(grid, origin, horizontal)
		and not _combat_environment.is_transition_blocked(grid, origin, vertical)
	)


func _cell_is_safe(grid: BattleGrid, cell: Vector2i, occupied: Dictionary) -> bool:
	if not grid.is_cell_valid(cell) or occupied.has(cell) or _combat_environment.is_cell_blocked(grid, cell):
		return false
	return not _combat_environment.is_position_blocked(grid.cell_to_world_center(cell), NPC_COLLISION_RADIUS_PIXELS)


func _nearest_safe_cell(grid: BattleGrid, requested: Vector2i, occupied: Dictionary) -> Vector2i:
	if _cell_is_safe(grid, requested, occupied):
		return requested
	for radius: int in range(1, 9):
		for y: int in range(-radius, radius + 1):
			for x: int in range(-radius, radius + 1):
				if maxi(absi(x), absi(y)) != radius:
					continue
				var candidate: Vector2i = requested + Vector2i(x, y)
				if _cell_is_safe(grid, candidate, occupied):
					return candidate
	return Vector2i(-99999, -99999)


func _repair_actor_position_if_needed(actor: Node2D) -> void:
	if actor == null or _combat_environment == null or not _combat_environment.is_position_blocked(actor.global_position, NPC_COLLISION_RADIUS_PIXELS):
		return
	actor.global_position = _resolve_safe_actor_position(actor, actor.global_position)


func _resolve_safe_actor_position(actor: Node2D, requested_position: Vector2) -> Vector2:
	var grid: BattleGrid = _get_battle_grid()
	if grid == null or _combat_environment == null:
		return requested_position
	var requested_cell: Vector2i = grid.world_to_cell(requested_position)
	var safe_cell: Vector2i = _nearest_safe_cell(grid, requested_cell, _occupied_cells(actor))
	return grid.cell_to_world_center(safe_cell) if grid.is_cell_valid(safe_cell) else actor.global_position


func _vector_to_value(value: Vector2) -> Array[float]:
	return [value.x, value.y]


func _vector_from_value(value: Variant, fallback: Vector2) -> Vector2:
	if value is Array and (value as Array).size() >= 2:
		return Vector2(float((value as Array)[0]), float((value as Array)[1]))
	if value is Vector2:
		return value as Vector2
	return fallback
