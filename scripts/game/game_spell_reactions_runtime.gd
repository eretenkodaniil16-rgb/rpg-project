extends "res://scripts/game/game_final_v017.gd"

const SPELL_REACTION_PROMPT_SCRIPT: Script = preload("res://scripts/ui/spell_reaction_prompt.gd")
const RUNE_TRAINING_CONSTRUCT_SCRIPT: Script = preload("res://scripts/game/rune_training_construct.gd")
const ENEMY_GRID_STEP_FEET: int = 5

var _spell_reaction_runtime: SpellReactionSystem = SpellReactionSystem.new()
var _spell_reaction_prompt: SpellReactionPrompt
var _rune_training_construct: RuneTrainingConstruct
var _enemy_spell_cast_in_progress: bool = false


func _ready() -> void:
	super._ready()
	_build_spell_reaction_runtime()


func _any_overlay_visible() -> bool:
	return super._any_overlay_visible() or (
		_spell_reaction_prompt != null
		and _spell_reaction_prompt.visible
	)


func _build_spell_reaction_runtime() -> void:
	var existing_prompt: SpellReactionPrompt = get_node_or_null("Interface/SpellReactionPrompt") as SpellReactionPrompt
	if existing_prompt != null:
		_spell_reaction_prompt = existing_prompt
	else:
		_spell_reaction_prompt = SPELL_REACTION_PROMPT_SCRIPT.new() as SpellReactionPrompt
		_spell_reaction_prompt.name = "SpellReactionPrompt"
		$Interface.add_child(_spell_reaction_prompt)

	var existing_construct: RuneTrainingConstruct = get_node_or_null("RuneTrainingConstruct") as RuneTrainingConstruct
	if existing_construct != null:
		_rune_training_construct = existing_construct
	else:
		_rune_training_construct = RUNE_TRAINING_CONSTRUCT_SCRIPT.new() as RuneTrainingConstruct
		_rune_training_construct.name = "RuneTrainingConstruct"
		_rune_training_construct.position = Vector2(930.0, 175.0)
		add_child(_rune_training_construct)


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
			movement_feet >= ENEMY_GRID_STEP_FEET
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
		if (
			not action_used
			and is_instance_valid(actor)
			and _target_is_valid(actor)
			and DistanceSystem.distance_feet((actor as Node2D).global_position, player.global_position) <= DistanceSystem.MELEE_REACH_FEET
			and actor.has_method("perform_combat_turn_attack")
		):
			actor.call("perform_combat_turn_attack")
			_update_status()
			await get_tree().create_timer(0.35).timeout
	_enemy_turn_running = false
	if not _player_combat_state.dead:
		_advance_combat_turn()


func _enemy_preferred_distance_feet(actor: Node) -> int:
	var spell: Dictionary = _enemy_spell_definition(actor)
	if spell.is_empty() or not _enemy_has_spell_slot(actor, spell):
		return DistanceSystem.MELEE_REACH_FEET
	return maxi(_enemy_spell_reach_feet(spell), DistanceSystem.MELEE_REACH_FEET)


func _enemy_spell_definition(actor: Node) -> Dictionary:
	if actor == null or not actor.has_method("get_combat_spell_id"):
		return {}
	var spell_id: String = str(actor.call("get_combat_spell_id"))
	if spell_id.is_empty():
		return {}
	var spell: Dictionary = _spell_area_runtime.get_spell_definition(spell_id)
	if str(spell.get("effect", "")) != "area_saving_throw_spell":
		return {}
	return spell


func _enemy_has_spell_slot(actor: Node, spell: Dictionary) -> bool:
	if actor == null or spell.is_empty():
		return false
	var slot_level: int = _enemy_spell_slot_level(actor, spell)
	if not actor.has_method("get_combat_spell_slot_count"):
		return false
	return int(actor.call("get_combat_spell_slot_count", slot_level)) > 0


func _enemy_spell_slot_level(actor: Node, spell: Dictionary) -> int:
	var base_level: int = maxi(int(spell.get("spell_level", 0)), 1)
	if actor != null and actor.has_method("get_combat_spell_slot_level"):
		return maxi(int(actor.call("get_combat_spell_slot_level")), base_level)
	return base_level


func _enemy_spell_reach_feet(spell: Dictionary) -> int:
	var reach: int = maxi(int(spell.get("range_ft", 0)), 0)
	var area_value: Variant = spell.get("area", {})
	if area_value is Dictionary:
		var area: Dictionary = area_value as Dictionary
		reach = maxi(
			reach,
			maxi(
				int(area.get("length_ft", 0)),
				maxi(int(area.get("radius_ft", 0)), int(area.get("size_ft", 0)))
			)
		)
	return maxi(reach, DistanceSystem.MELEE_REACH_FEET)


