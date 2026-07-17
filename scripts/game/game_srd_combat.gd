extends "res://scripts/game/game_turn_based.gd"

const COMBAT_ENVIRONMENT_SCRIPT: Script = preload("res://scripts/game/combat_environment.gd")
const SRD_COMBAT_UI_SCRIPT: Script = preload("res://scripts/ui/srd_combat_ui.gd")
const GRID_STEP_FEET_SRD: int = 5

var _srd_rules: SrdCombatRules = SrdCombatRules.new()
var _player_combat_state: CombatantState = CombatantState.new()
var _actor_states: Dictionary = {}
var _combat_environment: CombatEnvironment
var _srd_combat_ui: SrdCombatUI
var _death_save_running: bool = false
var _srd_dice: DiceRoller = DiceRoller.new()


func _ready() -> void:
	super._ready()
	_combat_environment = COMBAT_ENVIRONMENT_SCRIPT.new() as CombatEnvironment
	_combat_environment.name = "CombatEnvironment"
	_combat_environment.z_index = 2
	add_child(_combat_environment)
	_srd_combat_ui = SRD_COMBAT_UI_SCRIPT.new() as SrdCombatUI
	_srd_combat_ui.name = "SrdCombatUI"
	$Interface.add_child(_srd_combat_ui)
	_srd_combat_ui.prone_toggle_requested.connect(_on_prone_toggle_requested)
	_srd_combat_ui.grapple_requested.connect(_on_grapple_requested)
	_srd_combat_ui.shove_prone_requested.connect(_on_shove_prone_requested)
	_srd_combat_ui.shove_push_requested.connect(_on_shove_push_requested)
	_srd_combat_ui.escape_grapple_requested.connect(_on_escape_grapple_requested)
	_srd_combat_ui.ready_attack_requested.connect(_on_ready_attack_requested)
	_srd_combat_ui.hide_requested.connect(_on_hide_requested)
	_state_for(player)
	_refresh_srd_interface()


func _process(delta: float) -> void:
	super._process(delta)
	_sync_player_damage_traits()
	_refresh_srd_interface()


func get_player_combat_state() -> CombatantState:
	return _player_combat_state


func get_combatant_state(actor: Node) -> CombatantState:
	return _state_for(actor)


func _state_for(actor: Node) -> CombatantState:
	if actor == null:
		return null
	if actor == player:
		return _player_combat_state
	var actor_id: int = actor.get_instance_id()
	if _actor_states.has(actor_id):
		return _actor_states[actor_id] as CombatantState
	var state := CombatantState.new()
	if actor is TrainingDummy or actor.name == "TrainingDummy":
		state.condition_immunities = [
			"charmed", "deafened", "frightened", "grappled", "paralyzed", "petrified",
			"poisoned", "prone", "restrained", "stunned", "unconscious"
		]
		state.damage_immunities = ["poison", "psychic"]
	_actor_states[actor_id] = state
	return state


func _sync_player_damage_traits() -> void:
	_player_combat_state.damage_resistances.clear()
	if GameState.player_character.character_class_id == "barbarian" and int(GameState.player_character.active_effects.get("rage_attacks", 0)) > 0:
		_player_combat_state.damage_resistances = ["bludgeoning", "piercing", "slashing"]


func _start_turn_based_combat(trigger_target: Node) -> void:
	for target: Node in _available_targets():
		_state_for(target)
	super._start_turn_based_combat(trigger_target)
	_refresh_srd_interface()


