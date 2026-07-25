extends "res://scripts/game/game_spell_reactions_runtime.gd"

const REACTION_CHOICE_PROMPT_SCRIPT: Script = preload("res://scripts/ui/reaction_choice_prompt.gd")
const REACTION_OPPORTUNITY_SYSTEM_SCRIPT: Script = preload("res://scripts/systems/reaction_opportunity_system.gd")
const VICIOUS_MOCKERY_SYSTEM_SCRIPT: Script = preload("res://scripts/systems/vicious_mockery_system.gd")

var _reaction_choice_prompt: ReactionChoicePrompt
var _reaction_opportunities: ReactionOpportunitySystem = REACTION_OPPORTUNITY_SYSTEM_SCRIPT.new() as ReactionOpportunitySystem
var _vicious_mockery_system: ViciousMockerySystem = VICIOUS_MOCKERY_SYSTEM_SCRIPT.new() as ViciousMockerySystem
var _vicious_mockery_button: Button
var _vicious_mockery_effects: Dictionary = {}
var _reaction_resolution_in_progress: bool = false


func _ready() -> void:
	super._ready()
	_build_reaction_choice_prompt()
	_build_vicious_mockery_control()
	if _spell_reaction_prompt != null:
		_spell_reaction_prompt.hide()


func _process(delta: float) -> void:
	super._process(delta)
	_update_vicious_mockery_control()


func _any_overlay_visible() -> bool:
	return super._any_overlay_visible() or (
		_reaction_choice_prompt != null
		and _reaction_choice_prompt.visible
	)


func _build_reaction_choice_prompt() -> void:
	_reaction_choice_prompt = REACTION_CHOICE_PROMPT_SCRIPT.new() as ReactionChoicePrompt
	_reaction_choice_prompt.name = "ReactionChoicePrompt"
	$Interface.add_child(_reaction_choice_prompt)


func _build_vicious_mockery_control() -> void:
	_vicious_mockery_button = Button.new()
	_vicious_mockery_button.name = "ViciousMockeryButton"
	_vicious_mockery_button.text = "ЗЛАЯ НАСМЕШКА"
	_vicious_mockery_button.tooltip_text = str(_vicious_mockery_system.get_definition().get("description", ""))
	_vicious_mockery_button.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	_vicious_mockery_button.offset_left = -620.0
	_vicious_mockery_button.offset_top = -220.0
	_vicious_mockery_button.offset_right = -250.0
	_vicious_mockery_button.offset_bottom = -154.0
	_vicious_mockery_button.add_theme_font_size_override("font_size", 18)
	_vicious_mockery_button.pressed.connect(_request_vicious_mockery)
	$Interface.add_child(_vicious_mockery_button)
	_add_exploration_hud_node(_vicious_mockery_button)
	_update_vicious_mockery_control()


func _update_vicious_mockery_control() -> void:
	if _vicious_mockery_button == null:
		return
	var is_bard: bool = GameState.player_character != null and GameState.player_character.character_class_id == "bard"
	_vicious_mockery_button.visible = is_bard and not _any_overlay_visible()
	var player_turn: bool = not _turn_system.active or _turn_system.is_player_turn(player)
	var action_available: bool = not _turn_system.active or _turn_system.action_available
	_vicious_mockery_button.disabled = (
		not is_bard
		or GameState.input_locked
		or _attack_in_progress
		or _enemy_turn_running
		or not player_turn
		or not action_available
	)


