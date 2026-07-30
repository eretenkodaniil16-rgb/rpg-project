extends "res://scripts/game/game_corpse_interactions_runtime.gd"

const ADVANCED_AI_SCRIPT: Script = preload("res://scripts/systems/advanced_npc_combat_ai_system.gd")
const CASUALTY_AI_SCRIPT: Script = preload("res://scripts/systems/npc_casualty_awareness_system.gd")
const SPELL_SELECTOR_SCRIPT: Script = preload("res://scripts/systems/npc_spell_selection_system.gd")

const ADVANCED_MOVEMENT_INTENTS: Array[String] = [
	NpcAiSystem.INTENT_ADVANCE,
	NpcAiSystem.INTENT_RETREAT,
	NpcCombatAiSystem.INTENT_REPOSITION,
	NpcCombatAiSystem.INTENT_INTERCEPT,
	NpcCombatAiSystem.INTENT_SEARCH,
	NpcCombatAiSystem.INTENT_GUARD,
	AdvancedNpcCombatAiSystem.INTENT_CAST_SPELL,
	AdvancedNpcCombatAiSystem.INTENT_TAKE_COVER,
	AdvancedNpcCombatAiSystem.INTENT_REGROUP
]

var _advanced_ai: AdvancedNpcCombatAiSystem
var _casualty_ai: NpcCasualtyAwarenessSystem = CASUALTY_AI_SCRIPT.new() as NpcCasualtyAwarenessSystem
var _npc_spell_selector: NpcSpellSelectionSystem = SPELL_SELECTOR_SCRIPT.new() as NpcSpellSelectionSystem
var _advanced_spell_area: SpellAreaSystem = SpellAreaSystem.new()
var _ai_dodge_until_round: Dictionary = {}
var _preplanned_ai_turns: Dictionary = {}


func _ready() -> void:
	super._ready()
	_advanced_ai = ADVANCED_AI_SCRIPT.new() as AdvancedNpcCombatAiSystem
	_combat_ai = _advanced_ai
	_npc_ai = _advanced_ai


func _process(delta: float) -> void:
	var combat_before: bool = _turn_system.active
	super._process(delta)
	if combat_before and not _turn_system.active:
		_casualty_ai.clear()
		_ai_dodge_until_round.clear()
		_preplanned_ai_turns.clear()


func _build_srd_attack_context(target: Node, distance: int) -> Dictionary:
	var context: Dictionary = super._build_srd_attack_context(target, distance)
	if is_instance_valid(target) and int(_ai_dodge_until_round.get(target.get_instance_id(), -1)) >= _turn_system.round_number:
		context["disadvantage"] = true
		context["defender_dodging"] = true
	return context