func _request_attack() -> void:
	if GameState.input_locked or _any_overlay_visible() or _attack_in_progress or _enemy_turn_running:
		return
	if _turn_system.active and not _turn_system.is_player_turn(player):
		show_combat_message("Атаковать можно только на своём ходу.", false)
		return
	if not _srd_rules.can_take_action(_player_combat_state):
		show_combat_message("Текущее состояние не позволяет совершать действия.", false)
		return

	var weapon: Dictionary = _class_data.get_equipped_weapon(GameState.player_character)
	var selected_before: Node = _selected_target
	var predicted_target: Node = selected_before if _target_is_valid(selected_before) else _predict_directional_target(weapon)
	if _target_is_valid(selected_before) and _target_has_total_cover(selected_before):
		show_combat_message("Цель находится за полным укрытием.", false)
		return
	var valid_attempt: bool = _weapon_attempt_is_valid(weapon, selected_before, predicted_target)
	if _turn_system.active and valid_attempt and not _turn_system.consume_action():
		show_combat_message("Действие на этом ходу уже использовано.", false)
		return

	if _target_is_valid(selected_before):
		_face_toward((selected_before as Node2D).global_position)
		var ammo_id: String = str(weapon.get("ammunition_id", ""))
		await _perform_srd_weapon_attack(selected_before, weapon, ammo_id)
	else:
		if not DistanceSystem.is_ranged_weapon(weapon):
			show_combat_message("Для атаки оружием ближнего боя сначала выберите цель.", false)
			return
		await _request_directional_ranged_attack(weapon)

	if not _turn_system.active and valid_attempt and _target_is_valid(predicted_target):
		_start_turn_based_combat(predicted_target)
	_after_player_action()


func _perform_directional_attack_on_target(target: Node, weapon: Dictionary, ammo_id: String) -> void:
	await _perform_srd_weapon_attack(target, weapon, ammo_id)


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
		_apply_mitigation_to_result(result, _state_for(target))
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


func _build_srd_attack_context(target: Node, distance: int) -> Dictionary:
	var cover: Dictionary = _get_cover_to_target(target)
	return {
		"target_name": _target_name(target),
		"distance_feet": distance,
		"disadvantage": false,
		"ranged_threat": _has_hostile_within_five_feet(),
		"advantage": _player_combat_state.hidden,
		"cover_bonus": int(cover.get("bonus", 0)),
		"total_cover": bool(cover.get("total_cover", false)),
		"attacker_can_see_defender": not bool(cover.get("total_cover", false)),
		"defender_can_see_attacker": not _player_combat_state.hidden,
		"attacker_state": _player_combat_state,
		"defender_state": _state_for(target),
		"target_save_modifier": int(target.call("get_saving_throw_modifier", "dexterity")) if target.has_method("get_saving_throw_modifier") else 0
	}


func _apply_mitigation_to_result(result: AttackResult, state: CombatantState) -> void:
	result.damage_before_mitigation = result.damage
	var mitigation: Dictionary = _srd_rules.resolve_damage(result.damage, result.damage_type, state)
	result.damage = int(mitigation.get("applied", result.damage))
	var absorbed: int = int(mitigation.get("absorbed", 0))
	var reason: String = str(mitigation.get("reason", ""))
	if absorbed > 0:
		result.note = _append_srd_note(result.note, "Временные HP поглотили %d урона." % absorbed)
	if not reason.is_empty():
		result.note = _append_srd_note(result.note, "%s изменяет полученный урон." % reason.capitalize())


func _weapon_attempt_is_valid(weapon: Dictionary, selected_target: Node, predicted_target: Node) -> bool:
	if not _srd_rules.can_take_action(_player_combat_state):
		return false
	if _target_is_valid(selected_target) and _target_has_total_cover(selected_target):
		return false
	return super._weapon_attempt_is_valid(weapon, selected_target, predicted_target)


