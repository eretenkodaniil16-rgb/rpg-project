extends "res://scripts/game/game_ai_stealth_v2_runtime.gd"

const PARTY_TARGET_ADAPTER_SCRIPT: Script = preload("res://scripts/systems/combat_ai_party_target_adapter.gd")

var _party_target_adapter_v3: CombatAiPartyTargetAdapter = PARTY_TARGET_ADAPTER_SCRIPT.new() as CombatAiPartyTargetAdapter


func _run_enemy_turn(actor: Node) -> void:
	if not _enemy_supports_party_targeting(actor):
		await super._run_enemy_turn(actor)
		return
	var target: Node = _select_enemy_party_target(actor)
	if not is_instance_valid(target) or target == player:
		await super._run_enemy_turn(actor)
		return
	await _run_enemy_turn_against_party_target_v3(actor, target)


func _select_enemy_party_target(actor: Node) -> Node:
	if not actor is Node2D:
		return player
	_reset_target_claims_if_needed_v2()
	var actor_node: Node2D = actor as Node2D
	var actor_instance_id: int = actor.get_instance_id()
	var actor_key: String = str(actor.call("get_actor_id")) if actor.has_method("get_actor_id") else ""
	var profile: Dictionary = _combat_ai.get_profile(actor_key) if _combat_ai != null and not actor_key.is_empty() else {}
	var role_id: String = str(profile.get("role", NpcCombatAiSystem.ROLE_MELEE))
	var attack_range: int = maxi(int(profile.get("attack_range_feet", DistanceSystem.MELEE_REACH_FEET)), DistanceSystem.MELEE_REACH_FEET)
	var minimum_range: int = maxi(int(profile.get("minimum_range_feet", 0)), 0)
	var preferred_range: int = clampi(int(profile.get("preferred_range_feet", attack_range)), minimum_range, attack_range)
	var previous_target_id: int = int(_enemy_party_target_by_actor_id.get(actor_instance_id, 0))
	var candidates: Array[Dictionary] = []
	for target: Node in _party_combat_targets_v3():
		if not _enemy_party_target_is_available(target):
			continue
		if not _enemy_can_see_party_target_from(actor_node.global_position, target):
			continue
		var distance: int = DistanceSystem.distance_feet(actor_node.global_position, (target as Node2D).global_position)
		var target_id: int = target.get_instance_id()
		candidates.append({
			"target": target,
			"target_id": target_id,
			"available": true,
			"visible": true,
			"distance_feet": distance,
			"attack_ready": distance <= attack_range and distance >= minimum_range,
			"preferred_range_feet": preferred_range,
			"health_ratio": _party_target_health_ratio_v3(target),
			"previous_target": target_id == previous_target_id,
			"claim_count": _claim_count_for_target_v2(target_id, actor_instance_id),
			"immediate_melee_threat": distance <= DistanceSystem.MELEE_REACH_FEET,
			"full_tactics_supported": _party_target_adapter_v3.is_supported(target, player),
			"role": role_id
		})
	if candidates.is_empty():
		_release_actor_target_claim_v2(actor_instance_id)
		_enemy_party_target_by_actor_id.erase(actor_instance_id)
		return player
	var selection: Dictionary = _tactical_targeting.choose_target(candidates, previous_target_id)
	var selected: Node = selection.get("target") as Node
	if not is_instance_valid(selected):
		selected = candidates[0].get("target") as Node
	_assign_actor_target_claim_v2(actor_instance_id, selected.get_instance_id())
	_enemy_party_target_by_actor_id[actor_instance_id] = selected.get_instance_id()
	_enemy_attack_range_by_actor_id[actor_instance_id] = attack_range
	_last_targeting_diagnostics_v2 = {
		"actor_id": actor_key,
		"selected_target_id": selected.get_instance_id(),
		"selected_target_name": _party_target_name_v3(selected),
		"selected_score": float(selection.get("utility_score", 0.0)),
		"candidate_count": candidates.size(),
		"round": _turn_system.round_number,
		"targeting_version": 3
	}
	return selected


func _enemy_party_target_is_available(target: Node) -> bool:
	return _party_target_adapter_v3.is_available(
		target,
		player,
		GameState.player_character as PlayerCharacter,
		_player_combat_state
	)


func _party_has_living_combatant() -> bool:
	for target: Node in _party_combat_targets_v3():
		if _enemy_party_target_is_available(target):
			return true
	return false


