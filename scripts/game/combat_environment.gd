class_name CombatEnvironment
extends Node2D

signal environment_object_changed(event_type: String, object_id: String, world_position: Vector2, payload: Dictionary)

const DIFFICULT_COLOR: Color = Color(0.46, 0.34, 0.22, 0.34)
const HALF_COVER_COLOR: Color = Color(0.38, 0.42, 0.46, 0.94)
const HEAVY_COVER_COLOR: Color = Color(0.24, 0.27, 0.31, 0.98)
const HAZARD_COLOR: Color = Color(0.9, 0.24, 0.08, 0.34)
const INVALID_CELL: Vector2i = Vector2i(-99999, -99999)

var difficult_terrain: Array[Rect2] = []
var cover_objects: Array[Dictionary] = []
var dynamic_hazards: Dictionary = {}
var edge_blockers: Dictionary = {}
var _collision_root: Node2D


func _ready() -> void:
	add_to_group("combat_environment")
	_build_test_lobby_layout()
	_rebuild_collision_bodies()
	queue_redraw()


func _build_test_lobby_layout() -> void:
	difficult_terrain = [
		Rect2(365.0, 301.0, 192.0, 128.0)
	]
	cover_objects = [
		{
			"id": "low_barricade",
			"rect": Rect2(621.0, 173.0, 64.0, 128.0),
			"cover_bonus": 2,
			"blocks_movement": true,
			"blocks_cells": true,
			"blocks_line_of_sight": false,
			"jumpable": true,
			"active": true
		},
		{
			"id": "high_barricade",
			"rect": Rect2(621.0, 429.0, 64.0, 128.0),
			"cover_bonus": 5,
			"blocks_movement": true,
			"blocks_cells": true,
			"blocks_line_of_sight": false,
			"jumpable": true,
			"active": true
		},
		{
			"id": "solid_wall",
			"rect": Rect2(813.0, 493.0, 64.0, 128.0),
			"cover_bonus": 0,
			"blocks_movement": true,
			"blocks_cells": true,
			"blocks_line_of_sight": true,
			"jumpable": false,
			"active": true
		}
	]


func set_cover_object_active(object_id: String, active: bool, report_change: bool = true) -> bool:
	for index: int in range(cover_objects.size()):
		if str(cover_objects[index].get("id", "")) != object_id:
			continue
		var previous: bool = bool(cover_objects[index].get("active", true))
		if previous == active:
			return false
		cover_objects[index]["active"] = active
		_rebuild_collision_bodies()
		queue_redraw()
		if report_change:
			var rect: Rect2 = cover_objects[index].get("rect", Rect2()) as Rect2
			var event_type: String = EnvironmentEventSystem.EVENT_COVER_RESTORED if active else EnvironmentEventSystem.EVENT_COVER_DESTROYED
			_report_environment_change(event_type, object_id, to_global(rect.get_center()), {
				"cover_bonus": int(cover_objects[index].get("cover_bonus", 0)),
				"blocks_line_of_sight": bool(cover_objects[index].get("blocks_line_of_sight", false)),
				"active": active
			})
		return true
	return false


func register_edge_blocker(object_id: String, edges: Array, active: bool = true) -> void:
	if object_id.is_empty():
		return
	var normalized_edges: Array[Dictionary] = []
	for edge_value: Variant in edges:
		if not (edge_value is Dictionary):
			continue
		var edge: Dictionary = edge_value as Dictionary
		var first_value: Variant = edge.get("a", null)
		var second_value: Variant = edge.get("b", null)
		if not (first_value is Vector2i) or not (second_value is Vector2i):
			continue
		var first: Vector2i = first_value as Vector2i
		var second: Vector2i = second_value as Vector2i
		var delta: Vector2i = second - first
		if maxi(absi(delta.x), absi(delta.y)) != 1 or (delta.x != 0 and delta.y != 0):
			continue
		normalized_edges.append({"a": first, "b": second})
	edge_blockers[object_id] = {
		"active": active,
		"edges": normalized_edges
	}


