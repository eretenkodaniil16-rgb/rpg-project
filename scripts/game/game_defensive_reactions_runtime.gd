extends "res://scripts/game/game_all_reaction_prompts_runtime.gd"

const DEFENSIVE_REACTION_SYSTEM_SCRIPT: Script = preload("res://scripts/systems/defensive_reaction_system.gd")
const DEFENSIVE_ENEMY_GRID_STEP_FEET: int = 5

var _defensive_reactions: DefensiveReactionSystem = DEFENSIVE_REACTION_SYSTEM_SCRIPT.new() as DefensiveReactionSystem
var _defensive_resolution_in_progress: bool = false
var _shield_active: bool = false
var _shield_ac_bonus: int = 0
var _absorb_resistance_type: String = ""
var _absorb_bonus_pending: bool = false
var _absorb_bonus_ready: bool = false
var _absorb_bonus_type: String = ""
var _absorb_bonus_dice_count: int = 0
var _absorb_bonus_die_sides: int = 6


func _process(delta: float) -> void:
	super._process(delta)
	_apply_absorb_resistance_to_state()


func _begin_current_turn() -> void:
	var actor: Node = _turn_system.current_actor() if _turn_system != null and _turn_system.active else null
	if actor == player:
		_expire_shield_at_start_of_turn()
		_expire_absorb_resistance_at_start_of_turn()
		if _absorb_bonus_pending:
			_absorb_bonus_pending = false
			_absorb_bonus_ready = true
			show_combat_message(
				"Поглощённая стихия готова: первое рукопашное попадание добавит %dк%d урона %s." % [
					_absorb_bonus_dice_count,
					_absorb_bonus_die_sides,
					_absorb_bonus_type
				],
				true
			)
	super._begin_current_turn()


func _advance_combat_turn() -> void:
	var previous: Node = _turn_system.current_actor() if _turn_system != null and _turn_system.active else null
	if previous == player and _absorb_bonus_ready:
		_clear_absorb_bonus()
	super._advance_combat_turn()


func _run_enemy_turn(actor: Node) -> void:
	if not _turn_system.active or _turn_system.current_actor() != actor:
		return
	_enemy_turn_running = true
	_refresh_turn_interface()
	while _turn_system.active and _any_overlay_visible():
		await get_tree().process_frame
	await get_tree().create_timer(0.3).timeout
	var state: CombatantState = _state_for(actor)
	if not _srd_rules.can_take_action(state):
		_enemy_turn_running = false
		_advance_combat_turn()
		return
	if state.has_condition("grappled"):
		var escape_dc: int = _condition_save_dc(state, "grappled", 10)
		var escape: Dictionary = _srd_rules.resolve_d20_test(
			int(actor.call("get_initiative_modifier")) if actor.has_method("get_initiative_modifier") else 0,
			escape_dc
		)
		if bool(escape.get("success", false)):
			state.remove_condition("grappled")
			_release_grapples_for(actor)
		show_combat_message("%s пытается вырваться из захвата." % _target_name(actor), bool(escape.get("success", false)))
	else:
		var movement_feet: int = _srd_rules.effective_speed_feet(
			int(actor.call("get_combat_speed_feet")) if actor.has_method("get_combat_speed_feet") else 30,
			state
		)
		var preferred_distance: int = _enemy_preferred_distance_feet(actor)
		while (
			movement_feet >= DEFENSIVE_ENEMY_GRID_STEP_FEET
			and DistanceSystem.distance_feet((actor as Node2D).global_position, player.global_position) > preferred_distance
		):
			var cost: int = _move_enemy_srd_one_step(actor as Node2D, state)
			if cost <= 0 or cost > movement_feet:
				break
			movement_feet -= cost
			await _trigger_readied_attack_if_possible(actor)
			if not _target_is_valid(actor):
				break
			await get_tree().create_timer(0.1).timeout

		var action_used: bool = false
		if is_instance_valid(actor) and _target_is_valid(actor):
			action_used = await _try_enemy_spell_turn(actor)
		if action_used:
			await _wait_for_defensive_reaction_resolution()
		if (
			not action_used
			and is_instance_valid(actor)
			and _target_is_valid(actor)
			and DistanceSystem.distance_feet((actor as Node2D).global_position, player.global_position) <= DistanceSystem.MELEE_REACH_FEET
			and actor.has_method("perform_combat_turn_attack")
		):
			actor.call("perform_combat_turn_attack")
			await _wait_for_defensive_reaction_resolution()
			_update_status()
			await get_tree().create_timer(0.35).timeout
	_enemy_turn_running = false
	if not _player_combat_state.dead:
		_advance_combat_turn()


