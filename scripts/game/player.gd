extends CharacterBody2D

@export var movement_speed: float = 220.0
@export var movement_bounds: Rect2 = Rect2(28.0, 28.0, 1224.0, 664.0)

var interactable: Node = null
var _mobile_up: bool = false
var _mobile_down: bool = false
var _mobile_left: bool = false
var _mobile_right: bool = false


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


func clear_mobile_input() -> void:
	_mobile_up = false
	_mobile_down = false
	_mobile_left = false
	_mobile_right = false


func set_interactable(target: Node) -> void:
	interactable = target


func clear_interactable(target: Node) -> void:
	if interactable == target:
		interactable = null


func _get_mobile_direction() -> Vector2:
	return Vector2(
		float(_mobile_right) - float(_mobile_left),
		float(_mobile_down) - float(_mobile_up)
	)