func _run_enemy_turn_against_party_target_v3(actor: Node, target: Node) -> void:
	if not actor is Node2D or not target is Node2D or not _turn_system.active or _turn_system.current_actor() != actor:
		return
	_enemy_turn_running = true
	_refresh_turn_interface()
	while _turn_system.active and _any_overlay_visible():
		await get_tree().process_frame
	await get_tree().create_timer(0.28).timeout

	if is_instance_valid(actor) and is_instance_valid(target) and (
		not actor.has_method("can_take_combat_turn") or bool(actor.call("can_take_combat_turn"))
	):
		var actor_node: Node2D = actor as Node2D
		var target_node: Node2D = target as Node2D
		var actor_id: String = str(actor.call("get_actor_id"))
		var profile: Dictionary = _advanced_ai.get_profile(actor_id) if _advanced_ai != null else _combat_ai.get_profile(actor_id)
		var attack_range: int = maxi(int(profile.get("attack_range_feet", DistanceSystem.MELEE_REACH_FEET)), DistanceSystem.MELEE_REACH_FEET)
		var minimum_range: int = maxi(int(profile.get("minimum_range_feet", 0)), 0)
		var preferred_range: int = clampi(int(profile.get("preferred_range_feet", attack_range)), minimum_range, attack_range)
		var movement_feet: int = int(actor.call("get_combat_speed_feet")) if actor.has_method("get_combat_speed_feet") else 30
		var target_visible: bool = _enemy_can_see_party_target_from(actor_node.global_position, target)
		var distance: int = DistanceSystem.distance_feet(actor_node.global_position, target_node.global_position)
		var spell_plan: Dictionary = _evaluate_spell_plan_for_target_v3(actor, profile, actor_node.global_position, target)
		var role_id: String = str(profile.get("role", NpcCombatAiSystem.ROLE_MELEE))
		var wants_spell: bool = role_id == AdvancedNpcCombatAiSystem.ROLE_CASTER and not spell_plan.is_empty()
		var attack_ready: bool = target_visible and distance <= attack_range and distance >= minimum_range

		if not attack_ready and movement_feet >= GRID_STEP_FEET:
			var plan: Dictionary = _plan_enemy_movement_to_party_target(
				actor_node,
				actor,
				target,
				movement_feet,
				attack_range,
				minimum_range,
				preferred_range
			)
			await _execute_combat_ai_path(actor_node, plan.get("path", []) as Array, NpcAiSystem.INTENT_ADVANCE)

		target_visible = _enemy_can_see_party_target_from(actor_node.global_position, target)
		distance = DistanceSystem.distance_feet(actor_node.global_position, target_node.global_position)
		attack_ready = target_visible and distance <= attack_range and distance >= minimum_range
		if wants_spell:
			spell_plan = _evaluate_spell_plan_for_target_v3(actor, profile, actor_node.global_position, target)
			if not spell_plan.is_empty():
				await _cast_enemy_spell_at_party_target_v3(actor, target, spell_plan)
			elif attack_ready and actor.has_method("perform_combat_turn_attack"):
				actor.call("perform_combat_turn_attack")
		elif attack_ready and actor.has_method("perform_combat_turn_attack"):
			actor.call("perform_combat_turn_attack")
		elif distance <= DistanceSystem.MELEE_REACH_FEET:
			_resolve_ai_shove_against_target_v3(actor_node, actor, target)
		else:
			_ai_dodge_until_round[actor.get_instance_id()] = _turn_system.round_number
			show_combat_message("%s удерживает позицию и готовится защищаться." % _target_name(actor), true)
		_update_status()
		await get_tree().create_timer(0.35).timeout

	_enemy_turn_running = false
	if _party_has_living_combatant():
		_advance_combat_turn()


func _evaluate_spell_plan_for_target_v3(
	actor: Node,
	profile: Dictionary,
	caster_position: Vector2,
	target: Node
) -> Dictionary:
	if actor == null or not actor.has_method("get_combat_spell_ids") or not target is Node2D:
		return {}
	var spell_ids: Array[String] = []
	var raw_spell_ids: Variant = actor.call("get_combat_spell_ids")
	if not raw_spell_ids is Array:
		return {}
	for value: Variant in raw_spell_ids as Array:
		spell_ids.append(str(value))
	var contexts: Dictionary = {}
	for spell_id: String in spell_ids:
		var spell: Dictionary = _npc_spell_selector.get_spell(spell_id)
		if spell.is_empty():
			continue
		contexts[spell_id] = _spell_option_context_for_target_v3(actor, spell, caster_position, target)
	var policy: Dictionary = {
		"friendly_fire_tolerance": int(profile.get("friendly_fire_tolerance", 0)),
		"slot_reserve": int(profile.get("slot_reserve", 0)),
		"slot_conservation": float(profile.get("slot_conservation", 0.55))
	}
	return _npc_spell_selector.choose_spell(spell_ids, contexts, policy)


