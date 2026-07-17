extends Control

@onready var virtual_joystick: VirtualJoystick = $VirtualJoystick
@onready var interact_button: Button = $InteractButton
@onready var menu_button: Button = $MenuButton

var _player: CharacterBody2D = null
var _game_world: Node = null


func _ready() -> void:
	visible = _is_mobile_device()
	if not visible:
		return

	_player = get_tree().get_first_node_in_group("player") as CharacterBody2D
	_game_world = get_tree().get_first_node_in_group("game_world")
	_configure_visuals()

	virtual_joystick.vector_changed.connect(_on_joystick_vector_changed)
	interact_button.pressed.connect(_on_interact_pressed)
	menu_button.pressed.connect(_on_menu_pressed)


func _process(_delta: float) -> void:
	if not visible:
		return
	if not is_instance_valid(_player):
		_player = get_tree().get_first_node_in_group("player") as CharacterBody2D
	if not is_instance_valid(_game_world):
		_game_world = get_tree().get_first_node_in_group("game_world")


func _exit_tree() -> void:
	if is_instance_valid(_player) and _player.has_method("clear_mobile_input"):
		_player.call("clear_mobile_input")


func _on_joystick_vector_changed(direction: Vector2) -> void:
	if is_instance_valid(_player) and _player.has_method("set_mobile_vector"):
		_player.call("set_mobile_vector", direction)


func _on_interact_pressed() -> void:
	if is_instance_valid(_player) and _player.has_method("request_interaction"):
		_player.call("request_interaction")


func _on_menu_pressed() -> void:
	if is_instance_valid(_game_world) and _game_world.has_method("return_to_menu"):
		_game_world.call("return_to_menu")


func _configure_visuals() -> void:
	virtual_joystick.modulate = Color(1.0, 1.0, 1.0, 1.0)
	interact_button.modulate = Color(1.0, 1.0, 1.0, 0.88)
	menu_button.modulate = Color(1.0, 1.0, 1.0, 0.88)
	interact_button.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	menu_button.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND


func _is_mobile_device() -> bool:
	var platform_name: String = OS.get_name()
	return platform_name == "Android" or platform_name == "iOS" or OS.has_feature("mobile") or DisplayServer.is_touchscreen_available()
