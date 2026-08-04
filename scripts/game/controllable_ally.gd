class_name ControllableAlly
extends CharacterBody2D

const FOLLOW_DISTANCE_PIXELS: float = 82.0
const FOLLOW_RESUME_DISTANCE_PIXELS: float = 108.0
const DEFAULT_FOLLOW_SPEED_PIXELS: float = 150.0
const MELEE_REACH_FEET: int = 5

@export var character_id: String = "companion_irna_guard_01"
@export var combat_name: String = "Ирна"
@export var armor_class: int = 14
@export var maximum_health: int = 12
@export var initiative_modifier: int = 2
@export var combat_speed_feet: int = 30
@export var attack_bonus: int = 4
@export var damage_die: int = 6
@export var damage_bonus: int = 2
@export var damage_type: String = "slashing"
@export var strength_save_modifier: int = 1
@export var dexterity_save_modifier: int = 2
@export var constitution_save_modifier: int = 1
@export var follow_speed_pixels: float = DEFAULT_FOLLOW_SPEED_PIXELS

@onready var body_visual: Polygon2D = get_node_or_null("Body") as Polygon2D
@onready var name_label: Label = get_node_or_null("NameLabel") as Label

var current_health: int = 12
var hostile: bool = false
var defeated: bool = false

var _combat_state: CombatantState = CombatantState.new()
var _facing_direction: Vector2 = Vector2.RIGHT
var _turn_active: bool = false
var _turn_based_mode: bool = false
var _combat_overlay_visible: bool = true
var _dodging: bool = false
var _follow_engaged: bool = false
var _turn_marker: Label = null
var _status_label: Label = null
var _dice: DiceRoller = DiceRoller.new()


func _ready() -> void:
	add_to_group("controllable_allies")
	add_to_group("friendly_combatants")
	maximum_health = maxi(maximum_health, 1)
	current_health = clampi(current_health, 0, maximum_health)
	if current_health <= 0 and not _combat_state.dead:
		current_health = maximum_health
	if name_label != null:
		name_label.text = combat_name
	_build_runtime_labels()
	_update_combat_visuals()


func _physics_process(_delta: float) -> void:
	if _turn_based_mode or current_health <= 0 or _combat_state.dead:
		velocity = Vector2.ZERO
		return
	var state: Node = get_tree().root.get_node_or_null("GameState")
	if state != null and bool(state.get("input_locked")):
		velocity = Vector2.ZERO
		return
	var player: Node2D = get_tree().get_first_node_in_group("player") as Node2D
	if player == null:
		velocity = Vector2.ZERO
		return
	var offset: Vector2 = player.global_position - global_position
	var distance: float = offset.length()
	if distance >= FOLLOW_RESUME_DISTANCE_PIXELS:
		_follow_engaged = true
	elif distance <= FOLLOW_DISTANCE_PIXELS:
		_follow_engaged = false
	if not _follow_engaged or distance <= 0.001:
		velocity = Vector2.ZERO
		return
	_facing_direction = offset.normalized()
	velocity = _facing_direction * maxf(follow_speed_pixels, 1.0)
	move_and_slide()


func get_actor_id() -> String:
	return character_id


func get_combat_name() -> String:
	return combat_name


func get_armor_class() -> int:
	return maxi(armor_class, 1)


func get_current_health() -> int:
	return current_health


func get_maximum_health() -> int:
	return maximum_health


func get_initiative_modifier() -> int:
	return initiative_modifier


func get_initiative_proficiency_bonus() -> int:
	return 0


func get_combat_speed_feet() -> int:
	return maxi(combat_speed_feet, 0)


func get_saving_throw_modifier(ability_id: String) -> int:
	match ability_id:
		"strength":
			return strength_save_modifier
		"dexterity":
			return dexterity_save_modifier
		"constitution":
			return constitution_save_modifier
		_:
			return 0


func get_combatant_state() -> CombatantState:
	return _combat_state


func get_facing_direction() -> Vector2:
	return _facing_direction


func set_facing_direction(direction: Vector2) -> void:
	if direction.length_squared() <= 0.0001:
		return
	_facing_direction = direction.normalized()
	if body_visual != null:
		body_visual.scale.x = -1.0 if _facing_direction.x < -0.2 else 1.0


func set_turn_based_mode(value: bool) -> void:
	_turn_based_mode = value
	velocity = Vector2.ZERO
	if not value:
		_turn_active = false
		_dodging = false
	_update_combat_visuals()


