extends "res://scripts/game/game_planned_combat.gd"

var _race_data_runtime: RaceDataSystem = RaceDataSystem.new()
var _racial_dice: DiceRoller = DiceRoller.new()


func _ready() -> void:
	_race_data_runtime.ensure_character_race(GameState.player_character)
	super._ready()
	_sync_player_damage_traits()


func _process(delta: float) -> void:
	super._process(delta)
	_sync_player_damage_traits()


func _sync_player_damage_traits() -> void:
	super._sync_player_damage_traits()
	for damage_type: String in GameState.player_character.racial_damage_resistances:
		if damage_type not in _player_combat_state.damage_resistances:
			_player_combat_state.damage_resistances.append(damage_type)
	_player_combat_state.saving_throw_advantage_conditions = GameState.player_character.racial_condition_save_advantage.duplicate()
	_player_combat_state.saving_throw_advantage_abilities = GameState.player_character.racial_save_advantage_abilities.duplicate()
	_player_combat_state.magical_save_advantage_abilities = GameState.player_character.racial_magical_save_advantage_abilities.duplicate()
	_player_combat_state.reroll_natural_one = GameState.player_character.reroll_natural_one


func _begin_current_turn() -> void:
	super._begin_current_turn()
	if not _turn_system.active or _turn_system.current_actor() != player:
		return
	var speed: int = _srd_rules.effective_speed_feet(GameState.player_character.base_speed_feet, _player_combat_state)
	_turn_system.set_player_movement(speed)
	_invalidate_reachable_area()
	_refresh_turn_interface()
	_refresh_action_catalog()


func _build_catalog_entries() -> Dictionary:
	var entries: Dictionary = super._build_catalog_entries()
	var ability: Dictionary = _class_data.get_racial_ability(GameState.player_character)
	if ability.is_empty():
		return entries
	var ability_id: String = str(ability.get("id", GameState.player_character.racial_ability_id))
	var action_kind: String = _ability_action_kind(ability_id, ability)
	var category: String = "bonus" if action_kind == "bonus" else "action"
	var category_entries: Array = entries.get(category, []) as Array
	var player_turn: bool = _turn_system.active and _turn_system.is_player_turn(player) and not _enemy_turn_running
	var resource_ready: bool = _ability_attempt_is_valid(ability)
	var resource_available: bool = _turn_system.bonus_action_available if category == "bonus" else _turn_system.action_available
	var group: String = "attack" if str(ability.get("target", "self")) == "enemy" else "tactic"
	category_entries.append(_entry(
		"ability:%s" % ability_id,
		str(ability.get("name", "Расовая способность")),
		player_turn and resource_ready and resource_available and _srd_rules.can_take_action(_player_combat_state),
		"%s. Ресурс: %s." % [str(ability.get("description", "")), _class_data.get_resource_text(GameState.player_character, ability)],
		group
	))
	entries[category] = category_entries
	return entries


func _on_ability_requested(ability_id: String) -> void:
	var ability: Dictionary = _class_data.get_ability_definition(ability_id)
	var effect: String = str(ability.get("effect", ""))
	var resource_key: String = str(ability.get("resource_key", "unlimited"))
	var resource_before: int = GameState.player_character.get_resource(resource_key)
	await super._on_ability_requested(ability_id)
	var successfully_consumed: bool = resource_key == "unlimited" or GameState.player_character.get_resource(resource_key) < resource_before
	if not successfully_consumed:
		return
	if effect == "adrenaline_rush":
		var temporary_hit_points: int = CombatSystem.proficiency_bonus_for_level(GameState.player_character.level)
		var movement_bonus: int = maxi(GameState.player_character.base_speed_feet, 0)
		_player_combat_state.temporary_hit_points = maxi(_player_combat_state.temporary_hit_points, temporary_hit_points)
		if _turn_system.active:
			_turn_system.add_movement(movement_bonus)
		show_combat_message("Прилив адреналина: +%d футов перемещения и %d временных HP." % [movement_bonus, temporary_hit_points], true)
		_invalidate_reachable_area()
		_refresh_turn_interface()
		_refresh_action_catalog()