func _spell_option_context_for_target_v3(
	actor: Node,
	spell: Dictionary,
	caster_position: Vector2,
	target: Node
) -> Dictionary:
	var target_position: Vector2 = (target as Node2D).global_position
	var distance: int = DistanceSystem.distance_feet(caster_position, target_position)
	var visible: bool = _combat_environment == null or _combat_environment.has_line_of_sight(caster_position, target_position)
	var spell_level: int = maxi(int(spell.get("spell_level", 0)), 0)
	var slots: int = int(actor.call("get_combat_spell_slot_count", spell_level)) if actor.has_method("get_combat_spell_slot_count") else (1 if spell_level == 0 else 0)
	var option: Dictionary = {
		"available": spell_level == 0 or slots > 0,
		"line_of_sight": visible,
		"distance_feet": distance,
		"slots_remaining": slots,
		"target_health_ratio": _party_target_health_ratio_v3(target),
		"target_wounded": _party_target_health_ratio_v3(target) < 1.0,
		"hostile_hits": 0,
		"friendly_hits": 0,
		"caster_hit": false,
		"expected_damage": _npc_spell_selector.expected_damage_for(spell),
		"control_value": _npc_spell_selector.control_value_for(spell)
	}
	var area_value: Variant = spell.get("area", {})
	if area_value is Dictionary and _advanced_spell_area.is_area_definition(area_value as Dictionary):
		var grid: BattleGrid = _get_battle_grid()
		if grid == null:
			return option
		var caster_cell: Vector2i = grid.world_to_cell(caster_position)
		var aim_cell: Vector2i = grid.world_to_cell(target_position)
		var cells: Array[Vector2i] = _advanced_spell_area.get_area_cells(
			grid,
			caster_cell,
			aim_cell,
			area_value as Dictionary,
			target_position - caster_position
		)
		var hostile_hits: int = 0
		for party_target: Node in _party_combat_targets_v3():
			if _enemy_party_target_is_available(party_target) and grid.world_to_cell((party_target as Node2D).global_position) in cells:
				hostile_hits += 1
		option["hostile_hits"] = hostile_hits
		option["caster_hit"] = caster_cell in cells
		var friendly_hits: int = 0
		for ally: Node in _living_ai_allies(actor):
			if ally is Node2D and grid.world_to_cell((ally as Node2D).global_position) in cells:
				friendly_hits += 1
		option["friendly_hits"] = friendly_hits
	else:
		var range_feet: int = maxi(int(spell.get("range_ft", 0)), 0)
		option["hostile_hits"] = 1 if visible and (range_feet <= 0 or distance <= range_feet) else 0
	return option


func _cast_enemy_spell_at_party_target_v3(actor: Node, target: Node, spell_plan: Dictionary) -> void:
	if spell_plan.is_empty() or not is_instance_valid(actor) or not is_instance_valid(target):
		return
	var spell_value: Variant = spell_plan.get("spell", {})
	if not spell_value is Dictionary:
		return
	var spell: Dictionary = spell_value as Dictionary
	if spell.is_empty():
		return
	var spell_level: int = maxi(int(spell.get("spell_level", 0)), 0)
	if spell_level > 0 and (
		not actor.has_method("consume_combat_spell_slot")
		or not bool(actor.call("consume_combat_spell_slot", spell_level))
	):
		return
	var slot_level: int = _enemy_spell_slot_level(actor, spell)
	var area_value: Variant = spell.get("area", {})
	if area_value is Dictionary and _advanced_spell_area.is_area_definition(area_value as Dictionary):
		_resolve_enemy_area_spell_against_party_v3(actor, target, spell, slot_level)
	else:
		_resolve_enemy_single_target_spell_v3(actor, target, spell, slot_level)
	GameState.save_game()
	_update_status()


