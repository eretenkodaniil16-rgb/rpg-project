class_name StealthTestRoom
extends Node2D

const DOOR_SCRIPT: Script = preload("res://scripts/game/stealth_door.gd")
const PATROL_GUARD_SCENE: PackedScene = preload("res://scenes/game/stealth_patrol_guard.tscn")
const TRAINING_MARKSMAN_SCENE: PackedScene = preload("res://scenes/game/combat_ai_training_marksman.tscn")
const TRAINING_MAGE_SCENE: PackedScene = preload("res://scenes/game/combat_ai_training_mage.tscn")
const PATROL_SYSTEM_SCRIPT: Script = preload("res://scripts/systems/patrol_alert_group_system_ai.gd")

const PARTITION_LOCAL_X: float = -8.0
const PARTITION_THICKNESS: float = 4.0
const WEST_PARTITION_TOP_SIZE: Vector2 = Vector2(PARTITION_THICKNESS, 256.0)
const WEST_PARTITION_BOTTOM_SIZE: Vector2 = Vector2(PARTITION_THICKNESS, 246.0)
const WEST_SERVICE_DOOR_SIZE: Vector2 = Vector2(PARTITION_THICKNESS, 128.0)
const WEST_PARTITION_TOP_ID: String = "west_partition_top"
const WEST_PARTITION_BOTTOM_ID: String = "west_partition_bottom"
const WEST_SERVICE_DOOR_BLOCKER_ID: String = "west_service_door_blocker"

var _door: StealthDoor
var _patrol_observer: StealthPatrolObserver
var _training_marksman: Node2D
var _training_mage: Node2D
var _patrol_data: PatrolAlertGroupSystemAi = PATROL_SYSTEM_SCRIPT.new() as PatrolAlertGroupSystemAi
var _west_navigation_region: NavigationRegion2D
var _hall_navigation_region: NavigationRegion2D
var _door_navigation_link: NavigationLink2D
var _combat_environment: CombatEnvironment
var _activating_tactical_squad: bool = false


func _ready() -> void:
	add_to_group("stealth_world")
	_build_navigation()
	_build_wall("WestPartitionTop", Vector2(PARTITION_LOCAL_X, -187.0), WEST_PARTITION_TOP_SIZE)
	_build_wall("WestPartitionBottom", Vector2(PARTITION_LOCAL_X, 192.0), WEST_PARTITION_BOTTOM_SIZE)
	_door = DOOR_SCRIPT.new() as StealthDoor
	_door.name = "WestServiceDoor"
	_door.position = Vector2(PARTITION_LOCAL_X, 5.0)
	_door.door_id = "west_service_door"
	_door.door_label = "Дверь служебной комнаты"
	_door.door_size = WEST_SERVICE_DOOR_SIZE
	add_child(_door)
	set_navigation_door_state(_door.door_id, _door.get_door_state())
	_build_patrol_observer()
	_build_tactical_training_squad()
	call_deferred("_register_combat_obstacles")
	queue_redraw()


func get_test_door() -> StealthDoor:
	return _door


func get_patrol_observer() -> StealthPatrolObserver:
	return _patrol_observer


func get_training_marksman() -> Node2D:
	return _training_marksman


func get_training_mage() -> Node2D:
	return _training_mage


func get_navigation_link_for_testing() -> NavigationLink2D:
	return _door_navigation_link


func set_navigation_door_state(door_id: String, door_state: String) -> void:
	if door_id != "west_service_door":
		return
	if _door_navigation_link != null:
		_door_navigation_link.enabled = door_state in ["open", "broken"]
	if _combat_environment != null:
		var should_block: bool = door_state not in ["open", "broken"]
		_combat_environment.set_cover_object_active(WEST_SERVICE_DOOR_BLOCKER_ID, should_block, false)
		_combat_environment.set_edge_blocker_active(WEST_SERVICE_DOOR_BLOCKER_ID, should_block)


func activate_tactical_training_squad() -> void:
	if _activating_tactical_squad:
		return
	_activating_tactical_squad = true
	for actor: Node2D in [_training_marksman, _training_mage]:
		if not is_instance_valid(actor):
			continue
		if not actor.is_in_group("stealth_alert_actors"):
			actor.add_to_group("stealth_alert_actors")
		if actor.has_method("activate_combat_participant"):
			actor.call("activate_combat_participant")
	_activating_tactical_squad = false


