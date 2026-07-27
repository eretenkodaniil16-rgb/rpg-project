extends "res://scripts/game/game_defensive_reactions_complete_runtime.gd"

const DAMAGE_FALL_REACTION_SYSTEM_SCRIPT: Script = preload("res://scripts/systems/damage_fall_reaction_system.gd")

var _damage_fall_reactions: DamageFallReactionSystem = DAMAGE_FALL_REACTION_SYSTEM_SCRIPT.new() as DamageFallReactionSystem
var _hellish_rebuke_save_overrides: Array[int] = []
var _hellish_rebuke_damage_overrides: Array[int] = []


func resolve_npc_attack(
	attacker: Node,
	attack_bonus: int,
	damage_die: int,
	damage_bonus: int,
	damage_type: String = "slashing"
) -> Dictionary:
	var result: Dictionary = await super.resolve_npc_attack(attacker, attack_bonus, damage_die, damage_bonus, damage_type)
	await _offer_hellish_rebuke_after_damage(attacker, int(result.get("applied", 0)))
	return result


func resolve_npc_attack_for_testing(
	attacker: Node,
	attack_total_override: int,
	natural_roll_override: int,
	damage_override: int,
	damage_type: String = "slashing"
) -> Dictionary:
	var result: Dictionary = await super.resolve_npc_attack_for_testing(
		attacker,
		attack_total_override,
		natural_roll_override,
		damage_override,
		damage_type
	)
	await _offer_hellish_rebuke_after_damage(attacker, int(result.get("applied", 0)))
	return result


func _resolve_enemy_area_spell(actor: Node, spell: Dictionary, slot_level: int) -> void:
	if str(spell.get("effect", "")) == "auto_hit_spell":
		await _resolve_enemy_auto_hit_spell(actor, spell, slot_level)
		return
	var save_ability: String = str(spell.get("save_ability", "dexterity"))
	var save_modifier: int = GameState.player_character.get_ability_modifier(save_ability)
	if GameState.player_character.has_method("get_saving_throw_modifier"):
		save_modifier = int(GameState.player_character.call("get_saving_throw_modifier", save_ability))
	var save_dc: int = int(actor.call("get_spell_save_dc")) if actor.has_method("get_spell_save_dc") else 10
	var save_result: Dictionary = _srd_rules.resolve_saving_throw(
		save_ability,
		save_modifier,
		save_dc,
		_player_combat_state,
		false,
		_player_has_untrained_armor_d20_disadvantage(save_ability),
		[],
		{"magical": true, "spell_id": str(spell.get("id", ""))}
	)
	var damage: int = _roll_enemy_spell_damage(spell, slot_level)
	if bool(save_result.get("success", false)) and bool(spell.get("save_for_half", false)):
		damage = floori(float(damage) / 2.0)
	var absorption: Dictionary = await _offer_absorb_elements(damage, str(spell.get("damage_type", "force")), actor)
	var applied: Dictionary = apply_damage_to_player(damage, str(spell.get("damage_type", "force")), false, actor)
	show_combat_message(
		"%s: спасбросок %s %d против Сл %d; получено %d урона%s." % [
			str(spell.get("name", "Заклинание")),
			save_ability,
			int(save_result.get("total", 0)),
			save_dc,
			int(applied.get("applied", damage)),
			" после Поглощения стихий" if bool(absorption.get("resolved", false)) else ""
		],
		bool(save_result.get("success", false))
	)
	await _offer_hellish_rebuke_after_damage(actor, int(applied.get("applied", 0)))


