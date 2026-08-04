extends CharacterBody2D

@export var movement_speed: float = 220.0
@export var movement_bounds: Rect2 = Rect2(28.0, 28.0, 1224.0, 664.0)

@onready var body_visual: Polygon2D = $Body
@onready var name_label: Label = $NameLabel

# Compatibility pointer for older systems. It always references the nearest
# registered interaction target, while _interactables stores every active zone.
var interactable: Node = null
var _interactables: Dictionary = {}
var _mobile_up: bool = false
var _mobile_down: bool = false
var _mobile_left: bool = false
var _mobile_right: bool = false
var _mobile_vector: Vector2 = Vector2.ZERO
var _attack_tween: Tween = null


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
	_refresh_primary_interactable()
	_interact_with_target(interactable)


func request_interaction_with_instance(instance_id: int) -> void:
	if GameState.input_locked:
		return
	_prune_interactables()
	var target_value: Variant = _interactables.get(instance_id, null)
	var target: Node = null
	# Freed Objects must be rejected before any `is Node` type test. Godot raises
	# an error when `is` is evaluated against a previously freed instance.
	if is_instance_valid(target_value) and target_value is Node:
		target = target_value as Node
	_interact_with_target(target)


func register_interactable(target: Node) -> void:
	if target == null or not is_instance_valid(target):
		return
	_interactables[target.get_instance_id()] = target
	_refresh_primary_interactable()


func unregister_interactable(target: Node) -> void:
	if target == null or not is_instance_valid(target):
		return
	_interactables.erase(target.get_instance_id())
	_refresh_primary_interactable()


func get_nearby_interactables() -> Array[Node]:
	_prune_interactables()
	var result: Array[Node] = []
	for value: Variant in _interactables.values():
		if not is_instance_valid(value):
			continue
		if value is Node:
			result.append(value as Node)
	result.sort_custom(_interaction_target_before)
	return result


func has_registered_interactable(target: Node) -> bool:
	return target != null and is_instance_valid(target) and _interactables.has(target.get_instance_id())


func set_mobile_direction(direction: StringName, is_pressed: bool) -> void:
	match direction:
		&"up": _mobile_up = is_pressed
		&"down": _mobile_down = is_pressed
		&"left": _mobile_left = is_pressed
		&"right": _mobile_right = is_pressed


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
	register_interactable(target)


func clear_interactable(target: Node) -> void:
	unregister_interactable(target)


func play_attack_animation(target_global_position: Vector2) -> void:
	var direction: Vector2 = (target_global_position - global_position).normalized()
	if direction == Vector2.ZERO:
		direction = Vector2.RIGHT
	if _attack_tween != null:
		_attack_tween.kill()
	body_visual.position = Vector2.ZERO
	_attack_tween = create_tween()
	_attack_tween.tween_property(body_visual, "position", direction * 15.0, 0.07)
	_attack_tween.tween_property(body_visual, "position", Vector2.ZERO, 0.11)


func apply_character_appearance() -> void:
	var character: PlayerCharacter = GameState.player_character
	var display_name: String = character.character_name.strip_edges()
	name_label.text = display_name if not display_name.is_empty() else "Герой"
	name_label.offset_left = -120.0
	name_label.offset_right = 120.0
	name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	body_visual.color = Color.from_string(character.appearance_color_hex, Color(0.3, 0.64, 0.91, 1.0))
	var visual_scale: float = 0.78 if character.size_category == "small" else 1.0
	body_visual.scale = Vector2.ONE * visual_scale
	var collision: CollisionShape2D = get_node_or_null("CollisionShape2D") as CollisionShape2D
	if collision != null and collision.shape is RectangleShape2D:
		var shape: RectangleShape2D = (collision.shape as RectangleShape2D).duplicate() as RectangleShape2D
		shape.size = Vector2(30.0, 30.0) if character.size_category == "small" else Vector2(38.0, 38.0)
		collision.shape = shape


func _interact_with_target(target: Node) -> void:
	if not is_instance_valid(target):
		return
	if target.has_method("interact"):
		target.call("interact")
		return
	if target.has_method("perform_world_interaction"):
		target.call("perform_world_interaction")


func _refresh_primary_interactable() -> void:
	var nearby: Array[Node] = get_nearby_interactables()
	interactable = nearby[0] if not nearby.is_empty() else null


func _prune_interactables() -> void:
	var stale_ids: Array[int] = []
	for key: Variant in _interactables.keys():
		var value: Variant = _interactables.get(key, null)
		if not is_instance_valid(value):
			stale_ids.append(int(key))
			continue
		if not value is Node:
			stale_ids.append(int(key))
	for instance_id: int in stale_ids:
		_interactables.erase(instance_id)


func _interaction_target_before(first: Node, second: Node) -> bool:
	var first_distance: float = _interaction_distance_squared(first)
	var second_distance: float = _interaction_distance_squared(second)
	if not is_equal_approx(first_distance, second_distance):
		return first_distance < second_distance
	return first.get_instance_id() < second.get_instance_id()


func _interaction_distance_squared(target: Node) -> float:
	if target is Node2D:
		return global_position.distance_squared_to((target as Node2D).global_position)
	return INF


func _get_mobile_direction() -> Vector2:
	var button_direction: Vector2 = Vector2(
		float(_mobile_right) - float(_mobile_left),
		float(_mobile_down) - float(_mobile_up)
	)
	var combined: Vector2 = button_direction + _mobile_vector
	return combined.limit_length(1.0)
