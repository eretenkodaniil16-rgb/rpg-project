class_name LoadingProgressBarV03
extends Control

const CAP_WIDTH_RATIO: float = 1.375
const TRACK_HEIGHT_RATIO: float = 0.52
const TRACK_INSET_RATIO: float = 0.64
const INNER_MARGIN_RATIO: float = 0.14
const CENTER_RUNE_RATIO: float = 1.08
const GLINT_CYCLE_SECONDS: float = 2.8

@export_range(0.0, 100.0, 0.1) var value: float = 72.0:
	set(next_value):
		value = clampf(next_value, 0.0, 100.0)
		if is_node_ready():
			_apply_layout()

@export var animate_glint: bool = true
@export var show_decorative_frame: bool = true

@onready var _track: TextureRect = $Track
@onready var _fill_clip: Control = $FillClip
@onready var _fill_texture: TextureRect = $FillClip/FillTexture
@onready var _glint: TextureRect = $FillClip/Glint
@onready var _left_cap: TextureRect = $LeftCap
@onready var _right_cap: TextureRect = $RightCap
@onready var _center_rune: TextureRect = $CenterRune

var _reduced_motion: bool = false
var _glint_phase: float = 0.0
var _full_fill_width: float = 0.0


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	_reduced_motion = bool(ProjectSettings.get_setting("accessibility/reduced_motion", false))
	resized.connect(_apply_layout)
	_apply_frame_visibility()
	_apply_layout()
	set_process(animate_glint and not _reduced_motion)


func _process(delta: float) -> void:
	if _reduced_motion or not animate_glint or value <= 0.0:
		_glint.visible = false
		return
	_glint.visible = true
	_glint_phase = fmod(_glint_phase + delta / GLINT_CYCLE_SECONDS, 1.0)
	_apply_glint_position()


func set_progress(next_value: float) -> void:
	value = next_value


func normalized_value() -> float:
	return value / 100.0


func fill_width() -> float:
	return _fill_clip.size.x


func full_fill_width() -> float:
	return _full_fill_width


func has_complete_textures() -> bool:
	return (
		_track.texture != null
		and _fill_texture.texture != null
		and _glint.texture != null
		and _left_cap.texture != null
		and _right_cap.texture != null
		and _center_rune.texture != null
	)


func uses_mirrored_right_cap() -> bool:
	return _right_cap.texture == _left_cap.texture and _right_cap.scale.x < 0.0


func _apply_frame_visibility() -> void:
	_track.visible = show_decorative_frame
	_left_cap.visible = show_decorative_frame
	_right_cap.visible = show_decorative_frame
	_center_rune.visible = show_decorative_frame


func _apply_layout() -> void:
	if not is_node_ready():
		return
	var bar_height: float = maxf(size.y, 1.0)
	var cap_width: float = bar_height * CAP_WIDTH_RATIO
	var track_height: float = bar_height * TRACK_HEIGHT_RATIO
	var track_x: float = cap_width * TRACK_INSET_RATIO
	var track_width: float = maxf(size.x - track_x * 2.0, 1.0)
	var track_y: float = (bar_height - track_height) * 0.5

	_left_cap.position = Vector2.ZERO
	_left_cap.size = Vector2(cap_width, bar_height)
	_left_cap.pivot_offset = Vector2(cap_width * 0.5, bar_height * 0.5)
	_left_cap.scale = Vector2.ONE

	_right_cap.position = Vector2(size.x - cap_width, 0.0)
	_right_cap.size = Vector2(cap_width, bar_height)
	_right_cap.pivot_offset = Vector2(cap_width * 0.5, bar_height * 0.5)
	_right_cap.scale = Vector2(-1.0, 1.0)

	_track.position = Vector2(track_x, track_y)
	_track.size = Vector2(track_width, track_height)

	var inner_margin: float = track_height * INNER_MARGIN_RATIO
	var fill_height: float = maxf(track_height - inner_margin * 2.0, 1.0)
	_full_fill_width = maxf(track_width - inner_margin * 2.0, 1.0)
	_fill_clip.position = Vector2(track_x + inner_margin, track_y + inner_margin)
	_fill_clip.size = Vector2(_full_fill_width * normalized_value(), fill_height)
	_fill_texture.position = Vector2.ZERO
	_fill_texture.size = Vector2(_full_fill_width, fill_height)

	var rune_size: float = bar_height * CENTER_RUNE_RATIO
	_center_rune.position = Vector2((size.x - rune_size) * 0.5, (bar_height - rune_size) * 0.5)
	_center_rune.size = Vector2(rune_size, rune_size)
	_apply_glint_position()


func _apply_glint_position() -> void:
	if not is_node_ready():
		return
	var glint_width: float = maxf(_fill_clip.size.y * 1.45, 1.0)
	_glint.size = Vector2(glint_width, _fill_clip.size.y)
	var travel_width: float = _fill_clip.size.x + glint_width
	_glint.position = Vector2(-glint_width + travel_width * _glint_phase, 0.0)
