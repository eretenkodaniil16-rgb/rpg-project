extends "res://scripts/game/game_combat.gd"

const TURN_BASED_COMBAT_SYSTEM: Script = preload("res://scripts/systems/turn_based_combat_system.gd")
const TURN_COMBAT_UI: Script = preload("res://scripts/ui/turn_combat_ui.gd")
const GRID_STEP_FEET: int = 5

var _turn_system: TurnBasedCombatSystem = TURN_BASED_COMBAT_SYSTEM.new() as TurnBasedCombatSystem
var _turn_ui: TurnCombatUI
var _enemy_turn_running: bool = false


func _ready() -> void:
	super._ready()
	_turn_ui = TURN_COMBAT_UI.new() as TurnCombatUI
	_turn_ui.name = "TurnCombatUI"
	$Interface.add_child(_turn_ui)
	_turn_ui.dash_requested.connect(_on_dash_requested)
	_turn_ui.disengage_requested.connect(_on_disengage_requested)
	_turn_ui.dodge_requested.connect(_on_dodge_requested)
	_turn_ui.end_turn_requested.connect(_on_end_turn_requested)
	_refresh_turn_interface()


func _process(delta: float) -> void:
	super._process(delta)
	_refresh_turn_interface()
	_update_combat_controls()


func is_turn_based_combat_active() -> bool:
	return _turn_system.active


func player_is_dodging() -> bool:
	return _turn_system.active and _turn_system.dodging


func _cycle_target() -> void:
	if _turn_system.active and not _turn_system.is_player_turn(player):
		show_combat_message("Сейчас ход другого участника.", false)
		return
	super._cycle_target()


func _request_attack() -> void:
	if GameState.input_locked or _any_overlay_visible() or _attack_in_progress or _enemy_turn_running:
		return
	if _turn_system.active and not _turn_system.is_player_turn(player):
		show_combat_message("Атаковать можно только на своём ходу.", false)
		return

	var weapon: Dictionary = _class_data.get_equipped_weapon(GameState.player_character)
	var selected_before: Node = _selected_target
	var predicted_target: Node = selected_before if _target_is_valid(selected_before) else _predict_directional_target(weapon)
	var valid_attempt: bool = _weapon_attempt_is_valid(weapon, selected_before, predicted_target)
	if _turn_system.active and valid_attempt and not _turn_system.consume_action():
		show_combat_message("Действие на этом ходу уже использовано.", false)
		return

	await super._request_attack()
	if not _turn_system.active and valid_attempt and _target_is_valid(predicted_target):
		_start_turn_based_combat(predicted_target)
	_after_player_action()


func _on_ability_requested(ability_id: String) -> void:
	if GameState.input_locked or _attack_in_progress or _enemy_turn_running:
		return
	var ability: Dictionary = _class_data.get_ability_definition(ability_id)
	if ability.is_empty():
		await super._on_ability_requested(ability_id)
		return
	if _turn_system.active and not _turn_system.is_player_turn(player):
		_ability_panel.set_message("Способность можно применить только на своём ходу.", false)
		return

	var target_before: Node = _selected_target
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

	await super._on_ability_requested(ability_id)
	var effect: String = str(ability.get("effect", ""))
	if not _turn_system.active and can_attempt and effect in ["spell_attack", "auto_hit_spell"] and _target_is_valid(target_before):
		_start_turn_based_combat(target_before)
	_after_player_action()