func set_edge_blocker_active(object_id: String, active: bool) -> bool:
	var value: Variant = edge_blockers.get(object_id, null)
	if not (value is Dictionary):
		return false
	var record: Dictionary = value as Dictionary
	var previous: bool = bool(record.get("active", true))
	record["active"] = active
	edge_blockers[object_id] = record
	return previous != active


func get_edge_blocker_edges_for_testing(object_id: String) -> Array[Dictionary]:
	var value: Variant = edge_blockers.get(object_id, null)
	if not (value is Dictionary):
		return []
	var edges_value: Variant = (value as Dictionary).get("edges", [])
	var result: Array[Dictionary] = []
	if edges_value is Array:
		for edge_value: Variant in edges_value as Array:
			if edge_value is Dictionary:
				result.append((edge_value as Dictionary).duplicate(true))
	return result


func is_transition_blocked(grid: BattleGrid, from_cell: Vector2i, to_cell: Vector2i) -> bool:
	if grid == null or not grid.is_cell_valid(from_cell) or not grid.is_cell_valid(to_cell):
		return true
	var delta: Vector2i = to_cell - from_cell
	if delta == Vector2i.ZERO:
		return false
	if maxi(absi(delta.x), absi(delta.y)) != 1:
		return false
	if delta.x != 0 and delta.y != 0:
		var horizontal: Vector2i = from_cell + Vector2i(delta.x, 0)
		var vertical: Vector2i = from_cell + Vector2i(0, delta.y)
		var horizontal_route_blocked: bool = (
			_orthogonal_transition_blocked(from_cell, horizontal)
			or _orthogonal_transition_blocked(horizontal, to_cell)
		)
		var vertical_route_blocked: bool = (
			_orthogonal_transition_blocked(from_cell, vertical)
			or _orthogonal_transition_blocked(vertical, to_cell)
		)
		return horizontal_route_blocked and vertical_route_blocked
	return _orthogonal_transition_blocked(from_cell, to_cell)


func _orthogonal_transition_blocked(from_cell: Vector2i, to_cell: Vector2i) -> bool:
	for record_value: Variant in edge_blockers.values():
		if not (record_value is Dictionary):
			continue
		var record: Dictionary = record_value as Dictionary
		if not bool(record.get("active", true)):
			continue
		var edges_value: Variant = record.get("edges", [])
		if not (edges_value is Array):
			continue
		for edge_value: Variant in edges_value as Array:
			if not (edge_value is Dictionary):
				continue
			var edge: Dictionary = edge_value as Dictionary
			var first: Vector2i = edge.get("a", INVALID_CELL) as Vector2i
			var second: Vector2i = edge.get("b", INVALID_CELL) as Vector2i
			if (first == from_cell and second == to_cell) or (first == to_cell and second == from_cell):
				return true
	return false


func destroy_cover_object(object_id: String) -> bool:
	return set_cover_object_active(object_id, false, true)


func restore_cover_object(object_id: String) -> bool:
	return set_cover_object_active(object_id, true, true)


func add_hazard(
	hazard_id: String,
	world_rect: Rect2,
	hazard_type: String = "fire",
	severity: float = 1.0,
	blocks_movement: bool = false,
	audible_radius_feet: int = 35
) -> bool:
	if hazard_id.is_empty():
		return false
	var local_rect := Rect2(to_local(world_rect.position), world_rect.size)
	dynamic_hazards[hazard_id] = {
		"id": hazard_id,
		"rect": local_rect,
		"hazard_type": hazard_type,
		"severity": clampf(severity, 0.0, 3.0),
		"blocks_movement": blocks_movement
	}
	_rebuild_collision_bodies()
	queue_redraw()
	_report_environment_change(EnvironmentEventSystem.EVENT_HAZARD_ADDED, hazard_id, to_global(local_rect.get_center()), {
		"hazard_type": hazard_type,
		"severity": severity,
		"blocks_movement": blocks_movement,
		"audible_radius_feet": maxi(audible_radius_feet, 0),
		"rect": [world_rect.position.x, world_rect.position.y, world_rect.size.x, world_rect.size.y]
	})
	return true


