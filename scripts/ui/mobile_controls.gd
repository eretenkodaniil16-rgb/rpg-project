extends Control

@onready var up_button: Button = $MovePad/Up
@onready var down_button: Button = $MovePad/Down
@onready var left_button: Button = $MovePad/Left
@onready var right_button: Button = $MovePad/Right
@onready var interact_button: Button = $InteractButton
@onready var menu_button: Button = $MenuButton

var _player: CharacterBody2D = null
var _game_world: Node = null


func _ready() -> void:
	visible = OS.has_feature("mobile") or DisplayServer.is_touchscreen_available()
	if not visible:
		return

	_player = get_tree().get_first_node_in_group("player") as CharacterBody2D
	_game_world = get_tree().get_first_node_in_group("game_world")

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


func _exit_tree() -> void:
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
