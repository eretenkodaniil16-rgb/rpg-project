class_name CombatEnvironment
extends Node2D

const DIFFICULT_COLOR: Color = Color(0.46, 0.34, 0.22, 0.34)
const HALF_COVER_COLOR: Color = Color(0.38, 0.42, 0.46, 0.94)
const HEAVY_COVER_COLOR: Color = Color(0.24, 0.27, 0.31, 0.98)

var difficult_terrain: Array[Rect2] = []
var cover_objects: Array[Dictionary] = []


func _ready() -> void:
	add_to_group("combat_environment")
	_build_test_lobby_layout()
	queue_redraw()


func _build_test_lobby_layout() -> void:
	difficult_terrain = [
		Rect2(365.0, 301.0, 192.0, 128.0)
	]
	cover_objects = [
		{
			"rect": Rect2(621.0, 173.0, 64.0, 128.0),
			"cover_bonus": 2,
			"blocks_movement": true,
			"blocks_line_of_sight": false
		},
		{
			"rect": Rect2(621.0, 429.0, 64.0, 128.0),
			"cover_bonus": 5,
			"blocks_movement": true,
			"blocks_line_of_sight": false
		},
		{
			"rect": Rect2(813.0, 237.0, 64.0, 128.0),
			"cover_bonus": 0,
			"blocks_movement": true,
			"blocks_line_of_sight": true
		}
	]


func is_difficult_position(world_position: Vector2) -> bool:
	for terrain_rect: Rect2 in difficult_terrain:
		if terrain_rect.has_point(world_position):
			return true
	return false


func is_cell_blocked(grid: BattleGrid, cell: Vector2i) -> bool:
	if grid == null or not grid.is_cell_valid(cell):
		return true
	var center: Vector2 = grid.cell_to_world_center(cell)
	for obstacle: Dictionary in cover_objects:
		if bool(obstacle.get("blocks_movement", false)) and (obstacle.get("rect", Rect2()) as Rect2).has_point(center):
			return true
	return false


func get_cover(attacker_position: Vector2, target_position: Vector2) -> Dictionary:
	var best_bonus: int = 0
	var total_cover: bool = false
	for obstacle: Dictionary in cover_objects:
		var rect: Rect2 = obstacle.get("rect", Rect2()) as Rect2
		if not _segment_crosses_rect(attacker_position, target_position, rect):
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


func _draw_cross_hatch(rect: Rect2) -> void:
	var step: float = 24.0
	var offset: float = -rect.size.y
	while offset < rect.size.x:
		var start := Vector2(rect.position.x + maxf(offset, 0.0), rect.position.y + maxf(-offset, 0.0))
		var finish := Vector2(rect.position.x + minf(offset + rect.size.y, rect.size.x), rect.end.y - maxf(offset + rect.size.y - rect.size.x, 0.0))
		draw_line(start, finish, Color(0.78, 0.58, 0.31, 0.28), 1.0)
		offset += step
