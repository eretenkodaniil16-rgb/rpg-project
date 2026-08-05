class_name LoadingScreenTiledLogoV01
extends Control

const SOURCE_SIZE: Vector2 = Vector2(896.0, 430.0)
const SEAM_OVERLAP: float = 0.75
const STRIP_DIRECTORY: String = "res://assets/branding/loading_screen/approved/loading_screen_logo_blue_v01/strips/"
const STRIP_NAMES: Array[String] = [
	"loading_screen_logo_base_c00.webp",
	"loading_screen_logo_base_c01.webp",
	"loading_screen_logo_base_c02.webp",
	"loading_screen_logo_base_c03.webp",
	"loading_screen_logo_base_c04.webp",
	"loading_screen_logo_base_c05.webp",
	"loading_screen_logo_mid_c00.webp",
	"loading_screen_logo_mid_c01.webp",
	"loading_screen_logo_mid_c02.webp",
	"loading_screen_logo_mid_c03.webp",
	"loading_screen_logo_tail_c00.webp",
	"loading_screen_logo_tail_c01.webp",
	"loading_screen_logo_tail_c02.webp",
	"loading_screen_logo_tail_c03.webp",
	"loading_screen_logo_tail_c04.webp",
	"loading_screen_logo_tail_c05.webp",
	"loading_screen_logo_tail_c06.webp",
	"loading_screen_logo_tail_c07.webp",
	"loading_screen_logo_tail_c08.webp",
	"loading_screen_logo_tail_c09.webp",
	"loading_screen_logo_tail_c10.webp",
	"loading_screen_logo_tail_c11.webp",
]
const STRIP_WIDTHS: Array[float] = [
	112.0, 112.0, 112.0, 112.0, 112.0, 112.0,
	14.0, 14.0, 14.0, 14.0,
	14.0, 14.0, 14.0, 14.0, 14.0, 14.0,
	14.0, 14.0, 14.0, 14.0, 14.0, 14.0,
]

var _textures: Array[Texture2D] = []
var _complete: bool = false


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	_load_strips()
	visible = _complete
	queue_redraw()


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		queue_redraw()


func has_complete_logo() -> bool:
	return _complete


func expected_strip_count() -> int:
	return STRIP_NAMES.size()


func source_size() -> Vector2:
	return SOURCE_SIZE


func _load_strips() -> void:
	_textures.clear()
	_complete = STRIP_NAMES.size() == STRIP_WIDTHS.size()
	for strip_name: String in STRIP_NAMES:
		var path: String = STRIP_DIRECTORY + strip_name
		if not ResourceLoader.exists(path, "Texture2D"):
			_complete = false
			_textures.append(null)
			continue
		var resource: Resource = load(path)
		if resource is Texture2D:
			_textures.append(resource as Texture2D)
		else:
			_complete = false
			_textures.append(null)


func _draw() -> void:
	if not _complete or size.x <= 1.0 or size.y <= 1.0:
		return
	var scale_factor: float = minf(size.x / SOURCE_SIZE.x, size.y / SOURCE_SIZE.y)
	var draw_size: Vector2 = SOURCE_SIZE * scale_factor
	var origin: Vector2 = (size - draw_size) * 0.5
	var x_offset: float = 0.0
	for index: int in range(_textures.size()):
		var texture: Texture2D = _textures[index]
		var strip_width: float = STRIP_WIDTHS[index]
		if texture != null:
			var extra_width: float = SEAM_OVERLAP if index < _textures.size() - 1 else 0.0
			var rect := Rect2(
				origin + Vector2(x_offset * scale_factor, 0.0),
				Vector2(strip_width * scale_factor + extra_width, draw_size.y)
			)
			draw_texture_rect(texture, rect, false)
		x_offset += strip_width