func _run_enemy_turn(actor: Node) -> void:
	if actor == null or not actor.has_method("get_actor_id") or _advanced_ai == null or not _advanced_ai.has_profile(str(actor.call("get_actor_id"))):
		await super._run_enemy_turn(actor)
		return
	if not (actor is Node2D) or not _turn_system.active or _turn_system.current_actor() != actor:
		return

	_enemy_turn_running = true
	_refresh_turn_interface()
	while _turn_system.active and _any_overlay_visible():
		await get_tree().process_frame
	await get_tree().create_timer(0.28).timeout

	if is_instance_valid(actor) and (not actor.has_method("can_take_combat_turn") or bool(actor.call("can_take_combat_turn"))):
		var actor_node: Node2D = actor as Node2D
		var actor_id: String = str(actor.call("get_actor_id"))
		var profile: Dictionary = _advanced_ai.get_profile(actor_id)
		var guard_anchor: Vector2 = _ensure_combat_ai_guard_anchor(actor_id, actor_node.global_position)
		var casualty_observation: Dictionary = _observe_allied_bodies(actor_node, actor_id, profile)
		var target_visible: bool = _combat_ai_can_see_player_from(actor_node.global_position)
		if target_visible:
			_record_combat_ai_target_sighting(actor_id, profile, player.global_position)
		var target_memory: Dictionary = _get_combat_ai_target_memory(actor_id, profile)
		var has_target_memory: bool = not target_memory.is_empty()
		var perceived_target_position: Vector2 = player.global_position if target_visible else (target_memory.get("position", guard_anchor) as Vector2 if has_target_memory else guard_anchor)
		var context: Dictionary = _build_combat_ai_context(actor_node, actor, profile, guard_anchor, perceived_target_position, target_visible, target_memory)
		_enrich_advanced_context(context, actor_node, actor, actor_id, profile, casualty_observation)

		var movement_feet: int = int(actor.call("get_combat_speed_feet")) if actor.has_method("get_combat_speed_feet") else 30
		var preplan: Dictionary = {}
		if str(profile.get("role", "")) == AdvancedNpcCombatAiSystem.ROLE_CASTER and movement_feet >= GRID_STEP_FEET:
			preplan = _plan_combat_ai_movement(actor_node, actor, profile, guard_anchor, perceived_target_position, AdvancedNpcCombatAiSystem.INTENT_CAST_SPELL, movement_feet)
			context["spell_plan_score"] = float(preplan.get("score", NpcCombatAiSystem.BLOCKED_SCORE))
			context["no_useful_attack"] = preplan.is_empty()

		var intent: Dictionary = _advanced_ai.choose_combat_intent(actor_id, context)
		var intent_id: String = str(intent.get("intent", NpcAiSystem.INTENT_WAIT))
		var attack_range_feet: int = int(intent.get("attack_range_feet", DistanceSystem.MELEE_REACH_FEET))
		var selected_plan: Dictionary = preplan if intent_id == AdvancedNpcCombatAiSystem.INTENT_CAST_SPELL and not preplan.is_empty() else {}

		if intent_id in ADVANCED_MOVEMENT_INTENTS and movement_feet >= GRID_STEP_FEET:
			var objective_position: Vector2 = _objective_for_advanced_intent(actor, guard_anchor, perceived_target_position, intent_id)
			if selected_plan.is_empty():
				selected_plan = _plan_combat_ai_movement(actor_node, actor, profile, guard_anchor, objective_position, intent_id, movement_feet)
			await _execute_combat_ai_path(actor_node, selected_plan.get("path", []) as Array, intent_id)

		match intent_id:
			AdvancedNpcCombatAiSystem.INTENT_RALLY:
				_resolve_ai_rally(actor, profile)
			AdvancedNpcCombatAiSystem.INTENT_DODGE:
				_ai_dodge_until_round[actor.get_instance_id()] = _turn_system.round_number
				show_combat_message("%s принимает защитную стойку и затрудняет атаки до своего следующего хода." % _target_name(actor), true)
			AdvancedNpcCombatAiSystem.INTENT_SHOVE:
				_resolve_ai_shove(actor_node, actor)
			AdvancedNpcCombatAiSystem.INTENT_CAST_SPELL:
				var spell_plan: Dictionary = selected_plan.get("spell_plan", {}) as Dictionary if selected_plan.get("spell_plan", {}) is Dictionary else _evaluate_spell_plan(actor, profile, actor_node.global_position)
				if not spell_plan.is_empty() and actor.has_method("set_selected_combat_spell_id"):
					actor.call("set_selected_combat_spell_id", str(spell_plan.get("spell_id", "")))
					await _try_enemy_spell_turn(actor)
			NpcAiSystem.INTENT_WAIT:
				show_combat_message("%s удерживает позицию и наблюдает за изменением боя." % _target_name(actor), true)

		var visible_after: bool = _combat_ai_can_see_player_from(actor_node.global_position)
		if visible_after:
			_record_combat_ai_target_sighting(actor_id, profile, player.global_position)
		elif intent_id == NpcCombatAiSystem.INTENT_SEARCH and has_target_memory:
			var searched_position: Vector2 = target_memory.get("position", perceived_target_position) as Vector2
			if DistanceSystem.distance_feet(actor_node.global_position, searched_position) <= DistanceSystem.MELEE_REACH_FEET:
				_invalidate_combat_ai_target_memory(actor_id, profile, searched_position)

		var action_intents: Array[String] = [
			AdvancedNpcCombatAiSystem.INTENT_CAST_SPELL,
			AdvancedNpcCombatAiSystem.INTENT_RALLY,
			AdvancedNpcCombatAiSystem.INTENT_DODGE,
			AdvancedNpcCombatAiSystem.INTENT_SHOVE
		]
		var distance_after: int = DistanceSystem.distance_feet(actor_node.global_position, player.global_position)
		if intent_id not in action_intents and intent_id not in [NpcAiSystem.INTENT_RETREAT, NpcAiSystem.INTENT_WAIT, NpcCombatAiSystem.INTENT_GUARD] and visible_after and distance_after <= attack_range_feet:
			if actor.has_method("perform_combat_turn_attack"):
				actor.call("perform_combat_turn_attack")
				_update_status()
				await get_tree().create_timer(0.35).timeout

	_enemy_turn_running = false
	var character: PlayerCharacter = GameState.player_character as PlayerCharacter
	if character != null and character.current_health > 0:
		_advance_combat_turn()


