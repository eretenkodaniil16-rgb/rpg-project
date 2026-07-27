class_name DirectionalTargetingSystem
extends RefCounted

const DEFAULT_TARGET_RADIUS_PX: float = 42.0
const EDGE_PADDING_PX: float = 3.0


static func normalized_direction(direction: Vector2) -> Vector2:
	if direction.length_squared() <= 0.0001:
		return Vector2.RIGHT
	return direction.normalized()


static func feet_to_pixels(distance_feet: int) -> float:
	var cells: int = ceili(float(maxi(distance_feet, 0)) / 5.0)
	return float(cells) * DistanceSystem.PIXELS_PER_5_FEET


static func find_first_target(
	origin: Vector2,
	direction: Vector2,
	candidates: Array[Node],
	maximum_distance_pixels: float,
	default_radius_pixels: float = DEFAULT_TARGET_RADIUS_PX
) -> Node:
	var aim: Vector2 = normalized_direction(direction)
	var best_target: Node = null
	var best_forward_distance: float = INF
	for candidate: Node in candidates:
		if not candidate is Node2D or not is_instance_valid(candidate):
			continue
		if candidate.has_method("is_combat_active") and not bool(candidate.call("is_combat_active")):
			continue
		var offset: Vector2 = (candidate as Node2D).global_position - origin
		var forward_distance: float = offset.dot(aim)
		if forward_distance <= 0.0 or forward_distance > maximum_distance_pixels:
			continue
		var lateral_distance: float = absf(offset.cross(aim))
		var target_radius: float = default_radius_pixels
		if candidate.has_method("get_combat_target_radius"):
			target_radius = maxf(float(candidate.call("get_combat_target_radius")), 1.0)
		if lateral_distance <= target_radius and forward_distance < best_forward_distance:
			best_forward_distance = forward_distance
			best_target = candidate
	return best_target


static func endpoint_inside_rect(
	origin: Vector2,
	direction: Vector2,
	maximum_distance_pixels: float,
	bounds: Rect2
) -> Vector2:
	var aim: Vector2 = normalized_direction(direction)
	var permitted_distance: float = maxf(maximum_distance_pixels, 0.0)
	if absf(aim.x) > 0.0001:
		var boundary_x: float = bounds.end.x if aim.x > 0.0 else bounds.position.x
		var distance_x: float = (boundary_x - origin.x) / aim.x
		if distance_x >= 0.0:
			permitted_distance = minf(permitted_distance, distance_x)
	if absf(aim.y) > 0.0001:
		var boundary_y: float = bounds.end.y if aim.y > 0.0 else bounds.position.y
		var distance_y: float = (boundary_y - origin.y) / aim.y
		if distance_y >= 0.0:
			permitted_distance = minf(permitted_distance, distance_y)
	permitted_distance = maxf(permitted_distance - EDGE_PADDING_PX, 0.0)
	return origin + aim * permitted_distance
