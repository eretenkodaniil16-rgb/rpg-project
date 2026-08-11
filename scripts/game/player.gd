extends CharacterBody2D

signal melee_attack_contact(sequence_id: int)
signal melee_attack_finished(sequence_id: int)
signal hit_reaction_started(sequence_id: int, damage_amount: int)
signal hit_reaction_finished(sequence_id: int)
signal death_animation_started(sequence_id: int, death_variant_id: String, direction_id: String)
signal death_animation_finished(sequence_id: int, death_visual_state: Dictionary)

const HUMAN_WARRIOR_LIBRARY_SCRIPT: Script = preload("res://scripts/game/human_warrior_animation_library.gd")
const DEATH_ANIMATION_SELECTOR_SCRIPT: Script = preload("res://scripts/systems/death_animation_selector.gd")
const AUTHORED_SPRITE_OFFSET: Vector2 = Vector2(0.0, -43.0)
const VISUAL_MOVEMENT_EPSILON_SQUARED: float = 0.01
const VISUAL_STOP_GRACE_SECONDS: float = 0.10
const VISUAL_STATE_IDLE: StringName = &"idle"
const VISUAL_STATE_WALK: StringName = &"walk"
const VISUAL_MODE_AUTO: StringName = &"auto"
const VISUAL_MODE_UNARMED: StringName = &"unarmed"
const VISUAL_MODE_ONEHAND: StringName = &"onehand"
const VISUAL_MODE_TWOHAND: StringName = &"twohand"
const DEATH_STATE_PLAYING: String = "playing"
const DEATH_STATE_CORPSE_HOLD: String = "corpse_hold"

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
var _hit_tween: Tween = null

var _animation_library: HumanWarriorAnimationLibrary = null
var _character_sprite: AnimatedSprite2D = null
var _active_visual: Node2D = null
var _active_visual_base_position: Vector2 = Vector2.ZERO
var _visual_facing_direction: Vector2 = Vector2.DOWN
var _visual_motion_state: StringName = VISUAL_STATE_IDLE
var _visual_combat_mode: bool = false
var _visual_preview_mode: StringName = VISUAL_MODE_AUTO
var _visual_sample_initialized: bool = false
var _last_visual_sample_position: Vector2 = Vector2.ZERO
var _visual_stop_grace_remaining: float = 0.0
var _animation_library_error: String = ""
var _visual_class_data: ClassDataSystem = ClassDataSystem.new()
var _last_visual_weapon_id: String = ""

var _action_animation_locked: bool = false
var _attack_sequence_counter: int = 0
var _active_attack_sequence_id: int = 0
var _active_attack_animation: StringName = &""
var _active_attack_contact_frame: int = 3
var _attack_contact_fired: bool = false
var _pending_attack_contact: Callable = Callable()

var _hit_sequence_counter: int = 0
var _active_hit_sequence_id: int = 0
var _active_hit_animation: StringName = &""
var _queued_hit_damage: int = 0
var _queued_hit_source_global_position: Vector2 = Vector2.INF

var _death_selector: DeathAnimationSelector = DEATH_ANIMATION_SELECTOR_SCRIPT.new() as DeathAnimationSelector
var _death_sequence_counter: int = 0
var _active_death_sequence_id: int = 0
var _active_death_animation: StringName = &""
var _death_visual_state: Dictionary = {}
var _death_animation_completed: bool = false
var _death_fallback_tween: Tween = null


func _ready() -> void:
	_install_character_sprite()
	apply_character_appearance()
	_last_visual_sample_position = global_position
	_last_visual_weapon_id = GameState.player_character.equipped_weapon_id
	_visual_sample_initialized = true
	_restore_death_visual_state_if_needed()


func _process(delta: float) -> void:
	var equipped_weapon_id: String = GameState.player_character.equipped_weapon_id
	if equipped_weapon_id != _last_visual_weapon_id:
		_last_visual_weapon_id = equipped_weapon_id
		_refresh_visual_animation()
	_sample_visual_motion(delta)