func _wait_for_defensive_reaction_resolution() -> void:
	while (
		_defensive_resolution_in_progress
		or (
			_reaction_choice_prompt != null
			and _reaction_choice_prompt.is_waiting_for_decision()
		)
	):
		await get_tree().process_frame


func _enemy_spell_definition(actor: Node) -> Dictionary:
	if actor == null or not actor.has_method("get_combat_spell_id"):
		return {}
	var spell_id: String = str(actor.call("get_combat_spell_id"))
	if spell_id.is_empty():
		return {}
	var spell: Dictionary = _spell_area_runtime.get_spell_definition(spell_id)
	if str(spell.get("effect", "")) not in ["area_saving_throw_spell", "auto_hit_spell"]:
		return {}
	return spell


func resolve_npc_attack(
	attacker: Node,
	attack_bonus: int,
	damage_die: int,
	damage_bonus: int,
	damage_type: String = "slashing"
) -> Dictionary:
	return await _resolve_npc_attack_with_reactions(
		attacker,
		attack_bonus,
		damage_die,
		damage_bonus,
		damage_type,
		-1,
		-1,
		-1
	)


func resolve_npc_attack_for_testing(
	attacker: Node,
	attack_total_override: int,
	natural_roll_override: int,
	damage_override: int,
	damage_type: String = "slashing"
) -> Dictionary:
	return await _resolve_npc_attack_with_reactions(
		attacker,
		0,
		6,
		0,
		damage_type,
		attack_total_override,
		natural_roll_override,
		damage_override
	)


func _resolve_npc_attack_with_reactions(
	attacker: Node,
	attack_bonus: int,
	damage_die: int,
	damage_bonus: int,
	damage_type: String,
	attack_total_override: int,
	natural_roll_override: int,
	damage_override: int
) -> Dictionary:
	if attacker == null or not (attacker is Node2D):
		return {"hit": false}
	var attacker_state: CombatantState = _state_for(attacker)
	var cover: Dictionary = _combat_environment.get_cover(
		(attacker as Node2D).global_position,
		player.global_position
	) if _combat_environment != null else {"bonus": 0, "total_cover": false}
	if bool(cover.get("total_cover", false)):
		show_combat_message("%s не видит героя за полным укрытием." % _target_name(attacker), false)
		return {"hit": false, "total_cover": true}
	var adjustments: Dictionary = _srd_rules.attack_roll_adjustments(
		attacker_state,
		_player_combat_state,
		DistanceSystem.distance_feet((attacker as Node2D).global_position, player.global_position),
		true,
		true
	)
	var mockery_disadvantage: bool = _consume_vicious_mockery_on_attack(attacker)
	var disadvantage: bool = bool(adjustments.get("disadvantage", false)) or player_is_dodging() or mockery_disadvantage
	var advantage: bool = bool(adjustments.get("advantage", false))
	var roll: Dictionary = _srd_rules.roll_d20(attack_bonus, advantage, disadvantage)
	var natural: int = clampi(
		natural_roll_override if natural_roll_override >= 1 else int(roll.get("natural", 1)),
		1,
		20
	)
	var attack_total: int = attack_total_override if attack_total_override >= 0 else int(roll.get("total", 0))
	var base_ac: int = _class_data.get_armor_class(GameState.player_character) + int(cover.get("bonus", 0))
	var target_ac: int = base_ac + (_shield_ac_bonus if _shield_active else 0)
	var hit: bool = natural != 1 and (natural == 20 or attack_total >= target_ac)
	if not hit:
		var miss_reason: String = " с помехой от Злой насмешки" if mockery_disadvantage else ""
		show_combat_message("%s промахивается%s: %d против КД %d." % [_target_name(attacker), miss_reason, attack_total, target_ac], false)
		return {"hit": false, "natural": natural, "total": attack_total, "target_ac": target_ac}

	var shield_resolution: Dictionary = {}
	if not _shield_active:
		shield_resolution = await _offer_shield_for_attack(attacker, attack_total, natural, base_ac)
		if bool(shield_resolution.get("resolved", false)):
			target_ac = base_ac + _shield_ac_bonus
			hit = natural == 20 or attack_total >= target_ac
			if not hit:
				show_combat_message("Щит отражает атаку %s: %d против КД %d." % [_target_name(attacker), attack_total, target_ac], true)
				return {
					"hit": false,
					"natural": natural,
					"total": attack_total,
					"target_ac": target_ac,
					"shield_used": true
				}

	var critical: bool = natural == 20 or bool(adjustments.get("automatic_critical", false))
	var damage: int = damage_override if damage_override >= 0 else damage_bonus
	if damage_override < 0:
		for _index: int in range(2 if critical else 1):
			damage += _srd_dice.roll_die(maxi(damage_die, 2))
	var absorption: Dictionary = await _offer_absorb_elements(damage, damage_type, attacker)
	var applied: Dictionary = apply_damage_to_player(damage, damage_type, critical, attacker)
	applied["vicious_mockery_disadvantage"] = mockery_disadvantage
	applied["shield_used"] = bool(shield_resolution.get("resolved", false))
	applied["absorb_elements_used"] = bool(absorption.get("resolved", false))
	applied["target_ac"] = target_ac
	return applied


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
		false,
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


