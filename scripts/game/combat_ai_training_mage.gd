class_name CombatAiTrainingMage
extends "res://scripts/game/stealth_patrol_observer.gd"

@export var spell_save_dc: int = 13
@export var spell_attack_bonus: int = 5
@export var level_one_spell_slots: int = 3
@export var combat_spell_ids: Array[String] = [
	"magic_missile",
	"ray_of_sickness",
	"burning_hands",
	"thunderwave",
	"sorcerous_burst"
]

var _remaining_level_one_slots: int = 3
var _selected_combat_spell_id: String = "sorcerous_burst"


func _ready() -> void:
	_remaining_level_one_slots = maxi(level_one_spell_slots, 0)
	super._ready()


func enter_combat_hostile() -> void:
	if not is_combat_participant_active():
		get_tree().call_group("stealth_world", "activate_tactical_training_squad")
	super.enter_combat_hostile()


func get_spell_save_dc() -> int:
	return maxi(spell_save_dc, 1)


func get_spell_attack_bonus() -> int:
	return spell_attack_bonus


func get_combat_spell_ids() -> Array[String]:
	return combat_spell_ids.duplicate()


func set_selected_combat_spell_id(spell_id: String) -> void:
	if spell_id in combat_spell_ids:
		_selected_combat_spell_id = spell_id


func get_combat_spell_id() -> String:
	return _selected_combat_spell_id


func get_combat_spell_slot_level() -> int:
	return 1


func get_combat_spell_slot_count(spell_level: int = 1) -> int:
	return _remaining_level_one_slots if spell_level == 1 else 0


func consume_combat_spell_slot(spell_level: int = 1) -> bool:
	if spell_level <= 0:
		return true
	if spell_level != 1 or _remaining_level_one_slots <= 0:
		return false
	_remaining_level_one_slots -= 1
	return true


func restore_combat_spell_slots() -> void:
	_remaining_level_one_slots = maxi(level_one_spell_slots, 0)


func reset_combat_state(full_restore: bool = true) -> void:
	super.reset_combat_state(full_restore)
	if full_restore:
		restore_combat_spell_slots()


func get_context_status_text() -> String:
	if is_body_interactable():
		return super.get_context_status_text()
	return "%s Роль: боевой маг. Оставшиеся ячейки определяются только по его поведению." % super.get_context_status_text()
