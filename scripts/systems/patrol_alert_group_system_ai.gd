class_name PatrolAlertGroupSystemAi
extends PatrolAlertGroupSystem


func can_join_active_combat(actor_id: String) -> bool:
	return bool(get_actor_config(actor_id).get("can_join_active_combat", false))


func get_current_patrol_waypoint(actor_id: String, record: Dictionary) -> Dictionary:
	var config: Dictionary = get_actor_config(actor_id)
	var route: Dictionary = get_patrol_route(str(config.get("patrol_id", "")))
	var waypoints_value: Variant = route.get("waypoints", [])
	if not waypoints_value is Array or (waypoints_value as Array).is_empty():
		return {}
	var waypoints: Array = waypoints_value as Array
	var index: int = clampi(int(record.get("patrol_waypoint_index", 0)), 0, waypoints.size() - 1)
	var value: Variant = waypoints[index]
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func get_current_patrol_target(actor_id: String, record: Dictionary) -> Vector2:
	var waypoint: Dictionary = get_current_patrol_waypoint(actor_id, record)
	var value: Variant = waypoint.get("position", [])
	if value is Array and (value as Array).size() >= 2:
		return Vector2(float((value as Array)[0]), float((value as Array)[1]))
	return Vector2.ZERO
