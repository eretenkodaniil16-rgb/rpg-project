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
		show_combat_message("Прилив адреналина: +%d футов перемещения и %d временного здоровья." % [movement_bonus, temporary_hit_points], true)
		_invalidate_reachable_area()
		_refresh_turn_interface()
		_refresh_action_catalog()


func apply_damage_to_player(amount: int, damage_type: String, critical_hit: bool = false, source: Node = null) -> Dictionary:
	if _player_combat_state.dead:
		return {"applied": 0, "dead": true}
	if GameState.player_character.current_health <= 0:
		var zero_result: Dictionary = _srd_rules.damage_at_zero_hit_points(_player_combat_state, critical_hit)
		show_combat_message("Урон при нулевом здоровье: получено %d провала спасброска смерти." % int(zero_result.get("failures_added", 0)), false)
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
	var message: String = "%s наносит %d урона %s. Здоровье: %d/%d." % [
		_target_name(source) if source != null else "Источник",
		applied,
		_srd_rules.normalize_damage_type(damage_type),
		GameState.player_character.current_health,
		GameState.player_character.maximum_health
	]
	if stone_reduction > 0:
		message += " Каменная выносливость уменьшила удар на %d и израсходовала реакцию." % stone_reduction
	if int(mitigation.get("absorbed", 0)) > 0:
		message += " Временное здоровье поглотило %d урона." % int(mitigation.get("absorbed", 0))
	if not str(mitigation.get("reason", "")).is_empty():
		message += " Сработало: %s." % str(mitigation.get("reason", ""))
	if relentless:
		message += " Неукротимая стойкость оставила персонажу 1 очко здоровья."
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


func _occupied_cells(excluded_actor: Node = null) -> Dictionary:
	var occupied: Dictionary = super._occupied_cells(excluded_actor)
	if excluded_actor != player or not GameState.player_character.can_move_through_larger_creatures:
		return occupied
	var player_rank: int = RaceDataSystem.size_rank(GameState.player_character.size_category)
	for cell_value: Variant in occupied.keys():
		var actor: Node = occupied[cell_value] as Node
		if _actor_size_rank(actor) > player_rank:
			occupied.erase(cell_value)
	return occupied


func _plan_to_cell(destination_cell: Vector2i) -> void:
	var real_occupied: Dictionary = super._occupied_cells(player)
	if real_occupied.has(destination_cell):
		show_combat_message("Через более крупное существо можно пройти, но нельзя закончить перемещение в его клетке.", false)
		return
	super._plan_to_cell(destination_cell)


func _apply_candidate_path(candidate: Array[Vector2i]) -> void:
	if not candidate.is_empty() and super._occupied_cells(player).has(candidate[candidate.size() - 1]):
		show_combat_message("Нельзя закончить маршрут в клетке другого существа.", false)
		return
	super._apply_candidate_path(candidate)


func _on_escape_grapple_requested() -> void:
	if not _player_turn_available() or not _player_combat_state.has_condition("grappled"):
		return
	if not _turn_system.consume_action():
		show_combat_message("Для освобождения требуется действие.", false)
		return
	var dc: int = _condition_save_dc(_player_combat_state, "grappled", 10)
	var modifier: int = maxi(GameState.player_character.get_ability_modifier("strength"), GameState.player_character.get_ability_modifier("dexterity"))
	var check: Dictionary = _srd_rules.resolve_d20_test(
		modifier,
		dc,
		GameState.player_character.grapple_escape_advantage,
		false,
		[],
		GameState.player_character.reroll_natural_one
	)
	if bool(check.get("success", false)):
		_player_combat_state.remove_condition("grappled")
		show_combat_message("Персонаж освобождается из захвата%s." % (" с преимуществом Могучего сложения" if GameState.player_character.grapple_escape_advantage else ""), true)
	else:
		show_combat_message("Не удалось вырваться: %d против Сл %d." % [int(check.get("total", 0)), dc], false)
	_refresh_srd_interface()


func _on_hide_requested() -> void:
	if not _player_turn_available():
		return
	if not _turn_system.consume_action():
		show_combat_message("Для попытки скрыться требуется действие.", false)
		return
	for entry: Dictionary in _turn_system.entries:
		if bool(entry.get("is_player", false)):
			continue
		var actor: Node = entry.get("node") as Node
		if not is_instance_valid(actor) or not (actor is Node2D) or not _target_is_valid(actor):
			continue
		if _combat_environment == null or not _combat_environment.has_line_of_sight((actor as Node2D).global_position, player.global_position):
			continue
		if GameState.player_character.naturally_stealthy and _has_larger_creature_cover(actor):
			continue
		show_combat_message("Нельзя скрыться: противник видит персонажа.", false)
		return
	_player_combat_state.hidden = true
	show_combat_message("Персонаж скрыт. Следующая атака получает преимущество и раскрывает позицию.", true)


func _has_larger_creature_cover(observer: Node) -> bool:
	var player_rank: int = RaceDataSystem.size_rank(GameState.player_character.size_category)
	for candidate: Node in _available_targets():
		if candidate == observer or not is_instance_valid(candidate) or not (candidate is Node2D):
			continue
		if DistanceSystem.distance_feet(player.global_position, (candidate as Node2D).global_position) > 5:
			continue
		if _actor_size_rank(candidate) > player_rank:
			return true
	return false


func _actor_size_rank(actor: Node) -> int:
	if actor == null:
		return RaceDataSystem.size_rank("medium")
	if actor.has_method("get_size_category"):
		return RaceDataSystem.size_rank(str(actor.call("get_size_category")))
	var size_value: Variant = actor.get("size_category")
	return RaceDataSystem.size_rank(str(size_value)) if size_value != null else RaceDataSystem.size_rank("medium")


func _predict_directional_target(weapon: Dictionary) -> Node:
	if DistanceSystem.is_ranged_weapon(weapon):
		return super._predict_directional_target(weapon)
	return _find_directional_melee_target(weapon)


func _weapon_attempt_is_valid(weapon: Dictionary, selected_target: Node, predicted_target: Node) -> bool:
	if _target_is_valid(selected_target) or DistanceSystem.is_ranged_weapon(weapon):
		return super._weapon_attempt_is_valid(weapon, selected_target, predicted_target)
	return maxi(int(weapon.get("reach_ft", 5)), 0) > 0