func _physics_process(_delta: float) -> void:
	if GameState.input_locked or _action_animation_locked:
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
	if _action_animation_locked:
		return
	if event.is_action_pressed("ui_accept"):
		request_interaction()
		if is_instance_valid(interactable):
			get_viewport().set_input_as_handled()


func request_interaction() -> void:
	if GameState.input_locked or _action_animation_locked:
		return
	_refresh_primary_interactable()
	_interact_with_target(interactable)


func request_interaction_with_instance(instance_id: int) -> void:
	if GameState.input_locked or _action_animation_locked:
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
	if _action_animation_locked:
		return
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


func start_melee_attack_animation(
	target_global_position: Vector2,
	weapon: Dictionary,
	contact_callback: Callable = Callable()
) -> int:
	if _action_animation_locked:
		return -1
	var direction: Vector2 = target_global_position - global_position
	if direction.length_squared() <= 0.0001:
		direction = _visual_facing_direction
	if direction.length_squared() <= 0.0001:
		direction = Vector2.RIGHT
	var normalized_attack_direction: Vector2 = direction.normalized()
	# Synchronize both the authored visual and the production combat-facing state
	# before enabling the lock. Subsequent external facing requests are ignored
	# until the attack has completed.
	if has_method("set_facing_direction"):
		call("set_facing_direction", normalized_attack_direction)
	else:
		set_visual_facing(normalized_attack_direction)
	_visual_motion_state = VISUAL_STATE_IDLE
	_visual_stop_grace_remaining = 0.0
	velocity = Vector2.ZERO

	_attack_sequence_counter += 1
	_active_attack_sequence_id = _attack_sequence_counter
	_action_animation_locked = true
	_attack_contact_fired = false
	_pending_attack_contact = contact_callback
	if _attack_tween != null:
		_attack_tween.kill()
		_attack_tween = null
	get_active_visual().position = _active_visual_base_position

	var attack_set_id: StringName = _attack_set_for_weapon(weapon)
	var direction_id: StringName = _direction_id(_visual_facing_direction)
	var animation_name := StringName("%s_%s" % [str(attack_set_id), str(direction_id)])
	if (
		not str(attack_set_id).is_empty()
		and is_instance_valid(_character_sprite)
		and _character_sprite.visible
		and _character_sprite.sprite_frames.has_animation(animation_name)
	):
		_active_attack_animation = animation_name
		_active_attack_contact_frame = _animation_library.get_attack_contact_frame_index(attack_set_id) if _animation_library != null else 3
		_character_sprite.stop()
		_character_sprite.play(animation_name)
		return _active_attack_sequence_id

	_active_attack_animation = &""
	_active_attack_contact_frame = 0
	_start_fallback_melee_attack(_active_attack_sequence_id, _visual_facing_direction)
	return _active_attack_sequence_id


func is_action_animation_locked() -> bool:
	return _action_animation_locked


func is_hit_reaction_active() -> bool:
	return _active_hit_sequence_id > 0


func is_death_animation_active() -> bool:
	return (
		_active_death_sequence_id > 0
		and str(_death_visual_state.get("corpse_state", "")) == DEATH_STATE_PLAYING
	)


func is_corpse_hold_active() -> bool:
	return (
		_active_death_sequence_id > 0
		and str(_death_visual_state.get("corpse_state", "")) == DEATH_STATE_CORPSE_HOLD
	)


func get_death_visual_state() -> Dictionary:
	return _death_visual_state.duplicate(true)


func get_visual_facing_direction_id() -> StringName:
	return _direction_id(_visual_facing_direction)


