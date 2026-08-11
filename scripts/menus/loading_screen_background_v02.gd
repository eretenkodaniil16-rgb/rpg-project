class_name LoadingScreenBackgroundV02
extends Control

const BACKGROUND_TEXTURE_PATH: String = "res://assets/branding/loading_screen/approved/loading_screen_visual_v02/background/loading_screen_tower_blue_v02.png"
const EXPECTED_SOURCE_SIZE: Vector2 = Vector2(1672.0, 941.0)

var _background_texture: Texture2D = null


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	texture_repeat = CanvasItem.TEXTURE_REPEAT_DISABLED
	_load_background_texture()
	visible = has_background_texture()
	queue_redraw()


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		queue_redraw()


func has_background_texture() -> bool:
	return _background_texture != null


func source_size() -> Vector2:
	if _background_texture == null:
		return Vector2.ZERO
	return _background_texture.get_size()


func texture_path() -> String:
	return BACKGROUND_TEXTURE_PATH


func _load_background_texture() -> void:
	_background_texture = null
	if not ResourceLoader.exists(BACKGROUND_TEXTURE_PATH, "Texture2D"):
		return
	var resource: Resource = load(BACKGROUND_TEXTURE_PATH)
	if resource is Texture2D:
		_background_texture = resource as Texture2D


func _draw() -> void:
	if _background_texture == null or size.x <= 1.0 or size.y <= 1.0:
		return
	var texture_size: Vector2 = _background_texture.get_size()
	if texture_size.x <= 0.0 or texture_size.y <= 0.0:
		return
	var scale_factor: float = maxf(size.x / texture_size.x, size.y / texture_size.y)
	var covered_size: Vector2 = texture_size * scale_factor
	var origin: Vector2 = (size - covered_size) * 0.5
	draw_texture_rect(_background_texture, Rect2(origin, covered_size), false)