func _resolve_enemy_auto_hit_spell(actor: Node, spell: Dictionary, slot_level: int) -> void:
	var damage: int = _roll_enemy_spell_damage(spell, slot_level)
	var spell_id: String = str(spell.get("id", ""))
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


func _roll_enemy_spell_damage(spell: Dictionary, slot_level: int) -> int:
	var dice_value: Variant = spell.get("damage_dice", [1, 6])
	var base_dice: Array[int] = [1, 6]
	if dice_value is Array and (dice_value as Array).size() >= 2:
		base_dice = [maxi(int((dice_value as Array)[0]), 1), maxi(int((dice_value as Array)[1]), 2)]
	var scaled_dice: Array[int] = _spell_area_runtime.scale_dice_for_slot(spell, base_dice, slot_level, "damage")
	var damage: int = _spell_area_runtime.damage_bonus_for_slot(spell, slot_level)
	for _index: int in range(scaled_dice[0]):
		damage += _srd_dice.roll_die(scaled_dice[1])
	return damage


func _offer_shield_for_attack(attacker: Node, attack_total: int, natural_roll: int, current_ac: int) -> Dictionary:
	var context: Dictionary = {
		"reactor": GameState.player_character,
		"reaction_available": _turn_system.has_reaction(player),
		"trigger_id": ReactionOpportunitySystem.TRIGGER_ATTACK_ROLL_HIT,
		"attack_hit": true,
		"attack_total": attack_total,
		"natural_roll": natural_roll,
		"current_ac": current_ac,
		"shield_already_active": _shield_active,
		"casting_context": _build_spellcasting_context()
	}
	var options: Array[Dictionary] = _reaction_opportunities.sort_options(
		_reaction_opportunities.collect_options(ReactionOpportunitySystem.TRIGGER_ATTACK_ROLL_HIT, context)
	)
	if options.is_empty() or _reaction_choice_prompt == null:
		return {}
	_defensive_resolution_in_progress = true
	var chosen_id: String = await _reaction_choice_prompt.request_reaction(
		"ПО ВАМ ПОПАЛИ",
		"%s попадает с результатом %d против КД %d. Выберите доступную реакцию до броска урона." % [
			_target_name(attacker),
			attack_total,
			current_ac
		],
		options
	)
	_defensive_resolution_in_progress = false
	if chosen_id != ReactionOpportunitySystem.OPTION_SHIELD:
		return {}
	var result: Dictionary = _reaction_opportunities.resolve_defensive_option(chosen_id, context)
	_apply_defensive_reaction_payment(result)
	if bool(result.get("resolved", false)):
		_activate_shield(int(result.get("armor_class_bonus", 5)))
	return result


