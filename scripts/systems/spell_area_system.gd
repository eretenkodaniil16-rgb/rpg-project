class_name SpellAreaSystem
extends RefCounted

const SHAPE_CONE: String = "cone"
const SHAPE_CUBE: String = "cube"
const SHAPE_CYLINDER: String = "cylinder"
const SHAPE_EMANATION: String = "emanation"
const SHAPE_LINE: String = "line"
const SHAPE_SPHERE: String = "sphere"
const VALID_SHAPES: Array[String] = [
	SHAPE_CONE,
	SHAPE_CUBE,
	SHAPE_CYLINDER,
	SHAPE_EMANATION,
	SHAPE_LINE,
	SHAPE_SPHERE
]

const FEET_PER_CELL: int = 5
const ORIGIN_SELF: String = "self"
const ORIGIN_POINT: String = "point"


func is_area_definition(area: Dictionary) -> bool:
	return str(area.get("shape", "")) in VALID_SHAPES


func get_area_cells(
	grid: BattleGrid,
	caster_cell: Vector2i,
	aim_cell: Vector2i,
	area: Dictionary
) -> Array[Vector2i]:
	var result: Array[Vector2i] = []
	if grid == null or not is_area_definition(area):
		return result
	var origin_mode: String = str(area.get("origin", ORIGIN_POINT))
	var origin_cell: Vector2i = get_origin_cell(caster_cell, aim_cell, area)
	if not grid.is_cell_valid(origin_cell):
		return result
	var direction_delta: Vector2i = aim_cell - caster_cell if origin_mode == ORIGIN_POINT else aim_cell - origin_cell
	var direction := Vector2(direction_delta)
	if direction.length_squared() <= 0.0001:
		direction = Vector2.RIGHT
	direction = direction.normalized()
	var shape: String = str(area.get("shape", ""))
	var maximum_extent: int = _maximum_extent_cells(area)
	for x_offset: int in range(-maximum_extent, maximum_extent + 1):
		for y_offset: int in range(-maximum_extent, maximum_extent + 1):
			var cell := origin_cell + Vector2i(x_offset, y_offset)
			if not grid.is_cell_valid(cell):
				continue
			if _cell_is_inside(shape, origin_cell, cell, direction, area):
				result.append(cell)
	return result


func get_origin_cell(caster_cell: Vector2i, aim_cell: Vector2i, area: Dictionary) -> Vector2i:
	return caster_cell if str(area.get("origin", ORIGIN_POINT)) == ORIGIN_SELF else aim_cell


func filter_cells_by_total_cover(
	grid: BattleGrid,
	cells: Array[Vector2i],
	origin_world: Vector2,
	environment: Node
) -> Array[Vector2i]:
	var result: Array[Vector2i] = []
	if grid == null:
		return result
	for cell: Vector2i in cells:
		if _cell_has_clear_path(grid, cell, origin_world, environment):
			result.append(cell)
	return result


func collect_targets(
	grid: BattleGrid,
	cells: Array[Vector2i],
	candidates: Array[Node],
	origin_world: Vector2,
	environment: Node
) -> Array[Node]:
	var result: Array[Node] = []
	if grid == null or cells.is_empty():
		return result
	for candidate: Node in candidates:
		if not is_instance_valid(candidate) or not candidate is Node2D:
			continue
		var target := candidate as Node2D
		var target_cell: Vector2i = grid.world_to_cell(target.global_position)
		if target_cell not in cells:
			continue
		if not _cell_has_clear_path(grid, target_cell, origin_world, environment):
			continue
		if candidate not in result:
			result.append(candidate)
	return result


func resolve_point_of_origin(
	caster_world: Vector2,
	requested_world: Vector2,
	environment: Node,
	sample_step_pixels: float = 4.0
) -> Vector2:
	if environment == null or not environment.has_method("has_line_of_sight"):
		return requested_world
	if bool(environment.call("has_line_of_sight", caster_world, requested_world)):
		return requested_world
	var distance: float = caster_world.distance_to(requested_world)
	if distance <= 0.001:
		return caster_world
	var samples: int = maxi(ceili(distance / maxf(sample_step_pixels, 1.0)), 1)
	var last_visible: Vector2 = caster_world
	for index: int in range(1, samples + 1):
		var point: Vector2 = caster_world.lerp(requested_world, float(index) / float(samples))
		if not bool(environment.call("has_line_of_sight", caster_world, point)):
			break
		last_visible = point
	return last_visible