func request_combat_move(step: Vector2i) -> void:
	if not _turn_system.active or not _turn_system.is_player_turn(player):
		return
	if GameState.input_locked or _any_overlay_visible() or _attack_in_progress or _enemy_turn_running:
		return
	if step == Vector2i.ZERO:
		return
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return
	var current_cell: Vector2i = grid.world_to_cell(player.global_position)
	var destination_cell: Vector2i = current_cell + step
	if not grid.is_cell_valid(destination_cell):
		show_combat_message("Эта клетка находится за пределами поля боя.", false)
		return
	if _occupied_cells(player).has(destination_cell):
		show_combat_message("Клетка занята другим участником.", false)
		return
	if _turn_system.movement_remaining_feet < GRID_STEP_FEET:
		show_combat_message("На этом ходу не осталось перемещения.", false)
		return
	var destination: Vector2 = grid.cell_to_world_center(destination_cell)
	if not _turn_system.disengaged:
		_trigger_enemy_opportunity_attacks(player.global_position, destination)
		if GameState.player_character.current_health <= 0:
			return
	if not _turn_system.spend_movement(GRID_STEP_FEET):
		return
	player.global_position = destination
	GameState.player_position = destination
	if player.has_method("set_facing_direction"):
		player.call("set_facing_direction", Vector2(step))
	_refresh_turn_interface()


func force_player_turn_for_testing() -> void:
	if _turn_system.active:
		_turn_system.force_current_actor_for_testing(player)
		_begin_current_turn()


func _start_turn_based_combat(trigger_target: Node) -> void:
	if _turn_system.active or not _target_is_valid(trigger_target):
		return
	if trigger_target.has_method("enter_combat_hostile"):
		trigger_target.call("enter_combat_hostile")
	var opponents: Array[Node] = []
	for target: Node in _available_targets():
		var include_target: bool = target == trigger_target
		if target.has_method("is_hostile") and bool(target.call("is_hostile")):
			include_target = true
		if include_target and not opponents.has(target):
			opponents.append(target)
	if opponents.is_empty():
		return
	_snap_combatants_to_cells()
	_turn_system.start_combat(player, opponents, GameState.player_character.get_ability_modifier("dexterity"))
	if player.has_method("set_turn_based_mode"):
		player.call("set_turn_based_mode", true)
	show_combat_message("Начинается пошаговый бой. Инициатива определила порядок ходов.", true)
	_begin_current_turn()


func _snap_combatants_to_cells() -> void:
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return
	var occupied: Dictionary = {}
	var player_cell: Vector2i = grid.snap_actor_to_free_cell(player, occupied)
	occupied[player_cell] = player
	GameState.player_position = player.global_position
	for target: Node in _available_targets():
		if target is Node2D:
			var target_cell: Vector2i = grid.snap_actor_to_free_cell(target as Node2D, occupied)
			occupied[target_cell] = target


func _begin_current_turn() -> void:
	if not _turn_system.active:
		return
	_set_all_turn_markers(false)
	var actor: Node = _turn_system.current_actor()
	if not is_instance_valid(actor):
		_stop_turn_based_combat("Бой завершён: участников не осталось.")
		return
	if actor.has_method("set_turn_active"):
		actor.call("set_turn_active", true)
	var grid: BattleGrid = _get_battle_grid()
	if grid != null:
		grid.set_active_actor(actor)
	_refresh_turn_interface()
	if actor == player:
		show_combat_message("Ваш ход: перемещение, действие и бонусное действие доступны.", true)
	else:
		call_deferred("_run_enemy_turn", actor)


func _run_enemy_turn(actor: Node) -> void:
	if not _turn_system.active or _turn_system.current_actor() != actor:
		return
	_enemy_turn_running = true
	_refresh_turn_interface()
	while _turn_system.active and _any_overlay_visible():
		await get_tree().process_frame
	await get_tree().create_timer(0.35).timeout
	if is_instance_valid(actor) and (not actor.has_method("can_take_combat_turn") or bool(actor.call("can_take_combat_turn"))):
		var movement_feet: int = int(actor.call("get_combat_speed_feet")) if actor.has_method("get_combat_speed_feet") else 30
		while movement_feet >= GRID_STEP_FEET and DistanceSystem.distance_feet((actor as Node2D).global_position, player.global_position) > DistanceSystem.MELEE_REACH_FEET:
			if not _move_enemy_one_step(actor as Node2D):
				break
			movement_feet -= GRID_STEP_FEET
			await get_tree().create_timer(0.12).timeout
		if is_instance_valid(actor) and DistanceSystem.distance_feet((actor as Node2D).global_position, player.global_position) <= DistanceSystem.MELEE_REACH_FEET:
			if actor.has_method("perform_combat_turn_attack"):
				actor.call("perform_combat_turn_attack")
				_update_status()
				await get_tree().create_timer(0.4).timeout
	_enemy_turn_running = false
	if GameState.player_character.current_health > 0:
		_advance_combat_turn()