func apply_damage_to_player(amount: int, damage_type: String, critical_hit: bool = false, source: Node = null) -> Dictionary:
	if _player_combat_state.dead:
		return {"applied": 0, "dead": true}
	if GameState.player_character.current_health <= 0:
		var zero_result: Dictionary = _srd_rules.damage_at_zero_hit_points(_player_combat_state, critical_hit)
		show_combat_message("Урон при 0 HP: получено %d провала спасброска смерти." % int(zero_result.get("failures_added", 0)), false)
		if bool(zero_result.get("dead", false)):
			_handle_srd_player_death(source)
		return zero_result

	var incoming_damage: int = maxi(amount, 0)
	var stone_reduction: int = 0
	var stone_reaction_ready: bool = not _turn_system.active or _turn_system.has_reaction(player)
	if incoming_damage > 0 and stone_reaction_ready and GameState.player_character.get_resource("stone_endurance") > 0:
		GameState.player_character.consume_resource("stone_endurance", 1)
		if _turn_system.active:
			_turn_system.consume_reaction(player)
		stone_reduction = maxi(1, _racial_dice.roll_die(12) + GameState.player_character.get_ability_modifier("constitution"))
		incoming_damage = maxi(incoming_damage - stone_reduction, 0)

	var mitigation: Dictionary = _srd_rules.resolve_damage(incoming_damage, damage_type, _player_combat_state)
	var applied: int = int(mitigation.get("applied", 0))
	var before: int = GameState.player_character.current_health
	var remaining_damage: int = maxi(applied - before, 0)
	var killed_outright: bool = remaining_damage >= GameState.player_character.maximum_health
	var relentless: bool = false
	if applied >= before and before > 0 and not killed_outright and GameState.player_character.get_resource("relentless_endurance") > 0:
		GameState.player_character.consume_resource("relentless_endurance", 1)
		applied = maxi(before - 1, 0)
		remaining_damage = 0
		GameState.player_character.current_health = 1
		relentless = true
	else:
		GameState.player_character.current_health = maxi(0, before - applied)
	var concentration: Dictionary = _srd_rules.resolve_concentration_check(GameState.player_character.get_ability_modifier("constitution"), applied, _player_combat_state)
	var message: String = "%s наносит %d урона %s. HP: %d/%d." % [
		_target_name(source) if source != null else "Источник",
		applied,
		_srd_rules.normalize_damage_type(damage_type),
		GameState.player_character.current_health,
		GameState.player_character.maximum_health
	]
	if stone_reduction > 0:
		message += " Каменная выносливость уменьшила удар на %d и израсходовала реакцию." % stone_reduction
	if int(mitigation.get("absorbed", 0)) > 0:
		message += " Временные HP поглотили %d." % int(mitigation.get("absorbed", 0))
	if not str(mitigation.get("reason", "")).is_empty():
		message += " Сработало: %s." % str(mitigation.get("reason", ""))
	if relentless:
		message += " Неукротимая стойкость оставила персонажу 1 HP."
	if bool(concentration.get("required", false)):
		message += " Концентрация: %s." % ("сохранена" if bool(concentration.get("success", false)) else "потеряна")
	show_combat_message(message, false)
	if GameState.player_character.current_health <= 0:
		if remaining_damage >= GameState.player_character.maximum_health:
			_player_combat_state.dead = true
			_handle_srd_player_death(source)
		else:
			_player_combat_state.enter_dying()
			show_combat_message("Персонаж без сознания и начинает совершать спасброски смерти.", false)
	GameState.save_game()
	_update_status()
	return {"hit": true, "applied": applied, "critical": critical_hit, "dead": _player_combat_state.dead, "relentless": relentless, "stone_reduction": stone_reduction}
