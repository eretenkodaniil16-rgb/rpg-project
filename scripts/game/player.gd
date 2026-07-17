extends CharacterBody2D

@export var movement_speed: float = 220.0
@export var movement_bounds: Rect2 = Rect2(28.0, 28.0, 1224.0, 664.0)

@onready var body_visual: Polygon2D = $Body
@onready var name_label: Label = $NameLabel

var interactable: Node = null
var _mobile_up: bool = false
var _mobile_down: bool = false
var _mobile_left: bool = false
var _mobile_right: bool = false
var _mobile_vector: Vector2 = Vector2.ZERO


func _ready() -> void:
	apply_character_appearance()


func _physics_process(_delta: float) -> void:
	if GameState.input_locked:
		velocity = Vector2.ZERO
		return

	var keyboard_direction: Vector2 = Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	var direction: Vector2 = keyboard_direction + _get_mobile_direction()
	if direction.length_squared() > 1.0:
		direction = direction.normalized()

	velocity = direction * movement_speed
	move_and_slide()

	global_position.x = clampf(global_position.x, movement_bounds.position.x, movement_bounds.end.x)
	global_position.y = clampf(global_position.y, movement_bounds.position.y, movement_bounds.end.y)
	GameState.player_position = global_position


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_accept"):
		request_interaction()
		if is_instance_valid(interactable):
			get_viewport().set_input_as_handled()


func request_interaction() -> void:
	if GameState.input_locked:
		return
	if is_instance_valid(interactable) and interactable.has_method("interact"):
		interactable.call("interact")


func set_mobile_direction(direction: StringName, is_pressed: bool) -> void:
	match direction:
		&"up":
			_mobile_up = is_pressed
		&"down":
			_mobile_down = is_pressed
		&"left":
			_mobile_left = is_pressed
		&"right":
			_mobile_right = is_pressed


func set_mobile_vector(direction: Vector2) -> void:
	_mobile_vector = direction.limit_length(1.0)


func get_mobile_direction() -> Vector2:
	return _get_mobile_direction()


func clear_mobile_input() -> void:
	_mobile_up = false
	_mobile_down = false
	_mobile_left = false
	_mobile_right = false
	_mobile_vector = Vector2.ZERO


func set_interactable(target: Node) -> void:
	interactable = target


func clear_interactable(target: Node) -> void:
	if interactable == target:
		interactable = null


func apply_character_appearance() -> void:
	var character: PlayerCharacter = GameState.player_character
	var display_name: String = character.character_name.strip_edges()
	name_label.text = display_name if not display_name.is_empty() else "Герой"
	name_label.offset_left = -120.0
	name_label.offset_right = 120.0
	name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	body_visual.color = Color.from_string(
		character.appearance_color_hex,
		Color(0.3, 0.64, 0.91, 1.0)
	)


func _get_mobile_direction() -> Vector2:
	var button_direction: Vector2 = Vector2(
		float(_mobile_right) - float(_mobile_left),
		float(_mobile_down) - float(_mobile_up)
	)
	var combined: Vector2 = button_direction + _mobile_vector
	return combined.limit_length(1.0)
