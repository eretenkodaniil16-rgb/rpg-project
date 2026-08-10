class_name LoadingScreenApprovedCompositeV03
extends Control

const SOURCE_SIZE: Vector2 = Vector2(1672.0, 941.0)
const SEGMENT_HEIGHT: float = 941.0
const SEAM_OVERLAP: float = 0.75
const SEGMENT_DIRECTORY: String = "res://assets/branding/loading_screen/approved/loading_screen_composite_v03/strips/"
const SEGMENT_NAMES: Array[String] = [
	"loading_screen_composite_c00.webp",
	"loading_screen_composite_c01.webp",
	"loading_screen_composite_c02.webp",
	"loading_screen_composite_c03.webp",
	"loading_screen_composite_c04.webp",
	"loading_screen_composite_c05.webp",
	"loading_screen_composite_c06.webp",
	"loading_screen_composite_c07.webp",
	"loading_screen_composite_c08.webp",
	"loading_screen_composite_c09.webp",
	"loading_screen_composite_c10.webp",
	"loading_screen_composite_c11.webp",
	"loading_screen_composite_c12.webp",
	"loading_screen_composite_c13.webp",
	"loading_screen_composite_c14.webp",
	"loading_screen_composite_c15.webp",
	"loading_screen_composite_c16.webp",
	"loading_screen_composite_c17.webp",
	"loading_screen_composite_c18.webp",
	"loading_screen_composite_c19.webp",
	"loading_screen_composite_c20.webp",
	"loading_screen_composite_c21.webp",
	"loading_screen_composite_c22.webp",
	"loading_screen_composite_c23.webp",
	"loading_screen_composite_c24.webp",
	"loading_screen_composite_c25.webp",
]
const SEGMENT_WIDTHS: Array[float] = [
	64.0, 64.0, 64.0, 64.0, 64.0, 64.0, 64.0, 64.0, 64.0,
	64.0, 64.0, 64.0, 64.0, 64.0, 64.0, 64.0, 64.0, 64.0,
	64.0, 64.0, 64.0, 64.0, 64.0, 64.0, 64.0, 72.0,
]

var _segments: Array[Texture2D] = []
var _complete: bool = false


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	texture_repeat = CanvasItem.TEXTURE_REPEAT_DISABLED
	_load_segments()
	visible = _complete
	queue_redraw()


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		queue_redraw()


func has_complete_tiles() -> bool:
	return _complete


func expected_tile_count() -> int:
	return SEGMENT_NAMES.size()


func source_size() -> Vector2:
	return SOURCE_SIZE


func _load_segments() -> void:
	_segments.clear()
	_complete = SEGMENT_NAMES.size() == SEGMENT_WIDTHS.size()
	for segment_name: String in SEGMENT_NAMES:
		var path: String = SEGMENT_DIRECTORY + segment_name
		if not ResourceLoader.exists(path, "Texture2D"):
			_complete = false
			_segments.append(null)
			continue
		var resource: Resource = load(path)
		if resource is Texture2D:
			_segments.append(resource as Texture2D)
		else:
			_complete = false
			_segments.append(null)


func _draw() -> void:
	if not _complete or _segments.size() != expected_tile_count():
		return
	if size.x <= 1.0 or size.y <= 1.0:
		return

	var scale_factor: float = maxf(size.x / SOURCE_SIZE.x, size.y / SOURCE_SIZE.y)
	var covered_size: Vector2 = SOURCE_SIZE * scale_factor
	var origin: Vector2 = (size - covered_size) * 0.5
	var x_offset: float = 0.0

	for index: int in range(_segments.size()):
		var texture: Texture2D = _segments[index]
		var source_width: float = SEGMENT_WIDTHS[index]
		if texture != null:
			var segment_origin: Vector2 = origin + Vector2(x_offset * scale_factor, 0.0)
			var draw_size := Vector2(source_width * scale_factor, SEGMENT_HEIGHT * scale_factor)
			if index < _segments.size() - 1:
				draw_size.x += SEAM_OVERLAP
			draw_texture_rect(texture, Rect2(segment_origin, draw_size), false)
		x_offset += source_width
