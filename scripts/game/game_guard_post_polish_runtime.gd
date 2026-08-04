extends "res://scripts/game/game_consumable_inventory_base_runtime.gd"


func _target_is_valid(target: Node) -> bool:
	# Neutral world actors remain valid informational targets before combat even
	# though they are deliberately absent from combat_targets and initiative.
	if not _turn_system.active and is_instance_valid(target) and target.is_in_group("context_action_targets"):
		if not target is Node2D:
			return false
		if target.has_method("is_combat_active") and not bool(target.call("is_combat_active")):
			return false
		return _target_is_visible_to_player(target)
	return super._target_is_valid(target)


func _cycle_target() -> void:
	if _turn_system.active:
		super._cycle_target()
		return
	_cycle_exploration_context_target()


func _on_feedback_target_requested() -> void:
	_close_action_catalog_immediately()
	if not _turn_system.active:
		if GameState.input_locked or _attack_in_progress or _any_overlay_visible():
			return
		_cycle_exploration_context_target()
		return
	super._on_feedback_target_requested()


func _cycle_exploration_context_target() -> void:
	var targets: Array[Node] = []
	for target: Node in _context_targets():
		if _target_is_valid(target):
			targets.append(target)
	if targets.is_empty():
		_set_selected_target(null)
		show_combat_message("В поле зрения нет доступных целей.", false)
		return
	var current_index: int = targets.find(_selected_target)
	if current_index < 0:
		_set_selected_target(targets[0])
		show_combat_message("Цель выбрана. Нажмите ДЕЙСТВИЯ, чтобы осмотреть её.", true)
	elif current_index + 1 < targets.size():
		_set_selected_target(targets[current_index + 1])
		show_combat_message("Выбрана следующая видимая цель.", true)
	else:
		_set_selected_target(null)
		show_combat_message("Цель снята.", true)


func _update_exploration_alerts(delta: float) -> void:
	# Fog, room concealment and the non-blocking Actions catalogue affect only
	# presentation and player input. They must never stop the world simulation.
	# The inherited pursuit layer paused every observer while any overlay was
	# visible, which made the service guard appear to lose its AI off-screen.
	if GameState.input_locked:
		return
	for actor: Node in _exploration_alert_actors():
		_update_exploration_actor(actor, delta)


func _request_directional_ranged_attack(weapon: Dictionary) -> void:
	var normal_range: int = int(weapon.get("range_normal_ft", 0))
	var long_range: int = int(weapon.get("range_long_ft", normal_range))
	if normal_range <= 0 or long_range <= 0:
		show_combat_message("У оружия не задана дальность.", false)
		return
	var direction: Vector2 = player.get_facing_direction()
	var target: Node = _find_directional_ranged_target(
		weapon,
		direction,
		_eligible_targets_for_free_aim()
	)
	var ammo_id: String = str(weapon.get("ammunition_id", ""))
	if _target_is_valid(target):
		await _perform_directional_attack_on_target(target, weapon, ammo_id)
		return

	var endpoint: Vector2 = player.global_position + direction * DistanceSystem.feet_to_pixels(normal_range)
	var consumable_item_id: String = _weapon_consumable_item_id(weapon, ammo_id, normal_range)
	var transaction_id: String = ""
	if not consumable_item_id.is_empty():
		var reservation: Dictionary = GameState.reserve_inventory_item(
			consumable_item_id,
			1,
			"directional_empty_attack",
			{
				"weapon_id": str(weapon.get("id", "")),
				"endpoint": [endpoint.x, endpoint.y],
				"distance_feet": normal_range
			}
		)
		if not bool(reservation.get("success", false)):
			var definition: Dictionary = GameState.get_item_definition(consumable_item_id)
			show_combat_message(
				"Нет подходящего расходуемого предмета: %s." % str(definition.get("name", consumable_item_id)),
				false
			)
			return
		transaction_id = str(reservation.get("transaction_id", ""))
		var committed: Dictionary = GameState.commit_inventory_transaction(transaction_id, false)
		if not bool(committed.get("success", false)):
			show_combat_message("Не удалось подтвердить расход предмета. Атака отменена.", false)
			return

	_set_combat_busy(true)
	await _play_weapon_projectile(weapon, endpoint, false)
	if _is_recoverable_thrown_attack(weapon, normal_range):
		_ensure_dropped_inventory_manager()
		if _dropped_inventory_manager != null:
			_dropped_inventory_manager.spawn_dropped_item(
				str(weapon.get("id", "")),
				1,
				_thrown_landing_position(endpoint, false)
			)
	_set_combat_busy(false)
	GameState.save_game()
	_update_status()
	show_combat_message("Снаряд ушёл по направлению взгляда, но никого не задел.", false)