func _move_enemy_one_step(actor: Node2D) -> bool:
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return false
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
		if grid.is_cell_valid(destination_cell) and not occupied.has(destination_cell):
			actor.global_position = grid.cell_to_world_center(destination_cell)
			return true
	return false


func _advance_combat_turn() -> void:
	if not _turn_system.active:
		return
	var previous: Node = _turn_system.current_actor()
	if is_instance_valid(previous) and previous.has_method("set_turn_active"):
		previous.call("set_turn_active", false)
	if _combat_should_end():
		_stop_turn_based_combat("Бой завершён.")
		return
	_turn_system.advance_turn()
	_begin_current_turn()


func _combat_should_end() -> bool:
	if not _turn_system.active:
		return true
	for entry: Dictionary in _turn_system.entries:
		if bool(entry.get("is_player", false)):
			continue
		var actor: Node = entry.get("node") as Node
		if is_instance_valid(actor) and (not actor.has_method("is_combat_active") or bool(actor.call("is_combat_active"))):
			return false
	return true


func _stop_turn_based_combat(message: String) -> void:
	if not _turn_system.active:
		return
	_set_all_turn_markers(false)
	_turn_system.stop_combat()
	_enemy_turn_running = false
	if player.has_method("set_turn_based_mode"):
		player.call("set_turn_based_mode", false)
	var grid: BattleGrid = _get_battle_grid()
	if grid != null:
		grid.set_active_actor(null)
	_refresh_turn_interface()
	show_combat_message(message, true)


func _set_all_turn_markers(value: bool) -> void:
	for target: Node in get_tree().get_nodes_in_group("combat_targets"):
		if target.has_method("set_turn_active"):
			target.call("set_turn_active", value)


func _trigger_enemy_opportunity_attacks(from_position: Vector2, to_position: Vector2) -> void:
	for entry: Dictionary in _turn_system.entries:
		if bool(entry.get("is_player", false)):
			continue
		var actor: Node = entry.get("node") as Node
		if not is_instance_valid(actor) or not (actor is Node2D):
			continue
		if actor.has_method("is_hostile") and not bool(actor.call("is_hostile")):
			continue
		if not _turn_system.has_reaction(actor):
			continue
		var current_distance: int = DistanceSystem.distance_feet((actor as Node2D).global_position, from_position)
		var future_distance: int = DistanceSystem.distance_feet((actor as Node2D).global_position, to_position)
		if current_distance <= DistanceSystem.MELEE_REACH_FEET and future_distance > DistanceSystem.MELEE_REACH_FEET:
			_turn_system.consume_reaction(actor)
			if actor.has_method("perform_opportunity_attack"):
				actor.call("perform_opportunity_attack")
				if GameState.player_character.current_health <= 0:
					return


func _occupied_cells(excluded_actor: Node = null) -> Dictionary:
	var occupied: Dictionary = {}
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return occupied
	if player != excluded_actor:
		occupied[grid.world_to_cell(player.global_position)] = player
	for target: Node in _available_targets():
		if target != excluded_actor and target is Node2D:
			occupied[grid.world_to_cell((target as Node2D).global_position)] = target
	return occupied


func _predict_directional_target(weapon: Dictionary) -> Node:
	if not DistanceSystem.is_ranged_weapon(weapon):
		return null
	var long_range_feet: int = int(weapon.get("range_long_ft", int(weapon.get("range_normal_ft", 0))))
	if long_range_feet <= 0:
		return null
	var eligible: Array[Node] = []
	for candidate: Node in _available_targets():
		if DistanceSystem.distance_feet(player.global_position, (candidate as Node2D).global_position) <= long_range_feet:
			eligible.append(candidate)
	return DirectionalTargetingSystem.find_first_target(
		player.global_position,
		_get_player_facing_direction(),
		eligible,
		DirectionalTargetingSystem.feet_to_pixels(long_range_feet)
	)


