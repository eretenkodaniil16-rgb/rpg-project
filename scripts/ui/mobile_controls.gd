extends Control

const DEAD_ZONE: float = 0.16
const JOYSTICK_CONTAINER_SIZE: float = 260.0
const JOYSTICK_BASE_SIZE: float = 220.0
const JOYSTICK_KNOB_SIZE: float = 86.0

@onready var move_pad: Control = $MovePad
@onready var interact_button: Button = $InteractButton
@onready var menu_button: Button = $MenuButton

var _player: CharacterBody2D = null
var _game_world: Node = null
var _joystick_base: Panel = null
var _joystick_knob: Panel = null
var _active_touch_index: int = -1
var _initialized: bool = false


func _ready() -> void:
	visible = _is_mobile_device()
	if not visible:
		return
	_initialize_mobile_controls()


func _process(_delta: float) -> void:
	if not visible:
		return
	if not is_instance_valid(_player):
		_player = get_tree().get_first_node_in_group("player") as CharacterBody2D
	if not is_instance_valid(_game_world):
		_game_world = get_tree().get_first_node_in_group("game_world")


func _input(event: InputEvent) -> void:
	if not visible or not _initialized:
		return

	if event is InputEventScreenTouch:
		var touch: InputEventScreenTouch = event as InputEventScreenTouch
		if touch.pressed and _active_touch_index < 0 and move_pad.get_global_rect().has_point(touch.position):
			_active_touch_index = touch.index
			_update_joystick(touch.position)
			get_viewport().set_input_as_handled()
		elif not touch.pressed and touch.index == _active_touch_index:
			_active_touch_index = -1
			_reset_joystick()
			get_viewport().set_input_as_handled()
	elif event is InputEventScreenDrag:
		var drag: InputEventScreenDrag = event as InputEventScreenDrag
		if drag.index == _active_touch_index:
			_update_joystick(drag.position)
			get_viewport().set_input_as_handled()
	elif event is InputEventMouseButton:
		var mouse_button: InputEventMouseButton = event as InputEventMouseButton
		if mouse_button.button_index == MOUSE_BUTTON_LEFT:
			if mouse_button.pressed and move_pad.get_global_rect().has_point(mouse_button.position):
				_active_touch_index = -2
				_update_joystick(mouse_button.position)
			elif not mouse_button.pressed and _active_touch_index == -2:
				_active_touch_index = -1
				_reset_joystick()
	elif event is InputEventMouseMotion and _active_touch_index == -2:
		var mouse_motion: InputEventMouseMotion = event as InputEventMouseMotion
		_update_joystick(mouse_motion.position)


func _exit_tree() -> void:
	_active_touch_index = -1
	_reset_player_input()


func enable_for_testing() -> void:
	visible = true
	_initialize_mobile_controls()


func get_joystick_output_for_testing() -> Vector2:
	if not is_instance_valid(_player) or not _player.has_method("get_mobile_direction"):
		return Vector2.ZERO
	return _player.call("get_mobile_direction") as Vector2


func move_joystick_for_testing(normalized_direction: Vector2) -> void:
	if not _initialized:
		_initialize_mobile_controls()
	var center: Vector2 = move_pad.get_global_rect().get_center()
	var travel_radius: float = _travel_radius()
	_update_joystick(center + normalized_direction.limit_length(1.0) * travel_radius)


func release_joystick_for_testing() -> void:
	_reset_joystick()


func _initialize_mobile_controls() -> void:
	if _initialized:
		return
	_initialized = true
	_player = get_tree().get_first_node_in_group("player") as CharacterBody2D
	_game_world = get_tree().get_first_node_in_group("game_world")
	_configure_layout()
	_build_joystick_visuals()
	interact_button.pressed.connect(_on_interact_pressed)
	menu_button.pressed.connect(_on_menu_pressed)


func _configure_layout() -> void:
	move_pad.anchor_left = 0.0
	move_pad.anchor_top = 1.0
	move_pad.anchor_right = 0.0
	move_pad.anchor_bottom = 1.0
	move_pad.offset_left = 30.0
	move_pad.offset_top = -290.0
	move_pad.offset_right = 30.0 + JOYSTICK_CONTAINER_SIZE
	move_pad.offset_bottom = -30.0
	move_pad.mouse_filter = Control.MOUSE_FILTER_IGNORE

	interact_button.modulate = Color(1.0, 1.0, 1.0, 0.88)
	menu_button.modulate = Color(1.0, 1.0, 1.0, 0.88)
	interact_button.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	menu_button.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND

	# Legacy directional buttons remain in the scene for compatibility but are hidden.
	for child: Node in move_pad.get_children():
		if child is CanvasItem:
			(child as CanvasItem).visible = false


