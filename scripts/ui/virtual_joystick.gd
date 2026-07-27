extends Control

# Godot 4.7 provides a native VirtualJoystick class, so this project script
# intentionally avoids registering the same global class name.
signal vector_changed(direction: Vector2)

@export_range(0.0, 0.5, 0.01) var dead_zone: float = 0.16
@export var base_color: Color = Color(0.08, 0.11, 0.16, 0.42)
@export var base_outline_color: Color = Color(0.72, 0.82, 1.0, 0.72)
@export var guide_color: Color = Color(0.72, 0.82, 1.0, 0.22)
@export var knob_color: Color = Color(0.68, 0.82, 1.0, 0.72)
@export var knob_outline_color: Color = Color(0.92, 0.96, 1.0, 0.92)

var _active_touch_index: int = -1
var _mouse_active: bool = false
var _output_vector: Vector2 = Vector2.ZERO
var _visual_vector: Vector2 = Vector2.ZERO


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	focus_mode = Control.FOCUS_NONE
	resized.connect(queue_redraw)
	queue_redraw()


func _draw() -> void:
	var center: Vector2 = size * 0.5
	var base_radius: float = _base_radius()
	var knob_radius: float = base_radius * 0.36
	var travel_radius: float = maxf(base_radius - knob_radius * 0.72, 1.0)
	var knob_center: Vector2 = center + _visual_vector * travel_radius

	draw_circle(center, base_radius + 9.0, Color(0.25, 0.42, 0.72, 0.10))
	draw_circle(center, base_radius, base_color)
	draw_arc(center, base_radius, 0.0, TAU, 72, base_outline_color, 4.0, true)

	var dead_zone_radius: float = travel_radius * dead_zone
	draw_arc(center, dead_zone_radius, 0.0, TAU, 40, guide_color, 2.0, true)
	draw_line(center + Vector2(-base_radius * 0.68, 0.0), center + Vector2(base_radius * 0.68, 0.0), guide_color, 2.0, true)
	draw_line(center + Vector2(0.0, -base_radius * 0.68), center + Vector2(0.0, base_radius * 0.68), guide_color, 2.0, true)

	draw_circle(knob_center, knob_radius + 5.0, Color(0.25, 0.42, 0.72, 0.16))
	draw_circle(knob_center, knob_radius, knob_color)
	draw_arc(knob_center, knob_radius, 0.0, TAU, 48, knob_outline_color, 3.0, true)


func _gui_input(event: InputEvent) -> void:
	if event is InputEventScreenTouch:
		var touch: InputEventScreenTouch = event as InputEventScreenTouch
		if touch.pressed and _active_touch_index < 0:
			_active_touch_index = touch.index
			_update_from_local_position(touch.position)
			accept_event()
		elif not touch.pressed and touch.index == _active_touch_index:
			_active_touch_index = -1
			_reset_joystick()
			accept_event()
	elif event is InputEventScreenDrag:
		var drag: InputEventScreenDrag = event as InputEventScreenDrag
		if drag.index == _active_touch_index:
			_update_from_local_position(drag.position)
			accept_event()
	elif event is InputEventMouseButton:
		var mouse_button: InputEventMouseButton = event as InputEventMouseButton
		if mouse_button.button_index == MOUSE_BUTTON_LEFT and _active_touch_index < 0:
			_mouse_active = mouse_button.pressed
			if _mouse_active:
				_update_from_local_position(mouse_button.position)
			else:
				_reset_joystick()
			accept_event()
	elif event is InputEventMouseMotion and _mouse_active and _active_touch_index < 0:
		var mouse_motion: InputEventMouseMotion = event as InputEventMouseMotion
		_update_from_local_position(mouse_motion.position)
		accept_event()


func _exit_tree() -> void:
	_reset_joystick()


func get_output_vector() -> Vector2:
	return _output_vector


func _update_from_local_position(local_position: Vector2) -> void:
	var center: Vector2 = size * 0.5
	var base_radius: float = _base_radius()
	var knob_radius: float = base_radius * 0.36
	var travel_radius: float = maxf(base_radius - knob_radius * 0.72, 1.0)
	var raw_vector: Vector2 = (local_position - center) / travel_radius
	_visual_vector = raw_vector.limit_length(1.0)
	_output_vector = calculate_output_vector(_visual_vector, dead_zone)
	vector_changed.emit(_output_vector)
	queue_redraw()


func _reset_joystick() -> void:
	_mouse_active = false
	_visual_vector = Vector2.ZERO
	_output_vector = Vector2.ZERO
	vector_changed.emit(Vector2.ZERO)
	queue_redraw()


func _base_radius() -> float:
	return maxf(minf(size.x, size.y) * 0.45, 1.0)


static func calculate_output_vector(raw_vector: Vector2, dead_zone_value: float) -> Vector2:
	var limited_vector: Vector2 = raw_vector.limit_length(1.0)
	var strength: float = limited_vector.length()
	var safe_dead_zone: float = clampf(dead_zone_value, 0.0, 0.95)
	if strength <= safe_dead_zone or strength <= 0.0001:
		return Vector2.ZERO
	var adjusted_strength: float = (strength - safe_dead_zone) / (1.0 - safe_dead_zone)
	return limited_vector.normalized() * clampf(adjusted_strength, 0.0, 1.0)