func _enrich_advanced_context(context: Dictionary, actor_node: Node2D, actor: Node, actor_id: String, profile: Dictionary, observation: Dictionary) -> void:
	var squad_id: String = str(profile.get("squad_id", ""))
	var casualty_context: Dictionary = _casualty_ai.get_context(actor_id, squad_id, _turn_system.round_number)
	var rally_active: bool = bool(casualty_context.get("rally_active", false))
	context["new_casualty_seen"] = bool(observation.get("new", false))
	context["casualty_count"] = int(casualty_context.get("casualty_count", 0))
	context["rally_active"] = rally_active
	context["defeated_ally_count"] = maxi(int(context.get("defeated_ally_count", 0)) - (1 if rally_active else 0), 0)
	context["nearest_ally_distance_feet"] = _nearest_combat_ai_ally_distance(actor, actor_node.global_position)
	context["can_shove"] = DistanceSystem.distance_feet(actor_node.global_position, player.global_position) <= DistanceSystem.MELEE_REACH_FEET
	context["target_prone"] = _player_combat_state.has_condition("prone")
	context["can_dodge"] = true
	context["no_safe_retreat"] = int(context.get("escape_route_count", 0)) <= 1
	context["better_cover_available"] = _better_cover_available(actor_node, actor)
	context["target_near_hazard"] = _target_near_blocked_edge()
	context["no_useful_attack"] = not bool(context.get("can_attack", false)) and not bool(context.get("has_target_memory", false))
	if str(profile.get("role", "")) == AdvancedNpcCombatAiSystem.ROLE_CASTER:
		var spell_plan: Dictionary = _evaluate_spell_plan(actor, profile, actor_node.global_position)
		context["spell_plan_score"] = float(spell_plan.get("score", NpcCombatAiSystem.BLOCKED_SCORE))


func _observe_allied_bodies(actor: Node2D, actor_id: String, profile: Dictionary) -> Dictionary:
	var squad_id: String = str(profile.get("squad_id", ""))
	if squad_id.is_empty():
		return {"new": false}
	var awareness_feet: int = maxi(int(profile.get("corpse_awareness_feet", 60)), 0)
	var newest: Dictionary = {"new": false}
	for body: Node in get_tree().get_nodes_in_group("visible_bodies"):
		if not is_instance_valid(body) or body == actor or not (body is Node2D):
			continue
		if not body.has_method("is_dead_body") or not bool(body.call("is_dead_body")):
			continue
		var body_actor_id: String = str(body.call("get_body_actor_id")) if body.has_method("get_body_actor_id") else ""
		if body_actor_id.is_empty() or body_actor_id == actor_id:
			continue
		var body_profile: Dictionary = _advanced_ai.get_profile(body_actor_id)
		var same_squad: bool = not body_profile.is_empty() and str(body_profile.get("squad_id", "")) == squad_id
		var body_position: Vector2 = (body as Node2D).global_position
		var visible: bool = DistanceSystem.distance_feet(actor.global_position, body_position) <= awareness_feet and (_combat_environment == null or _combat_environment.has_line_of_sight(actor.global_position, body_position))
		var event: Dictionary = _casualty_ai.observe_body(actor_id, squad_id, "corpse_%s" % body_actor_id, body_actor_id, body_position, _turn_system.round_number, visible, same_squad)
		if bool(event.get("new", false)):
			newest = event
			show_combat_message("%s замечает тело союзника и меняет тактику." % _target_name(actor), false)
	return newest


