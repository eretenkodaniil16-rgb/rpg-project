extends "res://scripts/game/game_controllable_ally_control_runtime.gd"

const ALLY_MOBILE_DEAD_ZONE: float = 0.25
const ALLY_MOBILE_MOVE_REPEAT_SECONDS: float = 0.18
const ALLY_WORLD_INTERACTION_PREFIX: String = "world_interact"

var _party_mobile_vector: Vector2 = Vector2.ZERO
var _party_mobile_last_step: Vector2i = Vector2i.ZERO
var _party_mobile_move_cooldown: float = 0.0


func _process(delta: float) -> void:
	super._process(delta)
	_process_controllable_ally_mobile_movement(delta)


func set_mobile_control_vector(direction: Vector2) -> void:
	var normalized: Vector2 = direction.limit_length(1.0)
	if _is_controllable_ally_turn():
		_party_mobile_vector = normalized
		if is_instance_valid(player):
			if player.has_method("set_mobile_vector"):
				player.call("set_mobile_vector", Vector2.ZERO)
			if player.has_method("clear_mobile_facing_input"):
				player.call("clear_mobile_facing_input")
		if normalized.length() >= ALLY_MOBILE_DEAD_ZONE:
			_call_ally("set_facing_direction", [normalized])
		return

	_clear_ally_mobile_input()
	if not is_instance_valid(player):
		return
	if _turn_system.active and not _turn_system.is_player_turn(player):
		if player.has_method("clear_mobile_facing_input"):
			player.call("clear_mobile_facing_input")
		return
	if player.has_method("set_mobile_facing_vector"):
		player.call("set_mobile_facing_vector", normalized)


func clear_mobile_control_vector() -> void:
	set_mobile_control_vector(Vector2.ZERO)


func get_mobile_control_vector_for_testing() -> Vector2:
	if _is_controllable_ally_turn():
		return _party_mobile_vector
	if is_instance_valid(player) and player.has_method("get_mobile_facing_direction"):
		return player.call("get_mobile_facing_direction") as Vector2
	return Vector2.ZERO


func is_player_combat_turn() -> bool:
	return _is_controllable_ally_turn() or super.is_player_combat_turn()


func _process_controllable_ally_mobile_movement(delta: float) -> void:
	_party_mobile_move_cooldown = maxf(_party_mobile_move_cooldown - delta, 0.0)
	if not _is_controllable_ally_turn():
		_clear_ally_mobile_input()
		return
	if not _ally_turn_input_available():
		return

	var step := Vector2i(
		int(signf(_party_mobile_vector.x)) if absf(_party_mobile_vector.x) >= ALLY_MOBILE_DEAD_ZONE else 0,
		int(signf(_party_mobile_vector.y)) if absf(_party_mobile_vector.y) >= ALLY_MOBILE_DEAD_ZONE else 0
	)
	if step == Vector2i.ZERO:
		_party_mobile_last_step = Vector2i.ZERO
		_party_mobile_move_cooldown = 0.0
		return
	if step == _party_mobile_last_step and _party_mobile_move_cooldown > 0.0:
		return

	_party_mobile_last_step = step
	_try_move_controllable_ally(step)
	_party_mobile_move_cooldown = ALLY_MOBILE_MOVE_REPEAT_SECONDS


func _clear_ally_mobile_input() -> void:
	_party_mobile_vector = Vector2.ZERO
	_party_mobile_last_step = Vector2i.ZERO
	_party_mobile_move_cooldown = 0.0


func _begin_controllable_ally_turn() -> void:
	_clear_ally_mobile_input()
	super._begin_controllable_ally_turn()
	_refresh_action_catalog()


func _advance_combat_turn() -> void:
	_clear_ally_mobile_input()
	super._advance_combat_turn()


func _stop_turn_based_combat(message: String) -> void:
	_clear_ally_mobile_input()
	super._stop_turn_based_combat(message)


func _build_catalog_entries() -> Dictionary:
	if not _is_controllable_ally_turn():
		return super._build_catalog_entries()

	var ally_state: CombatantState = _ally_state()
	var can_act: bool = (
		ally_state != null
		and _turn_system.action_available
		and _srd_rules.can_take_action(ally_state)
	)
	var target_melee: bool = (
		_target_is_valid(_selected_target)
		and _controllable_ally is Node2D
		and DistanceSystem.distance_feet(
			(_controllable_ally as Node2D).global_position,
			(_selected_target as Node2D).global_position
		) <= 5
	)
	var target_label: String = "ВЫБРАТЬ ЦЕЛЬ"
	if _target_is_valid(_selected_target):
		target_label = "СМЕНИТЬ ЦЕЛЬ"

	var action_entries: Array[Dictionary] = [
		_entry("select_ally_target", target_label, true, "Выбрать следующего видимого противника для Ирины.", "target"),
		_entry("attack", "АТАКА КОРОТКИМ МЕЧОМ", can_act, "Атаковать выбранную цель. Расходует основное действие.", "attack"),
		_entry("dash", "РЫВОК", can_act, "Удвоить доступное перемещение Ирины. Расходует основное действие.", "movement"),
		_entry("disengage", "ОТХОД", can_act, "До конца хода перемещение Ирины не вызывает атак по возможности.", "movement"),
		_entry("dodge", "УКЛОНЕНИЕ", can_act, "Атаки видимых противников получают помеху до начала следующего хода Ирины.", "tactic"),
		_entry("end_turn", "ЗАВЕРШИТЬ ХОД ИРИНЫ", true, "Передать инициативу следующему участнику.", "tactic")
	]
	if target_melee:
		action_entries[1]["description"] = "Выбранная цель находится в пределах 5 футов. Расходует основное действие."
	var reaction_entries: Array[Dictionary] = [
		_entry(
			"ally_reaction_status",
			"РЕАКЦИЯ ГОТОВА" if _turn_system.has_reaction(_controllable_ally) else "РЕАКЦИЯ ИСПОЛЬЗОВАНА",
			false,
			"Реакция Ирины расходуется по правилам боя.",
			"tactic"
		)
	]
	return {"action": action_entries, "bonus": [], "reaction": reaction_entries}


func _refresh_action_catalog() -> void:
	if not _is_controllable_ally_turn():
		super._refresh_action_catalog()
		return
	if _action_catalog_ui == null:
		return
	var resource_text: String = "Ирина · Раунд %d · Действие: %s · Реакция: %s · Перемещение: %d футов" % [
		_turn_system.round_number,
		"готово" if _turn_system.action_available else "использовано",
		"готова" if _turn_system.has_reaction(_controllable_ally) else "использована",
		_turn_system.movement_remaining_feet
	]
	_action_catalog_ui.refresh(
		true,
		true,
		_any_overlay_visible(),
		_build_catalog_entries(),
		resource_text,
		"управление джойстиком",
		false,
		0
	)


func _on_feedback_catalog_action_requested(action_id: String) -> void:
	if not _is_controllable_ally_turn():
		super._on_feedback_catalog_action_requested(action_id)
		return
	if action_id.begins_with(ALLY_WORLD_INTERACTION_PREFIX):
		show_combat_message("Взаимодействия с миром выполняет основной герой на своём ходу.", false)
		return
	match action_id:
		"select_ally_target":
			_cycle_ally_target()
		"attack":
			_request_controllable_ally_attack()
		"dash":
			_on_dash_requested()
		"disengage":
			_on_disengage_requested()
		"dodge":
			_on_dodge_requested()
		"end_turn":
			_on_end_turn_requested()
		_:
			show_combat_message("Это действие недоступно Ирине.", false)
	_invalidate_reachable_area()
	_refresh_action_catalog()
