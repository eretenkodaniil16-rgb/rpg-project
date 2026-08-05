extends "res://scripts/game/game_party_control_social_entry_runtime.gd"

const PLAYER_PARTY_MEMBER_ID: String = "player_character"
const IRINA_PARTY_MEMBER_ID: String = "companion_irna_guard_01"

var _exploration_controlled_actor: Node = null
var _exploration_mobile_vector: Vector2 = Vector2.ZERO
var _party_menu_ui: PartyMenuUI = null


func _ready() -> void:
	super._ready()
	_exploration_controlled_actor = player
	_apply_exploration_control_owner(player)
	_replace_bound_handler(
		_target_button,
		&"pressed",
		&"_on_feedback_target_requested",
		Callable(self, "_on_party_target_requested")
	)
	call_deferred("_bind_party_menu")


func _process(delta: float) -> void:
	super._process(delta)
	_validate_exploration_control_owner()
	_refresh_party_menu()


func _bind_party_menu() -> void:
	_party_menu_ui = get_node_or_null("Interface/PartyMenuUI") as PartyMenuUI
	if _party_menu_ui == null:
		push_error("PartyMenuUI is missing from the game scene.")
		return
	var callback := Callable(self, "_on_party_member_control_requested")
	if not _party_menu_ui.member_control_requested.is_connected(callback):
		_party_menu_ui.member_control_requested.connect(callback)
	_refresh_party_menu()


func _on_party_target_requested() -> void:
	_close_action_catalog_immediately()
	if _is_controllable_ally_turn():
		if GameState.input_locked or _attack_in_progress or _any_overlay_visible():
			return
		_cycle_ally_target()
		_refresh_party_menu()
		return
	super._on_feedback_target_requested()


func _on_party_member_control_requested(character_id: String) -> void:
	var requested_actor: Node = _party_actor_for_id(character_id)
	if not is_instance_valid(requested_actor):
		show_combat_message("Этот участник отряда недоступен.", false)
		_refresh_party_menu()
		return
	if _turn_system.active:
		var current_actor: Node = _turn_system.current_actor()
		if requested_actor != current_actor:
			show_combat_message("В бою активного персонажа определяет инициатива.", false)
		_refresh_party_menu()
		return
	if requested_actor == _controllable_ally and not _irina_can_be_manually_controlled():
		show_combat_message("Ирина сейчас не может перемещаться самостоятельно.", false)
		_apply_exploration_control_owner(player)
		_refresh_party_menu()
		return
	_apply_exploration_control_owner(requested_actor)
	show_combat_message(
		"Управление передано Ирине." if requested_actor == _controllable_ally else "Управление возвращено герою. Ирина снова следует за ним.",
		true
	)
	_refresh_party_menu()


func _apply_exploration_control_owner(actor: Node) -> void:
	if not is_instance_valid(actor):
		actor = player
	_exploration_controlled_actor = actor
	_exploration_mobile_vector = Vector2.ZERO
	if is_instance_valid(player):
		if player.has_method("set_party_input_enabled"):
			player.call("set_party_input_enabled", actor == player)
		if player.has_method("set_mobile_vector"):
			player.call("set_mobile_vector", Vector2.ZERO)
		if player.has_method("clear_mobile_facing_input"):
			player.call("clear_mobile_facing_input")
	if is_instance_valid(_controllable_ally):
		_call_ally("set_manual_move_vector", [Vector2.ZERO])
		_call_ally("set_manual_control_enabled", [actor == _controllable_ally])


func _validate_exploration_control_owner() -> void:
	if _turn_system.active:
		return
	if not is_instance_valid(_exploration_controlled_actor):
		_apply_exploration_control_owner(player)
		return
	if _exploration_controlled_actor == _controllable_ally and not _irina_can_be_manually_controlled():
		_apply_exploration_control_owner(player)


func _party_actor_for_id(character_id: String) -> Node:
	match character_id:
		PLAYER_PARTY_MEMBER_ID:
			return player
		IRINA_PARTY_MEMBER_ID:
			return _controllable_ally
		_:
			return null


func _party_member_id_for_actor(actor: Node) -> String:
	if actor == player:
		return PLAYER_PARTY_MEMBER_ID
	if actor == _controllable_ally:
		return IRINA_PARTY_MEMBER_ID
	return ""


func _irina_can_be_manually_controlled() -> bool:
	if not is_instance_valid(_controllable_ally):
		return false
	var state: CombatantState = _ally_state()
	return (
		state != null
		and not state.dead
		and _ally_current_health() > 0
		and not state.has_condition("incapacitated")
		and not state.has_condition("unconscious")
	)