func _build_patrol_observer() -> void:
	_patrol_observer = PATROL_GUARD_SCENE.instantiate() as StealthPatrolObserver
	if _patrol_observer == null:
		return
	_patrol_observer.name = "ServiceGuard"
	add_child(_patrol_observer)
	var initial_position: Vector2 = _patrol_data.get_initial_patrol_position("service_guard")
	_patrol_observer.global_position = initial_position if initial_position != Vector2.ZERO else Vector2(760.0, 160.0)


func _build_tactical_training_squad() -> void:
	_training_marksman = TRAINING_MARKSMAN_SCENE.instantiate() as Node2D
	if _training_marksman != null:
		_training_marksman.name = "TrainingMarksman"
		add_child(_training_marksman)
		_training_marksman.global_position = Vector2(1035.0, 185.0)
		_prepare_dormant_training_actor(_training_marksman)
	_training_mage = TRAINING_MAGE_SCENE.instantiate() as Node2D
	if _training_mage != null:
		_training_mage.name = "TrainingMage"
		add_child(_training_mage)
		_training_mage.global_position = Vector2(1035.0, 535.0)
		_prepare_dormant_training_actor(_training_mage)


func _prepare_dormant_training_actor(actor: Node2D) -> void:
	actor.remove_from_group("stealth_alert_actors")
	if not actor.is_in_group("combat_targets"):
		actor.add_to_group("combat_targets")


func _register_combat_obstacles() -> void:
	for _frame: int in range(6):
		_combat_environment = get_tree().get_first_node_in_group("combat_environment") as CombatEnvironment
		if _combat_environment != null:
			break
		await get_tree().process_frame
	if _combat_environment == null:
		push_warning("CombatEnvironment is unavailable; room walls were not registered for grid movement.")
		return
	var grid: BattleGrid = get_tree().get_first_node_in_group("battle_grid") as BattleGrid
	if grid == null:
		push_warning("BattleGrid is unavailable; room wall edges were not registered.")
		return
	var top_wall: Node2D = get_node_or_null("WestPartitionTop") as Node2D
	var bottom_wall: Node2D = get_node_or_null("WestPartitionBottom") as Node2D
	if top_wall != null:
		var top_rect: Rect2 = _rect_around(top_wall.global_position, WEST_PARTITION_TOP_SIZE)
		_add_environment_obstacle(WEST_PARTITION_TOP_ID, top_rect, true, false, true, false)
		_combat_environment.register_edge_blocker(
			WEST_PARTITION_TOP_ID,
			_vertical_edge_pairs(grid, top_wall.global_position.x, top_rect),
			true
		)
	if bottom_wall != null:
		var bottom_rect: Rect2 = _rect_around(bottom_wall.global_position, WEST_PARTITION_BOTTOM_SIZE)
		_add_environment_obstacle(WEST_PARTITION_BOTTOM_ID, bottom_rect, true, false, true, false)
		_combat_environment.register_edge_blocker(
			WEST_PARTITION_BOTTOM_ID,
			_vertical_edge_pairs(grid, bottom_wall.global_position.x, bottom_rect),
			true
		)
	if _door != null:
		var door_active: bool = _door.get_door_state() not in ["open", "broken"]
		_add_environment_obstacle(
			WEST_SERVICE_DOOR_BLOCKER_ID,
			_door.get_world_rect(),
			true,
			false,
			door_active,
			false
		)
		_combat_environment.register_edge_blocker(
			WEST_SERVICE_DOOR_BLOCKER_ID,
			_vertical_edge_pairs(grid, _door.global_position.x, _door.get_world_rect()),
			door_active
		)
	_combat_environment.call("_rebuild_collision_bodies")
	_combat_environment.queue_redraw()


func _vertical_edge_pairs(grid: BattleGrid, edge_world_x: float, world_span: Rect2) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	if grid == null:
		return result
	var local_edge: Vector2 = grid.to_local(Vector2(edge_world_x, world_span.position.y))
	var field: Rect2 = grid.get_field_rect()
	var cell_size: float = grid.get_cell_size()
	var edge_column: int = roundi((local_edge.x - field.position.x) / cell_size)
	var left_column: int = edge_column - 1
	var right_column: int = edge_column
	var top_local: float = grid.to_local(world_span.position).y
	var bottom_local: float = grid.to_local(world_span.end).y
	var first_row: int = floori((top_local - field.position.y + 0.01) / cell_size)
	var last_row: int = ceili((bottom_local - field.position.y - 0.01) / cell_size) - 1
	for row: int in range(first_row, last_row + 1):
		var left_cell := Vector2i(left_column, row)
		var right_cell := Vector2i(right_column, row)
		if grid.is_cell_valid(left_cell) and grid.is_cell_valid(right_cell):
			result.append({"a": left_cell, "b": right_cell})
	return result