func resolve_transactional_weapon_attack_for_testing(
	target: Node,
	weapon: Dictionary,
	ammo_id: String,
	attack_roll_override: int
) -> Dictionary:
	# Deterministic integration hook: it exercises the same inventory reservation,
	# CombatSystem resolution, commit/rollback and thrown-item persistence as the
	# production path, but intentionally skips Tween presentation.
	if not _target_is_valid(target):
		return {"success": false, "status": "invalid_target"}
	var target_position: Vector2 = (target as Node2D).global_position
	var distance: int = DistanceSystem.distance_feet(player.global_position, target_position)
	var consumable_item_id: String = _weapon_consumable_item_id(weapon, ammo_id, distance)
	var transaction_id: String = ""
	var context: Dictionary = _build_srd_attack_context(target, distance)
	if not consumable_item_id.is_empty():
		var reservation: Dictionary = GameState.reserve_inventory_item(
			consumable_item_id,
			1,
			"weapon_attack_test",
			{
				"weapon_id": str(weapon.get("id", "")),
				"target_instance_id": target.get_instance_id(),
				"distance_feet": distance
			}
		)
		if not bool(reservation.get("success", false)):
			context["no_ammunition"] = true
		else:
			transaction_id = str(reservation.get("transaction_id", ""))
			context["no_ammunition"] = false
	else:
		context["no_ammunition"] = false

	var result: AttackResult = _combat_system.perform_basic_attack(
		GameState.player_character,
		int(target.call("get_armor_class")),
		weapon,
		attack_roll_override,
		[],
		context
	)
	var rejected_before_attack: bool = (
		result.out_of_range
		or result.no_ammunition
		or (
			result.automatic_miss
			and result.natural_roll <= 0
			and not result.note.is_empty()
		)
	)
	if rejected_before_attack:
		if not transaction_id.is_empty():
			GameState.rollback_inventory_transaction(transaction_id)
		return {
			"success": true,
			"status": "rejected",
			"consumed": false,
			"natural_roll": result.natural_roll,
			"hit": result.hit,
			"out_of_range": result.out_of_range,
			"no_ammunition": result.no_ammunition
		}

	if not transaction_id.is_empty():
		var committed: Dictionary = GameState.commit_inventory_transaction(
			transaction_id,
			false
		)
		if not bool(committed.get("success", false)):
			return {
				"success": false,
				"status": "commit_failed",
				"consumed": false
			}

	var drop_id: String = ""
	if _is_recoverable_thrown_attack(weapon, distance):
		_ensure_dropped_inventory_manager()
		if _dropped_inventory_manager != null:
			var dropped: DroppedInventoryItem = _dropped_inventory_manager.spawn_dropped_item(
				str(weapon.get("id", "")),
				1,
				_thrown_landing_position(target_position, result.hit)
			)
			if dropped != null:
				drop_id = dropped.get_drop_id()
	GameState.save_game()
	return {
		"success": true,
		"status": "resolved",
		"consumed": not consumable_item_id.is_empty(),
		"consumed_item_id": consumable_item_id,
		"natural_roll": result.natural_roll,
		"hit": result.hit,
		"out_of_range": result.out_of_range,
		"no_ammunition": result.no_ammunition,
		"drop_id": drop_id
	}
