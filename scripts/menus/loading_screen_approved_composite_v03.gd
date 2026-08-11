class_name LoadingScreenApprovedCompositeV03
extends Control

const SOURCE_SIZE: Vector2 = Vector2(768.0, 432.0)
const ASSET_PATH: String = "res://assets/branding/loading_screen/approved/loading_screen_composite_v03/loading_screen_approved_composite_v03.webp"

var _texture: Texture2D = null


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	texture_repeat = CanvasItem.TEXTURE_REPEAT_DISABLED
	_load_texture()
	visible = _texture != null
	queue_redraw()


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		queue_redraw()


func has_complete_tiles() -> bool:
	# Compatibility contract used by LoadingScreenVisualV02.
	return _texture != null


func expected_tile_count() -> int:
	# v03 intentionally uses one pixel master: no strip seams and one draw call.
	return 1


func source_size() -> Vector2:
	return SOURCE_SIZE


func _load_texture() -> void:
	_texture = null
	if not ResourceLoader.exists(ASSET_PATH, "Texture2D"):
		return
	var resource: Resource = load(ASSET_PATH)
	if resource is Texture2D:
		_texture = resource as Texture2D


func _draw() -> void:
	if _texture == null:
		return
	if size.x <= 1.0 or size.y <= 1.0:
		return

	var scale_factor: float = maxf(size.x / SOURCE_SIZE.x, size.y / SOURCE_SIZE.y)
	var covered_size: Vector2 = SOURCE_SIZE * scale_factor
	var origin: Vector2 = (size - covered_size) * 0.5
	draw_texture_rect(_texture, Rect2(origin, covered_size), false)