func _add_environment_obstacle(
	object_id: String,
	world_rect: Rect2,
	blocks_line_of_sight: bool,
	jumpable: bool,
	active: bool = true,
	blocks_cells: bool = true
) -> void:
	if _combat_environment == null:
		return
	for index: int in range(_combat_environment.cover_objects.size() - 1, -1, -1):
		if str(_combat_environment.cover_objects[index].get("id", "")) == object_id:
			_combat_environment.cover_objects.remove_at(index)
	var local_rect := Rect2(_combat_environment.to_local(world_rect.position), world_rect.size)
	_combat_environment.cover_objects.append({
		"id": object_id,
		"rect": local_rect,
		"cover_bonus": 0,
		"blocks_movement": true,
		"blocks_cells": blocks_cells,
		"blocks_line_of_sight": blocks_line_of_sight,
		"jumpable": jumpable,
		"active": active
	})


func _rect_around(world_position: Vector2, rect_size: Vector2) -> Rect2:
	return Rect2(world_position - rect_size * 0.5, rect_size)


func _build_navigation() -> void:
	_west_navigation_region = _build_navigation_region(
		"WestServiceNavigationRegion",
		Rect2(Vector2(-200.0, -315.0), Vector2(192.0, 630.0))
	)
	_hall_navigation_region = _build_navigation_region(
		"MainHallNavigationRegion",
		Rect2(Vector2(PARTITION_LOCAL_X, -315.0), Vector2(998.0, 630.0))
	)
	_door_navigation_link = NavigationLink2D.new()
	_door_navigation_link.name = "WestServiceDoorNavigationLink"
	_door_navigation_link.start_position = Vector2(-40.0, 5.0)
	_door_navigation_link.end_position = Vector2(24.0, 5.0)
	_door_navigation_link.bidirectional = true
	_door_navigation_link.enter_cost = 0.0
	_door_navigation_link.travel_cost = 1.0
	_door_navigation_link.enabled = false
	add_child(_door_navigation_link)


func _build_navigation_region(node_name: String, local_rect: Rect2) -> NavigationRegion2D:
	var region := NavigationRegion2D.new()
	region.name = node_name
	var polygon := NavigationPolygon.new()
	polygon.vertices = PackedVector2Array([
		local_rect.position,
		local_rect.position + Vector2(local_rect.size.x, 0.0),
		local_rect.end,
		local_rect.position + Vector2(0.0, local_rect.size.y)
	])
	polygon.add_polygon(PackedInt32Array([0, 1, 2, 3]))
	region.navigation_polygon = polygon
	add_child(region)
	return region


func _build_wall(node_name: String, local_position: Vector2, wall_size: Vector2) -> void:
	var body := StaticBody2D.new()
	body.name = node_name
	body.position = local_position
	body.collision_layer = 1
	body.collision_mask = 1
	var shape := RectangleShape2D.new()
	shape.size = wall_size
	var collision := CollisionShape2D.new()
	collision.shape = shape
	body.add_child(collision)
	var visual := Polygon2D.new()
	visual.polygon = PackedVector2Array([
		Vector2(-wall_size.x * 0.5, -wall_size.y * 0.5),
		Vector2(wall_size.x * 0.5, -wall_size.y * 0.5),
		Vector2(wall_size.x * 0.5, wall_size.y * 0.5),
		Vector2(-wall_size.x * 0.5, wall_size.y * 0.5)
	])
	visual.color = Color(0.2, 0.22, 0.24, 1.0)
	visual.z_index = 4
	body.add_child(visual)
	add_child(body)


func _draw() -> void:
	var room_rect := Rect2(Vector2(-200.0, -315.0), Vector2(192.0, 630.0))
	draw_rect(room_rect, Color(0.1, 0.14, 0.16, 0.42), true)
	draw_rect(room_rect, Color(0.44, 0.56, 0.6, 0.8), false, 2.0)
	var hiding_rect := Rect2(Vector2(-183.0, -286.0), Vector2(126.0, 104.0))
	draw_rect(hiding_rect, Color(0.25, 0.16, 0.1, 0.9), true)
	draw_rect(hiding_rect, Color(0.62, 0.42, 0.22, 0.95), false, 2.0)
	draw_string(
		ThemeDB.fallback_font,
		hiding_rect.position + Vector2(7.0, 22.0),
		"УКРОМНОЕ МЕСТО",
		HORIZONTAL_ALIGNMENT_LEFT,
		hiding_rect.size.x - 14.0,
		12,
		Color(0.84, 0.76, 0.58, 0.88)
	)