func _resolve_enemy_single_target_spell_v3(
	actor: Node,
	target: Node,
	spell: Dictionary,
	_slot_level: int
) -> void:
	if not actor is Node2D or not target is Node2D:
		return
	var effect: String = str(spell.get("effect", ""))
	var target_state: CombatantState = _party_target_state_v3(target)
	var hit: bool = true
	if effect == "spell_attack":
		var cover: Dictionary = _combat_environment.get_cover((actor as Node2D).global_position, (target as Node2D).global_position) if _combat_environment != null else {"bonus": 0, "total_cover": false}
		var roll: Dictionary = _srd_rules.roll_d20(
			int(actor.call("get_spell_attack_bonus")) if actor.has_method("get_spell_attack_bonus") else 0,
			false,
			_party_target_is_dodging_v3(target)
		)
		var natural: int = int(roll.get("natural", 1))
		var target_ac: int = _party_target_armor_class_v3(target) + int(cover.get("bonus", 0))
		hit = not bool(cover.get("total_cover", false)) and natural != 1 and (natural == 20 or int(roll.get("total", 0)) >= target_ac)
	elif effect == "saving_throw_spell":
		var save_ability: String = str(spell.get("save_ability", "dexterity"))
		var save_dc: int = int(actor.call("get_spell_save_dc")) if actor.has_method("get_spell_save_dc") else 10
		var save: Dictionary = _srd_rules.resolve_saving_throw(
			save_ability,
			_party_target_save_modifier_v3(target, save_ability),
			save_dc,
			target_state
		)
		hit = not bool(save.get("success", false))
	if hit:
		_apply_party_target_damage_v3(target, _roll_enemy_spell_damage_v3(spell), str(spell.get("damage_type", "force")), actor, false)
		_apply_enemy_spell_condition_v3(target, actor, spell)
	show_combat_message(
		"%s применяет «%s» против %s: %s." % [
			_target_name(actor),
			str(spell.get("name", "Заклинание")),
			_party_target_name_v3(target),
			"цель поражена" if hit else "цель избегает эффекта"
		],
		hit
	)


func _resolve_enemy_area_spell_against_party_v3(
	actor: Node,
	aim_target: Node,
	spell: Dictionary,
	_slot_level: int
) -> void:
	if not actor is Node2D or not aim_target is Node2D:
		return
	var grid: BattleGrid = _get_battle_grid()
	var area_value: Variant = spell.get("area", {})
	if grid == null or not area_value is Dictionary:
		return
	var caster_position: Vector2 = (actor as Node2D).global_position
	var aim_position: Vector2 = (aim_target as Node2D).global_position
	var cells: Array[Vector2i] = _advanced_spell_area.get_area_cells(
		grid,
		grid.world_to_cell(caster_position),
		grid.world_to_cell(aim_position),
		area_value as Dictionary,
		aim_position - caster_position
	)
	var base_damage: int = _roll_enemy_spell_damage_v3(spell)
	var hit_count: int = 0
	for target: Node in _party_combat_targets_v3():
		if not _enemy_party_target_is_available(target):
			continue
		if grid.world_to_cell((target as Node2D).global_position) not in cells:
			continue
		var damage: int = base_damage
		var failed_save: bool = true
		if str(spell.get("effect", "")) == "area_saving_throw_spell":
			var save_ability: String = str(spell.get("save_ability", "dexterity"))
			var save_dc: int = int(actor.call("get_spell_save_dc")) if actor.has_method("get_spell_save_dc") else 10
			var save: Dictionary = _srd_rules.resolve_saving_throw(
				save_ability,
				_party_target_save_modifier_v3(target, save_ability),
				save_dc,
				_party_target_state_v3(target)
			)
			failed_save = not bool(save.get("success", false))
			if not failed_save:
				damage = int(floor(float(base_damage) * (0.5 if bool(spell.get("half_damage_on_save", true)) else 0.0)))
		if damage > 0:
			_apply_party_target_damage_v3(target, damage, str(spell.get("damage_type", "force")), actor, false)
		if failed_save:
			_apply_enemy_spell_condition_v3(target, actor, spell)
		hit_count += 1
	show_combat_message(
		"%s применяет «%s»: затронуто целей отряда — %d." % [
			_target_name(actor),
			str(spell.get("name", "Заклинание")),
			hit_count
		],
		hit_count > 0
	)