func _resolve_enemy_auto_hit_spell(actor: Node, spell: Dictionary, slot_level: int) -> void:
	var spell_id: String = str(spell.get("id", ""))
	if _shield_active and spell_id in ["magic_missile", "origin_magic_missile"]:
		show_combat_message("Уже действующий Щит полностью блокирует все снаряды Магической стрелы.", true)
		return
	var damage: int = _roll_enemy_spell_damage(spell, slot_level)
	if spell_id in ["magic_missile", "origin_magic_missile"]:
		var shield_resolution: Dictionary = await _offer_shield_for_magic_missile(actor, str(spell.get("name", "Магическая стрела")))
		if bool(shield_resolution.get("blocks_magic_missile", false)):
			show_combat_message("Щит полностью блокирует все снаряды Магической стрелы.", true)
			return
	var absorption: Dictionary = await _offer_absorb_elements(damage, str(spell.get("damage_type", "force")), actor)
	var applied: Dictionary = apply_damage_to_player(damage, str(spell.get("damage_type", "force")), false, actor)
	show_combat_message(
		"%s автоматически поражает героя: получено %d урона%s." % [
			str(spell.get("name", "Заклинание")),
			int(applied.get("applied", damage)),
			" после Поглощения стихий" if bool(absorption.get("resolved", false)) else ""
		],
		false
	)
	await _offer_hellish_rebuke_after_damage(actor, int(applied.get("applied", 0)))


func _offer_hellish_rebuke_after_damage(source: Node, damage_applied: int) -> Dictionary:
	if damage_applied <= 0 or not is_instance_valid(source) or not (source is Node2D):
		return {}
	var distance_feet: int = DistanceSystem.distance_feet(player.global_position, (source as Node2D).global_position)
	var can_see_source: bool = true
	if _combat_environment != null:
		can_see_source = _combat_environment.has_line_of_sight(player.global_position, (source as Node2D).global_position)
	var source_is_creature: bool = source.is_in_group("combat_targets") or source.has_method("get_combat_name")
	var save_overrides: Array[int] = _hellish_rebuke_save_overrides.duplicate()
	var damage_overrides: Array[int] = _hellish_rebuke_damage_overrides.duplicate()
	_hellish_rebuke_save_overrides.clear()
	_hellish_rebuke_damage_overrides.clear()
	if source.has_method("get_hellish_rebuke_save_roll_overrides"):
		var source_save_overrides: Variant = source.call("get_hellish_rebuke_save_roll_overrides")
		if source_save_overrides is Array:
			save_overrides.clear()
			for value: Variant in source_save_overrides as Array:
				save_overrides.append(int(value))
	var context: Dictionary = {
		"reactor": GameState.player_character,
		"reaction_available": _turn_system.has_reaction(player),
		"reactor_can_react": not _player_combat_state.dead and GameState.player_character.current_health > 0,
		"trigger_id": ReactionOpportunitySystem.TRIGGER_CREATURE_DAMAGE_RECEIVED,
		"damage_applied": damage_applied,
		"source_is_creature": source_is_creature,
		"can_see_source": can_see_source,
		"distance_feet": distance_feet,
		"casting_context": _build_spellcasting_context(),
		"target_name": _target_name(source),
		"target_state": _state_for(source),
		"target_dexterity_save_modifier": int(source.call("get_saving_throw_modifier", "dexterity")) if source.has_method("get_saving_throw_modifier") else 0,
		"save_roll_overrides": save_overrides,
		"damage_roll_overrides": damage_overrides
	}
	var options: Array[Dictionary] = _reaction_opportunities.sort_options(
		_reaction_opportunities.collect_options(ReactionOpportunitySystem.TRIGGER_CREATURE_DAMAGE_RECEIVED, context)
	)
	if options.is_empty() or _reaction_choice_prompt == null:
		return {}
	_defensive_resolution_in_progress = true
	var chosen_id: String = await _reaction_choice_prompt.request_reaction(
		"ВАМ НАНЕСЛИ УРОН",
		"%s наносит вам %d урона на расстоянии %d футов. Можно немедленно ответить реакцией." % [
			_target_name(source),
			damage_applied,
			distance_feet
		],
		options
	)
	_defensive_resolution_in_progress = false
	if chosen_id != ReactionOpportunitySystem.OPTION_HELLISH_REBUKE:
		return {}
	var result: Dictionary = _reaction_opportunities.resolve_damage_fall_option(chosen_id, context)
	if bool(result.get("consume_reaction", false)):
		_turn_system.consume_reaction(player)
	var attack_result: AttackResult = result.get("result") as AttackResult
	if bool(result.get("resolved", false)) and attack_result != null and _target_is_valid(source):
		_apply_mitigation_to_result(attack_result, _state_for(source))
		source.call("receive_player_attack", attack_result, true)
		if source.has_method("get_current_health") and int(source.call("get_current_health")) <= 0:
			_release_grapples_for(source)
	if not str(result.get("message", "")).is_empty():
		show_combat_message(str(result.get("message", "Адское возмездие разрешено.")), bool(result.get("resolved", false)))
	GameState.save_game()
	_update_status()
	return result


