class_name PatrolAlertGroupSystem
extends RefCounted

const DATA_PATH: String = "res://data/world/patrol_alert_groups.json"

var _actors: Dictionary = {}
var _alert_groups: Dictionary = {}
var _patrol_routes: Dictionary = {}


func _init() -> void:
	_load_data()


func get_actor_config(actor_id: String) -> Dictionary:
	var value: Variant = _actors.get(actor_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func get_alert_group(group_id: String) -> Dictionary:
	var value: Variant = _alert_groups.get(group_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func get_patrol_route(route_id: String) -> Dictionary:
	var value: Variant = _patrol_routes.get(route_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func has_actor_config(actor_id: String) -> bool:
	return not get_actor_config(actor_id).is_empty()


func can_start_combat(actor_id: String) -> bool:
	return bool(get_actor_config(actor_id).get("can_start_combat", true))


func participates_in_combat(actor_id: String) -> bool:
	return bool(get_actor_config(actor_id).get("participates_in_combat", true))


func get_alert_group_id(actor_id: String) -> String:
	return str(get_actor_config(actor_id).get("alert_group_id", ""))


func get_initial_patrol_position(actor_id: String) -> Vector2:
	var config: Dictionary = get_actor_config(actor_id)
	var route: Dictionary = get_patrol_route(str(config.get("patrol_id", "")))
	var waypoints: Array = route.get("waypoints", []) as Array if route.get("waypoints", []) is Array else []
	if waypoints.is_empty() or not waypoints[0] is Dictionary:
		return Vector2.ZERO
	return _vector_from((waypoints[0] as Dictionary).get("position", []))


func advance_patrol(actor_id: String, record: Dictionary, current_position: Vector2, delta: float) -> Dictionary:
	var config: Dictionary = get_actor_config(actor_id)
	var route_id: String = str(config.get("patrol_id", ""))
	var route: Dictionary = get_patrol_route(route_id)
	var waypoints: Array = route.get("waypoints", []) as Array if route.get("waypoints", []) is Array else []
	var result_record: Dictionary = record.duplicate(true)
	if route_id.is_empty() or waypoints.is_empty():
		return {
			"active": false,
			"moved": false,
			"position": current_position,
			"facing": Vector2.ZERO,
			"record": result_record
		}
	var waypoint_index: int = clampi(int(result_record.get("patrol_waypoint_index", 0)), 0, waypoints.size() - 1)
	var direction: int = 1 if int(result_record.get("patrol_direction", 1)) >= 0 else -1
	var waypoint: Dictionary = waypoints[waypoint_index] as Dictionary if waypoints[waypoint_index] is Dictionary else {}
	var target_position: Vector2 = _vector_from(waypoint.get("position", []))
	var reached_distance: float = maxf(float(route.get("waypoint_reached_distance_pixels", 10.0)), 1.0)
	var distance: float = current_position.distance_to(target_position)
	if distance > reached_distance:
		var speed: float = maxf(float(config.get("patrol_speed_pixels", 70.0)), 0.0)
		var next_position: Vector2 = current_position.move_toward(target_position, speed * maxf(delta, 0.0))
		result_record["patrol_waypoint_index"] = waypoint_index
		result_record["patrol_direction"] = direction
		result_record["patrol_wait_remaining"] = 0.0
		result_record["patrol_wait_initialized"] = false
		return {
			"active": true,
			"moved": next_position.distance_squared_to(current_position) > 0.0001,
			"position": next_position,
			"facing": target_position - current_position,
			"record": result_record
		}
	var wait_initialized: bool = bool(result_record.get("patrol_wait_initialized", false))
	var wait_remaining: float = maxf(float(result_record.get("patrol_wait_remaining", 0.0)), 0.0)
	if not wait_initialized:
		wait_remaining = maxf(float(waypoint.get("wait_seconds", 0.0)), 0.0)
		result_record["patrol_wait_initialized"] = true
	if wait_remaining > 0.0:
		wait_remaining = maxf(wait_remaining - maxf(delta, 0.0), 0.0)
		result_record["patrol_wait_remaining"] = wait_remaining
		result_record["patrol_waypoint_index"] = waypoint_index
		result_record["patrol_direction"] = direction
		return {
			"active": true,
			"moved": false,
			"position": target_position,
			"facing": _vector_from(waypoint.get("facing", [])),
			"record": result_record
		}
	var next_state: Dictionary = _next_waypoint_state(waypoint_index, direction, waypoints.size(), str(route.get("loop_mode", "loop")))
	result_record["patrol_waypoint_index"] = int(next_state.get("index", waypoint_index))
	result_record["patrol_direction"] = int(next_state.get("direction", direction))
	result_record["patrol_wait_remaining"] = 0.0
	result_record["patrol_wait_initialized"] = false
	return {
		"active": bool(next_state.get("active", true)),
		"moved": false,
		"position": target_position,
		"facing": _vector_from(waypoint.get("facing", [])),
		"record": result_record
	}


func can_relay_alert(
	source_actor_id: String,
	listener_actor_id: String,
	source_position: Vector2,
	listener_position: Vector2,
	audibility_multiplier: float = 1.0
) -> bool:
	if source_actor_id.is_empty() or listener_actor_id.is_empty() or source_actor_id == listener_actor_id:
		return false
	var source_group_id: String = get_alert_group_id(source_actor_id)
	if source_group_id.is_empty() or source_group_id != get_alert_group_id(listener_actor_id):
		return false
	var group: Dictionary = get_alert_group(source_group_id)
	if group.is_empty():
		return false
	var relay_radius: float = maxf(float(group.get("relay_radius_feet", 40.0)), 0.0) * clampf(audibility_multiplier, 0.0, 1.0)
	return float(DistanceSystem.distance_feet(source_position, listener_position)) <= relay_radius


func apply_alert_relay(
	listener_actor_id: String,
	listener_record: Dictionary,
	source_actor_id: String,
	source_record: Dictionary,
	listener_profile: Dictionary
) -> Dictionary:
	var result: Dictionary = listener_record.duplicate(true)
	var current_state: String = str(result.get("state", StealthAlertSystem.STATE_CALM))
	if current_state in [StealthAlertSystem.STATE_ALERTED, StealthAlertSystem.STATE_COMBAT]:
		return result
	var group_id: String = get_alert_group_id(listener_actor_id)
	var group: Dictionary = get_alert_group(group_id)
	result["actor_id"] = listener_actor_id
	result["state"] = str(group.get("relay_state", StealthAlertSystem.STATE_INVESTIGATING))
	result["suspicion"] = maxf(
		float(result.get("suspicion", 0.0)),
		float(group.get("relay_suspicion", StealthAlertSystem.SUSPICION_INVESTIGATING))
	)
	result["last_known_position"] = (source_record.get("last_known_position", [0.0, 0.0]) as Array).duplicate()
	result["search_seconds_remaining"] = float(listener_profile.get("search_duration_seconds", 10.0))
	result["alert_cooldown_seconds"] = float(listener_profile.get("alert_cooldown_seconds", 20.0))
	result["last_alert_source_id"] = source_actor_id
	result["alert_relay_count"] = int(result.get("alert_relay_count", 0)) + 1
	return result


func _next_waypoint_state(index: int, direction: int, count: int, loop_mode: String) -> Dictionary:
	if count <= 1:
		return {"index": 0, "direction": 1, "active": loop_mode != "once"}
	match loop_mode:
		"ping_pong":
			var next_index: int = index + direction
			var next_direction: int = direction
			if next_index >= count:
				next_direction = -1
				next_index = count - 2
			elif next_index < 0:
				next_direction = 1
				next_index = 1
			return {"index": next_index, "direction": next_direction, "active": true}
		"once":
			if index >= count - 1:
				return {"index": count - 1, "direction": 1, "active": false}
			return {"index": index + 1, "direction": 1, "active": true}
		_:
			return {"index": (index + 1) % count, "direction": 1, "active": true}


func _vector_from(value: Variant) -> Vector2:
	if value is Vector2:
		return value as Vector2
	if value is Array and (value as Array).size() >= 2:
		return Vector2(float((value as Array)[0]), float((value as Array)[1]))
	return Vector2.ZERO


func _load_data() -> void:
	_actors.clear()
	_alert_groups.clear()
	_patrol_routes.clear()
	if not FileAccess.file_exists(DATA_PATH):
		return
	var file: FileAccess = FileAccess.open(DATA_PATH, FileAccess.READ)
	if file == null:
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		return
	var data: Dictionary = parsed as Dictionary
	_actors = (data.get("actors", {}) as Dictionary).duplicate(true) if data.get("actors", {}) is Dictionary else {}
	_alert_groups = (data.get("alert_groups", {}) as Dictionary).duplicate(true) if data.get("alert_groups", {}) is Dictionary else {}
	_patrol_routes = (data.get("patrol_routes", {}) as Dictionary).duplicate(true) if data.get("patrol_routes", {}) is Dictionary else {}
