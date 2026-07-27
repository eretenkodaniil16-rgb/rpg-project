class_name RuneTrainingConstruct
extends Node2D

@export var armor_class: int = 13
@export var maximum_health: int = 30
@export var spell_slots_level_1: int = 2

var current_health: int = 30
var hostile: bool = false
var counterspell_save_roll_override: int = -1
var _turn_active: bool = false
var _targeted: bool = false
var _combat_overlay_visible: bool = true
var _status_label: Label
var _target_marker: Label
var _turn_marker: Label


func _ready() -> void:
	add_to_group("combat_targets")
	add_to_group("reaction_spellcasters")
	current_health = maxi(maximum_health, 1)
	spell_slots_level_1 = maxi(spell_slots_level_1, 0)
	_build_labels()
	queue_redraw()
	_update_status()


func get_combat_name() -> String:
	return "Рунический учебный конструкт"


func get_current_health() -> int:
	return current_health


func get_armor_class() -> int:
	return armor_class


func get_initiative_modifier() -> int:
	return 1


func get_combat_speed_feet() -> int:
	return 30


func get_saving_throw_modifier(ability_id: String) -> int:
	match ability_id:
		"constitution": return 2
		"dexterity": return 1
		"wisdom": return 0
		_: return 0


func get_spell_save_dc() -> int:
	return 12


func get_combat_spell_id() -> String:
	return "burning_hands" if spell_slots_level_1 > 0 else ""


func get_combat_spell_slot_level() -> int:
	return 1


func get_combat_spell_slot_count(level: int) -> int:
	return spell_slots_level_1 if level == 1 else 0


func consume_combat_spell_slot(level: int) -> bool:
	if level != 1 or spell_slots_level_1 <= 0:
		return false
	spell_slots_level_1 -= 1
	_update_status()
	return true


func get_counterspell_save_roll_overrides() -> Array[int]:
	return [counterspell_save_roll_override] if counterspell_save_roll_override >= 1 else []


func can_take_combat_turn() -> bool:
	return current_health > 0


func is_combat_active() -> bool:
	return current_health > 0


func is_hostile() -> bool:
	return hostile and current_health > 0


func enter_combat_hostile() -> void:
	hostile = true
	_update_status()


func perform_combat_turn_attack() -> void:
	if current_health <= 0:
		return
	get_tree().call_group("game_world", "resolve_npc_attack", self, 3, 6, 1, "force")


func perform_opportunity_attack() -> void:
	perform_combat_turn_attack()


func receive_player_attack(result: AttackResult, show_interface: bool = true) -> void:
	if current_health <= 0:
		return
	if result.hit:
		current_health = maxi(current_health - maxi(result.damage, 0), 0)
		queue_redraw()
	result.target_health_after = current_health
	result.target_max_health = maximum_health
	_update_status()
	if show_interface:
		get_tree().call_group("combat_ui", "show_result", result)
	if current_health <= 0:
		hostile = false


func set_turn_active(value: bool) -> void:
	_turn_active = value
	_update_status()


func set_combat_targeted(value: bool) -> void:
	_targeted = value
	_update_status()


func set_combat_overlay_visible(value: bool) -> void:
	_combat_overlay_visible = value
	_update_status()


func reset_for_testing() -> void:
	current_health = maximum_health
	spell_slots_level_1 = 2
	hostile = false
	counterspell_save_roll_override = -1
	_update_status()
	queue_redraw()


func _draw() -> void:
	var disabled: bool = current_health <= 0
	var body_color: Color = Color(0.22, 0.28, 0.38, 1.0) if not disabled else Color(0.12, 0.13, 0.16, 0.72)
	var rune_color: Color = Color(0.35, 0.78, 1.0, 1.0) if not disabled else Color(0.24, 0.28, 0.31, 0.7)
	draw_circle(Vector2.ZERO, 34.0, body_color)
	draw_circle(Vector2.ZERO, 34.0, Color(0.7, 0.78, 0.88, 0.8), false, 3.0)
	draw_line(Vector2(-16.0, 0.0), Vector2(16.0, 0.0), rune_color, 4.0)
	draw_line(Vector2(0.0, -16.0), Vector2(0.0, 16.0), rune_color, 4.0)
	draw_circle(Vector2.ZERO, 8.0, rune_color, false, 3.0)


func _build_labels() -> void:
	_status_label = Label.new()
	_status_label.position = Vector2(-125.0, 46.0)
	_status_label.custom_minimum_size = Vector2(250.0, 54.0)
	_status_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_status_label.add_theme_font_size_override("font_size", 15)
	add_child(_status_label)
	_target_marker = Label.new()
	_target_marker.text = "▼ ЦЕЛЬ"
	_target_marker.position = Vector2(-42.0, -74.0)
	_target_marker.add_theme_color_override("font_color", Color(1.0, 0.35, 0.3, 1.0))
	_target_marker.add_theme_font_size_override("font_size", 16)
	add_child(_target_marker)
	_turn_marker = Label.new()
	_turn_marker.text = "◆ ХОД"
	_turn_marker.position = Vector2(-34.0, -98.0)
	_turn_marker.add_theme_color_override("font_color", Color(0.5, 1.0, 0.55, 1.0))
	_turn_marker.add_theme_font_size_override("font_size", 15)
	add_child(_turn_marker)


func _update_status() -> void:
	if _status_label != null:
		_status_label.text = "%s\nHP %d/%d · ячейки %d" % [
			get_combat_name(),
			current_health,
			maximum_health,
			spell_slots_level_1
		]
		_status_label.visible = _combat_overlay_visible
	if _target_marker != null:
		_target_marker.visible = _combat_overlay_visible and _targeted and current_health > 0
	if _turn_marker != null:
		_turn_marker.visible = _combat_overlay_visible and _turn_active and current_health > 0