func _offer_shield_for_magic_missile(attacker: Node, spell_name: String) -> Dictionary:
	var context: Dictionary = {
		"reactor": GameState.player_character,
		"reaction_available": _turn_system.has_reaction(player),
		"trigger_id": ReactionOpportunitySystem.TRIGGER_MAGIC_MISSILE_TARGETED,
		"current_ac": _class_data.get_armor_class(GameState.player_character),
		"shield_already_active": _shield_active,
		"casting_context": _build_spellcasting_context()
	}
	var options: Array[Dictionary] = _reaction_opportunities.sort_options(
		_reaction_opportunities.collect_options(ReactionOpportunitySystem.TRIGGER_MAGIC_MISSILE_TARGETED, context)
	)
	if options.is_empty() or _reaction_choice_prompt == null:
		return {}
	_defensive_resolution_in_progress = true
	var chosen_id: String = await _reaction_choice_prompt.request_reaction(
		"МАГИЧЕСКАЯ СТРЕЛА НАЦЕЛЕНА НА ВАС",
		"%s завершает «%s». Щит может полностью заблокировать все снаряды." % [_target_name(attacker), spell_name],
		options
	)
	_defensive_resolution_in_progress = false
	if chosen_id != ReactionOpportunitySystem.OPTION_SHIELD:
		return {}
	var result: Dictionary = _reaction_opportunities.resolve_defensive_option(chosen_id, context)
	_apply_defensive_reaction_payment(result)
	if bool(result.get("resolved", false)):
		_activate_shield(int(result.get("armor_class_bonus", 5)))
	return result


func _offer_absorb_elements(incoming_damage: int, damage_type: String, source: Node) -> Dictionary:
	var normalized_type: String = _normalize_defensive_damage_type(damage_type)
	var context: Dictionary = {
		"reactor": GameState.player_character,
		"reaction_available": _turn_system.has_reaction(player),
		"trigger_id": ReactionOpportunitySystem.TRIGGER_ELEMENTAL_DAMAGE_TAKEN,
		"incoming_damage": maxi(incoming_damage, 0),
		"damage_type": normalized_type,
		"same_absorption_active": _absorb_resistance_type == normalized_type and not normalized_type.is_empty(),
		"casting_context": _build_spellcasting_context()
	}
	var options: Array[Dictionary] = _reaction_opportunities.sort_options(
		_reaction_opportunities.collect_options(ReactionOpportunitySystem.TRIGGER_ELEMENTAL_DAMAGE_TAKEN, context)
	)
	if options.is_empty() or _reaction_choice_prompt == null:
		return {}
	_defensive_resolution_in_progress = true
	var chosen_id: String = await _reaction_choice_prompt.request_reaction(
		"ВЫ ПОЛУЧАЕТЕ СТИХИЙНЫЙ УРОН",
		"Источник %s должен нанести %d урона типа «%s». Реакция применяется до окончательного уменьшения HP." % [
			_target_name(source) if source != null else "неизвестен",
			incoming_damage,
			normalized_type
		],
		options
	)
	_defensive_resolution_in_progress = false
	if chosen_id != ReactionOpportunitySystem.OPTION_ABSORB_ELEMENTS:
		return {}
	var result: Dictionary = _reaction_opportunities.resolve_defensive_option(chosen_id, context)
	_apply_defensive_reaction_payment(result)
	if bool(result.get("resolved", false)):
		_activate_absorb_elements(
			str(result.get("damage_type", normalized_type)),
			int(result.get("bonus_dice_count", 1)),
			int(result.get("bonus_die_sides", 6))
		)
	return result


func _apply_defensive_reaction_payment(result: Dictionary) -> void:
	if bool(result.get("consume_reaction", false)):
		_turn_system.consume_reaction(player)
	if not str(result.get("message", "")).is_empty():
		show_combat_message(str(result.get("message", "Реакция разрешена.")), bool(result.get("resolved", false)))
	GameState.save_game()
	_update_status()


func _activate_shield(ac_bonus: int) -> void:
	_shield_active = true
	_shield_ac_bonus = maxi(ac_bonus, 0)


func _expire_shield_at_start_of_turn() -> void:
	_shield_active = false
	_shield_ac_bonus = 0


func _activate_absorb_elements(damage_type: String, dice_count: int, die_sides: int) -> void:
	_absorb_resistance_type = _normalize_defensive_damage_type(damage_type)
	_absorb_bonus_type = _absorb_resistance_type
	_absorb_bonus_dice_count = maxi(dice_count, 1)
	_absorb_bonus_die_sides = maxi(die_sides, 2)
	_absorb_bonus_pending = true
	_absorb_bonus_ready = false
	_apply_absorb_resistance_to_state()