func _try_enemy_spell_turn(actor: Node) -> bool:
	if _enemy_spell_cast_in_progress or actor == null or not (actor is Node2D):
		return false
	var spell: Dictionary = _enemy_spell_definition(actor)
	if spell.is_empty() or not _enemy_has_spell_slot(actor, spell):
		return false
	var distance_feet: int = DistanceSystem.distance_feet((actor as Node2D).global_position, player.global_position)
	if distance_feet > _enemy_spell_reach_feet(spell):
		return false
	var cover: Dictionary = _combat_environment.get_cover(
		(actor as Node2D).global_position,
		player.global_position
	) if _combat_environment != null else {"bonus": 0, "total_cover": false}
	if bool(cover.get("total_cover", false)):
		return false

	_enemy_spell_cast_in_progress = true
	var slot_level: int = _enemy_spell_slot_level(actor, spell)
	var attempt := SpellCastAttempt.new(spell, actor, slot_level)
	attempt.caster_constitution_modifier = (
		int(actor.call("get_saving_throw_modifier", "constitution"))
		if actor.has_method("get_saving_throw_modifier")
		else 0
	)
	attempt.caster_state = _state_for(actor)
	attempt.action_kind = "action"
	attempt.original_resource_key = "enemy_spell_slots_%d" % slot_level

	show_combat_message(
		"%s начинает сотворять «%s»." % [attempt.caster_name, attempt.get_spell_name()],
		false
	)
	var casting_context: Dictionary = _build_spellcasting_context()
	var offer: Dictionary = _spell_reaction_runtime.evaluate_counterspell(
		GameState.player_character,
		attempt,
		_turn_system.has_reaction(player),
		true,
		distance_feet,
		casting_context
	)
	if bool(offer.get("available", false)) and _spell_reaction_prompt != null:
		var use_counterspell: bool = await _spell_reaction_prompt.request_counterspell(attempt, offer)
		if use_counterspell:
			var save_overrides: Array[int] = []
			if actor.has_method("get_counterspell_save_roll_overrides"):
				var overrides_value: Variant = actor.call("get_counterspell_save_roll_overrides")
				if overrides_value is Array:
					for value: Variant in overrides_value as Array:
						save_overrides.append(int(value))
			var reaction_result: Dictionary = _spell_reaction_runtime.resolve_counterspell(
				GameState.player_character,
				attempt,
				_turn_system.has_reaction(player),
				true,
				distance_feet,
				casting_context,
				save_overrides
			)
			if bool(reaction_result.get("consume_reaction", false)):
				_turn_system.consume_reaction(player)
			show_combat_message(
				str(reaction_result.get("message", "Контрзаклинание разрешено.")),
				bool(reaction_result.get("countered", false))
			)
			GameState.save_game()
			_update_status()
			if bool(reaction_result.get("countered", false)):
				_enemy_spell_cast_in_progress = false
				return true
			if not bool(reaction_result.get("resolved", false)):
				attempt.mark_proceeds()
		else:
			attempt.mark_proceeds()
	else:
		attempt.mark_proceeds()

	await get_tree().create_timer(0.18).timeout
	if attempt.countered:
		_enemy_spell_cast_in_progress = false
		return true
	if not actor.has_method("consume_combat_spell_slot") or not bool(actor.call("consume_combat_spell_slot", slot_level)):
		show_combat_message("%s не смог завершить сотворение: ячейка недоступна." % attempt.caster_name, false)
		_enemy_spell_cast_in_progress = false
		return true
	attempt.mark_original_resource_expended("enemy_spell_slots_%d" % slot_level)
	_resolve_enemy_area_spell(actor, spell, slot_level)
	_enemy_spell_cast_in_progress = false
	return true


func _resolve_enemy_area_spell(actor: Node, spell: Dictionary, slot_level: int) -> void:
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
	var dice_value: Variant = spell.get("damage_dice", [1, 6])
	var base_dice: Array[int] = [1, 6]
	if dice_value is Array and (dice_value as Array).size() >= 2:
		base_dice = [maxi(int((dice_value as Array)[0]), 1), maxi(int((dice_value as Array)[1]), 2)]
	var scaled_dice: Array[int] = _spell_area_runtime.scale_dice_for_slot(spell, base_dice, slot_level, "damage")
	var damage: int = _spell_area_runtime.damage_bonus_for_slot(spell, slot_level)
	for _index: int in range(scaled_dice[0]):
		damage += _srd_dice.roll_die(scaled_dice[1])
	if bool(save_result.get("success", false)) and bool(spell.get("save_for_half", false)):
		damage = floori(float(damage) / 2.0)
	var applied: Dictionary = apply_damage_to_player(damage, str(spell.get("damage_type", "force")), false, actor)
	show_combat_message(
		"%s: спасбросок %s %d против Сл %d; получено %d урона." % [
			str(spell.get("name", "Заклинание")),
			save_ability,
			int(save_result.get("total", 0)),
			save_dc,
			int(applied.get("applied", damage))
		],
		bool(save_result.get("success", false))
	)


func get_spell_reaction_prompt_for_testing() -> SpellReactionPrompt:
	return _spell_reaction_prompt


func get_rune_training_construct_for_testing() -> RuneTrainingConstruct:
	return _rune_training_construct
