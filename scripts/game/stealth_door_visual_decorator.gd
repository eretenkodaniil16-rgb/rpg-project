class_name StealthDoorVisualDecorator
extends Node2D

const CLOSED_LEAF_WIDTH: float = 20.0
const FRAME_WIDTH: float = 7.0
const FRAME_OFFSET_X: float = 14.0
const OPEN_ROTATION_DEGREES: float = 82.0

var _door: StealthDoor
var _leaf_pivot: Node2D
var _leaf_body: Polygon2D
var _handle: Polygon2D
var _last_state: String = ""


func configure(door: StealthDoor) -> void:
	_door = door
	if is_inside_tree():
		_install_visuals()


func _ready() -> void:
	z_index = 7
	_install_visuals()


func _process(_delta: float) -> void:
	_sync_state()


func get_visual_width_for_testing() -> float:
	return FRAME_OFFSET_X * 2.0 + FRAME_WIDTH


func get_leaf_rotation_degrees_for_testing() -> float:
	return rad_to_deg(_leaf_pivot.rotation) if is_instance_valid(_leaf_pivot) else 0.0


func has_handle_for_testing() -> bool:
	return is_instance_valid(_handle) and _handle.visible


func _install_visuals() -> void:
	if not is_instance_valid(_door) or is_instance_valid(_leaf_pivot):
		return
	var legacy_visual: CanvasItem = _door.get_node_or_null("Visual") as CanvasItem
	if legacy_visual != null:
		legacy_visual.hide()
	_build_recess()
	_build_frame()
	_build_leaf()
	_sync_state(true)


func _build_recess() -> void:
	var height: float = maxf(_door.door_size.y, 48.0)
	var recess := Polygon2D.new()
	recess.name = "DoorRecess"
	recess.polygon = _rect_polygon(Vector2(32.0, height + 10.0))
	recess.color = Color(0.025, 0.032, 0.038, 1.0)
	recess.z_index = 0
	add_child(recess)


func _build_frame() -> void:
	var height: float = maxf(_door.door_size.y, 48.0)
	for side: int in [-1, 1]:
		var frame := Polygon2D.new()
		frame.name = "DoorFrameLeft" if side < 0 else "DoorFrameRight"
		frame.position = Vector2(float(side) * FRAME_OFFSET_X, 0.0)
		frame.polygon = _rect_polygon(Vector2(FRAME_WIDTH, height + 16.0))
		frame.color = Color(0.32, 0.24, 0.17, 1.0)
		frame.z_index = 1
		add_child(frame)
	var cap_size := Vector2(FRAME_OFFSET_X * 2.0 + FRAME_WIDTH, FRAME_WIDTH)
	for side: int in [-1, 1]:
		var cap := Polygon2D.new()
		cap.name = "DoorFrameTop" if side < 0 else "DoorFrameBottom"
		cap.position = Vector2(0.0, float(side) * (height * 0.5 + 5.0))
		cap.polygon = _rect_polygon(cap_size)
		cap.color = Color(0.40, 0.29, 0.19, 1.0)
		cap.z_index = 2
		add_child(cap)


func _build_leaf() -> void:
	var height: float = maxf(_door.door_size.y - 10.0, 42.0)
	_leaf_pivot = Node2D.new()
	_leaf_pivot.name = "DoorLeafPivot"
	_leaf_pivot.position = Vector2(0.0, -height * 0.5)
	_leaf_pivot.z_index = 3
	add_child(_leaf_pivot)

	_leaf_body = Polygon2D.new()
	_leaf_body.name = "DoorLeaf"
	_leaf_body.position = Vector2(0.0, height * 0.5)
	_leaf_body.polygon = _rect_polygon(Vector2(CLOSED_LEAF_WIDTH, height))
	_leaf_body.color = Color(0.44, 0.25, 0.12, 1.0)
	_leaf_body.z_index = 0
	_leaf_pivot.add_child(_leaf_body)

	for ratio: float in [0.23, 0.5, 0.77]:
		var band := Polygon2D.new()
		band.name = "MetalBand%d" % roundi(ratio * 100.0)
		band.position = Vector2(0.0, height * ratio)
		band.polygon = _rect_polygon(Vector2(CLOSED_LEAF_WIDTH + 4.0, 5.0))
		band.color = Color(0.39, 0.43, 0.46, 1.0)
		band.z_index = 1
		_leaf_pivot.add_child(band)

	_handle = Polygon2D.new()
	_handle.name = "DoorHandle"
	_handle.position = Vector2(5.5, height * 0.58)
	_handle.polygon = _circle_polygon(4.0, 10)
	_handle.color = Color(0.86, 0.68, 0.26, 1.0)
	_handle.z_index = 2
	_leaf_pivot.add_child(_handle)


func _sync_state(force: bool = false) -> void:
	if not is_instance_valid(_door) or not is_instance_valid(_leaf_pivot):
		return
	var state: String = _door.get_door_state()
	if not force and state == _last_state:
		return
	_last_state = state
	var opened: bool = state in ["open", "broken"]
	_leaf_pivot.rotation = deg_to_rad(OPEN_ROTATION_DEGREES) if opened else 0.0
	_leaf_body.color = _leaf_color(state)
	_handle.visible = state != "broken"
	visible = true


func _leaf_color(state: String) -> Color:
	match state:
		"locked": return Color(0.34, 0.16, 0.08, 1.0)
		"blocked": return Color(0.25, 0.19, 0.15, 1.0)
		"broken": return Color(0.27, 0.16, 0.10, 0.78)
		"open": return Color(0.50, 0.29, 0.14, 0.94)
		_: return Color(0.44, 0.25, 0.12, 1.0)


func _rect_polygon(size: Vector2) -> PackedVector2Array:
	var half: Vector2 = size * 0.5
	return PackedVector2Array([
		Vector2(-half.x, -half.y),
		Vector2(half.x, -half.y),
		Vector2(half.x, half.y),
		Vector2(-half.x, half.y)
	])


func _circle_polygon(radius: float, point_count: int) -> PackedVector2Array:
	var result := PackedVector2Array()
	for index: int in range(maxi(point_count, 3)):
		var angle: float = TAU * float(index) / float(maxi(point_count, 3))
		result.append(Vector2(cos(angle), sin(angle)) * radius)
	return result