func _on_ability_requested(ability_id: String) -> void:
	if GameState.input_locked or _attack_in_progress or _enemy_turn_running:
		return
	var ability: Dictionary = _class_data.get_ability_definition(ability_id)
	if ability.is_empty():
		_ability_panel.set_message("Способность не найдена.", false)
		return
	if _turn_system.active and not _turn_system.is_player_turn(player):
		_ability_panel.set_message("Способность можно применить только на своём ходу.", false)
		return
	if not _srd_rules.can_take_action(_player_combat_state):
		_ability_panel.set_message("Текущее состояние не позволяет применять способности.", false)
		return

	var target_type: String = str(ability.get("target", "self"))
	var can_attempt: bool = _ability_attempt_is_valid(ability)
	if _turn_system.active and can_attempt:
		var action_kind: String = _ability_action_kind(ability_id, ability)
		if action_kind == "bonus":
			if not _turn_system.consume_bonus_action():
				_ability_panel.set_message("Бонусное действие уже использовано.", false)
				return
		elif not _turn_system.consume_action():
			_ability_panel.set_message("Действие уже использовано.", false)
			return

	var response: Dictionary = {}
	var trigger_target: Node = null
	if target_type == "self":
		response = _ability_system.use_self_ability(GameState.player_character, ability)
		if bool(response.get("success", false)) and int(response.get("healing", 0)) > 0 and GameState.player_character.current_health > 0:
			_player_combat_state.recover_from_zero_hit_points()
	else:
		if not _target_is_valid(_selected_target):
			_ability_panel.set_message("Сначала выберите боевую цель.", false)
			return
		if _target_has_total_cover(_selected_target):
			_ability_panel.set_message("Цель находится за полным укрытием.", false)
			return
		trigger_target = _selected_target
		var target_position: Vector2 = (trigger_target as Node2D).global_position
		var distance: int = DistanceSystem.distance_feet(player.global_position, target_position)
		var effect: String = str(ability.get("effect", ""))
		if effect == "hunters_mark":
			response = _ability_system.apply_target_ability(GameState.player_character, ability)
			if bool(response.get("success", false)):
				_player_combat_state.set_concentration(ability_id, player.get_instance_id())
		elif effect in ["spell_attack", "auto_hit_spell", "saving_throw_spell"]:
			var context: Dictionary = _build_srd_attack_context(trigger_target, distance)
			var result: AttackResult = _ability_system.perform_offensive_ability(
				GameState.player_character,
				ability,
				int(trigger_target.call("get_armor_class")),
				-1,
				[],
				context
			)
			if result.out_of_range or (result.automatic_miss and not result.note.is_empty()):
				_attack_popup.show_result(result)
				response = {"success": false, "message": result.note}
			else:
				_set_combat_busy(true)
				await _play_magic_projectiles(ability, target_position)
				if result.hit:
					_apply_mitigation_to_result(result, _state_for(trigger_target))
				trigger_target.call("receive_player_attack", result, true)
				_set_combat_busy(false)
				response = {"success": true, "message": "%s применена." % result.attack_name}
			if bool(ability.get("concentration", false)):
				_player_combat_state.set_concentration(ability_id, player.get_instance_id())
		else:
			response = trigger_target.call("receive_signature_ability", ability, true, _build_srd_attack_context(trigger_target, distance)) as Dictionary

	_ability_panel.set_message(str(response.get("message", "Способность применена.")), bool(response.get("success", false)))
	GameState.save_game()
	_update_status()
	_sync_exploration_hud_visibility()
	if not _turn_system.active and trigger_target != null and bool(response.get("success", false)):
		_start_turn_based_combat(trigger_target)
	_after_player_action()