func _request_vicious_mockery() -> void:
	if GameState.input_locked or _attack_in_progress or _enemy_turn_running or _any_overlay_visible():
		return
	if GameState.player_character.character_class_id != "bard":
		show_combat_message("Злая насмешка доступна Барду.", false)
		return
	if _turn_system.active and not _turn_system.is_player_turn(player):
		show_combat_message("Заклинание можно применить только на своём ходу.", false)
		return
	if not _target_is_valid(_selected_target):
		_select_nearest_target()
	if not _target_is_valid(_selected_target):
		show_combat_message("Для Злой насмешки нужна боевая цель.", false)
		return
	var target: Node = _selected_target
	if not target.has_method("receive_player_attack"):
		show_combat_message("Эта цель пока не поддерживает боевые заклинания.", false)
		return
	var target_position: Vector2 = (target as Node2D).global_position
	var distance_feet: int = DistanceSystem.distance_feet(player.global_position, target_position)
	var can_see_or_hear: bool = true
	if target.has_method("can_be_seen_or_heard_by"):
		can_see_or_hear = bool(target.call("can_be_seen_or_heard_by", player))
	var casting_context: Dictionary = _build_spellcasting_context()
	var validation: Dictionary = _vicious_mockery_system.validate_cast(
		GameState.player_character,
		distance_feet,
		can_see_or_hear,
		casting_context
	)
	if not bool(validation.get("success", false)):
		show_combat_message(str(validation.get("message", "Злая насмешка недоступна.")), false)
		return
	if _turn_system.active and not _turn_system.consume_action():
		show_combat_message("Действие на этом ходу уже использовано.", false)
		return

	var target_save_modifier: int = (
		int(target.call("get_saving_throw_modifier", "wisdom"))
		if target.has_method("get_saving_throw_modifier")
		else 0
	)
	_set_combat_busy(true)
	_face_toward(target_position)
	player.play_attack_animation(target_position)
	await get_tree().create_timer(0.24).timeout
	var resolution: Dictionary = _vicious_mockery_system.resolve(
		GameState.player_character,
		_target_name(target),
		_state_for(target),
		target_save_modifier,
		distance_feet,
		can_see_or_hear,
		casting_context
	)
	if not bool(resolution.get("success", false)):
		_set_combat_busy(false)
		show_combat_message(str(resolution.get("message", "Злая насмешка не сработала.")), false)
		return
	var result: AttackResult = resolution.get("result") as AttackResult
	if result == null:
		_set_combat_busy(false)
		show_combat_message("Не удалось сформировать результат Злой насмешки.", false)
		return
	if bool(resolution.get("failed_save", false)):
		_apply_mitigation_to_result(result, _state_for(target))
		_apply_vicious_mockery_disadvantage(target)
	target.call("receive_player_attack", result, true)
	if target.has_method("get_current_health") and int(target.call("get_current_health")) <= 0:
		_vicious_mockery_effects.erase(target.get_instance_id())
		_release_grapples_for(target)
	_set_combat_busy(false)
	show_combat_message(str(resolution.get("message", "Злая насмешка применена.")), bool(resolution.get("failed_save", false)))
	GameState.save_game()
	_update_status()
	_sync_exploration_hud_visibility()
	if not _turn_system.active and _target_is_valid(target):
		_start_turn_based_combat(target)
	_after_player_action()


func _apply_vicious_mockery_disadvantage(target: Node) -> void:
	if not is_instance_valid(target):
		return
	_vicious_mockery_effects[target.get_instance_id()] = {
		"actor": target,
		"turn_started": false
	}


func _begin_current_turn() -> void:
	var actor: Node = _turn_system.current_actor() if _turn_system != null and _turn_system.active else null
	if is_instance_valid(actor):
		var actor_id: int = actor.get_instance_id()
		if _vicious_mockery_effects.has(actor_id):
			var effect: Dictionary = _vicious_mockery_effects[actor_id] as Dictionary
			effect["turn_started"] = true
			_vicious_mockery_effects[actor_id] = effect
	super._begin_current_turn()


func _advance_combat_turn() -> void:
	var previous: Node = _turn_system.current_actor() if _turn_system != null and _turn_system.active else null
	if is_instance_valid(previous):
		var previous_id: int = previous.get_instance_id()
		if _vicious_mockery_effects.has(previous_id):
			var effect: Dictionary = _vicious_mockery_effects[previous_id] as Dictionary
			if bool(effect.get("turn_started", false)):
				_vicious_mockery_effects.erase(previous_id)
	super._advance_combat_turn()


