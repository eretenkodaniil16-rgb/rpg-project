class_name StealthTestRoom
extends Node2D

const DOOR_SCRIPT: Script = preload("res://scripts/game/stealth_door.gd")
const PATROL_OBSERVER_SCRIPT: Script = preload("res://scripts/game/stealth_patrol_observer.gd")
const PATROL_SYSTEM_SCRIPT: Script = preload("res://scripts/systems/patrol_alert_group_system.gd")

var _door: StealthDoor
var _patrol_observer: StealthPatrolObserver
var _patrol_data: PatrolAlertGroupSystem = PATROL_SYSTEM_SCRIPT.new() as PatrolAlertGroupSystem


func _ready() -> void:
	add_to_group("stealth_world")
	_build_wall("WestPartitionTop", Vector2(0.0, -187.5), Vector2(36.0, 255.0))
	_build_wall("WestPartitionBottom", Vector2(0.0, 187.5), Vector2(36.0, 255.0))
	_door = DOOR_SCRIPT.new() as StealthDoor
	_door.name = "WestServiceDoor"
	_door.door_id = "west_service_door"
	_door.door_label = "Дверь служебной комнаты"
	_door.door_size = Vector2(36.0, 120.0)
	add_child(_door)
	_build_patrol_observer()
	queue_redraw()


func get_test_door() -> StealthDoor:
	return _door


func get_patrol_observer() -> StealthPatrolObserver:
	return _patrol_observer


func _build_patrol_observer() -> void:
	_patrol_observer = PATROL_OBSERVER_SCRIPT.new() as StealthPatrolObserver
	_patrol_observer.name = "ServiceGuard"
	_patrol_observer.actor_id = "service_guard"
	_patrol_observer.display_name = "Служебный дозорный"
	_patrol_observer.default_facing_direction = Vector2.RIGHT
	add_child(_patrol_observer)
	var initial_position: Vector2 = _patrol_data.get_initial_patrol_position("service_guard")
	_patrol_observer.global_position = initial_position if initial_position != Vector2.ZERO else Vector2(760.0, 160.0)


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
	var room_rect := Rect2(Vector2(-200.0, -315.0), Vector2(180.0, 630.0))
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