func remove_hazard(hazard_id: String) -> bool:
	var value: Variant = dynamic_hazards.get(hazard_id, {})
	if not value is Dictionary:
		return false
	var hazard: Dictionary = value as Dictionary
	var rect: Rect2 = hazard.get("rect", Rect2()) as Rect2
	var hazard_type: String = str(hazard.get("hazard_type", "hazard"))
	dynamic_hazards.erase(hazard_id)
	_rebuild_collision_bodies()
	queue_redraw()
	_report_environment_change(EnvironmentEventSystem.EVENT_HAZARD_REMOVED, hazard_id, to_global(rect.get_center()), {
		"hazard_type": hazard_type,
		"severity": float(hazard.get("severity", 1.0))
	})
	return true


func is_hazardous_position(world_position: Vector2) -> bool:
	return not get_hazard_at_position(world_position).is_empty()


func get_hazard_at_position(world_position: Vector2) -> Dictionary:
	var local_position: Vector2 = to_local(world_position)
	for value: Variant in dynamic_hazards.values():
		if value is Dictionary and ((value as Dictionary).get("rect", Rect2()) as Rect2).has_point(local_position):
			return (value as Dictionary).duplicate(true)
	return {}


func is_hazardous_cell(grid: BattleGrid, cell: Vector2i) -> bool:
	return grid != null and grid.is_cell_valid(cell) and is_hazardous_position(grid.cell_to_world_center(cell))


func get_environment_object_position(object_id: String) -> Vector2:
	for obstacle: Dictionary in cover_objects:
		if str(obstacle.get("id", "")) == object_id:
			return to_global((obstacle.get("rect", Rect2()) as Rect2).get_center())
	var hazard_value: Variant = dynamic_hazards.get(object_id, {})
	if hazard_value is Dictionary:
		return to_global(((hazard_value as Dictionary).get("rect", Rect2()) as Rect2).get_center())
	return Vector2.INF


func is_difficult_position(world_position: Vector2) -> bool:
	for terrain_rect: Rect2 in difficult_terrain:
		if terrain_rect.has_point(to_local(world_position)):
			return true
	return false


func is_position_blocked(world_position: Vector2, actor_radius: float = 18.0) -> bool:
	var local_position: Vector2 = to_local(world_position)
	for obstacle: Dictionary in cover_objects:
		if not _obstacle_is_active(obstacle) or not bool(obstacle.get("blocks_movement", false)):
			continue
		var rect: Rect2 = obstacle.get("rect", Rect2()) as Rect2
		if rect.grow(actor_radius).has_point(local_position):
			return true
	for value: Variant in dynamic_hazards.values():
		if value is Dictionary and bool((value as Dictionary).get("blocks_movement", false)):
			var hazard_rect: Rect2 = (value as Dictionary).get("rect", Rect2()) as Rect2
			if hazard_rect.grow(actor_radius).has_point(local_position):
				return true
	return false


func is_cell_blocked(grid: BattleGrid, cell: Vector2i) -> bool:
	if grid == null or not grid.is_cell_valid(cell):
		return true
	var size: float = grid.get_cell_size()
	var center: Vector2 = to_local(grid.cell_to_world_center(cell))
	var cell_rect := Rect2(center - Vector2(size, size) * 0.5, Vector2(size, size)).grow(-2.0)
	for obstacle: Dictionary in cover_objects:
		if (
			_obstacle_is_active(obstacle)
			and bool(obstacle.get("blocks_movement", false))
			and bool(obstacle.get("blocks_cells", true))
			and (obstacle.get("rect", Rect2()) as Rect2).intersects(cell_rect)
		):
			return true
	for value: Variant in dynamic_hazards.values():
		if value is Dictionary and bool((value as Dictionary).get("blocks_movement", false)) and ((value as Dictionary).get("rect", Rect2()) as Rect2).intersects(cell_rect):
			return true
	return false