func resolve_npc_attack(attacker: Node, attack_bonus: int, damage_die: int, damage_bonus: int, damage_type: String = "slashing") -> Dictionary:
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
	var natural: int = int(roll.get("natural", 1))
	var target_ac: int = _class_data.get_armor_class(GameState.player_character) + int(cover.get("bonus", 0))
	var hit: bool = natural != 1 and (natural == 20 or int(roll.get("total", 0)) >= target_ac)
	if not hit:
		var reason: String = " с помехой от Злой насмешки" if mockery_disadvantage else ""
		show_combat_message("%s промахивается%s: %d против КД %d." % [_target_name(attacker), reason, int(roll.get("total", 0)), target_ac], false)
		return {
			"hit": false,
			"natural": natural,
			"total": int(roll.get("total", 0)),
			"vicious_mockery_disadvantage": mockery_disadvantage
		}
	var critical: bool = natural == 20 or bool(adjustments.get("automatic_critical", false))
	var damage: int = damage_bonus
	for _index: int in range(2 if critical else 1):
		damage += _srd_dice.roll_die(maxi(damage_die, 2))
	var applied: Dictionary = apply_damage_to_player(damage, damage_type, critical, attacker)
	applied["vicious_mockery_disadvantage"] = mockery_disadvantage
	return applied


func _consume_vicious_mockery_on_attack(attacker: Node) -> bool:
	if not is_instance_valid(attacker):
		return false
	var attacker_id: int = attacker.get_instance_id()
	if not _vicious_mockery_effects.has(attacker_id):
		return false
	_vicious_mockery_effects.erase(attacker_id)
	return true


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
	show_combat_message("%s начинает сотворять «%s»." % [attempt.caster_name, attempt.get_spell_name()], false)

	var save_overrides: Array[int] = []
	if actor.has_method("get_counterspell_save_roll_overrides"):
		var overrides_value: Variant = actor.call("get_counterspell_save_roll_overrides")
		if overrides_value is Array:
			for value: Variant in overrides_value as Array:
				save_overrides.append(int(value))
	var reaction_context: Dictionary = {
		"reactor": GameState.player_character,
		"attempt": attempt,
		"reaction_available": _turn_system.has_reaction(player),
		"can_see_caster": true,
		"distance_feet": distance_feet,
		"casting_context": _build_spellcasting_context(),
		"save_roll_overrides": save_overrides
	}
	var options: Array[Dictionary] = _reaction_opportunities.sort_options(
		_reaction_opportunities.collect_options(
			ReactionOpportunitySystem.TRIGGER_SPELL_CAST_STARTED,
			reaction_context
		)
	)
	if not options.is_empty() and _reaction_choice_prompt != null:
		_reaction_resolution_in_progress = true
		var chosen_id: String = await _reaction_choice_prompt.request_reaction(
			"ВОЗМОЖНОСТЬ РЕАКЦИИ",
			"%s начинает сотворять «%s» на расстоянии %d футов. Выберите одну доступную реакцию." % [
				attempt.caster_name,
				attempt.get_spell_name(),
				distance_feet
			],
			options
		)
		_reaction_resolution_in_progress = false
		if not chosen_id.is_empty():
			var reaction_result: Dictionary = _reaction_opportunities.resolve_spell_cast_option(chosen_id, reaction_context)
			if bool(reaction_result.get("consume_reaction", false)):
				_turn_system.consume_reaction(player)
			show_combat_message(
				str(reaction_result.get("message", "Реакция разрешена.")),
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


func get_reaction_choice_prompt_for_testing() -> ReactionChoicePrompt:
	return _reaction_choice_prompt


func get_vicious_mockery_button_for_testing() -> Button:
	return _vicious_mockery_button


func get_vicious_mockery_system_for_testing() -> ViciousMockerySystem:
	return _vicious_mockery_system


func has_vicious_mockery_effect_for_testing(actor: Node) -> bool:
	return is_instance_valid(actor) and _vicious_mockery_effects.has(actor.get_instance_id())


func apply_vicious_mockery_effect_for_testing(actor: Node) -> void:
	_apply_vicious_mockery_disadvantage(actor)
