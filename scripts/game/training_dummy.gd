class_name TrainingDummy
extends Node2D

@export var armor_class: int = 10
@export var maximum_health: int = 12

@onready var visual: Node2D = $Visual
@onready var health_label: Label = $HealthLabel

var current_health: int = 12
var _player_in_range: Node = null
var _combat_system: CombatSystem = CombatSystem.new()
var _class_data: ClassDataSystem = ClassDataSystem.new()
var _ability_system: ClassAbilitySystem = ClassAbilitySystem.new()
var _resetting: bool = false
var _targeted: bool = false
var _target_marker: Label


func _ready() -> void:
	add_to_group("combat_targets")
	maximum_health = maxi(maximum_health, 1)
	current_health = maximum_health
	_target_marker = Label.new()
	_target_marker.text = "▼ ЦЕЛЬ"
	_target_marker.position = Vector2(-42, -116)
	_target_marker.add_theme_color_override("font_color", Color(1.0, 0.35, 0.3, 1.0))
	_target_marker.add_theme_font_size_override("font_size", 16)
	add_child(_target_marker)
	_reset_target_passives()
	_update_health_label()


func interact() -> void:
	get_tree().call_group("game_world", "show_combat_message", "Используйте отдельную кнопку АТАКА, чтобы ударить тренировочное чучело.", true)


func attack_for_testing(natural_roll: int) -> AttackResult:
	var weapon: Dictionary = _class_data.get_equipped_weapon(GameState.player_character)
	var context: Dictionary = {"target_name": get_combat_name(), "distance_feet": 5}
	var result: AttackResult = _combat_system.perform_basic_attack(GameState.player_character, armor_class, weapon, natural_roll, [], context)
	receive_player_attack(result, false)
	return result


func get_combat_name() -> String:
	return "Тренировочное чучело"


func get_current_health() -> int:
	return current_health


func get_armor_class() -> int:
	return armor_class


func is_combat_active() -> bool:
	return not _resetting


func is_hostile() -> bool:
	return false


func set_combat_targeted(value: bool) -> void:
	_targeted = value
	if _target_marker != null:
		_target_marker.visible = value and not _resetting


func receive_player_attack(result: AttackResult, show_interface: bool = true) -> void:
	if _resetting:
		result.note = "Чучело восстанавливается."
		return
	if is_instance_valid(_player_in_range) and _player_in_range.has_method("play_attack_animation"):
		_player_in_range.call("play_attack_animation", global_position)
	if result.hit:
		current_health = maxi(0, current_health - result.damage)
		GameState.report_quest_event("hit_training_dummy")
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
		GameState.add_item("straw_scrap", 1)
		_schedule_reset.call_deferred()


func receive_signature_ability(ability: Dictionary, show_interface: bool = true, attack_context: Dictionary = {}) -> Dictionary:
	if _resetting:
		return {"success": false, "message": "Чучело восстанавливается."}
	var effect: String = str(ability.get("effect", ""))
	if effect == "hunters_mark":
		var setup: Dictionary = _ability_system.apply_target_ability(GameState.player_character, ability)
		GameState.save_game()
		return setup
	if effect not in ["spell_attack", "auto_hit_spell"]:
		return {"success": false, "message": "Эта способность не действует на тренировочную цель."}
	var result: AttackResult = _ability_system.perform_offensive_ability(GameState.player_character, ability, armor_class, -1, [], attack_context)
	if result.out_of_range or (not result.note.is_empty() and not result.hit):
		return {"success": false, "message": result.note}
	receive_player_attack(result, show_interface)
	GameState.save_game()
	return {"success": true, "message": "%s применена." % result.attack_name}


func reset_combat_state(full_restore: bool = true) -> void:
	_resetting = false
	if full_restore:
		current_health = maximum_health
	visual.rotation_degrees = 0.0
	visual.modulate = Color.WHITE
	_reset_target_passives()
	_update_health_label()


func _schedule_reset() -> void:
	await get_tree().create_timer(1.6).timeout
	reset_combat_state(true)


func _reset_target_passives() -> void:
	if GameState.player_character.character_class_id == "rogue":
		GameState.player_character.active_effects["sneak_attack_ready"] = true


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
	if _target_marker != null:
		_target_marker.visible = _targeted and not _resetting


func _on_body_entered(body: Node2D) -> void:
	if not body.is_in_group("player"):
		return
	_player_in_range = body
	if body.has_method("set_interactable"):
		body.call("set_interactable", self)
	get_tree().call_group("game_world", "set_interaction_action", true, "осмотреть тренировочное чучело", "ОСМОТРЕТЬ")


func _on_body_exited(body: Node2D) -> void:
	if body != _player_in_range:
		return
	if body.has_method("clear_interactable"):
		body.call("clear_interactable", self)
	_player_in_range = null
	get_tree().call_group("game_world", "set_interaction_action", false, "", "ДЕЙСТВИЕ")