func request_combat_move(step: Vector2i) -> void:
	if not _turn_system.active or not _turn_system.is_player_turn(player):
		return
	if GameState.input_locked or _any_overlay_visible() or _attack_in_progress or _enemy_turn_running:
		return
	if step == Vector2i.ZERO:
		return
	if _srd_rules.effective_speed_feet(30, _player_combat_state) <= 0:
		show_combat_message("Состояние персонажа не позволяет перемещаться.", false)
		return
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return
	var current_cell: Vector2i = grid.world_to_cell(player.global_position)
	var destination_cell: Vector2i = current_cell + step
	if not grid.is_cell_valid(destination_cell):
		show_combat_message("Эта клетка находится за пределами поля боя.", false)
		return
	if _occupied_cells(player).has(destination_cell) or (_combat_environment != null and _combat_environment.is_cell_blocked(grid, destination_cell)):
		show_combat_message("Клетка занята или перекрыта препятствием.", false)
		return
	var destination: Vector2 = grid.cell_to_world_center(destination_cell)
	var difficult: bool = _combat_environment != null and _combat_environment.is_difficult_position(destination)
	var crawling: bool = _player_combat_state.has_condition("prone")
	var movement_cost: int = _srd_rules.movement_cost_feet(GRID_STEP_FEET_SRD, _player_combat_state, difficult, crawling)
	if _player_combat_state.grappling_target_id != 0:
		movement_cost *= 2
	if _turn_system.movement_remaining_feet < movement_cost:
		show_combat_message("Недостаточно перемещения: требуется %d футов." % movement_cost, false)
		return
	if not _turn_system.disengaged:
		_trigger_enemy_opportunity_attacks(player.global_position, destination)
		if _player_combat_state.dead:
			return
	if not _turn_system.spend_movement(movement_cost):
		return
	var previous_position: Vector2 = player.global_position
	player.global_position = destination
	GameState.player_position = destination
	if player.has_method("set_facing_direction"):
		player.call("set_facing_direction", Vector2(step))
	_drag_grappled_target(previous_position)
	_refresh_turn_interface()
	_refresh_srd_interface()


func _begin_current_turn() -> void:
	if not _turn_system.active:
		return
	var actor: Node = _turn_system.current_actor()
	if not is_instance_valid(actor):
		super._begin_current_turn()
		return
	var state: CombatantState = _state_for(actor)
	state.tick_conditions("start_turn")
	if actor == player and GameState.player_character.current_health <= 0:
		_resolve_player_zero_hp_turn()
		return
	if not _srd_rules.can_take_action(state):
		show_combat_message("%s пропускает ход из-за состояния: %s." % [_target_name(actor), _srd_rules.format_conditions(state)], false)
		call_deferred("_advance_combat_turn")
		return
	super._begin_current_turn()


func _advance_combat_turn() -> void:
	if _turn_system.active:
		var previous: Node = _turn_system.current_actor()
		if is_instance_valid(previous):
			_state_for(previous).tick_conditions("end_turn")
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
		var escape: Dictionary = _srd_rules.resolve_d20_test(int(actor.call("get_initiative_modifier")) if actor.has_method("get_initiative_modifier") else 0, escape_dc)
		if bool(escape.get("success", false)):
			state.remove_condition("grappled")
			_release_grapples_for(actor)
		show_combat_message("%s пытается вырваться из захвата." % _target_name(actor), bool(escape.get("success", false)))
	else:
		var movement_feet: int = _srd_rules.effective_speed_feet(int(actor.call("get_combat_speed_feet")) if actor.has_method("get_combat_speed_feet") else 30, state)
		while movement_feet >= GRID_STEP_FEET_SRD and DistanceSystem.distance_feet((actor as Node2D).global_position, player.global_position) > DistanceSystem.MELEE_REACH_FEET:
			var cost: int = _move_enemy_srd_one_step(actor as Node2D, state)
			if cost <= 0 or cost > movement_feet:
				break
			movement_feet -= cost
			await _trigger_readied_attack_if_possible(actor)
			if not _target_is_valid(actor):
				break
			await get_tree().create_timer(0.1).timeout
		if is_instance_valid(actor) and _target_is_valid(actor) and DistanceSystem.distance_feet((actor as Node2D).global_position, player.global_position) <= DistanceSystem.MELEE_REACH_FEET:
			if actor.has_method("perform_combat_turn_attack"):
				actor.call("perform_combat_turn_attack")
				_update_status()
				await get_tree().create_timer(0.35).timeout
	_enemy_turn_running = false
	if not _player_combat_state.dead:
		_advance_combat_turn()