func start_confirmed_death_animation(
	restored_state: Dictionary = {},
	roll_override: float = -1.0
) -> int:
	if _active_death_sequence_id > 0:
		return _active_death_sequence_id
	var character: PlayerCharacter = GameState.player_character
	if character == null or character.current_health > 0:
		return -1

	var source_state: Dictionary = PlayerCharacter.normalize_death_visual_state(restored_state)
	if source_state.is_empty():
		source_state = PlayerCharacter.normalize_death_visual_state(character.death_visual_state)
	var entries: Array[Dictionary] = (
		_animation_library.get_death_variant_entries()
		if _animation_library != null
		else []
	)
	var fallback_variant_id: String = (
		_animation_library.get_death_fallback_variant_id()
		if _animation_library != null
		else DeathAnimationSelector.DEFAULT_FALLBACK_VARIANT_ID
	)
	var requested_variant_id: String = str(source_state.get("death_variant_id", ""))
	var death_variant_id: String = ""
	if not requested_variant_id.is_empty():
		death_variant_id = _death_selector.resolve_available_variant(
			requested_variant_id,
			entries,
			fallback_variant_id
		)
	else:
		death_variant_id = _death_selector.select_variant(
			entries,
			character.last_death_variant_id,
			roll_override
		)
	if death_variant_id.is_empty():
		death_variant_id = fallback_variant_id

	var direction_id: StringName = _direction_id(_visual_facing_direction)
	if not source_state.is_empty():
		direction_id = StringName(str(source_state.get("direction_id", str(direction_id))))
	var restored_corpse_hold: bool = (
		str(source_state.get("corpse_state", "")) == DEATH_STATE_CORPSE_HOLD
	)
	var restored_frame_index: int = clampi(int(source_state.get("frame_index", 0)), 0, 7)

	_cancel_action_animation_for_death()
	_death_sequence_counter += 1
	_active_death_sequence_id = _death_sequence_counter
	_death_animation_completed = false
	_action_animation_locked = true
	_visual_motion_state = VISUAL_STATE_IDLE
	_visual_stop_grace_remaining = 0.0
	velocity = Vector2.ZERO
	_death_visual_state = {
		"death_variant_id": death_variant_id,
		"direction_id": str(direction_id),
		"corpse_state": DEATH_STATE_CORPSE_HOLD if restored_corpse_hold else DEATH_STATE_PLAYING,
		"frame_index": restored_frame_index
	}
	character.last_death_variant_id = death_variant_id
	_persist_death_visual_state()

	var set_id: StringName = (
		_animation_library.get_death_set_for_variant(death_variant_id)
		if _animation_library != null
		else &""
	)
	var animation_name := StringName("%s_%s" % [str(set_id), str(direction_id)])
	var authored_death_available: bool = (
		not str(set_id).is_empty()
		and is_instance_valid(_character_sprite)
		and _character_sprite.visible
		and _character_sprite.sprite_frames.has_animation(animation_name)
	)
	if authored_death_available:
		_active_death_animation = animation_name
		_character_sprite.position = (
			AUTHORED_SPRITE_OFFSET
			+ _animation_library.get_death_anchor_offset(death_variant_id, direction_id)
		)
		_character_sprite.stop()
		_character_sprite.play(animation_name)
		var hold_frame_index: int = _animation_library.get_death_corpse_hold_frame_index(
			death_variant_id
		)
		if restored_corpse_hold:
			_character_sprite.frame = hold_frame_index
			_character_sprite.pause()
		else:
			_character_sprite.frame = mini(restored_frame_index, hold_frame_index)
	else:
		_active_death_animation = &""
		if is_instance_valid(_character_sprite):
			_character_sprite.pause()

	death_animation_started.emit(
		_active_death_sequence_id,
		death_variant_id,
		str(direction_id)
	)
	if restored_corpse_hold:
		call_deferred("_complete_death_animation", _active_death_sequence_id)
	elif not authored_death_available:
		_start_static_death_fallback(_active_death_sequence_id)
	return _active_death_sequence_id


func clear_death_visual_state() -> void:
	if _death_fallback_tween != null:
		_death_fallback_tween.kill()
		_death_fallback_tween = null
	_active_death_sequence_id = 0
	_active_death_animation = &""
	_death_visual_state.clear()
	_death_animation_completed = false
	_action_animation_locked = false
	if GameState.player_character != null:
		GameState.player_character.death_visual_state.clear()
	if is_instance_valid(_character_sprite):
		_character_sprite.position = AUTHORED_SPRITE_OFFSET
	_refresh_visual_animation()


