extends CharacterBody2D

const HUMAN_WARRIOR_LIBRARY_SCRIPT: Script = preload("res://scripts/game/human_warrior_animation_library.gd")
const HUMAN_WARRIOR_TEST_PANEL_SCRIPT: Script = preload("res://scripts/ui/human_warrior_animation_test_panel.gd")
const AUTHORED_SPRITE_OFFSET: Vector2 = Vector2(0.0, -43.0)
const VISUAL_MOVEMENT_EPSILON_SQUARED: float = 0.01
const VISUAL_STATE_IDLE: StringName = &"idle"
const VISUAL_STATE_WALK: StringName = &"walk"
const VISUAL_MODE_AUTO: StringName = &"auto"
const VISUAL_MODE_UNARMED: StringName = &"unarmed"
const VISUAL_MODE_ONEHAND: StringName = &"onehand"
const VISUAL_MODE_TWOHAND: StringName = &"twohand"

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
var _attack_tween: Tween = null
var _character_sprite: AnimatedSprite2D = null
var _active_visual: Node2D = null
var _active_visual_base_position: Vector2 = Vector2.ZERO
var _visual_facing_direction: Vector2 = Vector2.DOWN
var _visual_motion_state: StringName = VISUAL_STATE_IDLE
var _visual_combat_mode: bool = false
var _visual_preview_mode: StringName = VISUAL_MODE_AUTO
var _visual_combat_preview_enabled: bool = false
var _visual_combat_preview: bool = false
var _visual_sample_initialized: bool = false
var _last_visual_sample_position: Vector2 = Vector2.ZERO
var _animation_library_error: String = ""
var _visual_class_data: ClassDataSystem = ClassDataSystem.new()
var _last_visual_weapon_id: String = ""


func _ready() -> void:
	_install_character_sprite()
	apply_character_appearance()
	_install_animation_test_panel()


func _process(_delta: float) -> void:
	if not _visual_sample_initialized:
		_last_visual_sample_position = global_position
		_last_visual_weapon_id = GameState.player_character.equipped_weapon_id
		_visual_sample_initialized = true
		return
	var movement_delta: Vector2 = global_position - _last_visual_sample_position
	_last_visual_sample_position = global_position
	set_visual_motion(
		movement_delta.length_squared() > VISUAL_MOVEMENT_EPSILON_SQUARED,
		movement_delta
	)
	var equipped_weapon_id: String = GameState.player_character.equipped_weapon_id
	if equipped_weapon_id != _last_visual_weapon_id:
		_last_visual_weapon_id = equipped_weapon_id
		_refresh_visual_animation()


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
	interactable = target


func clear_interactable(target: Node) -> void:
	if interactable == target:
		interactable = null


func play_attack_animation(target_global_position: Vector2) -> void:
	var direction: Vector2 = (target_global_position - global_position).normalized()
	if direction == Vector2.ZERO:
		direction = Vector2.RIGHT
	if _attack_tween != null:
		_attack_tween.kill()
	var visual: Node2D = get_active_visual()
	visual.position = _active_visual_base_position
	_attack_tween = create_tween()
	_attack_tween.tween_property(
		visual,
		"position",
		_active_visual_base_position + direction * 15.0,
		0.07
	)
	_attack_tween.tween_property(visual, "position", _active_visual_base_position, 0.11)


