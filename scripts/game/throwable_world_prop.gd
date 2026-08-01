class_name ThrowableWorldProp
extends Node2D

var prop_id: String = ""
var prop_type_id: String = ""
var definition: Dictionary = {}
var available: bool = true

var _body: Polygon2D
var _label: Label


func configure(new_prop_id: String, new_prop_type_id: String, new_definition: Dictionary) -> void:
	prop_id = new_prop_id
	prop_type_id = new_prop_type_id
	definition = new_definition.duplicate(true)
	if is_inside_tree():
		_rebuild_visuals()


func _ready() -> void:
	add_to_group("throwable_world_props")
	_rebuild_visuals()


func set_available(value: bool) -> void:
	available = value
	visible = value
	process_mode = Node.PROCESS_MODE_INHERIT if value else Node.PROCESS_MODE_DISABLED


func is_available_for_pickup() -> bool:
	return available and visible


func get_prop_id() -> String:
	return prop_id


func get_prop_type_id() -> String:
	return prop_type_id


func get_prop_label() -> String:
	return str(definition.get("label", prop_type_id))


func get_definition() -> Dictionary:
	return definition.duplicate(true)


func play_throw(from_position: Vector2, landing_position: Vector2, duration: float = 0.28) -> void:
	set_available(true)
	global_position = from_position
	var tween: Tween = create_tween()
	tween.set_trans(Tween.TRANS_QUAD)
	tween.set_ease(Tween.EASE_OUT)
	tween.tween_property(self, "global_position", landing_position, maxf(duration, 0.05))
	await tween.finished


func mark_broken() -> void:
	available = false
	visible = false
	queue_free()


func _rebuild_visuals() -> void:
	if _body != null:
		_body.queue_free()
	if _label != null:
		_label.queue_free()
	var size_value: Variant = definition.get("visual_size", [24.0, 20.0])
	var visual_size := Vector2(24.0, 20.0)
	if size_value is Array and (size_value as Array).size() >= 2:
		visual_size = Vector2(float((size_value as Array)[0]), float((size_value as Array)[1]))
	var color_value: Variant = definition.get("visual_color", [0.7, 0.7, 0.7, 1.0])
	var visual_color := Color(0.7, 0.7, 0.7, 1.0)
	if color_value is Array and (color_value as Array).size() >= 4:
		visual_color = Color(
			float((color_value as Array)[0]),
			float((color_value as Array)[1]),
			float((color_value as Array)[2]),
			float((color_value as Array)[3])
		)
	_body = Polygon2D.new()
	_body.name = "Body"
	_body.polygon = PackedVector2Array([
		Vector2(-visual_size.x * 0.5, -visual_size.y * 0.5),
		Vector2(visual_size.x * 0.5, -visual_size.y * 0.5),
		Vector2(visual_size.x * 0.5, visual_size.y * 0.5),
		Vector2(-visual_size.x * 0.5, visual_size.y * 0.5)
	])
	_body.color = visual_color
	_body.z_index = 4
	add_child(_body)
	_label = Label.new()
	_label.name = "NameLabel"
	_label.position = Vector2(-70.0, -44.0)
	_label.size = Vector2(140.0, 24.0)
	_label.text = get_prop_label().capitalize()
	_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_label.add_theme_font_size_override("font_size", 12)
	_label.add_theme_color_override("font_color", Color(0.88, 0.82, 0.66, 0.92))
	_label.z_index = 5
	add_child(_label)