func _restore_death_visual_state_if_needed() -> void:
	var character: PlayerCharacter = GameState.player_character
	if character == null:
		return
	if character.current_health > 0:
		character.death_visual_state.clear()
		return
	var restored_state: Dictionary = PlayerCharacter.normalize_death_visual_state(
		character.death_visual_state
	)
	if restored_state.is_empty():
		return
	start_confirmed_death_animation(restored_state)


func _persist_death_visual_state() -> void:
	var character: PlayerCharacter = GameState.player_character
	if character == null:
		return
	var normalized_state: Dictionary = PlayerCharacter.normalize_death_visual_state(
		_death_visual_state
	)
	character.death_visual_state = normalized_state.duplicate(true)
	if not normalized_state.is_empty():
		character.last_death_variant_id = str(
			normalized_state.get("death_variant_id", character.last_death_variant_id)
		)


func _start_static_death_fallback(sequence_id: int) -> void:
	if sequence_id != _active_death_sequence_id:
		return
	if _death_fallback_tween != null:
		_death_fallback_tween.kill()
	var duration_seconds: float = (
		_animation_library.get_death_duration_seconds()
		if _animation_library != null
		else 0.8
	)
	_death_fallback_tween = create_tween()
	_death_fallback_tween.tween_interval(maxf(duration_seconds, 0.8))
	_death_fallback_tween.tween_callback(
		Callable(self, "_complete_death_animation").bind(sequence_id)
	)


func _complete_death_animation(sequence_id: int) -> void:
	if sequence_id != _active_death_sequence_id or _death_animation_completed:
		return
	_death_animation_completed = true
	_death_fallback_tween = null
	var death_variant_id: String = str(_death_visual_state.get("death_variant_id", ""))
	var hold_frame_index: int = 7
	if _animation_library != null:
		hold_frame_index = _animation_library.get_death_corpse_hold_frame_index(
			death_variant_id
		)
	if (
		is_instance_valid(_character_sprite)
		and not str(_active_death_animation).is_empty()
		and _character_sprite.animation == _active_death_animation
	):
		_character_sprite.frame = hold_frame_index
		_character_sprite.pause()
	_death_visual_state["corpse_state"] = DEATH_STATE_CORPSE_HOLD
	_death_visual_state["frame_index"] = hold_frame_index
	_persist_death_visual_state()
	death_animation_finished.emit(sequence_id, get_death_visual_state())


func play_hit_reaction(
	damage_amount: int,
	source_global_position: Vector2 = Vector2.INF
) -> int:
	if damage_amount <= 0 or GameState.player_character.current_health <= 0:
		return -1
	if _action_animation_locked:
		_queue_hit_reaction(damage_amount, source_global_position)
		return _active_hit_sequence_id if _active_hit_sequence_id > 0 else 0
	return _start_hit_reaction(damage_amount, source_global_position)


func cancel_hit_reaction_for_death() -> void:
	_cancel_action_animation_for_death()


func _cancel_action_animation_for_death() -> void:
	if _active_death_sequence_id > 0:
		return
	var cancelled_attack_sequence_id: int = _active_attack_sequence_id
	var cancelled_hit_sequence_id: int = _active_hit_sequence_id
	_queued_hit_damage = 0
	_queued_hit_source_global_position = Vector2.INF
	_pending_attack_contact = Callable()
	_attack_contact_fired = true
	if _attack_tween != null:
		_attack_tween.kill()
		_attack_tween = null
	if _hit_tween != null:
		_hit_tween.kill()
		_hit_tween = null
	if is_instance_valid(_character_sprite) and (
		_character_sprite.animation == _active_attack_animation
		or _character_sprite.animation == _active_hit_animation
	):
		_character_sprite.stop()
	get_active_visual().position = _active_visual_base_position
	_active_attack_animation = &""
	_active_attack_sequence_id = 0
	_active_hit_animation = &""
	_active_hit_sequence_id = 0
	_action_animation_locked = false
	if cancelled_attack_sequence_id > 0:
		melee_attack_finished.emit(cancelled_attack_sequence_id)
	if cancelled_hit_sequence_id > 0:
		hit_reaction_finished.emit(cancelled_hit_sequence_id)


