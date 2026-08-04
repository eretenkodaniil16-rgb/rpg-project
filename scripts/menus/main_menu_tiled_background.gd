class_name MainMenuTiledBackground
extends Control

const COLUMNS: int = 8
const ROWS: int = 4
const TILE_SIZE: Vector2 = Vector2(160.0, 180.0)
const SOURCE_SIZE: Vector2 = Vector2(1280.0, 720.0)
const TILE_PATH_PATTERN: String = "res://assets/branding/main_menu/approved/tiles/main_menu_tile_r%02d_c%02d.webp"
const SEAM_OVERLAP: float = 0.65

var _tiles: Array[Texture2D] = []
var _complete: bool = false


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_load_tiles()
	visible = _complete
	queue_redraw()


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		queue_redraw()


func has_complete_tiles() -> bool:
	return _complete


func expected_tile_count() -> int:
	return COLUMNS * ROWS


func _load_tiles() -> void:
	_tiles.clear()
	_complete = true
	for row: int in range(ROWS):
		for column: int in range(COLUMNS):
			var path: String = TILE_PATH_PATTERN % [row, column]
			if not ResourceLoader.exists(path, "Texture2D"):
				_complete = false
				_tiles.append(null)
				continue
			var resource: Resource = load(path)
			if resource is Texture2D:
				_tiles.append(resource as Texture2D)
			else:
				_complete = false
				_tiles.append(null)


func _draw() -> void:
	if not _complete or _tiles.size() != expected_tile_count():
		return
	if size.x <= 1.0 or size.y <= 1.0:
		return

	var scale_factor: float = maxf(size.x / SOURCE_SIZE.x, size.y / SOURCE_SIZE.y)
	var covered_size: Vector2 = SOURCE_SIZE * scale_factor
	var origin: Vector2 = (size - covered_size) * 0.5
	var scaled_tile: Vector2 = TILE_SIZE * scale_factor

	for row: int in range(ROWS):
		for column: int in range(COLUMNS):
			var index: int = row * COLUMNS + column
			var texture: Texture2D = _tiles[index]
			if texture == null:
				continue
			var tile_origin: Vector2 = origin + Vector2(column * scaled_tile.x, row * scaled_tile.y)
			var draw_size: Vector2 = scaled_tile
			if column < COLUMNS - 1:
				draw_size.x += SEAM_OVERLAP
			if row < ROWS - 1:
				draw_size.y += SEAM_OVERLAP
			draw_texture_rect(texture, Rect2(tile_origin, draw_size), false)