func area_label(area: Dictionary) -> String:
	var names: Dictionary = {
		SHAPE_CONE: "конус",
		SHAPE_CUBE: "куб",
		SHAPE_CYLINDER: "цилиндр",
		SHAPE_EMANATION: "эманация",
		SHAPE_LINE: "линия",
		SHAPE_SPHERE: "сфера"
	}
	var shape: String = str(area.get("shape", ""))
	var distance: int = _primary_distance_feet(area)
	return "%s %d футов" % [str(names.get(shape, shape)), distance] if distance > 0 else str(names.get(shape, shape))


func _cell_is_inside(
	shape: String,
	origin_cell: Vector2i,
	cell: Vector2i,
	direction: Vector2,
	area: Dictionary
) -> bool:
	var include_origin: bool = bool(area.get("include_origin", _default_include_origin(shape)))
	if cell == origin_cell:
		return include_origin
	var delta := Vector2(cell - origin_cell)
	var forward_distance: float = direction.dot(delta)
	var lateral_distance: float = absf(direction.cross(delta))
	match shape:
		SHAPE_SPHERE, SHAPE_CYLINDER, SHAPE_EMANATION:
			var radius_cells: int = _feet_to_cells(int(area.get("radius_ft", area.get("distance_ft", 5))))
			return maxi(absi(cell.x - origin_cell.x), absi(cell.y - origin_cell.y)) <= radius_cells
		SHAPE_CONE:
			var length_cells: int = _feet_to_cells(int(area.get("length_ft", 5)))
			return forward_distance > 0.0 and forward_distance <= float(length_cells) + 0.5 and lateral_distance <= forward_distance * 0.5
		SHAPE_LINE:
			var line_length_cells: int = _feet_to_cells(int(area.get("length_ft", 5)))
			var width_cells: int = maxi(_feet_to_cells(int(area.get("width_ft", 5))), 1)
			return forward_distance > 0.0 and forward_distance <= float(line_length_cells) + 0.5 and lateral_distance <= float(width_cells) * 0.5
		SHAPE_CUBE:
			var size_cells: int = maxi(_feet_to_cells(int(area.get("size_ft", 5))), 1)
			return forward_distance > 0.0 and forward_distance <= float(size_cells) + 0.5 and lateral_distance <= float(size_cells - 1) * 0.5 + 0.5
		_:
			return false


func _cell_has_clear_path(
	grid: BattleGrid,
	cell: Vector2i,
	origin_world: Vector2,
	environment: Node
) -> bool:
	if environment == null or not environment.has_method("has_line_of_sight"):
		return true
	var center: Vector2 = grid.cell_to_world_center(cell)
	var inset: float = grid.get_cell_size() * 0.4
	var sample_offsets: Array[Vector2] = [
		Vector2.ZERO,
		Vector2(inset, 0.0),
		Vector2(-inset, 0.0),
		Vector2(0.0, inset),
		Vector2(0.0, -inset),
		Vector2(inset, inset),
		Vector2(inset, -inset),
		Vector2(-inset, inset),
		Vector2(-inset, -inset)
	]
	for offset: Vector2 in sample_offsets:
		if bool(environment.call("has_line_of_sight", origin_world, center + offset)):
			return true
	return false


func _maximum_extent_cells(area: Dictionary) -> int:
	var shape: String = str(area.get("shape", ""))
	match shape:
		SHAPE_SPHERE, SHAPE_CYLINDER, SHAPE_EMANATION:
			return _feet_to_cells(int(area.get("radius_ft", area.get("distance_ft", 5))))
		SHAPE_CUBE:
			return maxi(_feet_to_cells(int(area.get("size_ft", 5))), 1)
		SHAPE_CONE, SHAPE_LINE:
			return maxi(_feet_to_cells(int(area.get("length_ft", 5))), 1)
		_:
			return 1


func _primary_distance_feet(area: Dictionary) -> int:
	for key: String in ["radius_ft", "length_ft", "size_ft", "distance_ft"]:
		if area.has(key):
			return maxi(int(area.get(key, 0)), 0)
	return 0


func _default_include_origin(shape: String) -> bool:
	return shape in [SHAPE_SPHERE, SHAPE_CYLINDER]


func _feet_to_cells(feet: int) -> int:
	return maxi(ceili(float(maxi(feet, 0)) / float(FEET_PER_CELL)), 0)
