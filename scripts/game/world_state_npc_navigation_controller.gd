class_name WorldStateNpcNavigationController
extends Node

const NAVIGATION_SCRIPT: Script = preload("res://scripts/systems/obstacle_aware_npc_navigation_system.gd")
const WORLD_LOCATION_ID: String = "guard_post"
const RESTORE_DELAY_FRAMES: int = 10
const TRIGGER_SCALE: float = 1.35
const VISIBLE_STANDOFF_PIXELS: float = 82.0
const VISIBLE_SPEED_MULTIPLIER: float = 0.72
const FOG_Z_INDEX: int = 45
const WALL_Z_INDEX: int = 50
const DOOR_Z_INDEX: int = 51
const ENTITY_GROUPS: Array[String] = [
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

var _game: Node
var _player: Node2D
var _navigation: ObstacleAwareNpcNavigationSystem
var _restored: bool = false
var _restore_running: bool = false
var _last_valid_positions: Dictionary = {}


func _ready() -> void:
	_game = get_parent()
	_player = get_tree().get_first_node_in_group("player") as Node2D
	_navigation = NAVIGATION_SCRIPT.new() as ObstacleAwareNpcNavigationSystem
	add_to_group("world_state_serializers")
	_install_navigation_backend()
	call_deferred("_restore_after_scene_ready")
	call_deferred("_expand_npc_trigger_zones")
	call_deferred("_configure_occlusion_rendering")


func _process(delta: float) -> void:
	if not is_instance_valid(_game):
		return
	if not is_instance_valid(_player):
		_player = get_tree().get_first_node_in_group("player") as Node2D
	_install_navigation_backend()
	_repair_invalid_actor_positions()
	_update_visible_actor_movement(delta)


func _unhandled_input(event: InputEvent) -> void:
	if not _can_accept_exploration_pointer():
		return
	var screen_position: Vector2 = Vector2.INF
	if event is InputEventScreenTouch:
		var touch: InputEventScreenTouch = event as InputEventScreenTouch
		if touch.pressed:
			screen_position = touch.position
	elif event is InputEventMouseButton:
		var mouse: InputEventMouseButton = event as InputEventMouseButton
		if mouse.pressed and mouse.button_index == MOUSE_BUTTON_LEFT:
			screen_position = mouse.position
	if screen_position == Vector2.INF:
		return
	var world_position: Vector2 = get_viewport().get_canvas_transform().affine_inverse() * screen_position
	var path: Array[Vector2] = _navigation.build_world_path(_player, world_position)
	if path.is_empty():
		_game.call("show_combat_message", "До выбранной точки нет безопасного пути.", false)
	elif _player.has_method("set_exploration_click_path"):
		_player.call("set_exploration_click_path", path)
		_game.call("show_combat_message", "Маршрут выбран касанием. Джойстик меняет только направление взгляда.", true)
	get_viewport().set_input_as_handled()


func can_capture_stable_world_state() -> bool:
	if not is_instance_valid(_game):
		return true
	var turn_system_value: Variant = _game.get("_turn_system")
	var turn_active: bool = turn_system_value is TurnBasedCombatSystem and (turn_system_value as TurnBasedCombatSystem).active
	return (
		not turn_active
		and not bool(_game.get("_movement_execution_running"))
		and not bool(_game.get("_attack_in_progress"))
		and not bool(_game.get("_enemy_turn_running"))
		and not bool(_game.get("_jump_in_progress"))
	)


func capture_world_state_for_save() -> Dictionary:
	var entities: Dictionary = {}
	for actor: Node in _persistent_world_actors():
		var actor_id: String = _actor_id(actor)
		if not actor_id.is_empty():
			entities[actor_id] = _capture_actor(actor)
	var doors: Dictionary = {}
	for door: Node in get_tree().get_nodes_in_group("stealth_doors"):
		if is_instance_valid(door) and door.has_method("get_door_id") and door.has_method("get_door_state"):
			var door_id: String = str(door.call("get_door_id"))
			if not door_id.is_empty():
				doors[door_id] = {"state": str(door.call("get_door_state"))}
	var facing: Vector2 = Vector2.RIGHT
	if is_instance_valid(_player) and _player.has_method("get_facing_direction"):
		facing = _player.call("get_facing_direction") as Vector2
	return {
		"revision": 1,
		"location_id": WORLD_LOCATION_ID,
		"captured_at_unix": int(Time.get_unix_time_from_system()),
		"player_facing": _vector_to_value(facing),
		"entities": entities,
		"doors": doors,
		"environment": _capture_environment()
	}


func plan_exploration_path_to_world_for_testing(world_position: Vector2) -> Array[Vector2]:
	return _navigation.build_world_path(_player, world_position) if _navigation != null and is_instance_valid(_player) else []


func find_safe_world_position_for_testing(actor: Node2D, position: Vector2) -> Vector2:
	return _navigation.resolve_safe_position(actor, position) if _navigation != null else position


func get_world_entity_state_for_testing(actor_id: String) -> Dictionary:
	for actor: Node in _persistent_world_actors():
		if _actor_id(actor) == actor_id:
			return _capture_actor(actor)
	return {}


func get_npc_trigger_extent_for_testing(actor_id: String) -> Vector2:
	for actor: Node in _persistent_world_actors():
		if _actor_id(actor) != actor_id:
			continue
		var collision: CollisionShape2D = _interaction_collision(actor)
		if collision == null or collision.shape == null:
			return Vector2.ZERO
		if collision.shape is CircleShape2D:
			var radius: float = (collision.shape as CircleShape2D).radius
			return Vector2(radius, radius)
		if collision.shape is RectangleShape2D:
			return (collision.shape as RectangleShape2D).size
	return Vector2.ZERO


func get_visibility_render_order_for_testing() -> Dictionary:
	var fog: CanvasItem = get_tree().get_first_node_in_group("player_visibility") as CanvasItem
	var room: Node = _game.get_node_or_null("StealthTestRoom") if is_instance_valid(_game) else null
	var wall: Polygon2D = room.get_node_or_null("WestPartitionTop/Polygon2D") as Polygon2D if room != null else null
	var door_visual: Polygon2D = null
	var doors: Array[Node] = get_tree().get_nodes_in_group("stealth_doors")
	if not doors.is_empty() and is_instance_valid(doors[0]):
		door_visual = doors[0].get_node_or_null("Visual") as Polygon2D
	return {
		"fog_z": fog.z_index if fog != null else -1,
		"wall_z": wall.z_index if wall != null else -1,
		"door_z": door_visual.z_index if door_visual != null else -1
	}


func restore_world_snapshot_for_testing() -> void:
	_restored = false
	await _restore_world_snapshot()


func _install_navigation_backend() -> void:
	if is_instance_valid(_game) and _navigation != null:
		_game.set("_npc_navigation", _navigation)


func _can_accept_exploration_pointer() -> bool:
	if not is_instance_valid(_game) or not is_instance_valid(_player) or GameState.input_locked:
		return false
	var turn_system_value: Variant = _game.get("_turn_system")
	if turn_system_value is TurnBasedCombatSystem and (turn_system_value as TurnBasedCombatSystem).active:
		return false
	if bool(_game.get("_attack_in_progress")) or bool(_game.get("_enemy_turn_running")):
		return false
	if _game.has_method("_any_overlay_visible") and bool(_game.call("_any_overlay_visible")):
		return false
	var catalog: Node = _game.get_node_or_null("Interface/ActionCatalogUI")
	return catalog == null or not catalog.has_method("is_catalog_open") or not bool(catalog.call("is_catalog_open"))


func _restore_after_scene_ready() -> void:
	if _restore_running or _restored:
		return
	_restore_running = true
	for _frame: int in range(RESTORE_DELAY_FRAMES):
		await get_tree().process_frame
	await _restore_world_snapshot()
	_restore_running = false


func _restore_world_snapshot() -> void:
	if _restored or not GameState.has_method("get_world_snapshot"):
		return
	var snapshot: Dictionary = GameState.call("get_world_snapshot") as Dictionary
	if snapshot.is_empty() or str(snapshot.get("location_id", "")) != WORLD_LOCATION_ID:
		_restored = true
		_initialize_valid_positions()
		return
	_restore_environment(snapshot.get("environment", {}) as Dictionary if snapshot.get("environment", {}) is Dictionary else {})
	_restore_doors(snapshot.get("doors", {}) as Dictionary if snapshot.get("doors", {}) is Dictionary else {})
	var actors_by_id: Dictionary = {}
	for actor: Node in _persistent_world_actors():
		actors_by_id[_actor_id(actor)] = actor
	var entities_value: Variant = snapshot.get("entities", {})
	if entities_value is Dictionary:
		for key: Variant in (entities_value as Dictionary).keys():
			var actor: Node = actors_by_id.get(str(key), null) as Node
			var state_value: Variant = (entities_value as Dictionary).get(key, {})
			if is_instance_valid(actor) and state_value is Dictionary:
				_restore_actor(actor, state_value as Dictionary)
	if is_instance_valid(_player) and _player.has_method("set_facing_direction"):
		_player.call("set_facing_direction", _vector_from_value(snapshot.get("player_facing", []), Vector2.RIGHT))
	_restored = true
	_initialize_valid_positions()
	if _game.has_method("_update_status"):
		_game.call("_update_status")
	if _game.has_method("_refresh_action_catalog"):
		_game.call("_refresh_action_catalog")


func _capture_actor(actor: Node) -> Dictionary:
	var actor_node: Node2D = actor as Node2D
	var facing: Vector2 = Vector2.DOWN
	if actor.has_method("get_facing_direction"):
		facing = actor.call("get_facing_direction") as Vector2
	var groups: Array[String] = []
	for group_id: String in PERSISTED_GROUPS:
		if actor.is_in_group(group_id):
			groups.append(group_id)
	var actor_id: String = _actor_id(actor)
	var alert: Dictionary = GameState.call("get_stealth_alert_record", actor_id) as Dictionary if GameState.has_method("get_stealth_alert_record") else {}
	var result: Dictionary = {
		"position": _vector_to_value(actor_node.global_position),
		"facing": _vector_to_value(facing),
		"groups": groups,
		"hostile": bool(actor.get("hostile")),
		"defeated": bool(actor.get("defeated")),
		"current_health": int(actor.call("get_current_health")) if actor.has_method("get_current_health") else int(actor.get("current_health")),
		"maximum_health": int(actor.call("get_maximum_health")) if actor.has_method("get_maximum_health") else int(actor.get("maximum_health")),
		"alert_record": alert
	}
	if actor.has_method("get_body_state"):
		result["body_state"] = str(actor.call("get_body_state"))
	return result


func _restore_actor(actor: Node, state: Dictionary) -> void:
	if not actor is Node2D:
		return
	var actor_node: Node2D = actor as Node2D
	actor_node.global_position = _navigation.resolve_safe_position(
		actor_node,
		_vector_from_value(state.get("position", []), actor_node.global_position)
	)
	if actor.has_method("set_facing_direction"):
		actor.call("set_facing_direction", _vector_from_value(state.get("facing", []), Vector2.DOWN))
	var maximum_health: int = maxi(int(state.get("maximum_health", actor.get("maximum_health"))), 1)
	actor.set("maximum_health", maximum_health)
	actor.set("current_health", clampi(int(state.get("current_health", actor.get("current_health"))), 0, maximum_health))
	actor.set("defeated", bool(state.get("defeated", false)))
	actor.set("hostile", bool(state.get("hostile", false)) and not bool(state.get("defeated", false)))
	_restore_groups(actor, state.get("groups", []) as Array if state.get("groups", []) is Array else [])
	if state.has("body_state"):
		actor.set("_body_state", str(state.get("body_state", "dead")))
	var alert_value: Variant = state.get("alert_record", {})
	var actor_id: String = _actor_id(actor)
	if alert_value is Dictionary and not actor_id.is_empty() and GameState.has_method("set_stealth_alert_record"):
		var alert: Dictionary = (alert_value as Dictionary).duplicate(true)
		GameState.call("set_stealth_alert_record", actor_id, alert, false, false)
		var runtime_records_value: Variant = _game.get("_alert_records")
		var runtime_records: Dictionary = runtime_records_value as Dictionary if runtime_records_value is Dictionary else {}
		runtime_records[actor_id] = alert.duplicate(true)
		_game.set("_alert_records", runtime_records)
		if actor.has_method("set_exploration_alert_state"):
			actor.call(
				"set_exploration_alert_state",
				str(alert.get("state", StealthAlertSystem.STATE_CALM)),
				float(alert.get("suspicion", 0.0)),
				_vector_from_value(alert.get("last_known_position", []), Vector2.ZERO)
			)
	if bool(state.get("defeated", false)) and actor.has_method("_apply_body_groups"):
		actor.call("_apply_body_groups")
	if actor.has_method("_update_combat_visuals"):
		actor.call("_update_combat_visuals")


func _restore_groups(actor: Node, stored: Array) -> void:
	var membership: Dictionary = {}
	for value: Variant in stored:
		membership[str(value)] = true
	for group_id: String in PERSISTED_GROUPS:
		if membership.has(group_id):
			if not actor.is_in_group(group_id):
				actor.add_to_group(group_id)
		elif actor.is_in_group(group_id):
			actor.remove_from_group(group_id)


func _update_visible_actor_movement(delta: float) -> void:
	if not _restored or GameState.input_locked or not is_instance_valid(_player):
		return
	var turn_system_value: Variant = _game.get("_turn_system")
	if turn_system_value is TurnBasedCombatSystem and (turn_system_value as TurnBasedCombatSystem).active:
		return
	for actor: Node in get_tree().get_nodes_in_group("stealth_alert_actors"):
		if not is_instance_valid(actor) or not actor is Node2D or not actor.has_method("get_actor_id"):
			continue
		if bool(actor.get("defeated")) or bool(actor.get("hostile")):
			continue
		var actor_id: String = str(actor.call("get_actor_id"))
		var profile: Dictionary = GameState.call("get_stealth_profile", actor_id) as Dictionary if GameState.has_method("get_stealth_profile") else {}
		if profile.is_empty() or not _game.has_method("_exploration_actor_can_see_player"):
			continue
		if not bool(_game.call("_exploration_actor_can_see_player", actor, profile)):
			continue
		var record: Dictionary = GameState.call("get_stealth_alert_record", actor_id) as Dictionary
		var state: String = str(record.get("state", StealthAlertSystem.STATE_CALM))
		var updated: Dictionary = record
		if state == StealthAlertSystem.STATE_CALM and _game.has_method("_advance_actor_patrol"):
			updated = _game.call("_advance_actor_patrol", actor, record, delta) as Dictionary
		elif state in [StealthAlertSystem.STATE_SUSPICIOUS, StealthAlertSystem.STATE_INVESTIGATING, StealthAlertSystem.STATE_SEARCHING] and actor_id != "caretaker":
			var actor_node: Node2D = actor as Node2D
			var away: Vector2 = actor_node.global_position - _player.global_position
			if away.length_squared() <= 0.0001:
				away = Vector2.LEFT
			var standoff: Vector2 = _player.global_position + away.normalized() * VISIBLE_STANDOFF_PIXELS
			var movement: Dictionary = _navigation.move_actor(
				actor_node,
				standoff,
				float(profile.get("investigation_speed_pixels", 90.0)) * VISIBLE_SPEED_MULTIPLIER,
				delta
			)
			updated = record.duplicate(true)
			updated["last_known_position"] = _vector_to_value(_player.global_position)
			updated["navigation_used"] = true
			updated["navigation_blocked"] = bool(movement.get("blocked", false))
			var direction: Vector2 = movement.get("direction", Vector2.ZERO) as Vector2
			if direction.length_squared() > 0.0001 and actor.has_method("set_facing_direction"):
				actor.call("set_facing_direction", direction)
		if updated != record:
			GameState.call("set_stealth_alert_record", actor_id, updated, false, false)
			var records_value: Variant = _game.get("_alert_records")
			var records: Dictionary = records_value as Dictionary if records_value is Dictionary else {}
			records[actor_id] = updated
			_game.set("_alert_records", records)
			if _game.has_method("_apply_record_to_actor"):
				_game.call("_apply_record_to_actor", actor, updated)


func _repair_invalid_actor_positions() -> void:
	if _navigation == null:
		return
	var grid: BattleGrid = get_tree().get_first_node_in_group("battle_grid") as BattleGrid
	var environment: CombatEnvironment = get_tree().get_first_node_in_group("combat_environment") as CombatEnvironment
	if grid == null or environment == null:
		return
	for actor: Node in _persistent_world_actors():
		if not actor is Node2D or (actor.has_method("is_body_being_dragged") and bool(actor.call("is_body_being_dragged"))):
			continue
		var actor_node: Node2D = actor as Node2D
		var actor_id: String = _actor_id(actor)
		var previous: Vector2 = _last_valid_positions.get(actor_id, actor_node.global_position) as Vector2
		var previous_cell: Vector2i = grid.world_to_cell(previous)
		var current_cell: Vector2i = grid.world_to_cell(actor_node.global_position)
		var invalid: bool = environment.is_position_blocked(actor_node.global_position, ObstacleAwareNpcNavigationSystem.ACTOR_RADIUS_PIXELS)
		if grid.is_cell_valid(previous_cell) and grid.is_cell_valid(current_cell) and environment.is_transition_blocked(grid, previous_cell, current_cell):
			invalid = true
		if invalid:
			actor_node.global_position = previous if not environment.is_position_blocked(previous, ObstacleAwareNpcNavigationSystem.ACTOR_RADIUS_PIXELS) else _navigation.resolve_safe_position(actor_node, actor_node.global_position)
		_last_valid_positions[actor_id] = actor_node.global_position


func _initialize_valid_positions() -> void:
	_last_valid_positions.clear()
	for actor: Node in _persistent_world_actors():
		_last_valid_positions[_actor_id(actor)] = (actor as Node2D).global_position


func _persistent_world_actors() -> Array[Node]:
	var result: Array[Node] = []
	var seen: Dictionary = {}
	for group_id: String in ENTITY_GROUPS:
		for actor: Node in get_tree().get_nodes_in_group(group_id):
			if not is_instance_valid(actor) or not actor is Node2D or actor == _player:
				continue
			var actor_id: String = _actor_id(actor)
			if actor_id.is_empty() or seen.has(actor.get_instance_id()):
				continue
			seen[actor.get_instance_id()] = true
			result.append(actor)
	result.sort_custom(func(left: Node, right: Node) -> bool: return _actor_id(left) < _actor_id(right))
	return result


func _actor_id(actor: Node) -> String:
	if is_instance_valid(actor) and actor.has_method("get_actor_id"):
		return str(actor.call("get_actor_id"))
	if is_instance_valid(actor) and actor.has_method("get_body_actor_id"):
		return str(actor.call("get_body_actor_id"))
	return ""


func _expand_npc_trigger_zones() -> void:
	for actor: Node in _persistent_world_actors():
		var collision: CollisionShape2D = _interaction_collision(actor)
		if collision == null or collision.shape == null or bool(collision.get_meta("expanded_world_trigger", false)):
			continue
		var expanded: Shape2D = collision.shape.duplicate() as Shape2D
		if expanded is CircleShape2D:
			(expanded as CircleShape2D).radius *= TRIGGER_SCALE
		elif expanded is RectangleShape2D:
			(expanded as RectangleShape2D).size *= TRIGGER_SCALE
		else:
			continue
		collision.shape = expanded
		collision.set_meta("expanded_world_trigger", true)


func _interaction_collision(actor: Node) -> CollisionShape2D:
	var area: Area2D = actor.get_node_or_null("InteractionArea") as Area2D if is_instance_valid(actor) else null
	if area != null:
		var dedicated: CollisionShape2D = area.get_node_or_null("CollisionShape2D") as CollisionShape2D
		if dedicated != null:
			return dedicated
	return actor.get_node_or_null("CollisionShape2D") as CollisionShape2D if is_instance_valid(actor) else null


func _configure_occlusion_rendering() -> void:
	for _frame: int in range(4):
		await get_tree().process_frame
	var fog: CanvasItem = get_tree().get_first_node_in_group("player_visibility") as CanvasItem
	if fog != null:
		fog.z_as_relative = false
		fog.z_index = FOG_Z_INDEX
	var room: Node = _game.get_node_or_null("StealthTestRoom") if is_instance_valid(_game) else null
	if room != null:
		for wall_name: String in ["WestPartitionTop", "WestPartitionBottom", "InnerPartitionTop", "InnerPartitionBottom"]:
			var wall: Node = room.get_node_or_null(wall_name)
			if wall == null:
				continue
			for child: Node in wall.get_children():
				if child is Polygon2D:
					(child as Polygon2D).z_as_relative = false
					(child as Polygon2D).z_index = WALL_Z_INDEX
	for door: Node in get_tree().get_nodes_in_group("stealth_doors"):
		var visual: Polygon2D = door.get_node_or_null("Visual") as Polygon2D if is_instance_valid(door) else null
		if visual != null:
			visual.z_as_relative = false
			visual.z_index = DOOR_Z_INDEX


func _capture_environment() -> Dictionary:
	var environment: CombatEnvironment = get_tree().get_first_node_in_group("combat_environment") as CombatEnvironment
	if environment == null:
		return {}
	var covers: Dictionary = {}
	for obstacle: Dictionary in environment.cover_objects:
		var object_id: String = str(obstacle.get("id", ""))
		if not object_id.is_empty():
			covers[object_id] = bool(obstacle.get("active", true))
	var hazards: Dictionary = {}
	for key: Variant in environment.dynamic_hazards.keys():
		var value: Variant = environment.dynamic_hazards.get(key, {})
		if not value is Dictionary:
			continue
		var hazard: Dictionary = value as Dictionary
		var local_rect: Rect2 = hazard.get("rect", Rect2()) as Rect2
		var world_position: Vector2 = environment.to_global(local_rect.position)
		hazards[str(key)] = {
			"rect": [world_position.x, world_position.y, local_rect.size.x, local_rect.size.y],
			"hazard_type": str(hazard.get("hazard_type", "hazard")),
			"severity": float(hazard.get("severity", 1.0)),
			"blocks_movement": bool(hazard.get("blocks_movement", false))
		}
	return {"cover_states": covers, "hazards": hazards}


func _restore_environment(state: Dictionary) -> void:
	var environment: CombatEnvironment = get_tree().get_first_node_in_group("combat_environment") as CombatEnvironment
	if environment == null:
		return
	var covers_value: Variant = state.get("cover_states", {})
	if covers_value is Dictionary:
		for key: Variant in (covers_value as Dictionary).keys():
			environment.set_cover_object_active(str(key), bool((covers_value as Dictionary)[key]), false)
	var hazards_value: Variant = state.get("hazards", {})
	if hazards_value is Dictionary:
		environment.dynamic_hazards.clear()
		for key: Variant in (hazards_value as Dictionary).keys():
			var value: Variant = (hazards_value as Dictionary).get(key, {})
			if not value is Dictionary:
				continue
			var hazard: Dictionary = value as Dictionary
			var rect_value: Variant = hazard.get("rect", [])
			if not rect_value is Array or (rect_value as Array).size() < 4:
				continue
			var world_rect := Rect2(
				Vector2(float((rect_value as Array)[0]), float((rect_value as Array)[1])),
				Vector2(float((rect_value as Array)[2]), float((rect_value as Array)[3]))
			)
			environment.dynamic_hazards[str(key)] = {
				"id": str(key),
				"rect": Rect2(environment.to_local(world_rect.position), world_rect.size),
				"hazard_type": str(hazard.get("hazard_type", "hazard")),
				"severity": float(hazard.get("severity", 1.0)),
				"blocks_movement": bool(hazard.get("blocks_movement", false))
			}
		environment.call("_rebuild_collision_bodies")
		environment.queue_redraw()


func _restore_doors(doors: Dictionary) -> void:
	for door: Node in get_tree().get_nodes_in_group("stealth_doors"):
		if not is_instance_valid(door) or not door.has_method("get_door_id") or not door.has_method("set_door_state"):
			continue
		var value: Variant = doors.get(str(door.call("get_door_id")), {})
		if value is Dictionary:
			door.call("set_door_state", str((value as Dictionary).get("state", "closed")), false)


func _vector_to_value(value: Vector2) -> Array[float]:
	return [value.x, value.y]


func _vector_from_value(value: Variant, fallback: Vector2) -> Vector2:
	if value is Array and (value as Array).size() >= 2:
		return Vector2(float((value as Array)[0]), float((value as Array)[1]))
	if value is Vector2:
		return value as Vector2
	return fallback