func apply_character_appearance() -> void:
	var character: PlayerCharacter = GameState.player_character
	var display_name: String = character.character_name.strip_edges()
	name_label.text = display_name if not display_name.is_empty() else "Герой"
	name_label.offset_left = -120.0
	name_label.offset_right = 120.0
	name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var visual_scale: float = 0.78 if character.size_category == "small" else 1.0
	var use_authored_sprite: bool = _supports_authored_human_warrior(character)
	body_visual.show()
	body_visual.position = Vector2.ZERO
	body_visual.rotation = 0.0
	body_visual.scale = Vector2.ONE * visual_scale
	_active_visual = body_visual
	_active_visual_base_position = Vector2.ZERO
	if use_authored_sprite and is_instance_valid(_character_sprite):
		body_visual.color = Color(0.0, 0.0, 0.0, 0.0)
		_character_sprite.show()
		_character_sprite.position = AUTHORED_SPRITE_OFFSET
		name_label.offset_top = -112.0
		name_label.offset_bottom = -86.0
		_refresh_visual_animation()
	else:
		if is_instance_valid(_character_sprite):
			_character_sprite.hide()
		body_visual.color = Color.from_string(
			character.appearance_color_hex,
			Color(0.3, 0.64, 0.91, 1.0)
		)
		name_label.offset_top = -50.0
		name_label.offset_bottom = -25.0
	var collision: CollisionShape2D = get_node_or_null("CollisionShape2D") as CollisionShape2D
	if collision != null and collision.shape is RectangleShape2D:
		var shape: RectangleShape2D = (collision.shape as RectangleShape2D).duplicate() as RectangleShape2D
		shape.size = Vector2(30.0, 30.0) if character.size_category == "small" else Vector2(38.0, 38.0)
		collision.shape = shape


func get_active_visual() -> Node2D:
	return _active_visual if is_instance_valid(_active_visual) else body_visual


func get_active_visual_base_position() -> Vector2:
	return _active_visual_base_position


func set_visual_facing(direction: Vector2) -> void:
	if direction.length_squared() <= 0.0001:
		return
	_visual_facing_direction = direction.normalized()
	_refresh_visual_animation()


func set_visual_motion(is_moving: bool, direction: Vector2 = Vector2.ZERO) -> void:
	var facing_changed: bool = false
	if direction.length_squared() > 0.0001:
		var previous_direction_id: StringName = _direction_id(_visual_facing_direction)
		_visual_facing_direction = direction.normalized()
		facing_changed = previous_direction_id != _direction_id(_visual_facing_direction)
	var next_state: StringName = VISUAL_STATE_WALK if is_moving else VISUAL_STATE_IDLE
	var motion_changed: bool = next_state != _visual_motion_state
	if not facing_changed and not motion_changed:
		return
	_visual_motion_state = next_state
	_refresh_visual_animation()


func set_visual_combat_mode(value: bool) -> void:
	_visual_combat_mode = value
	_refresh_visual_animation()


func set_visual_preview_mode(mode: StringName) -> void:
	if mode not in [VISUAL_MODE_AUTO, VISUAL_MODE_UNARMED, VISUAL_MODE_ONEHAND, VISUAL_MODE_TWOHAND]:
		mode = VISUAL_MODE_AUTO
	_visual_preview_mode = mode
	_refresh_visual_animation()


func set_visual_combat_preview(value: bool) -> void:
	_visual_combat_preview_enabled = true
	_visual_combat_preview = value
	_refresh_visual_animation()


func clear_visual_combat_preview() -> void:
	_visual_combat_preview_enabled = false
	_refresh_visual_animation()


func get_visual_motion_state_for_testing() -> StringName:
	return _visual_motion_state


func get_visual_debug_state() -> Dictionary:
	return {
		"mode": str(_visual_preview_mode),
		"combat": _effective_combat_mode(),
		"grip": str(_effective_grip_mode()),
		"animation": str(_character_sprite.animation) if is_instance_valid(_character_sprite) else "fallback",
		"library_error": _animation_library_error
	}


func _refresh_visual_animation() -> void:
	if not is_instance_valid(_character_sprite) or not _character_sprite.visible:
		return
	var direction_id: StringName = _direction_id(_visual_facing_direction)
	var grip_mode: StringName = _effective_grip_mode()
	var desired_animation: StringName = _desired_animation_name(
		grip_mode,
		_visual_motion_state,
		direction_id
	)
	var fallback_animation := StringName(
		"%s_%s" % ["walk" if _visual_motion_state == VISUAL_STATE_WALK else "idle", direction_id]
	)
	if not _character_sprite.sprite_frames.has_animation(desired_animation):
		desired_animation = fallback_animation
	if not _character_sprite.sprite_frames.has_animation(desired_animation):
		desired_animation = &"idle_down"
	if _character_sprite.animation != desired_animation:
		_character_sprite.play(desired_animation)