func _refresh_party_menu() -> void:
	if _party_menu_ui == null:
		return
	var combat_active: bool = _turn_system.active
	var active_actor: Node = _exploration_controlled_actor
	var enemy_turn: bool = false
	if combat_active:
		if _turn_system.is_player_controlled_turn() and not _enemy_turn_running:
			active_actor = _turn_system.current_actor()
		else:
			active_actor = null
			enemy_turn = true
	var irina_following: bool = true
	if is_instance_valid(_controllable_ally) and _controllable_ally.has_method("is_following_player"):
		irina_following = bool(_controllable_ally.call("is_following_player"))
	_party_menu_ui.refresh_party_state({
		"active_member_id": _party_member_id_for_actor(active_actor),
		"combat_active": combat_active,
		"enemy_turn": enemy_turn,
		"player_hp": GameState.player_character.current_health,
		"player_max_hp": GameState.player_character.maximum_health,
		"irina_hp": _ally_current_health(),
		"irina_max_hp": _ally_maximum_health(),
		"irina_following": irina_following,
		"irina_available": _irina_can_be_manually_controlled()
	})


func set_mobile_control_vector(direction: Vector2) -> void:
	if _turn_system.active:
		super.set_mobile_control_vector(direction)
		return
	var normalized: Vector2 = direction.limit_length(1.0)
	_exploration_mobile_vector = normalized
	if _exploration_controlled_actor == _controllable_ally:
		if is_instance_valid(player) and player.has_method("set_mobile_vector"):
			player.call("set_mobile_vector", Vector2.ZERO)
		_call_ally("set_manual_move_vector", [normalized])
		return
	_call_ally("set_manual_move_vector", [Vector2.ZERO])
	if is_instance_valid(player) and player.has_method("set_mobile_vector"):
		player.call("set_mobile_vector", normalized)


func clear_mobile_control_vector() -> void:
	if _turn_system.active:
		super.clear_mobile_control_vector()
		return
	set_mobile_control_vector(Vector2.ZERO)


func get_mobile_control_vector_for_testing() -> Vector2:
	if _turn_system.active:
		return super.get_mobile_control_vector_for_testing()
	return _exploration_mobile_vector


func is_controlled_actor_input_owner(actor: Node) -> bool:
	if _turn_system.active:
		return super.is_controlled_actor_input_owner(actor)
	return actor == _exploration_controlled_actor


func get_active_player_controlled_actor() -> Node:
	if _turn_system.active:
		return super.get_active_player_controlled_actor()
	return _exploration_controlled_actor


func _begin_current_turn() -> void:
	super._begin_current_turn()
	_refresh_party_menu()


func _stop_turn_based_combat(message: String) -> void:
	super._stop_turn_based_combat(message)
	_apply_exploration_control_owner(_exploration_controlled_actor)
	_refresh_party_menu()


func place_controllable_ally_adjacent_for_testing(target: Node) -> bool:
	if not is_instance_valid(target) or not target is Node2D or not _controllable_ally is Node2D:
		return false
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return false
	var target_position: Vector2 = (target as Node2D).global_position
	var target_cell: Vector2i = grid.world_to_cell(target_position)
	var occupied: Dictionary = _occupied_cells(_controllable_ally)
	for offset: Vector2i in [Vector2i.LEFT, Vector2i.RIGHT, Vector2i.UP, Vector2i.DOWN]:
		var candidate: Vector2i = target_cell + offset
		if not grid.is_cell_valid(candidate) or occupied.has(candidate):
			continue
		if _combat_environment != null:
			if _combat_environment.is_cell_blocked(grid, candidate):
				continue
			if _combat_environment.is_transition_blocked(grid, candidate, target_cell):
				continue
			var candidate_position: Vector2 = grid.cell_to_world_center(candidate)
			var cover: Dictionary = _combat_environment.get_cover(candidate_position, target_position)
			if bool(cover.get("total_cover", false)):
				continue
		(_controllable_ally as Node2D).global_position = grid.cell_to_world_center(candidate)
		return true
	return false


func get_exploration_controlled_actor_for_testing() -> Node:
	return _exploration_controlled_actor


func get_party_menu_snapshot_for_testing() -> Dictionary:
	return _party_menu_ui.get_snapshot_for_testing() if _party_menu_ui != null else {}


func request_party_member_control_for_testing(character_id: String) -> void:
	_on_party_member_control_requested(character_id)