func _build_joystick_visuals() -> void:
	# Use real Panel nodes instead of custom _draw(), so Android always renders them.
	_joystick_base = Panel.new()
	_joystick_base.name = "JoystickBase"
	_joystick_base.position = Vector2(
		(JOYSTICK_CONTAINER_SIZE - JOYSTICK_BASE_SIZE) * 0.5,
		(JOYSTICK_CONTAINER_SIZE - JOYSTICK_BASE_SIZE) * 0.5
	)
	_joystick_base.size = Vector2(JOYSTICK_BASE_SIZE, JOYSTICK_BASE_SIZE)
	_joystick_base.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_joystick_base.add_theme_stylebox_override("panel", _create_circle_style(
		Color(0.08, 0.12, 0.18, 0.52),
		Color(0.72, 0.84, 1.0, 0.78),
		3
	))
	move_pad.add_child(_joystick_base)

	var center_guide: Panel = Panel.new()
	center_guide.name = "CenterGuide"
	center_guide.size = Vector2(54.0, 54.0)
	center_guide.position = (Vector2(JOYSTICK_BASE_SIZE, JOYSTICK_BASE_SIZE) - center_guide.size) * 0.5
	center_guide.mouse_filter = Control.MOUSE_FILTER_IGNORE
	center_guide.add_theme_stylebox_override("panel", _create_circle_style(
		Color(0.72, 0.84, 1.0, 0.08),
		Color(0.72, 0.84, 1.0, 0.22),
		2
	))
	_joystick_base.add_child(center_guide)

	_joystick_knob = Panel.new()
	_joystick_knob.name = "JoystickKnob"
	_joystick_knob.size = Vector2(JOYSTICK_KNOB_SIZE, JOYSTICK_KNOB_SIZE)
	_joystick_knob.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_joystick_knob.add_theme_stylebox_override("panel", _create_circle_style(
		Color(0.65, 0.80, 1.0, 0.78),
		Color(0.94, 0.97, 1.0, 0.96),
		3
	))
	move_pad.add_child(_joystick_knob)
	_set_knob_vector(Vector2.ZERO)


func _create_circle_style(fill_color: Color, border_color: Color, border_width: int) -> StyleBoxFlat:
	var style: StyleBoxFlat = StyleBoxFlat.new()
	style.bg_color = fill_color
	style.border_color = border_color
	style.set_border_width_all(border_width)
	style.corner_radius_top_left = 999
	style.corner_radius_top_right = 999
	style.corner_radius_bottom_left = 999
	style.corner_radius_bottom_right = 999
	style.shadow_color = Color(0.12, 0.28, 0.55, 0.22)
	style.shadow_size = 8
	return style


func _update_joystick(screen_position: Vector2) -> void:
	var center: Vector2 = move_pad.get_global_rect().get_center()
	var travel_radius: float = _travel_radius()
	if travel_radius <= 0.0:
		_reset_joystick()
		return

	var raw_vector: Vector2 = (screen_position - center) / travel_radius
	var visual_vector: Vector2 = raw_vector.limit_length(1.0)
	var output_vector: Vector2 = _apply_dead_zone(visual_vector)
	_set_knob_vector(visual_vector)
	_set_player_vector(output_vector)


func _apply_dead_zone(direction: Vector2) -> Vector2:
	var strength: float = direction.length()
	if strength <= DEAD_ZONE:
		return Vector2.ZERO
	var adjusted_strength: float = (strength - DEAD_ZONE) / (1.0 - DEAD_ZONE)
	return direction.normalized() * clampf(adjusted_strength, 0.0, 1.0)


func _set_knob_vector(direction: Vector2) -> void:
	if not is_instance_valid(_joystick_knob):
		return
	var center: Vector2 = Vector2(JOYSTICK_CONTAINER_SIZE, JOYSTICK_CONTAINER_SIZE) * 0.5
	_joystick_knob.position = center - _joystick_knob.size * 0.5 + direction.limit_length(1.0) * _travel_radius()


func _travel_radius() -> float:
	return (JOYSTICK_BASE_SIZE - JOYSTICK_KNOB_SIZE) * 0.5


func _reset_joystick() -> void:
	_set_knob_vector(Vector2.ZERO)
	_set_player_vector(Vector2.ZERO)


func _reset_player_input() -> void:
	if is_instance_valid(_player) and _player.has_method("clear_mobile_input"):
		_player.call("clear_mobile_input")


func _set_player_vector(direction: Vector2) -> void:
	if is_instance_valid(_player) and _player.has_method("set_mobile_vector"):
		_player.call("set_mobile_vector", direction)


func _on_interact_pressed() -> void:
	if is_instance_valid(_player) and _player.has_method("request_interaction"):
		_player.call("request_interaction")


func _on_menu_pressed() -> void:
	if is_instance_valid(_game_world) and _game_world.has_method("return_to_menu"):
		_game_world.call("return_to_menu")


func _is_mobile_device() -> bool:
	var platform_name: String = OS.get_name()
	return platform_name == "Android" or platform_name == "iOS" or OS.has_feature("mobile") or DisplayServer.is_touchscreen_available()