func _desired_animation_name(
	grip_mode: StringName,
	motion_state: StringName,
	direction_id: StringName
) -> StringName:
	if grip_mode == VISUAL_MODE_ONEHAND:
		return StringName(
			"%s_%s" % [
				"walk_onehand" if motion_state == VISUAL_STATE_WALK else "combat_idle_onehand",
				direction_id
			]
		)
	if grip_mode == VISUAL_MODE_TWOHAND:
		return StringName(
			"%s_%s" % [
				"walk_twohand" if motion_state == VISUAL_STATE_WALK else "combat_idle_twohand",
				direction_id
			]
		)
	return StringName(
		"%s_%s" % ["walk" if motion_state == VISUAL_STATE_WALK else "idle", direction_id]
	)


func _effective_grip_mode() -> StringName:
	if _visual_preview_mode != VISUAL_MODE_AUTO:
		return _visual_preview_mode
	if not _effective_combat_mode():
		return VISUAL_MODE_UNARMED
	var weapon: Dictionary = _visual_class_data.get_equipped_weapon(GameState.player_character)
	if weapon.is_empty():
		return VISUAL_MODE_UNARMED
	var properties: Array[String] = _string_array(weapon.get("properties", []))
	return VISUAL_MODE_TWOHAND if "two_handed" in properties else VISUAL_MODE_ONEHAND


func _effective_combat_mode() -> bool:
	return _visual_combat_preview if _visual_combat_preview_enabled else _visual_combat_mode


func _direction_id(direction: Vector2) -> StringName:
	if absf(direction.x) > absf(direction.y):
		return &"right" if direction.x >= 0.0 else &"left"
	return &"down" if direction.y >= 0.0 else &"up"


func _install_character_sprite() -> void:
	var library: RefCounted = HUMAN_WARRIOR_LIBRARY_SCRIPT.new() as RefCounted
	var frames: SpriteFrames = library.call("build_sprite_frames") as SpriteFrames
	_animation_library_error = str(library.call("get_last_error"))
	if frames == null:
		push_warning(
			"human_warrior_m01 authored animation fallback enabled: %s"
			% _animation_library_error
		)
		return
	_character_sprite = AnimatedSprite2D.new()
	_character_sprite.name = "CharacterSprite"
	_character_sprite.centered = true
	_character_sprite.position = AUTHORED_SPRITE_OFFSET
	_character_sprite.sprite_frames = frames
	_character_sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_character_sprite.z_index = 1
	_character_sprite.hide()
	body_visual.add_child(_character_sprite)
	_character_sprite.play(&"idle_down")


func _install_animation_test_panel() -> void:
	if not OS.is_debug_build() or not _supports_authored_human_warrior(GameState.player_character):
		return
	var panel: CanvasLayer = HUMAN_WARRIOR_TEST_PANEL_SCRIPT.new() as CanvasLayer
	var host: Node = get_parent()
	if panel == null or host == null:
		return
	host.call_deferred("add_child", panel)
	panel.call_deferred("configure", self)


func _supports_authored_human_warrior(character: PlayerCharacter) -> bool:
	return (
		character != null
		and character.race_id == "human"
		and character.character_class_id == "fighter"
		and is_instance_valid(_character_sprite)
	)


func _string_array(value: Variant) -> Array[String]:
	var result: Array[String] = []
	if value is Array:
		for item: Variant in value as Array:
			result.append(str(item))
	return result


func _get_mobile_direction() -> Vector2:
	var button_direction: Vector2 = Vector2(
		float(_mobile_right) - float(_mobile_left),
		float(_mobile_down) - float(_mobile_up)
	)
	var combined: Vector2 = button_direction + _mobile_vector
	return combined.limit_length(1.0)
