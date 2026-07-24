class_name SpellCastAttempt
extends RefCounted

var caster: Node = null
var caster_name: String = "Заклинатель"
var caster_position: Vector2 = Vector2.ZERO
var caster_constitution_modifier: int = 0
var caster_state: CombatantState = null
var spell: Dictionary = {}
var slot_level: int = 0
var action_kind: String = "action"
var original_resource_key: String = ""
var original_resource_expended: bool = false
var countered: bool = false
var action_wasted: bool = false
var resolved: bool = false
var counterspell_save: Dictionary = {}


func _init(
	spell_definition: Dictionary = {},
	spell_caster: Node = null,
	spell_slot_level: int = 0
) -> void:
	spell = spell_definition.duplicate(true)
	caster = spell_caster
	slot_level = maxi(spell_slot_level, int(spell.get("spell_level", 0)))
	if is_instance_valid(caster):
		caster_name = str(caster.call("get_combat_name")) if caster.has_method("get_combat_name") else caster.name
		if caster is Node2D:
			caster_position = (caster as Node2D).global_position


func get_spell_id() -> String:
	return str(spell.get("id", ""))


func get_spell_name() -> String:
	return str(spell.get("name", "Заклинание"))


func has_observable_components() -> bool:
	var components_value: Variant = spell.get("components", [])
	if not components_value is Array:
		return false
	for component_value: Variant in components_value:
		if str(component_value).to_lower() in ["v", "s", "m"]:
			return true
	return false


func mark_countered(save_result: Dictionary) -> void:
	counterspell_save = save_result.duplicate(true)
	countered = true
	action_wasted = true
	resolved = true
	original_resource_expended = false


func mark_proceeds(save_result: Dictionary = {}) -> void:
	counterspell_save = save_result.duplicate(true)
	countered = false
	action_wasted = false
	resolved = true


func mark_original_resource_expended(resource_key: String = "") -> void:
	if countered:
		return
	original_resource_key = resource_key
	original_resource_expended = true


func should_expend_original_resource() -> bool:
	return not countered