func is_jumpable_cell(grid: BattleGrid, cell: Vector2i) -> bool:
	if grid == null or not grid.is_cell_valid(cell):
		return false
	var size: float = grid.get_cell_size()
	var center: Vector2 = to_local(grid.cell_to_world_center(cell))
	var cell_rect := Rect2(center - Vector2(size, size) * 0.5, Vector2(size, size)).grow(-2.0)
	for obstacle: Dictionary in cover_objects:
		if not _obstacle_is_active(obstacle) or not bool(obstacle.get("blocks_movement", false)) or not bool(obstacle.get("blocks_cells", true)):
			continue
		if (obstacle.get("rect", Rect2()) as Rect2).intersects(cell_rect):
			return bool(obstacle.get("jumpable", false))
	return false


func get_jump_landing_cell(
	grid: BattleGrid,
	origin_cell: Vector2i,
	direction: Vector2i,
	occupied_cells: Dictionary = {},
	maximum_crossed_cells: int = 2
) -> Vector2i:
	if grid == null or direction == Vector2i.ZERO:
		return INVALID_CELL
	var crossed_obstacle: bool = false
	var crossed_cells: int = 0
	var previous_cell: Vector2i = origin_cell
	for distance: int in range(1, maximum_crossed_cells + 2):
		var candidate: Vector2i = origin_cell + direction * distance
		if not grid.is_cell_valid(candidate) or is_transition_blocked(grid, previous_cell, candidate):
			return INVALID_CELL
		if is_cell_blocked(grid, candidate):
			if not is_jumpable_cell(grid, candidate):
				return INVALID_CELL
			crossed_obstacle = true
			crossed_cells += 1
			if crossed_cells > maximum_crossed_cells:
				return INVALID_CELL
			previous_cell = candidate
			continue
		if not crossed_obstacle or occupied_cells.has(candidate):
			return INVALID_CELL
		return candidate
	return INVALID_CELL


func get_cover(attacker_position: Vector2, target_position: Vector2) -> Dictionary:
	var start: Vector2 = to_local(attacker_position)
	var finish: Vector2 = to_local(target_position)
	var best_bonus: int = 0
	var total_cover: bool = false
	for obstacle: Dictionary in cover_objects:
		if not _obstacle_is_active(obstacle):
			continue
		var rect: Rect2 = obstacle.get("rect", Rect2()) as Rect2
		if not _segment_crosses_rect(start, finish, rect):
			continue
		if bool(obstacle.get("blocks_line_of_sight", false)):
			total_cover = true
			break
		best_bonus = maxi(best_bonus, int(obstacle.get("cover_bonus", 0)))
	return {
		"bonus": best_bonus,
		"total_cover": total_cover,
		"label": "полное укрытие" if total_cover else ("укрытие 3/4" if best_bonus >= 5 else ("половинное укрытие" if best_bonus >= 2 else "без укрытия"))
	}


func has_line_of_sight(attacker_position: Vector2, target_position: Vector2) -> bool:
	return not bool(get_cover(attacker_position, target_position).get("total_cover", false))


func _rebuild_collision_bodies() -> void:
	if is_instance_valid(_collision_root):
		_collision_root.queue_free()
	_collision_root = Node2D.new()
	_collision_root.name = "ObstacleCollisions"
	add_child(_collision_root)
	for obstacle: Dictionary in cover_objects:
		if not _obstacle_is_active(obstacle) or not bool(obstacle.get("blocks_movement", false)):
			continue
		_add_collision_rect(str(obstacle.get("id", "obstacle")), obstacle.get("rect", Rect2()) as Rect2)
	for value: Variant in dynamic_hazards.values():
		if value is Dictionary and bool((value as Dictionary).get("blocks_movement", false)):
			_add_collision_rect(str((value as Dictionary).get("id", "hazard")), (value as Dictionary).get("rect", Rect2()) as Rect2)