func _resolve_ai_shove_against_target_v3(actor_node: Node2D, actor: Node, target: Node) -> void:
	if not target is Node2D or DistanceSystem.distance_feet(actor_node.global_position, (target as Node2D).global_position) > DistanceSystem.MELEE_REACH_FEET:
		return
	var attack_modifier: int = int(actor.call("get_initiative_modifier")) if actor.has_method("get_initiative_modifier") else 0
	var defense_modifier: int = maxi(
		_party_target_save_modifier_v3(target, "strength"),
		_party_target_save_modifier_v3(target, "dexterity")
	)
	var attack_roll: Dictionary = _srd_rules.roll_d20(attack_modifier)
	var defense_roll: Dictionary = _srd_rules.roll_d20(defense_modifier)
	if int(attack_roll.get("total", 0)) <= int(defense_roll.get("total", 0)):
		show_combat_message("%s не удаётся сбить %s с ног." % [_target_name(actor), _party_target_name_v3(target)], false)
		return
	var state: CombatantState = _party_target_state_v3(target)
	if state != null:
		state.add_condition("prone", 1, actor.get_instance_id())
	show_combat_message("%s сбивает %s с ног." % [_target_name(actor), _party_target_name_v3(target)], true)


func resolve_npc_attack(
	attacker: Node,
	attack_bonus: int,
	damage_die: int,
	damage_bonus: int,
	damage_type: String = "slashing"
) -> Dictionary:
	var target: Node = _selected_party_target_for_attacker_v3(attacker)
	if not is_instance_valid(target) or target == player:
		return super.resolve_npc_attack(attacker, attack_bonus, damage_die, damage_bonus, damage_type)
	if not attacker is Node2D or not target is Node2D or not _enemy_party_target_is_available(target):
		return {"hit": false}
	var cover: Dictionary = _combat_environment.get_cover((attacker as Node2D).global_position, (target as Node2D).global_position) if _combat_environment != null else {"bonus": 0, "total_cover": false}
	if bool(cover.get("total_cover", false)):
		return {"hit": false, "total_cover": true}
	var attacker_state: CombatantState = _state_for(attacker)
	var defender_state: CombatantState = _party_target_state_v3(target)
	var distance: int = DistanceSystem.distance_feet((attacker as Node2D).global_position, (target as Node2D).global_position)
	var adjustments: Dictionary = _srd_rules.attack_roll_adjustments(attacker_state, defender_state, distance, true, true)
	var roll: Dictionary = _srd_rules.roll_d20(
		attack_bonus,
		bool(adjustments.get("advantage", false)),
		bool(adjustments.get("disadvantage", false)) or _party_target_is_dodging_v3(target)
	)
	var natural: int = int(roll.get("natural", 1))
	var target_ac: int = _party_target_armor_class_v3(target) + int(cover.get("bonus", 0))
	var hit: bool = natural != 1 and (natural == 20 or int(roll.get("total", 0)) >= target_ac)
	if not hit:
		show_combat_message("%s промахивается по %s: %d против КД %d." % [_target_name(attacker), _party_target_name_v3(target), int(roll.get("total", 0)), target_ac], false)
		return {"hit": false, "natural": natural, "total": int(roll.get("total", 0))}
	var critical: bool = natural == 20 or bool(adjustments.get("automatic_critical", false))
	var damage: int = damage_bonus
	for _die_index: int in range(2 if critical else 1):
		damage += _srd_dice.roll_die(maxi(damage_die, 2))
	var applied: int = _apply_party_target_damage_v3(target, maxi(damage, 0), damage_type, attacker, critical)
	show_combat_message("%s наносит %s %d урона." % [_target_name(attacker), _party_target_name_v3(target), applied], false)
	GameState.save_game()
	_update_status()
	return {"hit": true, "applied": applied, "critical": critical, "natural": natural}


func _apply_party_target_damage_v3(
	target: Node,
	raw_damage: int,
	damage_type: String,
	attacker: Node,
	critical_hit: bool
) -> int:
	if target == player:
		var player_result: Dictionary = apply_damage_to_player(raw_damage, damage_type, critical_hit, attacker)
		return int(player_result.get("applied", 0))
	var state: CombatantState = _party_target_state_v3(target)
	if state != null and state.dead:
		return 0
	if _party_target_adapter_v3.get_current_health(target, player, GameState.player_character as PlayerCharacter) <= 0:
		var zero_result: Dictionary = _srd_rules.damage_at_zero_hit_points(state, critical_hit)
		return int(zero_result.get("failures_added", 0))
	var mitigation: Dictionary = _srd_rules.resolve_damage(maxi(raw_damage, 0), damage_type, state)
	var applied: int = maxi(int(mitigation.get("applied", 0)), 0)
	var character: PlayerCharacter = GameState.player_character as PlayerCharacter
	var current: int = _party_target_adapter_v3.get_current_health(target, player, character)
	var next_health: int = maxi(current - applied, 0)
	_party_target_adapter_v3.set_current_health(target, next_health, player, character)
	if next_health <= 0:
		if target.has_method("enter_dying"):
			target.call("enter_dying")
		elif state != null:
			state.enter_dying()
	return applied