func _plan_combat_ai_movement(actor_node: Node2D, actor: Node, profile: Dictionary, guard_anchor: Vector2, objective_position: Vector2, intent_id: String, movement_feet: int) -> Dictionary:
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return {"path": [], "score": NpcCombatAiSystem.BLOCKED_SCORE}
	var candidates: Array[Dictionary] = _build_combat_ai_reachable_candidates(actor_node, movement_feet)
	var selected: Dictionary = {}
	var selected_score: float = NpcCombatAiSystem.BLOCKED_SCORE
	for candidate: Dictionary in candidates:
		var cell: Vector2i = candidate.get("cell", grid.world_to_cell(actor_node.global_position)) as Vector2i
		var position: Vector2 = grid.cell_to_world_center(cell)
		var target_visible: bool = _combat_ai_can_see_player_from(position)
		var distance_to_player: int = DistanceSystem.distance_feet(position, player.global_position)
		var cover: Dictionary = _combat_environment.get_cover(player.global_position, position) if _combat_environment != null else {"bonus": 0, "total_cover": false}
		var spell_plan: Dictionary = _evaluate_spell_plan(actor, profile, position) if str(profile.get("role", "")) == AdvancedNpcCombatAiSystem.ROLE_CASTER else {}
		var candidate_context: Dictionary = {
			"valid": not bool(cover.get("total_cover", false)) or intent_id in [NpcAiSystem.INTENT_RETREAT, AdvancedNpcCombatAiSystem.INTENT_TAKE_COVER],
			"distance_feet": distance_to_player if target_visible else DistanceSystem.distance_feet(position, objective_position),
			"distance_to_objective_feet": DistanceSystem.distance_feet(position, objective_position),
			"distance_from_guard_anchor_feet": DistanceSystem.distance_feet(position, guard_anchor),
			"nearest_ally_distance_feet": _nearest_combat_ai_ally_distance(actor, position),
			"mobility": _combat_ai_mobility_from(actor_node, position),
			"path_cost_feet": int(candidate.get("cost_feet", 0)),
			"target_visible": target_visible,
			"attack_ready": target_visible and distance_to_player <= int(profile.get("attack_range_feet", DistanceSystem.MELEE_REACH_FEET)),
			"cover_bonus": int(cover.get("bonus", 0)),
			"spell_plan_score": float(spell_plan.get("score", NpcCombatAiSystem.BLOCKED_SCORE))
		}
		var score: float = _advanced_ai.score_candidate_position(intent_id, profile, {}, candidate_context)
		candidate["score"] = score
		candidate["world_position"] = position
		candidate["spell_plan"] = spell_plan
		if _combat_ai_candidate_is_better(candidate, score, selected, selected_score):
			selected = candidate.duplicate(true)
			selected_score = score
	if selected.is_empty():
		return {"path": [], "score": NpcCombatAiSystem.BLOCKED_SCORE}
	selected["score"] = selected_score
	return selected


func _evaluate_spell_plan(actor: Node, profile: Dictionary, caster_position: Vector2) -> Dictionary:
	if actor == null or not actor.has_method("get_combat_spell_ids"):
		return {}
	var spell_ids: Array[String] = []
	for value: Variant in actor.call("get_combat_spell_ids") as Array:
		spell_ids.append(str(value))
	var contexts: Dictionary = {}
	for spell_id: String in spell_ids:
		var spell: Dictionary = _npc_spell_selector.get_spell(spell_id)
		if spell.is_empty():
			continue
		contexts[spell_id] = _spell_option_context(actor, spell, caster_position)
	var policy: Dictionary = {
		"friendly_fire_tolerance": int(profile.get("friendly_fire_tolerance", 0)),
		"slot_reserve": int(profile.get("slot_reserve", 0)),
		"slot_conservation": float(profile.get("slot_conservation", 0.55))
	}
	return _npc_spell_selector.choose_spell(spell_ids, contexts, policy)