func resolve_player_fall(distance_feet: int, damage_roll_overrides: Array[int] = []) -> Dictionary:
	var safe_distance: int = maxi(distance_feet, 0)
	var dice_count: int = mini(floori(float(safe_distance) / 10.0), 20)
	if dice_count <= 0:
		return {"distance_feet": safe_distance, "rolled_damage": 0, "applied": 0, "slow_fall_used": false}
	var rolled_damage: int = 0
	for index: int in range(dice_count):
		if index < damage_roll_overrides.size():
			rolled_damage += clampi(damage_roll_overrides[index], 1, 6)
		else:
			rolled_damage += _srd_dice.roll_die(6)
	var reaction_available: bool = true if not _turn_system.active else _turn_system.has_reaction(player)
	var context: Dictionary = {
		"reactor": GameState.player_character,
		"reaction_available": reaction_available,
		"reactor_can_react": not _player_combat_state.dead and GameState.player_character.current_health > 0,
		"trigger_id": ReactionOpportunitySystem.TRIGGER_FALL_DAMAGE_PENDING,
		"pending_fall_damage": rolled_damage,
		"fall_distance_feet": safe_distance
	}
	var options: Array[Dictionary] = _reaction_opportunities.sort_options(
		_reaction_opportunities.collect_options(ReactionOpportunitySystem.TRIGGER_FALL_DAMAGE_PENDING, context)
	)
	var slow_fall_result: Dictionary = {}
	if not options.is_empty() and _reaction_choice_prompt != null:
		_defensive_resolution_in_progress = true
		var chosen_id: String = await _reaction_choice_prompt.request_reaction(
			"ВЫ ПАДАЕТЕ",
			"Падение с высоты %d футов должно нанести %d дробящего урона. Выберите реакцию до приземления." % [safe_distance, rolled_damage],
			options
		)
		_defensive_resolution_in_progress = false
		if chosen_id == ReactionOpportunitySystem.OPTION_SLOW_FALL:
			slow_fall_result = _reaction_opportunities.resolve_damage_fall_option(chosen_id, context)
			if bool(slow_fall_result.get("consume_reaction", false)) and _turn_system.active:
				_turn_system.consume_reaction(player)
			if not str(slow_fall_result.get("message", "")).is_empty():
				show_combat_message(str(slow_fall_result.get("message", "Медленное падение разрешено.")), true)
	var final_damage: int = int(slow_fall_result.get("final_damage", rolled_damage))
	var applied: Dictionary = apply_damage_to_player(final_damage, "bludgeoning", false, null)
	if int(applied.get("applied", final_damage)) > 0 and _player_combat_state != null:
		_player_combat_state.add_condition("prone")
	elif _player_combat_state != null:
		_player_combat_state.remove_condition("prone")
	applied["distance_feet"] = safe_distance
	applied["rolled_damage"] = rolled_damage
	applied["slow_fall_used"] = bool(slow_fall_result.get("resolved", false))
	applied["slow_fall_reduction"] = int(slow_fall_result.get("reduction", 0))
	_refresh_srd_interface()
	return applied


func resolve_player_fall_for_testing(distance_feet: int, damage_roll_overrides: Array[int] = []) -> Dictionary:
	return await resolve_player_fall(distance_feet, damage_roll_overrides)


func set_hellish_rebuke_testing_overrides(save_rolls: Array[int], damage_rolls: Array[int]) -> void:
	_hellish_rebuke_save_overrides = save_rolls.duplicate()
	_hellish_rebuke_damage_overrides = damage_rolls.duplicate()


func get_damage_fall_reaction_system_for_testing() -> DamageFallReactionSystem:
	return _damage_fall_reactions
