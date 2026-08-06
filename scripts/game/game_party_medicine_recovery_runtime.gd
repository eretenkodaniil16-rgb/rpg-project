extends "res://scripts/game/game_party_combat_polish_runtime.gd"

const ALLY_MEDICINE_DIFFICULTY_CLASS: int = 10
const ALLY_MEDICINE_SKILL_ID: String = "medicine"
const ALLY_MEDICINE_ACTION_LABEL: String = "МЕДИЦИНА: СТАБИЛИЗИРОВАТЬ"

var _ally_skill_checks: SkillCheckSystem = SkillCheckSystem.new()
var _ally_medicine_running: bool = false


func _build_catalog_entries() -> Dictionary:
	var entries: Dictionary = super._build_catalog_entries()
	var action_entries: Array = entries.get("action", []) as Array
	for value: Variant in action_entries:
		if not value is Dictionary:
			continue
		var entry: Dictionary = value as Dictionary
		if str(entry.get("id", "")) != ALLY_STABILIZE_ACTION_ID:
			continue
		entry["label"] = ALLY_MEDICINE_ACTION_LABEL
		entry["description"] = (
			"Проверка Медицины СЛ %d с набором лекаря. " % ALLY_MEDICINE_DIFFICULTY_CLASS
			+ "Расходует одно применение набора; в бою — основное действие."
		)
	entries["action"] = action_entries
	return entries


func _on_feedback_catalog_action_requested(action_id: String) -> void:
	if action_id == ALLY_STABILIZE_ACTION_ID:
		_attempt_controllable_ally_medicine()
		_refresh_action_catalog()
		return
	if (
		action_id == ITEM_USE_ACTION_PREFIX + HEALERS_KIT_ID
		and _ally_needs_medicine()
	):
		_attempt_controllable_ally_medicine()
		_refresh_action_catalog()
		return
	super._on_feedback_catalog_action_requested(action_id)


func _request_item_use(item_id: String) -> void:
	if item_id == HEALERS_KIT_ID and _ally_needs_medicine():
		var result: Dictionary = _attempt_controllable_ally_medicine()
		show_combat_message(
			str(result.get("message", "Проверка Медицины завершена.")),
			bool(result.get("success", false))
		)
		_update_status()
		_refresh_turn_interface()
		_refresh_action_catalog()
		_sync_exploration_hud_visibility()
		return
	super._request_item_use(item_id)


func _attempt_controllable_ally_medicine(roll_override: int = -1) -> Dictionary:
	if _ally_medicine_running:
		return _medicine_failure("Помощь уже оказывается.")
	if not is_instance_valid(_controllable_ally):
		return _medicine_failure("Союзник недоступен.")
	if not _ally_needs_medicine():
		return _medicine_failure("Ирина не нуждается в стабилизации.")
	if _ally_distance_from_player() > ALLY_INTERACTION_DISTANCE_FEET:
		return _medicine_failure("Чтобы оказать помощь Ирине, нужно стоять в соседней клетке.")
	if GameState.get_item_count(HEALERS_KIT_ID) <= 0:
		return _medicine_failure("Для проверки нужен набор лекаря.")
	if _turn_system.active:
		if not _turn_system.is_player_turn(player) or _enemy_turn_running:
			return _medicine_failure("Помощь можно оказать только на ходу главного героя.")
		if not _turn_system.action_available:
			return _medicine_failure("Основное действие на этом ходу уже использовано.")

	_ally_medicine_running = true
	var context: Dictionary = {
		"source": "ally_medicine_check",
		"target_id": str(_controllable_ally.call("get_actor_id")),
		"difficulty_class": ALLY_MEDICINE_DIFFICULTY_CLASS
	}
	var prepared: Dictionary = _item_use_system.prepare_use(
		GameState,
		HEALERS_KIT_ID,
		_controllable_ally,
		context
	)
	if not bool(prepared.get("success", false)):
		_ally_medicine_running = false
		return prepared

	if _turn_system.active and not _turn_system.consume_action():
		_item_use_system.cancel_prepared_use(GameState, prepared)
		_ally_medicine_running = false
		return _medicine_failure("Основное действие на этом ходу уже использовано.")

	var check: SkillCheckResult = _ally_skill_checks.perform_skill_check(
		GameState.player_character,
		ALLY_MEDICINE_SKILL_ID,
		ALLY_MEDICINE_DIFFICULTY_CLASS,
		0,
		roll_override
	)
	var result: Dictionary
	if check.success:
		result = _item_use_system.execute_prepared_use(
			GameState,
			prepared,
			_controllable_ally,
			context
		)
		if bool(result.get("success", false)):
			result["message"] = (
				"Медицина: d20 %d, итог %d против СЛ %d — успех. "
				% [check.natural_roll, check.total, check.difficulty]
				+ "Ирина стабильна, но остаётся без сознания с 0 HP."
			)
	else:
		var committed: bool = _commit_medicine_supplies(prepared)
		result = {
			"success": false,
			"consumed": committed,
			"message": (
				"Медицина: d20 %d, итог %d против СЛ %d — неудача. "
				% [check.natural_roll, check.total, check.difficulty]
				+ "Ирина продолжает умирать; применение набора израсходовано."
			)
		}

	result["natural_roll"] = check.natural_roll
	result["total"] = check.total
	result["difficulty"] = check.difficulty
	result["medicine_success"] = check.success
	if not _turn_system.active:
		GameState.save_game()
	_ally_medicine_running = false
	show_combat_message(str(result.get("message", "Проверка Медицины завершена.")), bool(result.get("success", false)))
	_update_status()
	_refresh_turn_interface()
	return result


func _commit_medicine_supplies(prepared: Dictionary) -> bool:
	var transaction_id: String = str(prepared.get("transaction_id", ""))
	if transaction_id.is_empty():
		return true
	var commit_value: Variant = GameState.commit_inventory_transaction(transaction_id, false)
	return (
		commit_value is Dictionary
		and bool((commit_value as Dictionary).get("success", false))
	)


func _ally_needs_medicine() -> bool:
	return (
		is_instance_valid(_controllable_ally)
		and _controllable_ally.has_method("can_be_stabilized_with_healers_kit")
		and bool(_controllable_ally.call("can_be_stabilized_with_healers_kit"))
	)


func _on_rest_completed(rest_type: String) -> void:
	var ally_was_unconscious: bool = (
		rest_type == "long"
		and is_instance_valid(_controllable_ally)
		and _ally_current_health() <= 0
		and not bool(_ally_state().dead if _ally_state() != null else false)
	)
	super._on_rest_completed(rest_type)
	if rest_type != "long" or not is_instance_valid(_controllable_ally):
		return
	var state: CombatantState = _ally_state()
	if state != null and state.dead:
		return
	_call_ally("set_current_health", [_ally_maximum_health()])
	GameState.save_game()
	_update_status()
	if ally_was_unconscious:
		show_combat_message(
			"После долгого отдыха Ирина приходит в сознание и полностью восстанавливает HP.",
			true
		)


func attempt_controllable_ally_medicine_for_testing(natural_roll: int) -> Dictionary:
	return _attempt_controllable_ally_medicine(natural_roll)


func recover_controllable_ally_after_long_rest_for_testing() -> void:
	_on_rest_completed("long")


func _medicine_failure(message: String) -> Dictionary:
	show_combat_message(message, false)
	return {"success": false, "message": message}