func _spell_option_context(actor: Node, spell: Dictionary, caster_position: Vector2) -> Dictionary:
	var distance: int = DistanceSystem.distance_feet(caster_position, player.global_position)
	var visible: bool = _combat_environment == null or _combat_environment.has_line_of_sight(caster_position, player.global_position)
	var spell_level: int = maxi(int(spell.get("spell_level", 0)), 0)
	var slots: int = int(actor.call("get_combat_spell_slot_count", spell_level)) if actor.has_method("get_combat_spell_slot_count") else (1 if spell_level == 0 else 0)
	var option: Dictionary = {
		"available": spell_level == 0 or slots > 0,
		"line_of_sight": visible,
		"distance_feet": distance,
		"slots_remaining": slots,
		"target_health_ratio": _combat_ai_player_health_ratio(),
		"target_wounded": _combat_ai_player_health_ratio() < 1.0,
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
		var aim_cell: Vector2i = grid.world_to_cell(player.global_position)
		var cells: Array[Vector2i] = _advanced_spell_area.get_area_cells(grid, caster_cell, aim_cell, area_value as Dictionary, player.global_position - caster_position)
		option["hostile_hits"] = 1 if grid.world_to_cell(player.global_position) in cells else 0
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


func _living_ai_allies(actor: Node) -> Array[Node]:
	var result: Array[Node] = []
	for entry: Dictionary in _turn_system.entries:
		var participant: Node = entry.get("node") as Node
		if not is_instance_valid(participant) or participant == actor or participant == player or bool(entry.get("is_player", false)):
			continue
		if participant.has_method("is_combat_active") and not bool(participant.call("is_combat_active")):
			continue
		result.append(participant)
	return result


func _enemy_spell_definition(actor: Node) -> Dictionary:
	if actor == null or not actor.has_method("get_combat_spell_id"):
		return {}
	var spell: Dictionary = _npc_spell_selector.get_spell(str(actor.call("get_combat_spell_id")))
	return spell if str(spell.get("effect", "")) in ["area_saving_throw_spell", "auto_hit_spell", "spell_attack", "saving_throw_spell"] else {}


func _enemy_has_spell_slot(actor: Node, spell: Dictionary) -> bool:
	var spell_level: int = maxi(int(spell.get("spell_level", 0)), 0)
	if spell_level == 0:
		return true
	return actor != null and actor.has_method("get_combat_spell_slot_count") and int(actor.call("get_combat_spell_slot_count", spell_level)) > 0


func _enemy_spell_slot_level(actor: Node, spell: Dictionary) -> int:
	var base_level: int = maxi(int(spell.get("spell_level", 0)), 0)
	if base_level == 0:
		return 0
	return maxi(int(actor.call("get_combat_spell_slot_level")), base_level) if actor != null and actor.has_method("get_combat_spell_slot_level") else base_level


func _resolve_enemy_area_spell(actor: Node, spell: Dictionary, slot_level: int) -> void:
	var effect: String = str(spell.get("effect", ""))
	if effect == "area_saving_throw_spell":
		await super._resolve_enemy_area_spell(actor, spell, slot_level)
		return
	var damage: int = int(spell.get("damage_bonus", 0))
	var dice_value: Variant = spell.get("damage_dice", [1, 6])
	if dice_value is Array and (dice_value as Array).size() >= 2:
		for _index: int in range(maxi(int((dice_value as Array)[0]), 1)):
			damage += _srd_dice.roll_die(maxi(int((dice_value as Array)[1]), 2))
	var hit: bool = true
	if effect == "spell_attack":
		var cover: Dictionary = _combat_environment.get_cover((actor as Node2D).global_position, player.global_position) if _combat_environment != null else {"bonus": 0, "total_cover": false}
		var roll: Dictionary = _srd_rules.roll_d20(int(actor.call("get_spell_attack_bonus")) if actor.has_method("get_spell_attack_bonus") else 0, false, player_is_dodging())
		var natural: int = int(roll.get("natural", 1))
		var target_ac: int = _class_data.get_armor_class(GameState.player_character) + int(cover.get("bonus", 0))
		hit = not bool(cover.get("total_cover", false)) and natural != 1 and (natural == 20 or int(roll.get("total", 0)) >= target_ac)
	elif effect == "saving_throw_spell":
		var save_ability: String = str(spell.get("save_ability", "dexterity"))
		var save_dc: int = int(actor.call("get_spell_save_dc")) if actor.has_method("get_spell_save_dc") else 10
		var save: Dictionary = _srd_rules.resolve_saving_throw(save_ability, GameState.player_character.get_saving_throw_modifier(save_ability), save_dc, _player_combat_state)
		hit = not bool(save.get("success", false))
	if hit:
		apply_damage_to_player(damage, str(spell.get("damage_type", "force")), false, actor)
		var condition_id: String = str(spell.get("on_hit_condition", ""))
		if not condition_id.is_empty():
			_player_combat_state.add_condition(condition_id, maxi(int(spell.get("on_hit_condition_rounds", 1)), 1), actor.get_instance_id())
	show_combat_message("%s применяет «%s»: %s." % [_target_name(actor), str(spell.get("name", "Заклинание")), "цель поражена" if hit else "герой избегает эффекта"], hit)


func _resolve_ai_rally(actor: Node, profile: Dictionary) -> void:
	var squad_id: String = str(profile.get("squad_id", ""))
	var duration: int = maxi(int(profile.get("rally_duration_rounds", 2)), 1)
	_casualty_ai.rally_squad(squad_id, _turn_system.round_number, duration)
	show_combat_message("%s собирает союзников после потери бойца. Отряд временно удерживает строй." % _target_name(actor), true)


func _resolve_ai_shove(actor_node: Node2D, actor: Node) -> void:
	if DistanceSystem.distance_feet(actor_node.global_position, player.global_position) > DistanceSystem.MELEE_REACH_FEET:
		return
	var attack_modifier: int = int(actor.call("get_initiative_modifier")) if actor.has_method("get_initiative_modifier") else 0
	var defense_modifier: int = maxi(GameState.player_character.get_ability_modifier("strength"), GameState.player_character.get_ability_modifier("dexterity"))
	var attack_roll: Dictionary = _srd_rules.roll_d20(attack_modifier)
	var defense_roll: Dictionary = _srd_rules.roll_d20(defense_modifier)
	var success: bool = int(attack_roll.get("total", 0)) >= int(defense_roll.get("total", 0))
	if success:
		_player_combat_state.add_condition("prone", 1, actor.get_instance_id())
		_push_player_one_cell_away(actor_node.global_position)
	show_combat_message("%s пытается сбить героя с ног: %s." % [_target_name(actor), "успех" if success else "герой удерживает позицию"], success)


func _push_player_one_cell_away(source_position: Vector2) -> void:
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return
	var player_cell: Vector2i = grid.world_to_cell(player.global_position)
	var delta: Vector2 = player.global_position - source_position
	var step := Vector2i(int(signf(delta.x)), int(signf(delta.y)))
	if step == Vector2i.ZERO:
		step = Vector2i(1, 0)
	var destination: Vector2i = player_cell + step
	if grid.is_cell_valid(destination) and not _occupied_cells(player).has(destination) and (_combat_environment == null or not _combat_environment.is_cell_blocked(grid, destination)):
		player.global_position = grid.cell_to_world_center(destination)
		GameState.player_position = player.global_position


func _objective_for_advanced_intent(actor: Node, guard_anchor: Vector2, target_position: Vector2, intent_id: String) -> Vector2:
	if intent_id == NpcCombatAiSystem.INTENT_GUARD:
		return guard_anchor
	if intent_id == AdvancedNpcCombatAiSystem.INTENT_REGROUP:
		var ally: Node2D = _nearest_living_ally(actor)
		return ally.global_position if ally != null else guard_anchor
	return target_position


func _nearest_living_ally(actor: Node) -> Node2D:
	var nearest: Node2D
	var distance: float = INF
	for ally: Node in _living_ai_allies(actor):
		if not ally is Node2D:
			continue
		var value: float = (actor as Node2D).global_position.distance_squared_to((ally as Node2D).global_position)
		if value < distance:
			distance = value
			nearest = ally as Node2D
	return nearest


func _better_cover_available(actor_node: Node2D, actor: Node) -> bool:
	if _combat_environment == null:
		return false
	var current: Dictionary = _combat_environment.get_cover(player.global_position, actor_node.global_position)
	var current_bonus: int = int(current.get("bonus", 0))
	for candidate: Dictionary in _build_combat_ai_reachable_candidates(actor_node, 30):
		var grid: BattleGrid = _get_battle_grid()
		var cell: Vector2i = candidate.get("cell", Vector2i.ZERO) as Vector2i
		var cover: Dictionary = _combat_environment.get_cover(player.global_position, grid.cell_to_world_center(cell))
		if not bool(cover.get("total_cover", false)) and int(cover.get("bonus", 0)) > current_bonus:
			return true
	return false


func _target_near_blocked_edge() -> bool:
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return false
	var cell: Vector2i = grid.world_to_cell(player.global_position)
	var blocked: int = 0
	for step: Vector2i in [Vector2i.LEFT, Vector2i.RIGHT, Vector2i.UP, Vector2i.DOWN]:
		var neighbour: Vector2i = cell + step
		if not grid.is_cell_valid(neighbour) or (_combat_environment != null and _combat_environment.is_cell_blocked(grid, neighbour)):
			blocked += 1
	return blocked >= 2


func get_casualty_context_for_testing(actor_id: String) -> Dictionary:
	var profile: Dictionary = _advanced_ai.get_profile(actor_id) if _advanced_ai != null else {}
	return _casualty_ai.get_context(actor_id, str(profile.get("squad_id", "")), _turn_system.round_number)


func evaluate_spell_plan_for_testing(actor: Node, actor_id: String, caster_position: Vector2) -> Dictionary:
	return _evaluate_spell_plan(actor, _advanced_ai.get_profile(actor_id), caster_position) if _advanced_ai != null else {}