func _move_enemy_srd_one_step(actor: Node2D, state: CombatantState) -> int:
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return 0
	var actor_cell: Vector2i = grid.world_to_cell(actor.global_position)
	var player_cell: Vector2i = grid.world_to_cell(player.global_position)
	var delta: Vector2i = player_cell - actor_cell
	var horizontal: int = 0 if delta.x == 0 else (1 if delta.x > 0 else -1)
	var vertical: int = 0 if delta.y == 0 else (1 if delta.y > 0 else -1)
	var candidates: Array[Vector2i] = []
	if horizontal != 0 or vertical != 0:
		candidates.append(Vector2i(horizontal, vertical))
	if horizontal != 0:
		candidates.append(Vector2i(horizontal, 0))
	if vertical != 0:
		candidates.append(Vector2i(0, vertical))
	var occupied: Dictionary = _occupied_cells(actor)
	for step: Vector2i in candidates:
		var destination_cell: Vector2i = actor_cell + step
		if not grid.is_cell_valid(destination_cell) or occupied.has(destination_cell):
			continue
		if _combat_environment != null and _combat_environment.is_cell_blocked(grid, destination_cell):
			continue
		var destination: Vector2 = grid.cell_to_world_center(destination_cell)
		var difficult: bool = _combat_environment != null and _combat_environment.is_difficult_position(destination)
		var cost: int = _srd_rules.movement_cost_feet(GRID_STEP_FEET_SRD, state, difficult, state.has_condition("prone"))
		actor.global_position = destination
		return cost
	return 0


func resolve_npc_attack(attacker: Node, attack_bonus: int, damage_die: int, damage_bonus: int, damage_type: String = "slashing") -> Dictionary:
	if attacker == null or not (attacker is Node2D):
		return {"hit": false}
	var attacker_state: CombatantState = _state_for(attacker)
	var cover: Dictionary = _combat_environment.get_cover((attacker as Node2D).global_position, player.global_position) if _combat_environment != null else {"bonus": 0, "total_cover": false}
	if bool(cover.get("total_cover", false)):
		show_combat_message("%s не видит героя за полным укрытием." % _target_name(attacker), false)
		return {"hit": false, "total_cover": true}
	var adjustments: Dictionary = _srd_rules.attack_roll_adjustments(attacker_state, _player_combat_state, DistanceSystem.distance_feet((attacker as Node2D).global_position, player.global_position), true, true)
	var disadvantage: bool = bool(adjustments.get("disadvantage", false)) or player_is_dodging()
	var advantage: bool = bool(adjustments.get("advantage", false))
	var roll: Dictionary = _srd_rules.roll_d20(attack_bonus, advantage, disadvantage)
	var natural: int = int(roll.get("natural", 1))
	var target_ac: int = _class_data.get_armor_class(GameState.player_character) + int(cover.get("bonus", 0))
	var hit: bool = natural != 1 and (natural == 20 or int(roll.get("total", 0)) >= target_ac)
	if not hit:
		show_combat_message("%s промахивается: %d против КД %d." % [_target_name(attacker), int(roll.get("total", 0)), target_ac], false)
		return {"hit": false, "natural": natural, "total": int(roll.get("total", 0))}
	var critical: bool = natural == 20 or bool(adjustments.get("automatic_critical", false))
	var damage: int = damage_bonus
	for _index: int in range(2 if critical else 1):
		damage += _srd_dice.roll_die(maxi(damage_die, 2))
	return apply_damage_to_player(damage, damage_type, critical, attacker)


