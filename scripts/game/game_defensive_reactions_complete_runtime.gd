extends "res://scripts/game/game_defensive_reactions_runtime.gd"


func _resolve_enemy_auto_hit_spell(actor: Node, spell: Dictionary, slot_level: int) -> void:
	var spell_id: String = str(spell.get("id", ""))
	if _shield_active and spell_id in ["magic_missile", "origin_magic_missile"]:
		show_combat_message("Уже действующий Щит полностью блокирует все снаряды Магической стрелы.", true)
		return
	await super._resolve_enemy_auto_hit_spell(actor, spell, slot_level)


func apply_elemental_damage_for_testing(amount: int, damage_type: String, source: Node = null) -> Dictionary:
	var absorption: Dictionary = await _offer_absorb_elements(amount, damage_type, source)
	var applied: Dictionary = apply_damage_to_player(amount, damage_type, false, source)
	applied["absorb_elements_used"] = bool(absorption.get("resolved", false))
	return applied


func resolve_magic_missile_damage_for_testing(amount: int, source: Node = null) -> Dictionary:
	if _shield_active:
		return {
			"blocked": true,
			"applied": 0,
			"shield_already_active": true
		}
	var shield_resolution: Dictionary = await _offer_shield_for_magic_missile(source, "Магическая стрела")
	if bool(shield_resolution.get("blocks_magic_missile", false)):
		return {
			"blocked": true,
			"applied": 0,
			"shield_used": true
		}
	var applied: Dictionary = apply_damage_to_player(amount, "force", false, source)
	applied["blocked"] = false
	return applied