func _apply_absorb_resistance_to_state() -> void:
	if _absorb_resistance_type.is_empty() or _player_combat_state == null:
		return
	if _absorb_resistance_type not in _player_combat_state.damage_resistances:
		_player_combat_state.damage_resistances.append(_absorb_resistance_type)


func _expire_absorb_resistance_at_start_of_turn() -> void:
	if not _absorb_resistance_type.is_empty() and _player_combat_state != null:
		_player_combat_state.damage_resistances.erase(_absorb_resistance_type)
	_absorb_resistance_type = ""


func _clear_absorb_bonus() -> void:
	_absorb_bonus_pending = false
	_absorb_bonus_ready = false
	_absorb_bonus_type = ""
	_absorb_bonus_dice_count = 0
	_absorb_bonus_die_sides = 6


func _perform_srd_weapon_attack(target: Node, weapon: Dictionary, ammo_id: String) -> void:
	if not _target_is_valid(target):
		return
	var target_position: Vector2 = (target as Node2D).global_position
	var distance: int = DistanceSystem.distance_feet(player.global_position, target_position)
	var context: Dictionary = _build_srd_attack_context(target, distance)
	context["no_ammunition"] = not ammo_id.is_empty() and not GameState.has_item(ammo_id)
	var result: AttackResult = _combat_system.perform_basic_attack(
		GameState.player_character,
		int(target.call("get_armor_class")),
		weapon,
		-1,
		[],
		context
	)
	if result.out_of_range or result.no_ammunition or (result.automatic_miss and not result.note.is_empty()):
		_attack_popup.show_result(result)
		_sync_exploration_hud_visibility()
		return
	_set_combat_busy(true)
	if not ammo_id.is_empty():
		GameState.remove_item(ammo_id, 1, false)
	if result.hit:
		var target_state: CombatantState = _state_for(target)
		_apply_mitigation_to_result(result, target_state)
		if _absorb_bonus_ready and not DistanceSystem.is_ranged_weapon(weapon):
			var raw_bonus: int = 0
			var dice_count: int = _absorb_bonus_dice_count * (2 if result.critical else 1)
			for _index: int in range(dice_count):
				raw_bonus += _srd_dice.roll_die(_absorb_bonus_die_sides)
			var bonus_mitigation: Dictionary = _srd_rules.resolve_damage(raw_bonus, _absorb_bonus_type, target_state)
			var applied_bonus: int = int(bonus_mitigation.get("applied", raw_bonus))
			result.damage_before_mitigation += raw_bonus
			result.damage += applied_bonus
			result.note = _append_srd_note(
				result.note,
				"Поглощение стихий добавляет %d урона %s%s." % [
					applied_bonus,
					_absorb_bonus_type,
					"; кости удвоены критическим попаданием" if result.critical else ""
				]
			)
			_clear_absorb_bonus()
	if DistanceSystem.is_ranged_weapon(weapon):
		await _play_weapon_projectile(weapon, target_position, result.hit)
	else:
		player.play_attack_animation(target_position)
	if _target_is_valid(target):
		target.call("receive_player_attack", result, true)
		if int(target.call("get_current_health")) <= 0:
			_release_grapples_for(target)
	GameState.save_game()
	_update_status()
	_set_combat_busy(false)
	_sync_exploration_hud_visibility()


func _normalize_defensive_damage_type(value: String) -> String:
	var normalized: String = value.strip_edges().to_lower()
	match normalized:
		"кислотный", "кислота": return "acid"
		"холод", "холодный": return "cold"
		"огонь", "огненный": return "fire"
		"электричество", "электрический", "молния": return "lightning"
		"звук", "звуковой", "гром": return "thunder"
		_: return normalized


func get_defensive_reaction_system_for_testing() -> DefensiveReactionSystem:
	return _defensive_reactions


func is_shield_active_for_testing() -> bool:
	return _shield_active


func get_shield_ac_bonus_for_testing() -> int:
	return _shield_ac_bonus


func get_absorb_resistance_type_for_testing() -> String:
	return _absorb_resistance_type


func is_absorb_bonus_pending_for_testing() -> bool:
	return _absorb_bonus_pending


func is_absorb_bonus_ready_for_testing() -> bool:
	return _absorb_bonus_ready
