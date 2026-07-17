class_name TrainingDummy
extends Node2D

@export var armor_class: int = 10
@export var maximum_health: int = 12

@onready var visual: Node2D = $Visual
@onready var health_label: Label = $HealthLabel

var current_health: int = 12
var _player_in_range: Node = null
var _combat_system: CombatSystem = CombatSystem.new()
var _resetting: bool = false


func _ready() -> void:
	maximum_health = maxi(maximum_health, 1)
	current_health = maximum_health
	_update_health_label()


func interact() -> void:
	if GameState.input_locked or _resetting:
		return
	_perform_attack(-1, true)


func attack_for_testing(natural_roll: int) -> AttackResult:
	return _perform_attack(natural_roll, false)


func get_current_health() -> int:
	return current_health


func get_armor_class() -> int:
	return armor_class


func _perform_attack(natural_roll_override: int, show_interface: bool) -> AttackResult:
	var result: AttackResult = _combat_system.perform_unarmed_strike(
		GameState.player_character,
		armor_class,
		natural_roll_override
	)

	if is_instance_valid(_player_in_range) and _player_in_range.has_method("play_attack_animation"):
		_player_in_range.call("play_attack_animation", global_position)

	if result.hit:
		current_health = maxi(0, current_health - result.damage)
		_animate_hit()
	else:
		_animate_miss()

	result.target_health_after = current_health
	result.target_max_health = maximum_health
	_update_health_label()

	if show_interface:
		get_tree().call_group("combat_ui", "show_result", result)

	if current_health <= 0 and not _resetting:
		_resetting = true
		_schedule_reset.call_deferred()
	return result


func _schedule_reset() -> void:
	await get_tree().create_timer(1.6).timeout
	current_health = maximum_health
	_resetting = false
	visual.rotation_degrees = 0.0
	visual.modulate = Color.WHITE
	_update_health_label()


func _animate_hit() -> void:
	visual.modulate = Color(1.0, 0.58, 0.48, 1.0)
	var tween: Tween = create_tween()
	tween.tween_property(visual, "rotation_degrees", 7.0, 0.06)
	tween.tween_property(visual, "rotation_degrees", -6.0, 0.08)
	tween.tween_property(visual, "rotation_degrees", 0.0, 0.08)
	tween.parallel().tween_property(visual, "modulate", Color.WHITE, 0.22)


func _animate_miss() -> void:
	var tween: Tween = create_tween()
	tween.tween_property(visual, "modulate:a", 0.55, 0.08)
	tween.tween_property(visual, "modulate:a", 1.0, 0.12)


func _update_health_label() -> void:
	if _resetting and current_health <= 0:
		health_label.text = "Сломано · восстановление..."
	else:
		health_label.text = "КД %d · прочность %d/%d" % [armor_class, current_health, maximum_health]


func _on_body_entered(body: Node2D) -> void:
	if not body.is_in_group("player"):
		return
	_player_in_range = body
	if body.has_method("set_interactable"):
		body.call("set_interactable", self)
	get_tree().call_group(
		"game_world",
		"set_interaction_action",
		true,
		"атаковать тренировочное чучело",
		"АТАКА"
	)


func _on_body_exited(body: Node2D) -> void:
	if body != _player_in_range:
		return
	if body.has_method("clear_interactable"):
		body.call("clear_interactable", self)
	_player_in_range = null
	get_tree().call_group("game_world", "set_interaction_action", false, "", "ДЕЙСТВИЕ")
