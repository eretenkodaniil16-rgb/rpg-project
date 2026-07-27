class_name CombatEnvironment
extends Node2D

const DIFFICULT_COLOR: Color = Color(0.46, 0.34, 0.22, 0.34)
const HALF_COVER_COLOR: Color = Color(0.38, 0.42, 0.46, 0.94)
const HEAVY_COVER_COLOR: Color = Color(0.24, 0.27, 0.31, 0.98)
const INVALID_CELL: Vector2i = Vector2i(-99999, -99999)

var difficult_terrain: Array[Rect2] = []
var cover_objects: Array[Dictionary] = []
var _collision_root: Node2D


func _ready() -> void:
	add_to_group("combat_environment")
	_build_test_lobby_layout()
	_build_collision_bodies()
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
			"blocks_line_of_sight": false,
			"jumpable": true
		},
		{
			"id": "high_barricade",
			"rect": Rect2(621.0, 429.0, 64.0, 128.0),
			"cover_bonus": 5,
			"blocks_movement": true,
			"blocks_line_of_sight": false,
			"jumpable": true
		},
		{
			"id": "solid_wall",
			"rect": Rect2(813.0, 493.0, 64.0, 128.0),
			"cover_bonus": 0,
			"blocks_movement": true,
			"blocks_line_of_sight": true,
			"jumpable": false
		}
	]


func is_difficult_position(world_position: Vector2) -> bool:
	for terrain_rect: Rect2 in difficult_terrain:
		if terrain_rect.has_point(to_local(world_position)):
			return true
	return false


func is_position_blocked(world_position: Vector2, actor_radius: float = 18.0) -> bool:
	var local_position: Vector2 = to_local(world_position)
	for obstacle: Dictionary in cover_objects:
		if not bool(obstacle.get("blocks_movement", false)):
			continue
		var rect: Rect2 = obstacle.get("rect", Rect2()) as Rect2
		if rect.grow(actor_radius).has_point(local_position):
			return true
	return false


func is_cell_blocked(grid: BattleGrid, cell: Vector2i) -> bool:
	if grid == null or not grid.is_cell_valid(cell):
		return true
	var size: float = grid.get_cell_size()
	var center: Vector2 = to_local(grid.cell_to_world_center(cell))
	var cell_rect := Rect2(center - Vector2(size, size) * 0.5, Vector2(size, size)).grow(-2.0)
	for obstacle: Dictionary in cover_objects:
		if bool(obstacle.get("blocks_movement", false)) and (obstacle.get("rect", Rect2()) as Rect2).intersects(cell_rect):
			return true
	return false


func is_jumpable_cell(grid: BattleGrid, cell: Vector2i) -> bool:
	if grid == null or not grid.is_cell_valid(cell):
		return false
	var size: float = grid.get_cell_size()
	var center: Vector2 = to_local(grid.cell_to_world_center(cell))
	var cell_rect := Rect2(center - Vector2(size, size) * 0.5, Vector2(size, size)).grow(-2.0)
	for obstacle: Dictionary in cover_objects:
		if not bool(obstacle.get("blocks_movement", false)):
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
	for distance: int in range(1, maximum_crossed_cells + 2):
		var candidate: Vector2i = origin_cell + direction * distance
		if not grid.is_cell_valid(candidate):
			return INVALID_CELL
		if is_cell_blocked(grid, candidate):
			if not is_jumpable_cell(grid, candidate):
				return INVALID_CELL
			crossed_obstacle = true
			crossed_cells += 1
			if crossed_cells > maximum_crossed_cells:
				return INVALID_CELL
			continue
		if not crossed_obstacle:
			return INVALID_CELL
		if occupied_cells.has(candidate):
			return INVALID_CELL
		return candidate
	return INVALID_CELL


func get_cover(attacker_position: Vector2, target_position: Vector2) -> Dictionary:
	var start: Vector2 = to_local(attacker_position)
	var finish: Vector2 = to_local(target_position)
	var best_bonus: int = 0
	var total_cover: bool = false
	for obstacle: Dictionary in cover_objects:
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


func _build_collision_bodies() -> void:
	_collision_root = Node2D.new()
	_collision_root.name = "ObstacleCollisions"
	add_child(_collision_root)
	for obstacle: Dictionary in cover_objects:
		if not bool(obstacle.get("blocks_movement", false)):
			continue
		var rect: Rect2 = obstacle.get("rect", Rect2()) as Rect2
		var body := StaticBody2D.new()
		body.name = "%sCollision" % str(obstacle.get("id", "obstacle")).to_pascal_case()
		body.position = rect.get_center()
		body.collision_layer = 1
		body.collision_mask = 1
		var shape := RectangleShape2D.new()
		shape.size = rect.size
		var collision := CollisionShape2D.new()
		collision.shape = shape
		body.add_child(collision)
		_collision_root.add_child(body)


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
		var rect: Rect2 = obstacle.get("rect", Rect2()) as Rect2
		var blocks_sight: bool = bool(obstacle.get("blocks_line_of_sight", false))
		var bonus: int = int(obstacle.get("cover_bonus", 0))
		var color: Color = HEAVY_COVER_COLOR if blocks_sight or bonus >= 5 else HALF_COVER_COLOR
		draw_rect(rect, color, true)
		draw_rect(rect, Color(0.76, 0.8, 0.84, 0.86), false, 2.0)
		if bool(obstacle.get("jumpable", false)):
			draw_string(ThemeDB.fallback_font, rect.position + Vector2(4.0, 18.0), "ПРЫЖОК", HORIZONTAL_ALIGNMENT_LEFT, rect.size.x - 8.0, 11, Color(0.9, 0.88, 0.55, 0.8))


func _draw_cross_hatch(rect: Rect2) -> void:
	var step: float = 24.0
	var offset: float = -rect.size.y
	while offset < rect.size.x:
		var start := Vector2(rect.position.x + maxf(offset, 0.0), rect.position.y + maxf(-offset, 0.0))
		var finish := Vector2(rect.position.x + minf(offset + rect.size.y, rect.size.x), rect.end.y - maxf(offset + rect.size.y - rect.size.x, 0.0))
		draw_line(start, finish, Color(0.78, 0.58, 0.31, 0.28), 1.0)
		offset += step