func _add_collision_rect(object_id: String, rect: Rect2) -> void:
	var body := StaticBody2D.new()
	body.name = "%sCollision" % object_id.to_pascal_case()
	body.position = rect.get_center()
	body.collision_layer = 1
	body.collision_mask = 1
	var shape := RectangleShape2D.new()
	shape.size = rect.size
	var collision := CollisionShape2D.new()
	collision.shape = shape
	body.add_child(collision)
	_collision_root.add_child(body)


func _report_environment_change(event_type: String, object_id: String, world_position: Vector2, payload: Dictionary) -> void:
	var event_payload: Dictionary = payload.duplicate(true)
	event_payload["object_id"] = object_id
	environment_object_changed.emit(event_type, object_id, world_position, event_payload)
	get_tree().call_group("game_world", "report_environment_change", event_type, world_position, event_payload)


func _obstacle_is_active(obstacle: Dictionary) -> bool:
	return bool(obstacle.get("active", true))


func _segment_crosses_rect(start: Vector2, finish: Vector2, rect: Rect2) -> bool:
	var distance: float = start.distance_to(finish)
	var samples: int = maxi(ceili(distance / 8.0), 1)
	for index: int in range(1, samples):
		var point: Vector2 = start.lerp(finish, float(index) / float(samples))
		if rect.has_point(point):
			return true
	return false


func _draw() -> void:
	for terrain_rect: Rect2 in difficult_terrain:
		draw_rect(terrain_rect, DIFFICULT_COLOR, true)
		draw_rect(terrain_rect, Color(0.78, 0.58, 0.31, 0.72), false, 2.0)
		_draw_cross_hatch(terrain_rect)
	for obstacle: Dictionary in cover_objects:
		if not _obstacle_is_active(obstacle):
			continue
		var rect: Rect2 = obstacle.get("rect", Rect2()) as Rect2
		var blocks_sight: bool = bool(obstacle.get("blocks_line_of_sight", false))
		var bonus: int = int(obstacle.get("cover_bonus", 0))
		var color: Color = HEAVY_COVER_COLOR if blocks_sight or bonus >= 5 else HALF_COVER_COLOR
		draw_rect(rect, color, true)
		draw_rect(rect, Color(0.76, 0.8, 0.84, 0.86), false, 2.0)
		if bool(obstacle.get("jumpable", false)):
			draw_string(ThemeDB.fallback_font, rect.position + Vector2(4.0, 18.0), "ПРЫЖОК", HORIZONTAL_ALIGNMENT_LEFT, rect.size.x - 8.0, 11, Color(0.9, 0.88, 0.55, 0.8))
	for value: Variant in dynamic_hazards.values():
		if not value is Dictionary:
			continue
		var hazard: Dictionary = value as Dictionary
		var rect: Rect2 = hazard.get("rect", Rect2()) as Rect2
		draw_rect(rect, HAZARD_COLOR, true)
		draw_rect(rect, Color(1.0, 0.5, 0.18, 0.86), false, 2.0)
		draw_string(ThemeDB.fallback_font, rect.position + Vector2(4.0, 18.0), str(hazard.get("hazard_type", "ОПАСНОСТЬ")).to_upper(), HORIZONTAL_ALIGNMENT_LEFT, rect.size.x - 8.0, 11, Color(1.0, 0.78, 0.42, 0.9))


func _draw_cross_hatch(rect: Rect2) -> void:
	var step: float = 24.0
	var offset: float = -rect.size.y
	while offset < rect.size.x:
		var start := Vector2(rect.position.x + maxf(offset, 0.0), rect.position.y + maxf(-offset, 0.0))
		var finish := Vector2(rect.position.x + minf(offset + rect.size.y, rect.size.x), rect.end.y - maxf(offset + rect.size.y - rect.size.x, 0.0))
		draw_line(start, finish, Color(0.78, 0.58, 0.31, 0.28), 1.0)
		offset += step