func _start_hit_reaction(damage_amount: int, source_global_position: Vector2) -> int:
	_hit_sequence_counter += 1
	_active_hit_sequence_id = _hit_sequence_counter
	_action_animation_locked = true
	_visual_motion_state = VISUAL_STATE_IDLE
	_visual_stop_grace_remaining = 0.0
	velocity = Vector2.ZERO
	if _attack_tween != null:
		_attack_tween.kill()
		_attack_tween = null
	get_active_visual().position = _active_visual_base_position

	var grip_mode: StringName = _effective_grip_mode()
	var hit_set_id: StringName = &""
	if grip_mode == VISUAL_MODE_ONEHAND:
		hit_set_id = &"hit_01_onehand"
	elif grip_mode == VISUAL_MODE_TWOHAND:
		hit_set_id = &"hit_01_twohand"
	var direction_id: StringName = _direction_id(_visual_facing_direction)
	var animation_name := StringName("%s_%s" % [str(hit_set_id), str(direction_id)])
	if (
		not str(hit_set_id).is_empty()
		and is_instance_valid(_character_sprite)
		and _character_sprite.visible
		and _character_sprite.sprite_frames.has_animation(animation_name)
	):
		_active_hit_animation = animation_name
		_character_sprite.stop()
		_character_sprite.play(animation_name)
		hit_reaction_started.emit(_active_hit_sequence_id, damage_amount)
		return _active_hit_sequence_id

	_active_hit_animation = &""
	hit_reaction_started.emit(_active_hit_sequence_id, damage_amount)
	_start_fallback_hit_reaction(_active_hit_sequence_id, source_global_position)
	return _active_hit_sequence_id


func _queue_hit_reaction(damage_amount: int, source_global_position: Vector2) -> void:
	_queued_hit_damage = maxi(_queued_hit_damage, damage_amount)
	if source_global_position != Vector2.INF:
		_queued_hit_source_global_position = source_global_position


func _start_queued_hit_reaction() -> void:
	if _queued_hit_damage <= 0 or _action_animation_locked:
		return
	if GameState.player_character.current_health <= 0:
		_queued_hit_damage = 0
		_queued_hit_source_global_position = Vector2.INF
		return
	var damage_amount: int = _queued_hit_damage
	var source_position: Vector2 = _queued_hit_source_global_position
	_queued_hit_damage = 0
	_queued_hit_source_global_position = Vector2.INF
	_start_hit_reaction(damage_amount, source_position)


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
		_apply_active_death_anchor()
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
	if _active_death_sequence_id > 0:
		return
	if direction.length_squared() <= 0.0001:
		return
	_visual_facing_direction = direction.normalized()
	_refresh_visual_animation()


func set_visual_motion(is_moving: bool, direction: Vector2 = Vector2.ZERO) -> void:
	if _action_animation_locked:
		return
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


func get_visual_motion_state_for_testing() -> StringName:
	return _visual_motion_state


func get_visual_debug_state() -> Dictionary:
	return {
		"mode": str(_visual_preview_mode),
		"combat": _visual_combat_mode,
		"grip": str(_effective_grip_mode()),
		"animation": str(_character_sprite.animation) if is_instance_valid(_character_sprite) else "fallback",
		"action_locked": _action_animation_locked,
		"hit_active": _active_hit_sequence_id > 0,
		"death_active": is_death_animation_active(),
		"corpse_hold": is_corpse_hold_active(),
		"death_visual_state": get_death_visual_state(),
		"queued_hit_damage": _queued_hit_damage,
		"library_error": _animation_library_error
	}