func apply_damage_to_player(amount: int, damage_type: String, critical_hit: bool = false, source: Node = null) -> Dictionary:
	if _player_combat_state.dead:
		return {"applied": 0, "dead": true}
	if GameState.player_character.current_health <= 0:
		var zero_result: Dictionary = _srd_rules.damage_at_zero_hit_points(_player_combat_state, critical_hit)
		show_combat_message("Урон при 0 HP: получено %d провала спасброска смерти." % int(zero_result.get("failures_added", 0)), false)
		if bool(zero_result.get("dead", false)):
			_handle_srd_player_death(source)
		return zero_result
	var mitigation: Dictionary = _srd_rules.resolve_damage(amount, damage_type, _player_combat_state)
	var applied: int = int(mitigation.get("applied", 0))
	var before: int = GameState.player_character.current_health
	GameState.player_character.current_health = maxi(0, before - applied)
	var remaining_damage: int = maxi(applied - before, 0)
	var concentration: Dictionary = _srd_rules.resolve_concentration_check(GameState.player_character.get_ability_modifier("constitution"), applied, _player_combat_state)
	var message: String = "%s наносит %d урона %s. HP: %d/%d." % [
		_target_name(source) if source != null else "Источник",
		applied,
		_srd_rules.normalize_damage_type(damage_type),
		GameState.player_character.current_health,
		GameState.player_character.maximum_health
	]
	if int(mitigation.get("absorbed", 0)) > 0:
		message += " Временные HP поглотили %d." % int(mitigation.get("absorbed", 0))
	if not str(mitigation.get("reason", "")).is_empty():
		message += " Сработало: %s." % str(mitigation.get("reason", ""))
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
	return {"hit": true, "applied": applied, "critical": critical_hit, "dead": _player_combat_state.dead}


func _resolve_player_zero_hp_turn() -> void:
	if _death_save_running:
		return
	_death_save_running = true
	if _player_combat_state.dead:
		_handle_srd_player_death(null)
		_death_save_running = false
		return
	if _player_combat_state.stable:
		show_combat_message("Персонаж стабилен, но остаётся без сознания.", true)
		_death_save_running = false
		call_deferred("_advance_combat_turn")
		return
	var result: Dictionary = _srd_rules.resolve_death_save(_player_combat_state)
	if bool(result.get("regained_hit_point", false)):
		GameState.player_character.current_health = 1
		show_combat_message("Натуральная 20: персонаж приходит в сознание с 1 HP.", true)
		_death_save_running = false
		super._begin_current_turn()
		return
	show_combat_message("Спасбросок смерти: %d · успехи %d/3 · провалы %d/3." % [int(result.get("natural", 0)), int(result.get("successes", 0)), int(result.get("failures", 0))], not bool(result.get("dead", false)))
	_death_save_running = false
	if bool(result.get("dead", false)):
		_handle_srd_player_death(null)
	else:
		call_deferred("_advance_combat_turn")


func _handle_srd_player_death(source: Node) -> void:
	_player_combat_state.dead = true
	if _turn_system.active:
		_stop_turn_based_combat("Персонаж погиб.")
	await super.handle_player_defeat(source)
	_player_combat_state = CombatantState.new()


func handle_player_defeat(source: Node = null) -> void:
	if GameState.player_character.current_health > 0:
		return
	if not _turn_system.active:
		await super.handle_player_defeat(source)
		_player_combat_state = CombatantState.new()


func _on_prone_toggle_requested() -> void:
	if not _player_turn_available():
		return
	if _player_combat_state.has_condition("prone"):
		if _turn_system.movement_remaining_feet < 15:
			show_combat_message("Чтобы встать, требуется 15 футов перемещения.", false)
			return
		_turn_system.spend_movement(15)
		_player_combat_state.remove_condition("prone")
		show_combat_message("Персонаж встаёт, потратив половину базовой скорости.", true)
	else:
		_player_combat_state.add_condition("prone")
		show_combat_message("Персонаж ложится ничком без расхода действия.", true)
	_refresh_srd_interface()


func _on_grapple_requested() -> void:
	if not _player_turn_available() or not _selected_target_in_melee():
		return
	if not _turn_system.consume_action():
		show_combat_message("Для захвата требуется действие.", false)
		return
	var target_state: CombatantState = _state_for(_selected_target)
	var dc: int = 8 + CombatSystem.proficiency_bonus_for_level(GameState.player_character.level) + GameState.player_character.get_ability_modifier("strength")
	var save: Dictionary = _srd_rules.resolve_saving_throw("strength", _target_save_modifier(_selected_target, "strength"), dc, target_state)
	if bool(save.get("success", false)):
		show_combat_message("Цель избегает захвата: %d против Сл %d." % [int(save.get("total", 0)), dc], false)
	else:
		target_state.add_condition("grappled", -1, player.get_instance_id(), "strength", dc)
		target_state.grappled_by_id = player.get_instance_id()
		_player_combat_state.grappling_target_id = _selected_target.get_instance_id()
		show_combat_message("Цель захвачена; её скорость становится 0.", true)
	_refresh_srd_interface()


