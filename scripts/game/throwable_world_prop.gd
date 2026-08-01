class_name ThrowableWorldProp
extends Node2D

const INTERACTION_ZONE_SIZE: Vector2 = Vector2(90.0, 90.0)

var prop_id: String = ""
var prop_type_id: String = ""
var definition: Dictionary = {}
var available: bool = true

var _body: Polygon2D
var _label: Label
var _interaction_area: Area2D
var _registered_players: Dictionary = {}


func configure(new_prop_id: String, new_prop_type_id: String, new_definition: Dictionary) -> void:
	prop_id = new_prop_id
	prop_type_id = new_prop_type_id
	definition = new_definition.duplicate(true)
	if is_inside_tree():
		_rebuild_visuals()


func _ready() -> void:
	add_to_group("throwable_world_props")
	_rebuild_visuals()
	_build_interaction_area()
	call_deferred("_refresh_overlapping_players")


func _process(_delta: float) -> void:
	if available:
		_refresh_overlapping_players()


func set_available(value: bool) -> void:
	if not value:
		_unregister_all_players()
	available = value
	visible = value
	process_mode = Node.PROCESS_MODE_INHERIT if value else Node.PROCESS_MODE_DISABLED
	if _interaction_area != null:
		_interaction_area.set_deferred("monitoring", value)
	if value and is_inside_tree():
		call_deferred("_refresh_overlapping_players")


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


func get_interaction_zone_size_for_testing() -> Vector2:
	return INTERACTION_ZONE_SIZE


func play_throw(from_position: Vector2, landing_position: Vector2, duration: float = 0.28) -> void:
	set_available(true)
	global_position = from_position
	var tween: Tween = create_tween()
	tween.set_trans(Tween.TRANS_QUAD)
	tween.set_ease(Tween.EASE_OUT)
	tween.tween_property(self, "global_position", landing_position, maxf(duration, 0.05))
	await tween.finished
	_refresh_overlapping_players()


func mark_broken() -> void:
	_unregister_all_players()
	available = false
	visible = false
	queue_free()


func _build_interaction_area() -> void:
	if _interaction_area != null:
		return
	_interaction_area = Area2D.new()
	_interaction_area.name = "InteractionArea"
	_interaction_area.collision_layer = 0
	_interaction_area.collision_mask = 1
	_interaction_area.monitorable = false
	_interaction_area.monitoring = available
	var shape := RectangleShape2D.new()
	shape.size = INTERACTION_ZONE_SIZE
	var collision := CollisionShape2D.new()
	collision.name = "CollisionShape2D"
	collision.shape = shape
	_interaction_area.add_child(collision)
	_interaction_area.body_entered.connect(_on_body_entered)
	_interaction_area.body_exited.connect(_on_body_exited)
	add_child(_interaction_area)


func _on_body_entered(body: Node2D) -> void:
	_register_player(body)


func _on_body_exited(body: Node2D) -> void:
	_unregister_player(body)


func _register_player(body: Node) -> void:
	if not available or body == null or not body.is_in_group("player"):
		return
	_registered_players[body.get_instance_id()] = body
	if body.has_method("register_interactable"):
		body.call("register_interactable", self)
	elif body.has_method("set_interactable"):
		body.call("set_interactable", self)


func _unregister_player(body: Node) -> void:
	if body == null:
		return
	_registered_players.erase(body.get_instance_id())
	if body.has_method("unregister_interactable"):
		body.call("unregister_interactable", self)
	elif body.has_method("clear_interactable"):
		body.call("clear_interactable", self)


func _unregister_all_players() -> void:
	var players: Array[Node] = []
	for value: Variant in _registered_players.values():
		if value is Node and is_instance_valid(value as Node):
			players.append(value as Node)
	for body: Node in players:
		_unregister_player(body)
	_registered_players.clear()


func _refresh_overlapping_players() -> void:
	if not available or _interaction_area == null or not _interaction_area.monitoring:
		return
	var overlapping_ids: Dictionary = {}
	for body: Node2D in _interaction_area.get_overlapping_bodies():
		if not body.is_in_group("player"):
			continue
		overlapping_ids[body.get_instance_id()] = true
		_register_player(body)
	var stale_players: Array[Node] = []
	for key: Variant in _registered_players.keys():
		if overlapping_ids.has(key):
			continue
		var value: Variant = _registered_players.get(key, null)
		if value is Node and is_instance_valid(value as Node):
			stale_players.append(value as Node)
	for body: Node in stale_players:
		_unregister_player(body)


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