func _sample_visual_motion(delta: float) -> void:
	if _action_animation_locked:
		_last_visual_sample_position = global_position
		return
	if not _visual_sample_initialized:
		_last_visual_sample_position = global_position
		_visual_sample_initialized = true
		return
	var movement_delta: Vector2 = global_position - _last_visual_sample_position
	_last_visual_sample_position = global_position
	if movement_delta.length_squared() > VISUAL_MOVEMENT_EPSILON_SQUARED:
		_visual_stop_grace_remaining = VISUAL_STOP_GRACE_SECONDS
		set_visual_motion(true, movement_delta)
		return
	if _visual_motion_state != VISUAL_STATE_WALK:
		_visual_stop_grace_remaining = 0.0
		return
	_visual_stop_grace_remaining = maxf(_visual_stop_grace_remaining - delta, 0.0)
	if _visual_stop_grace_remaining <= 0.0:
		set_visual_motion(false)


func _refresh_visual_animation() -> void:
	if _action_animation_locked:
		return
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
	if _character_sprite.animation != desired_animation or not _character_sprite.is_playing():
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
	if not _visual_combat_mode:
		return VISUAL_MODE_UNARMED
	var weapon: Dictionary = _visual_class_data.get_equipped_weapon(GameState.player_character)
	var attack_set_id: StringName = _attack_set_for_weapon(weapon)
	if attack_set_id == &"attack_sword_01_onehand":
		return VISUAL_MODE_ONEHAND
	if attack_set_id == &"attack_sword_01_twohand":
		return VISUAL_MODE_TWOHAND
	return VISUAL_MODE_UNARMED


func _attack_set_for_weapon(weapon: Dictionary) -> StringName:
	if weapon.is_empty() or _animation_library == null:
		return &""
	return _animation_library.get_attack_set_for_weapon_id(str(weapon.get("id", "")))


func _direction_id(direction: Vector2) -> StringName:
	if absf(direction.x) > absf(direction.y):
		return &"right" if direction.x >= 0.0 else &"left"
	return &"down" if direction.y >= 0.0 else &"up"


func _install_character_sprite() -> void:
	_animation_library = HUMAN_WARRIOR_LIBRARY_SCRIPT.new() as HumanWarriorAnimationLibrary
	var frames: SpriteFrames = _animation_library.build_sprite_frames()
	_animation_library_error = _animation_library.get_last_error()
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
	_character_sprite.frame_changed.connect(_on_character_sprite_frame_changed)
	_character_sprite.animation_finished.connect(_on_character_sprite_animation_finished)
	body_visual.add_child(_character_sprite)
	_character_sprite.play(&"idle_down")


func _start_fallback_melee_attack(sequence_id: int, direction: Vector2) -> void:
	var visual: Node2D = get_active_visual()
	visual.position = _active_visual_base_position
	_attack_tween = create_tween()
	_attack_tween.tween_property(
		visual,
		"position",
		_active_visual_base_position + direction.normalized() * 15.0,
		0.07
	)
	_attack_tween.tween_callback(Callable(self, "_fire_attack_contact").bind(sequence_id))
	_attack_tween.tween_property(visual, "position", _active_visual_base_position, 0.11)
	_attack_tween.tween_callback(Callable(self, "_finish_melee_attack").bind(sequence_id))


func _start_fallback_hit_reaction(sequence_id: int, source_global_position: Vector2) -> void:
	var recoil_direction: Vector2 = -_visual_facing_direction
	if source_global_position != Vector2.INF:
		var away_from_source: Vector2 = global_position - source_global_position
		if away_from_source.length_squared() > 0.0001:
			recoil_direction = away_from_source.normalized()
	if recoil_direction.length_squared() <= 0.0001:
		recoil_direction = Vector2.DOWN
	var visual: Node2D = get_active_visual()
	visual.position = _active_visual_base_position
	_hit_tween = create_tween()
	_hit_tween.tween_property(
		visual,
		"position",
		_active_visual_base_position + recoil_direction.normalized() * 7.0,
		0.08
	)
	_hit_tween.tween_property(visual, "position", _active_visual_base_position, 0.18)
	_hit_tween.tween_callback(Callable(self, "_finish_hit_reaction").bind(sequence_id))