func _on_shove_prone_requested() -> void:
	if not _player_turn_available() or not _selected_target_in_melee():
		return
	if not _turn_system.consume_action():
		show_combat_message("Для попытки сбить цель требуется действие.", false)
		return
	var target_state: CombatantState = _state_for(_selected_target)
	var dc: int = 8 + CombatSystem.proficiency_bonus_for_level(GameState.player_character.level) + GameState.player_character.get_ability_modifier("strength")
	var save: Dictionary = _srd_rules.resolve_saving_throw("strength", _target_save_modifier(_selected_target, "strength"), dc, target_state)
	if bool(save.get("success", false)):
		show_combat_message("Цель удержалась на ногах.", false)
	else:
		target_state.add_condition("prone")
		show_combat_message("Цель сбита с ног.", true)
	_refresh_srd_interface()


func _on_shove_push_requested() -> void:
	if not _player_turn_available() or not _selected_target_in_melee():
		return
	if not _turn_system.consume_action():
		show_combat_message("Для толчка требуется действие.", false)
		return
	var target_state: CombatantState = _state_for(_selected_target)
	var dc: int = 8 + CombatSystem.proficiency_bonus_for_level(GameState.player_character.level) + GameState.player_character.get_ability_modifier("strength")
	var save: Dictionary = _srd_rules.resolve_saving_throw("strength", _target_save_modifier(_selected_target, "strength"), dc, target_state)
	if bool(save.get("success", false)):
		show_combat_message("Цель сопротивляется толчку.", false)
		return
	var grid: BattleGrid = _get_battle_grid()
	var target_node := _selected_target as Node2D
	var direction: Vector2 = (target_node.global_position - player.global_position).normalized()
	var step := Vector2i(signi(roundi(direction.x)), signi(roundi(direction.y)))
	if step == Vector2i.ZERO:
		step = Vector2i.RIGHT
	var destination_cell: Vector2i = grid.world_to_cell(target_node.global_position) + step
	if not grid.is_cell_valid(destination_cell) or _occupied_cells(target_node).has(destination_cell) or (_combat_environment != null and _combat_environment.is_cell_blocked(grid, destination_cell)):
		show_combat_message("Толчок успешен, но позади цели нет свободной клетки.", false)
		return
	target_node.global_position = grid.cell_to_world_center(destination_cell)
	show_combat_message("Цель оттолкнута на 5 футов.", true)
	_refresh_srd_interface()


func _on_escape_grapple_requested() -> void:
	if not _player_turn_available() or not _player_combat_state.has_condition("grappled"):
		return
	if not _turn_system.consume_action():
		show_combat_message("Для освобождения требуется действие.", false)
		return
	var dc: int = _condition_save_dc(_player_combat_state, "grappled", 10)
	var modifier: int = maxi(GameState.player_character.get_ability_modifier("strength"), GameState.player_character.get_ability_modifier("dexterity"))
	var check: Dictionary = _srd_rules.resolve_d20_test(modifier, dc)
	if bool(check.get("success", false)):
		_player_combat_state.remove_condition("grappled")
		show_combat_message("Персонаж освобождается из захвата.", true)
	else:
		show_combat_message("Не удалось вырваться: %d против Сл %d." % [int(check.get("total", 0)), dc], false)
	_refresh_srd_interface()


func _on_ready_attack_requested() -> void:
	if not _player_turn_available():
		return
	if not _turn_system.consume_action():
		show_combat_message("Для подготовки атаки требуется действие.", false)
		return
	_player_combat_state.readied_attack = true
	show_combat_message("Атака подготовлена и сработает реакцией, когда противник войдёт в дистанцию оружия.", true)


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
		if is_instance_valid(actor) and actor is Node2D and _target_is_valid(actor):
			if _combat_environment == null or _combat_environment.has_line_of_sight((actor as Node2D).global_position, player.global_position):
				show_combat_message("Нельзя скрыться: противник видит персонажа.", false)
				return
	_player_combat_state.hidden = true
	show_combat_message("Персонаж скрыт. Следующая атака получает преимущество и раскрывает позицию.", true)