func set_turn_active(value: bool) -> void:
	_turn_active = value
	_update_combat_visuals()


func on_combat_turn_started() -> void:
	_dodging = false
	_update_combat_visuals()


func set_dodging(value: bool) -> void:
	_dodging = value
	_update_combat_visuals()


func is_dodging() -> bool:
	return _dodging


func set_combat_overlay_visible(value: bool) -> void:
	_combat_overlay_visible = value
	_update_combat_visuals()


func set_combat_targeted(_value: bool) -> void:
	pass


func is_hostile() -> bool:
	return false


func is_combat_active() -> bool:
	return not _combat_state.dead


func can_take_combat_turn() -> bool:
	return (
		current_health > 0
		and not _combat_state.dead
		and not _combat_state.has_condition("incapacitated")
		and not _combat_state.has_condition("unconscious")
	)


func is_incapacitated() -> bool:
	return not can_take_combat_turn()


func can_receive_enemy_attack() -> bool:
	return not _combat_state.dead


func can_be_stabilized_with_healers_kit() -> bool:
	return (
		current_health <= 0
		and not _combat_state.dead
		and not _combat_state.stable
	)


func stabilize_with_healers_kit() -> Dictionary:
	if not can_be_stabilized_with_healers_kit():
		return {
			"success": false,
			"message": "%s не нуждается в стабилизации." % combat_name
		}
	_combat_state.stable = true
	_combat_state.death_save_successes = 0
	_combat_state.death_save_failures = 0
	_combat_state.add_condition("unconscious")
	_combat_state.add_condition("incapacitated")
	_update_combat_visuals()
	return {
		"success": true,
		"message": "%s стабилизирована. HP не восстановлены." % combat_name,
		"target_id": character_id
	}


func enter_dying() -> void:
	current_health = 0
	defeated = false
	_combat_state.enter_dying()
	_turn_active = false
	_update_combat_visuals()


func recover_to_one_hit_point() -> void:
	current_health = 1
	defeated = false
	_combat_state.recover_from_zero_hit_points()
	_update_combat_visuals()


func mark_dead() -> void:
	current_health = 0
	defeated = true
	_combat_state.dead = true
	_combat_state.stable = false
	_combat_state.add_condition("unconscious")
	_combat_state.add_condition("incapacitated")
	_turn_active = false
	velocity = Vector2.ZERO
	_update_combat_visuals()


func set_current_health(value: int) -> void:
	current_health = clampi(value, 0, maximum_health)
	if current_health > 0:
		defeated = false
		_combat_state.recover_from_zero_hit_points()
	_update_combat_visuals()


func build_basic_attack_result(target: Node, roll_override: int = -1) -> AttackResult:
	var result := AttackResult.new()
	result.attacker_name = combat_name
	result.attack_name = "Короткий меч"
	result.target_name = str(target.call("get_combat_name")) if is_instance_valid(target) and target.has_method("get_combat_name") else "Цель"
	result.ability_name = "Ловкость"
	result.damage_type = damage_type
	result.melee_attack = true
	if not is_instance_valid(target) or not target is Node2D:
		result.automatic_miss = true
		result.note = "Цель недоступна."
		return result
	var distance: int = DistanceSystem.distance_feet(global_position, (target as Node2D).global_position)
	result.distance_feet = distance
	result.range_state = "melee"
	if distance > MELEE_REACH_FEET:
		result.out_of_range = true
		result.automatic_miss = true
		result.note = "Ирна должна находиться в соседней клетке."
		return result
	var natural: int = clampi(roll_override, 1, 20) if roll_override >= 1 else _dice.roll_die(20)
	var target_ac: int = int(target.call("get_armor_class")) if target.has_method("get_armor_class") else 10
	result.natural_roll = natural
	result.first_roll = natural
	result.attack_bonus = attack_bonus
	result.ability_modifier = damage_bonus
	result.total = natural + attack_bonus
	result.target_armor_class = target_ac
	result.critical = natural == 20
	result.hit = natural != 1 and (result.critical or result.total >= target_ac)
	result.automatic_miss = natural == 1
	if result.hit:
		var damage: int = damage_bonus
		for _die_index: int in range(2 if result.critical else 1):
			damage += _dice.roll_die(maxi(damage_die, 2))
		result.damage = maxi(damage, 0)
	else:
		result.note = "Атака Ирны не достигает цели."
	return result


