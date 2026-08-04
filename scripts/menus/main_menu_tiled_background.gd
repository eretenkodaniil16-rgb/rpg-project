class_name MainMenuTiledBackground
extends Control

const COLUMNS: int = 8
const STRIP_SIZE: Vector2 = Vector2(160.0, 720.0)
const SOURCE_SIZE: Vector2 = Vector2(1280.0, 720.0)
const STRIP_PATH_PATTERN: String = "res://assets/branding/main_menu/approved/strips/main_menu_strip_c%02d.webp"
const SEAM_OVERLAP: float = 0.65

var _strips: Array[Texture2D] = []
var _complete: bool = false


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_load_strips()
	visible = _complete
	queue_redraw()


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		queue_redraw()


func has_complete_tiles() -> bool:
	return _complete


func expected_tile_count() -> int:
	return COLUMNS


func _load_strips() -> void:
	_strips.clear()
	_complete = true
	for column: int in range(COLUMNS):
		var path: String = STRIP_PATH_PATTERN % column
		if not ResourceLoader.exists(path, "Texture2D"):
			_complete = false
			_strips.append(null)
			continue
		var resource: Resource = load(path)
		if resource is Texture2D:
			_strips.append(resource as Texture2D)
		else:
			_complete = false
			_strips.append(null)


func _draw() -> void:
	if not _complete or _strips.size() != expected_tile_count():
		return
	if size.x <= 1.0 or size.y <= 1.0:
		return

	var scale_factor: float = maxf(size.x / SOURCE_SIZE.x, size.y / SOURCE_SIZE.y)
	var covered_size: Vector2 = SOURCE_SIZE * scale_factor
	var origin: Vector2 = (size - covered_size) * 0.5
	var scaled_strip: Vector2 = STRIP_SIZE * scale_factor

	for column: int in range(COLUMNS):
		var texture: Texture2D = _strips[column]
		if texture == null:
			continue
		var strip_origin: Vector2 = origin + Vector2(column * scaled_strip.x, 0.0)
		var draw_size: Vector2 = scaled_strip
		if column < COLUMNS - 1:
			draw_size.x += SEAM_OVERLAP
		draw_texture_rect(texture, Rect2(strip_origin, draw_size), false)