func _apply_enemy_spell_condition_v3(target: Node, actor: Node, spell: Dictionary) -> void:
	var condition_id: String = str(spell.get("on_hit_condition", ""))
	if condition_id.is_empty():
		return
	var state: CombatantState = _party_target_state_v3(target)
	if state != null:
		state.add_condition(condition_id, maxi(int(spell.get("on_hit_condition_rounds", 1)), 1), actor.get_instance_id())


func _roll_enemy_spell_damage_v3(spell: Dictionary) -> int:
	var damage: int = int(spell.get("damage_bonus", 0))
	var dice_value: Variant = spell.get("damage_dice", [1, 6])
	if dice_value is Array and (dice_value as Array).size() >= 2:
		for _index: int in range(maxi(int((dice_value as Array)[0]), 0)):
			damage += _srd_dice.roll_die(maxi(int((dice_value as Array)[1]), 2))
	return maxi(damage, 0)


func _party_combat_targets_v3() -> Array[Node]:
	var result: Array[Node] = []
	var seen: Dictionary = {}
	if is_instance_valid(player):
		result.append(player)
		seen[player.get_instance_id()] = true
	for target: Node in get_tree().get_nodes_in_group("controllable_allies"):
		if not is_instance_valid(target) or not target is Node2D or seen.has(target.get_instance_id()):
			continue
		if not _party_target_adapter_v3.is_supported(target, player):
			continue
		seen[target.get_instance_id()] = true
		result.append(target)
	return result


func _selected_party_target_for_attacker_v3(attacker: Node) -> Node:
	if not is_instance_valid(attacker):
		return null
	var selected_id: int = int(_enemy_party_target_by_actor_id.get(attacker.get_instance_id(), 0))
	if selected_id == 0:
		return null
	for target: Node in _party_combat_targets_v3():
		if target.get_instance_id() == selected_id:
			return target
	return null


func _party_target_health_ratio_v3(target: Node) -> float:
	return _party_target_adapter_v3.get_health_ratio(target, player, GameState.player_character as PlayerCharacter)


func _party_target_state_v3(target: Node) -> CombatantState:
	return _party_target_adapter_v3.get_combatant_state(target, player, _player_combat_state)


func _party_target_armor_class_v3(target: Node) -> int:
	var character: PlayerCharacter = GameState.player_character as PlayerCharacter
	var hero_ac: int = _class_data.get_armor_class(character) if character != null else 10
	return _party_target_adapter_v3.get_armor_class(target, player, hero_ac)


func _party_target_save_modifier_v3(target: Node, ability_id: String) -> int:
	return _party_target_adapter_v3.get_saving_throw_modifier(target, ability_id, player, GameState.player_character as PlayerCharacter)


func _party_target_is_dodging_v3(target: Node) -> bool:
	if target == player:
		return player_is_dodging()
	return bool(target.call("is_dodging")) if target.has_method("is_dodging") else false


func _party_target_name_v3(target: Node) -> String:
	return _party_target_adapter_v3.get_display_name(target, player)


func get_party_combat_target_ids_v3_for_testing() -> Array[String]:
	var result: Array[String] = []
	for target: Node in _party_combat_targets_v3():
		result.append(_party_target_adapter_v3.get_actor_id(target, player))
	return result


func get_party_target_snapshot_v3_for_testing(target: Node) -> Dictionary:
	return {
		"supported": _party_target_adapter_v3.is_supported(target, player),
		"available": _enemy_party_target_is_available(target),
		"actor_id": _party_target_adapter_v3.get_actor_id(target, player),
		"name": _party_target_name_v3(target),
		"health_ratio": _party_target_health_ratio_v3(target),
		"armor_class": _party_target_armor_class_v3(target),
		"dexterity_save": _party_target_save_modifier_v3(target, "dexterity")
	}


func evaluate_spell_plan_for_target_v3_for_testing(actor: Node, target: Node) -> Dictionary:
	if not actor is Node2D or not is_instance_valid(target):
		return {}
	var actor_id: String = str(actor.call("get_actor_id")) if actor.has_method("get_actor_id") else ""
	var profile: Dictionary = _advanced_ai.get_profile(actor_id) if _advanced_ai != null and not actor_id.is_empty() else {}
	return _evaluate_spell_plan_for_target_v3(actor, profile, (actor as Node2D).global_position, target)