func play_attack_animation(target_position: Vector2) -> void:
	if body_visual == null:
		return
	var direction: Vector2 = target_position - global_position
	set_facing_direction(direction)
	var original_position: Vector2 = body_visual.position
	var lunge: Vector2 = direction.normalized() * 8.0 if direction.length_squared() > 0.0001 else Vector2.RIGHT * 8.0
	var tween: Tween = create_tween()
	tween.tween_property(body_visual, "position", original_position + lunge, 0.09)
	tween.tween_property(body_visual, "position", original_position, 0.11)
	await tween.finished


func capture_world_state() -> Dictionary:
	return {
		"entity_type": "controllable_ally",
		"position": [global_position.x, global_position.y],
		"facing": [_facing_direction.x, _facing_direction.y],
		"groups": ["controllable_allies", "friendly_combatants"],
		"hostile": false,
		"defeated": defeated,
		"current_health": current_health,
		"maximum_health": maximum_health,
		"combat_state": _combat_state.to_dict()
	}


func restore_world_state(state: Dictionary) -> void:
	var position_value: Variant = state.get("position", [])
	if position_value is Array and (position_value as Array).size() >= 2:
		global_position = Vector2(
			float((position_value as Array)[0]),
			float((position_value as Array)[1])
		)
	var facing_value: Variant = state.get("facing", [])
	if facing_value is Array and (facing_value as Array).size() >= 2:
		set_facing_direction(Vector2(
			float((facing_value as Array)[0]),
			float((facing_value as Array)[1])
		))
	maximum_health = maxi(int(state.get("maximum_health", maximum_health)), 1)
	current_health = clampi(int(state.get("current_health", current_health)), 0, maximum_health)
	var combat_state_value: Variant = state.get("combat_state", {})
	if combat_state_value is Dictionary:
		_combat_state = CombatantState.from_dict(combat_state_value as Dictionary)
	defeated = bool(state.get("defeated", false)) or _combat_state.dead
	hostile = false
	_turn_active = false
	_turn_based_mode = false
	_update_combat_visuals()


func _build_runtime_labels() -> void:
	_turn_marker = Label.new()
	_turn_marker.name = "TurnMarker"
	_turn_marker.text = "◆ ХОД СОЮЗНИКА"
	_turn_marker.position = Vector2(-70.0, -102.0)
	_turn_marker.size = Vector2(140.0, 24.0)
	_turn_marker.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_turn_marker.add_theme_color_override("font_color", Color(0.45, 1.0, 0.68, 1.0))
	_turn_marker.add_theme_color_override("font_shadow_color", Color(0.0, 0.0, 0.0, 0.9))
	_turn_marker.add_theme_constant_override("shadow_offset_x", 2)
	_turn_marker.add_theme_constant_override("shadow_offset_y", 2)
	_turn_marker.add_theme_font_size_override("font_size", 14)
	add_child(_turn_marker)

	_status_label = Label.new()
	_status_label.name = "StatusLabel"
	_status_label.position = Vector2(-82.0, 44.0)
	_status_label.size = Vector2(164.0, 42.0)
	_status_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_status_label.add_theme_color_override("font_shadow_color", Color(0.0, 0.0, 0.0, 0.9))
	_status_label.add_theme_constant_override("shadow_offset_x", 2)
	_status_label.add_theme_constant_override("shadow_offset_y", 2)
	_status_label.add_theme_font_size_override("font_size", 13)
	add_child(_status_label)


func _update_combat_visuals() -> void:
	if _turn_marker != null:
		_turn_marker.visible = _combat_overlay_visible and _turn_active and not _combat_state.dead
	if _status_label != null:
		var state_label: String = "готова"
		if _combat_state.dead:
			state_label = "мертва"
		elif current_health <= 0 and _combat_state.stable:
			state_label = "стабильна"
		elif current_health <= 0:
			state_label = "умирает"
		elif _dodging:
			state_label = "уклоняется"
		_status_label.text = "%s · %d/%d HP" % [state_label, current_health, maximum_health]
		_status_label.visible = (
			_combat_overlay_visible
			and (_turn_active or current_health < maximum_health or _dodging)
		)
	if body_visual != null:
		if _combat_state.dead:
			body_visual.modulate = Color(0.28, 0.3, 0.34, 0.72)
		elif current_health <= 0:
			body_visual.modulate = Color(0.48, 0.52, 0.58, 0.82)
		elif _turn_active:
			body_visual.modulate = Color(0.72, 1.0, 0.78, 1.0)
		else:
			body_visual.modulate = Color.WHITE
