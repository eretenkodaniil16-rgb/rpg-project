class_name AreaEffectSystem
extends RefCounted


static func targets_in_sphere(center: Vector2, radius_feet: int, candidates: Array[Node]) -> Array[Node]:
	var result: Array[Node] = []
	var radius_pixels: float = DistanceSystem.feet_to_pixels(radius_feet)
	for candidate: Node in candidates:
		if candidate is Node2D and is_instance_valid(candidate):
			if center.distance_to((candidate as Node2D).global_position) <= radius_pixels:
				result.append(candidate)
	return result


static func targets_in_cube(center: Vector2, side_feet: int, candidates: Array[Node]) -> Array[Node]:
	var result: Array[Node] = []
	var half_pixels: float = DistanceSystem.feet_to_pixels(side_feet) * 0.5
	var rect := Rect2(center - Vector2(half_pixels, half_pixels), Vector2(half_pixels * 2.0, half_pixels * 2.0))
	for candidate: Node in candidates:
		if candidate is Node2D and is_instance_valid(candidate) and rect.has_point((candidate as Node2D).global_position):
			result.append(candidate)
	return result


static func targets_in_line(
	origin: Vector2,
	direction: Vector2,
	length_feet: int,
	width_feet: int,
	candidates: Array[Node]
) -> Array[Node]:
	var result: Array[Node] = []
	var safe_direction: Vector2 = direction.normalized() if direction.length_squared() > 0.0001 else Vector2.RIGHT
	var length_pixels: float = DistanceSystem.feet_to_pixels(length_feet)
	var half_width_pixels: float = DistanceSystem.feet_to_pixels(width_feet) * 0.5
	for candidate: Node in candidates:
		if not (candidate is Node2D) or not is_instance_valid(candidate):
			continue
		var relative: Vector2 = (candidate as Node2D).global_position - origin
		var forward: float = relative.dot(safe_direction)
		if forward < 0.0 or forward > length_pixels:
			continue
		var perpendicular: float = absf(relative.cross(safe_direction))
		if perpendicular <= half_width_pixels:
			result.append(candidate)
	return result


static func targets_in_cone(
	origin: Vector2,
	direction: Vector2,
	length_feet: int,
	candidates: Array[Node]
) -> Array[Node]:
	var result: Array[Node] = []
	var safe_direction: Vector2 = direction.normalized() if direction.length_squared() > 0.0001 else Vector2.RIGHT
	var length_pixels: float = DistanceSystem.feet_to_pixels(length_feet)
	for candidate: Node in candidates:
		if not (candidate is Node2D) or not is_instance_valid(candidate):
			continue
		var relative: Vector2 = (candidate as Node2D).global_position - origin
		var distance: float = relative.length()
		if distance <= 0.001 or distance > length_pixels:
			continue
		var forward: float = relative.dot(safe_direction)
		if forward <= 0.0:
			continue
		var half_width_at_distance: float = distance * 0.5
		var perpendicular: float = absf(relative.cross(safe_direction))
		if perpendicular <= half_width_at_distance:
			result.append(candidate)
	return result


static func sort_by_distance(origin: Vector2, candidates: Array[Node]) -> Array[Node]:
	var result: Array[Node] = candidates.duplicate()
	result.sort_custom(func(left: Node, right: Node) -> bool:
		if not (left is Node2D) or not (right is Node2D):
			return left.get_instance_id() < right.get_instance_id()
		return origin.distance_squared_to((left as Node2D).global_position) < origin.distance_squared_to((right as Node2D).global_position)
	)
	return result