func _selected_target_in_melee() -> bool:
	if not _target_is_valid(_selected_target):
		show_combat_message("Сначала выберите цель.", false)
		return false
	if DistanceSystem.distance_feet(player.global_position, (_selected_target as Node2D).global_position) > 5:
		show_combat_message("Цель должна находиться в соседней клетке.", false)
		return false
	return true


func _target_save_modifier(target: Node, ability_id: String) -> int:
	return int(target.call("get_saving_throw_modifier", ability_id)) if target != null and target.has_method("get_saving_throw_modifier") else 0


func _condition_save_dc(state: CombatantState, condition_id: String, fallback: int) -> int:
	if state == null or not state.conditions.has(condition_id):
		return fallback
	var value: Variant = state.conditions.get(condition_id, {})
	return int((value as Dictionary).get("save_dc", fallback)) if value is Dictionary else fallback


func _drag_grappled_target(previous_player_position: Vector2) -> void:
	if _player_combat_state.grappling_target_id == 0:
		return
	var target: Node = instance_from_id(_player_combat_state.grappling_target_id) as Node
	if not is_instance_valid(target) or not (target is Node2D):
		_player_combat_state.grappling_target_id = 0
		return
	(target as Node2D).global_position = previous_player_position


func _release_grapples_for(actor: Node) -> void:
	if actor == null:
		return
	var actor_id: int = actor.get_instance_id()
	if _player_combat_state.grappling_target_id == actor_id:
		_player_combat_state.grappling_target_id = 0
	for state_value: Variant in _actor_states.values():
		var state := state_value as CombatantState
		if state.grappled_by_id == actor_id:
			state.remove_condition("grappled")
		if state.grappling_target_id == actor_id:
			state.grappling_target_id = 0


func _trigger_readied_attack_if_possible(actor: Node) -> void:
	if not _player_combat_state.readied_attack or not _turn_system.has_reaction(player) or not _target_is_valid(actor):
		return
	var weapon: Dictionary = _class_data.get_equipped_weapon(GameState.player_character)
	var distance: int = DistanceSystem.distance_feet(player.global_position, (actor as Node2D).global_position)
	if DistanceSystem.weapon_range_state(weapon, distance) == "out_of_range":
		return
	_player_combat_state.readied_attack = false
	_turn_system.consume_reaction(player)
	show_combat_message("Срабатывает подготовленная атака.", true)
	await _perform_srd_weapon_attack(actor, weapon, str(weapon.get("ammunition_id", "")))


func _get_cover_to_target(target: Node) -> Dictionary:
	if _combat_environment == null or not _target_is_valid(target):
		return {"bonus": 0, "total_cover": false, "label": "без укрытия"}
	return _combat_environment.get_cover(player.global_position, (target as Node2D).global_position)


func _target_has_total_cover(target: Node) -> bool:
	return bool(_get_cover_to_target(target).get("total_cover", false))


func _refresh_srd_interface() -> void:
	if _srd_combat_ui == null:
		return
	var target_state: CombatantState = _state_for(_selected_target) if _target_is_valid(_selected_target) else null
	var cover_text: String = str(_get_cover_to_target(_selected_target).get("label", "без укрытия")) if _target_is_valid(_selected_target) else "цель не выбрана"
	_srd_combat_ui.refresh(
		_turn_system.active,
		_turn_system.is_player_turn(player) and not _enemy_turn_running,
		_any_overlay_visible(),
		_turn_system.action_available,
		_turn_system.movement_remaining_feet,
		_player_combat_state,
		target_state,
		cover_text
	)


func _append_srd_note(current: String, addition: String) -> String:
	return addition if current.is_empty() else "%s %s" % [current, addition]
