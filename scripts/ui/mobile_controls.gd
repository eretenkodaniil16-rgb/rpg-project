extends Control

const DEAD_ZONE: float = 0.18

@onready var move_pad: Control = $MovePad
@onready var up_button: Button = $MovePad/Up
@onready var down_button: Button = $MovePad/Down
@onready var left_button: Button = $MovePad/Left
@onready var right_button: Button = $MovePad/Right
@onready var interact_button: Button = $InteractButton
@onready var menu_button: Button = $MenuButton

var _player: CharacterBody2D = null
var _game_world: Node = null
var _active_touch_index: int = -1


func _ready() -> void:
	visible = _is_mobile_device()
	if not visible:
		return

	_player = get_tree().get_first_node_in_group("player") as CharacterBody2D
	_game_world = get_tree().get_first_node_in_group("game_world")
	_configure_visuals()

	up_button.button_down.connect(_on_direction_changed.bind(&"up", true))
	up_button.button_up.connect(_on_direction_changed.bind(&"up", false))
	down_button.button_down.connect(_on_direction_changed.bind(&"down", true))
	down_button.button_up.connect(_on_direction_changed.bind(&"down", false))
	left_button.button_down.connect(_on_direction_changed.bind(&"left", true))
	left_button.button_up.connect(_on_direction_changed.bind(&"left", false))
	right_button.button_down.connect(_on_direction_changed.bind(&"right", true))
	right_button.button_up.connect(_on_direction_changed.bind(&"right", false))
	interact_button.pressed.connect(_on_interact_pressed)
	menu_button.pressed.connect(_on_menu_pressed)


func _process(_delta: float) -> void:
	if not visible:
		return
	if not is_instance_valid(_player):
		_player = get_tree().get_first_node_in_group("player") as CharacterBody2D
	if not is_instance_valid(_game_world):
		_game_world = get_tree().get_first_node_in_group("game_world")


func _input(event: InputEvent) -> void:
	if not visible:
		return

	if event is InputEventScreenTouch:
		var touch: InputEventScreenTouch = event as InputEventScreenTouch
		if touch.pressed and _active_touch_index < 0 and move_pad.get_global_rect().has_point(touch.position):
			_active_touch_index = touch.index
			_update_touch_vector(touch.position)
			get_viewport().set_input_as_handled()
		elif not touch.pressed and touch.index == _active_touch_index:
			_active_touch_index = -1
			_set_player_vector(Vector2.ZERO)
			get_viewport().set_input_as_handled()
	elif event is InputEventScreenDrag:
		var drag: InputEventScreenDrag = event as InputEventScreenDrag
		if drag.index == _active_touch_index:
			_update_touch_vector(drag.position)
			get_viewport().set_input_as_handled()


func _exit_tree() -> void:
	_active_touch_index = -1
	if is_instance_valid(_player) and _player.has_method("clear_mobile_input"):
		_player.call("clear_mobile_input")


func _on_direction_changed(direction: StringName, is_pressed: bool) -> void:
	if is_instance_valid(_player) and _player.has_method("set_mobile_direction"):
		_player.call("set_mobile_direction", direction, is_pressed)


func _on_interact_pressed() -> void:
	if is_instance_valid(_player) and _player.has_method("request_interaction"):
		_player.call("request_interaction")


func _on_menu_pressed() -> void:
	if is_instance_valid(_game_world) and _game_world.has_method("return_to_menu"):
		_game_world.call("return_to_menu")


func _update_touch_vector(screen_position: Vector2) -> void:
	var pad_rect: Rect2 = move_pad.get_global_rect()
	var half_size: Vector2 = pad_rect.size * 0.5
	if half_size.x <= 0.0 or half_size.y <= 0.0:
		_set_player_vector(Vector2.ZERO)
		return

	var relative: Vector2 = screen_position - pad_rect.get_center()
	var direction: Vector2 = Vector2(relative.x / half_size.x, relative.y / half_size.y)
	if direction.length() < DEAD_ZONE:
		direction = Vector2.ZERO
	else:
		direction = direction.limit_length(1.0)
	_set_player_vector(direction)


func _set_player_vector(direction: Vector2) -> void:
	if is_instance_valid(_player) and _player.has_method("set_mobile_vector"):
		_player.call("set_mobile_vector", direction)


func _configure_visuals() -> void:
	move_pad.mouse_filter = Control.MOUSE_FILTER_PASS
	var buttons: Array[Button] = [up_button, down_button, left_button, right_button]
	for button: Button in buttons:
		button.modulate = Color(1.0, 1.0, 1.0, 0.92)
		button.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	interact_button.modulate = Color(1.0, 1.0, 1.0, 0.94)
	menu_button.modulate = Color(1.0, 1.0, 1.0, 0.94)


func _is_mobile_device() -> bool:
	var platform_name: String = OS.get_name()
	return platform_name == "Android" or platform_name == "iOS" or OS.has_feature("mobile") or DisplayServer.is_touchscreen_available()