func _on_character_sprite_frame_changed() -> void:
	if not _action_animation_locked or not is_instance_valid(_character_sprite):
		return
	if (
		_active_death_sequence_id > 0
		and not str(_active_death_animation).is_empty()
		and _character_sprite.animation == _active_death_animation
	):
		_death_visual_state["frame_index"] = clampi(_character_sprite.frame, 0, 7)
		_persist_death_visual_state()
		return
	if _character_sprite.animation != _active_attack_animation:
		return
	if _character_sprite.frame >= _active_attack_contact_frame:
		_fire_attack_contact(_active_attack_sequence_id)


func _on_character_sprite_animation_finished() -> void:
	if not _action_animation_locked or not is_instance_valid(_character_sprite):
		return
	if (
		_active_death_sequence_id > 0
		and not str(_active_death_animation).is_empty()
		and _character_sprite.animation == _active_death_animation
	):
		call_deferred("_complete_death_animation", _active_death_sequence_id)
		return
	if not str(_active_hit_animation).is_empty() and _character_sprite.animation == _active_hit_animation:
		call_deferred("_finish_hit_reaction", _active_hit_sequence_id)
		return
	if _character_sprite.animation != _active_attack_animation:
		return
	# AnimatedSprite2D completes its internal non-loop transition after emitting
	# animation_finished. Finalizing synchronously can restore the finished action
	# over the combat idle selected by _refresh_visual_animation().
	call_deferred("_finish_melee_attack", _active_attack_sequence_id)


func _fire_attack_contact(sequence_id: int) -> void:
	if sequence_id != _active_attack_sequence_id or _attack_contact_fired:
		return
	_attack_contact_fired = true
	var callback: Callable = _pending_attack_contact
	_pending_attack_contact = Callable()
	if callback.is_valid():
		callback.call()
	melee_attack_contact.emit(sequence_id)


func _finish_melee_attack(sequence_id: int) -> void:
	if sequence_id != _active_attack_sequence_id:
		return
	_fire_attack_contact(sequence_id)
	get_active_visual().position = _active_visual_base_position
	_attack_tween = null
	_active_attack_animation = &""
	_active_attack_sequence_id = 0
	_action_animation_locked = false
	_visual_motion_state = VISUAL_STATE_IDLE
	_visual_stop_grace_remaining = 0.0
	_last_visual_sample_position = global_position
	_refresh_visual_animation()
	melee_attack_finished.emit(sequence_id)
	call_deferred("_start_queued_hit_reaction")


func _finish_hit_reaction(sequence_id: int) -> void:
	if sequence_id != _active_hit_sequence_id:
		return
	get_active_visual().position = _active_visual_base_position
	_hit_tween = null
	_active_hit_animation = &""
	_active_hit_sequence_id = 0
	_action_animation_locked = false
	_visual_motion_state = VISUAL_STATE_IDLE
	_visual_stop_grace_remaining = 0.0
	_last_visual_sample_position = global_position
	if GameState.player_character.current_health > 0:
		_refresh_visual_animation()
	hit_reaction_finished.emit(sequence_id)
	call_deferred("_start_queued_hit_reaction")


func _apply_active_death_anchor() -> void:
	if not is_instance_valid(_character_sprite):
		return
	_character_sprite.position = AUTHORED_SPRITE_OFFSET
	if _active_death_sequence_id <= 0 or _animation_library == null:
		return
	var death_variant_id: String = str(_death_visual_state.get("death_variant_id", ""))
	var direction_id := StringName(str(_death_visual_state.get("direction_id", "down")))
	_character_sprite.position += _animation_library.get_death_anchor_offset(
		death_variant_id,
		direction_id
	)


func _supports_authored_human_warrior(character: PlayerCharacter) -> bool:
	return (
		character != null
		and character.race_id == "human"
		and character.character_class_id == "fighter"
		and is_instance_valid(_character_sprite)
	)


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