func _weapon_attempt_is_valid(weapon: Dictionary, selected_target: Node, predicted_target: Node) -> bool:
	var ammo_id: String = str(weapon.get("ammunition_id", ""))
	if not ammo_id.is_empty() and not GameState.has_item(ammo_id):
		return false
	if _target_is_valid(selected_target):
		var distance: int = DistanceSystem.distance_feet(player.global_position, (selected_target as Node2D).global_position)
		return DistanceSystem.weapon_range_state(weapon, distance) != "out_of_range"
	if not DistanceSystem.is_ranged_weapon(weapon):
		return false
	return int(weapon.get("range_normal_ft", 0)) > 0 or _target_is_valid(predicted_target)


func _ability_attempt_is_valid(ability: Dictionary) -> bool:
	var target_type: String = str(ability.get("target", "self"))
	if target_type != "self":
		if not _target_is_valid(_selected_target):
			return false
		var maximum_range: int = int(ability.get("range_ft", 5))
		if DistanceSystem.distance_feet(player.global_position, (_selected_target as Node2D).global_position) > maximum_range:
			return false
	var resource_key: String = str(ability.get("resource_key", "unlimited"))
	return resource_key == "unlimited" or resource_key.is_empty() or GameState.player_character.get_resource(resource_key) > 0


func _ability_action_kind(ability_id: String, ability: Dictionary) -> String:
	var explicit_kind: String = str(ability.get("action_type", ""))
	if explicit_kind in ["action", "bonus"]:
		return explicit_kind
	if ability_id in ["rage", "bardic_inspiration", "second_wind", "hunters_mark", "innate_sorcery", "martial_arts"]:
		return "bonus"
	return "action"


func _after_player_action() -> void:
	if _turn_system.active and _combat_should_end():
		_stop_turn_based_combat("Бой завершён.")
	if not _target_is_valid(_selected_target):
		_set_selected_target(null)
	_refresh_turn_interface()


func _on_dash_requested() -> void:
	if not _player_turn_available():
		return
	if _turn_system.use_dash():
		show_combat_message("Рывок: добавлено 30 футов перемещения.", true)
	else:
		show_combat_message("Для Рывка требуется свободное действие.", false)


func _on_disengage_requested() -> void:
	if not _player_turn_available():
		return
	if _turn_system.use_disengage():
		show_combat_message("Отход активен: перемещение не вызывает атак по возможности.", true)
	else:
		show_combat_message("Для Отхода требуется свободное действие.", false)


func _on_dodge_requested() -> void:
	if not _player_turn_available():
		return
	if _turn_system.use_dodge():
		show_combat_message("Уклонение активно до начала следующего хода.", true)
	else:
		show_combat_message("Для Уклонения требуется свободное действие.", false)


func _on_end_turn_requested() -> void:
	if _player_turn_available():
		_advance_combat_turn()


func _player_turn_available() -> bool:
	if not _turn_system.active or not _turn_system.is_player_turn(player) or _enemy_turn_running:
		show_combat_message("Сейчас не ваш ход.", false)
		return false
	return true


func _refresh_turn_interface() -> void:
	if _turn_ui != null:
		_turn_ui.refresh(_turn_system, player, _any_overlay_visible(), _enemy_turn_running)


func _update_combat_controls() -> void:
	var player_can_act: bool = not _turn_system.active or (_turn_system.is_player_turn(player) and not _enemy_turn_running)
	if _attack_button != null:
		_attack_button.disabled = _attack_in_progress or not player_can_act or (_turn_system.active and not _turn_system.action_available)
	if _target_button != null:
		_target_button.disabled = _attack_in_progress or not player_can_act


func _get_battle_grid() -> BattleGrid:
	return _battle_grid as BattleGrid if _battle_grid is BattleGrid else null


func handle_player_defeat(source: Node = null) -> void:
	if _turn_system.active:
		_stop_turn_based_combat("Персонаж повержен; пошаговый бой прекращён.")
	await super.handle_player_defeat(source)
