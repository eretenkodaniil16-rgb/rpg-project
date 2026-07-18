class_name DialoguePortrait
extends Control

var _target: Node = null
var _portrait_texture: Texture2D = null
var _polygon: PackedVector2Array = PackedVector2Array()
var _portrait_color: Color = Color(0.72, 0.76, 0.82, 1.0)


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	clip_contents = true
	queue_redraw()


func set_character(target: Node) -> void:
	_target = target if target != null and is_instance_valid(target) else null
	_portrait_texture = null
	_polygon = PackedVector2Array()
	_portrait_color = Color(0.72, 0.76, 0.82, 1.0)
	if _target != null:
		_read_target_visual(_target)
	queue_redraw()


func clear_character() -> void:
	_target = null
	_portrait_texture = null
	_polygon = PackedVector2Array()
	queue_redraw()


func has_character() -> bool:
	return _target != null and is_instance_valid(_target)


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		queue_redraw()


func _read_target_visual(target: Node) -> void:
	if target.has_method("get_dialogue_portrait_texture"):
		var texture_value: Variant = target.call("get_dialogue_portrait_texture")
		if texture_value is Texture2D:
			_portrait_texture = texture_value as Texture2D
			return
	var body: Node = target.get_node_or_null("Body")
	if body is Sprite2D:
		var sprite := body as Sprite2D
		_portrait_texture = sprite.texture
		_portrait_color = sprite.modulate
		return
	if body is Polygon2D:
		var polygon_body := body as Polygon2D
		_polygon = polygon_body.polygon
		_portrait_color = polygon_body.color * polygon_body.modulate


func _draw() -> void:
	if size.x <= 1.0 or size.y <= 1.0:
		return
	var outer := Rect2(Vector2.ZERO, size)
	var inner := outer.grow(-4.0)
	draw_rect(outer, Color(0.025, 0.035, 0.05, 0.97), true)
	draw_rect(inner, Color(0.11, 0.14, 0.17, 0.96), true)
	draw_rect(inner, Color(0.78, 0.64, 0.36, 0.92), false, 2.0)

	var art_rect := inner.grow(-12.0)
	draw_circle(art_rect.get_center() + Vector2(0.0, 8.0), minf(art_rect.size.x, art_rect.size.y) * 0.38, Color(0.18, 0.22, 0.26, 0.9))
	if _portrait_texture != null:
		draw_texture_rect(_portrait_texture, art_rect, true, _portrait_color)
		return
	if not _polygon.is_empty():
		_draw_polygon_portrait(art_rect)
		return
	_draw_placeholder_portrait(art_rect)


func _draw_polygon_portrait(art_rect: Rect2) -> void:
	var bounds: Rect2 = _polygon_bounds(_polygon)
	if bounds.size.x <= 0.001 or bounds.size.y <= 0.001:
		_draw_placeholder_portrait(art_rect)
		return
	var scale_factor: float = minf(art_rect.size.x / bounds.size.x, art_rect.size.y / bounds.size.y) * 0.62
	var source_center: Vector2 = bounds.get_center()
	var target_center: Vector2 = art_rect.get_center() + Vector2(0.0, 4.0)
	var transformed := PackedVector2Array()
	for point: Vector2 in _polygon:
		transformed.append(target_center + (point - source_center) * scale_factor)
	draw_colored_polygon(transformed, _portrait_color)
	var outline := transformed.duplicate()
	if not outline.is_empty():
		outline.append(outline[0])
		draw_polyline(outline, Color(1.0, 0.88, 0.62, 0.86), 3.0, true)


func _draw_placeholder_portrait(art_rect: Rect2) -> void:
	var center: Vector2 = art_rect.get_center()
	var radius: float = minf(art_rect.size.x, art_rect.size.y) * 0.18
	draw_circle(center - Vector2(0.0, radius * 0.85), radius, _portrait_color)
	var shoulders := PackedVector2Array([
		center + Vector2(-radius * 1.8, radius * 1.8),
		center + Vector2(-radius * 1.2, radius * 0.3),
		center + Vector2(radius * 1.2, radius * 0.3),
		center + Vector2(radius * 1.8, radius * 1.8)
	])
	draw_colored_polygon(shoulders, _portrait_color)


func _polygon_bounds(points: PackedVector2Array) -> Rect2:
	if points.is_empty():
		return Rect2()
	var minimum: Vector2 = points[0]
	var maximum: Vector2 = points[0]
	for point: Vector2 in points:
		minimum.x = minf(minimum.x, point.x)
		minimum.y = minf(minimum.y, point.y)
		maximum.x = maxf(maximum.x, point.x)
		maximum.y = maxf(maximum.y, point.y)
	return Rect2(minimum, maximum - minimum)
