extends "res://scripts/game/game_guard_post_stable_combat_start_runtime.gd"

const DROPPED_ITEM_MANAGER_SCRIPT: Script = preload("res://scripts/game/dropped_inventory_item_manager.gd")
const PICKUP_DROPPED_PREFIX: String = "pickup_dropped_inventory:"

var _dropped_inventory_manager: DroppedInventoryItemManager = null


func _ready() -> void:
	super._ready()
	_ensure_dropped_inventory_manager()


func _perform_srd_weapon_attack(target: Node, weapon: Dictionary, ammo_id: String) -> void:
	await _perform_transactional_weapon_attack(target, weapon, ammo_id, -1)


func perform_transactional_weapon_attack_for_testing(
	target: Node,
	weapon: Dictionary,
	ammo_id: String,
	attack_roll_override: int
) -> void:
	await _perform_transactional_weapon_attack(
		target,
		weapon,
		ammo_id,
		attack_roll_override
	)


func _perform_transactional_weapon_attack(
	target: Node,
	weapon: Dictionary,
	ammo_id: String,
	attack_roll_override: int
) -> void:
	if not _target_is_valid(target):
		return
	var target_position: Vector2 = (target as Node2D).global_position
	var distance: int = DistanceSystem.distance_feet(player.global_position, target_position)
	var consumable_item_id: String = _weapon_consumable_item_id(weapon, ammo_id, distance)
	var transaction_id: String = ""
	var context: Dictionary = _build_srd_attack_context(target, distance)
	if not consumable_item_id.is_empty():
		var reservation: Dictionary = GameState.reserve_inventory_item(
			consumable_item_id,
			1,
			"weapon_attack",
			{
				"weapon_id": str(weapon.get("id", "")),
				"target_instance_id": target.get_instance_id(),
				"distance_feet": distance
			}
		)
		if bool(reservation.get("success", false)):
			transaction_id = str(reservation.get("transaction_id", ""))
			context["no_ammunition"] = false
		else:
			context["no_ammunition"] = true
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
		_attack_popup.show_result(result)
		_sync_exploration_hud_visibility()
		return

	if not transaction_id.is_empty():
		var committed: Dictionary = GameState.commit_inventory_transaction(
			transaction_id,
			false
		)
		if not bool(committed.get("success", false)):
			show_combat_message("Не удалось подтвердить расход предмета. Атака отменена.", false)
			_sync_exploration_hud_visibility()
			return

	_set_combat_busy(true)
	if result.hit:
		_apply_mitigation_to_result(result, _state_for(target))
	var ranged_attack: bool = DistanceSystem.is_ranged_attack(weapon, distance)
	if ranged_attack:
		await _play_weapon_projectile(weapon, target_position, result.hit)
	else:
		player.play_attack_animation(target_position)
	if _is_recoverable_thrown_attack(weapon, distance):
		_ensure_dropped_inventory_manager()
		if _dropped_inventory_manager != null:
			_dropped_inventory_manager.spawn_dropped_item(
				str(weapon.get("id", "")),
				1,
				_thrown_landing_position(target_position, result.hit)
			)
	if _target_is_valid(target):
		target.call("receive_player_attack", result, true)
		if int(target.call("get_current_health")) <= 0:
			_release_grapples_for(target)
	_update_status()
	_set_combat_busy(false)
	# Capture only after the animation and damage application are complete. The
	# world readiness guard intentionally rejects snapshots during an active attack.
	GameState.save_game()
	_sync_exploration_hud_visibility()


func _weapon_attempt_is_valid(
	weapon: Dictionary,
	selected_target: Node,
	predicted_target: Node
) -> bool:
	if not super._weapon_attempt_is_valid(weapon, selected_target, predicted_target):
		return false
	var ammo_id: String = str(weapon.get("ammunition_id", ""))
	if not ammo_id.is_empty():
		return GameState.can_reserve_inventory_item(ammo_id, 1)
	var properties_value: Variant = weapon.get("properties", [])
	if properties_value is Array and "thrown" in (properties_value as Array):
		var weapon_id: String = str(weapon.get("id", ""))
		return (
			not weapon_id.is_empty()
			and GameState.can_reserve_inventory_item(weapon_id, 1)
		)
	# Empty melee swings remain valid in the target-free control mode. They do not
	# reserve or consume an inventory resource.
	return true


func _build_catalog_entries() -> Dictionary:
	var entries: Dictionary = super._build_catalog_entries()
	_enrich_attack_entry(entries)
	_append_dropped_item_entries(entries)
	return entries


func _on_feedback_catalog_action_requested(action_id: String) -> void:
	if action_id.begins_with(PICKUP_DROPPED_PREFIX):
		_pickup_dropped_item(action_id.trim_prefix(PICKUP_DROPPED_PREFIX))
		_invalidate_reachable_area()
		_refresh_action_catalog()
		return
	super._on_feedback_catalog_action_requested(action_id)


func _pickup_dropped_item(drop_id: String) -> void:
	var dropped: DroppedInventoryItem = _nearby_drop_by_id(drop_id)
	if dropped == null or not dropped.is_available_for_pickup():
		show_combat_message("Этот предмет больше недоступен.", false)
		return
	if not _can_fit_dropped_item(dropped):
		show_combat_message("В инвентаре нет места для этого предмета.", false)
		return
	if _turn_system.active:
		if not _turn_system.is_player_turn(player) or _enemy_turn_running:
			show_combat_message("Подбирать предмет можно только на своём ходу.", false)
			return
		if not _turn_system.consume_bonus_action():
			show_combat_message("Дополнительное действие уже использовано.", false)
			return
	if not dropped.collect():
		show_combat_message("Не удалось подобрать предмет.", false)
		return
	_refresh_turn_interface()
	_refresh_action_catalog()


func _append_dropped_item_entries(entries: Dictionary) -> void:
	var nearby: Array[DroppedInventoryItem] = _registered_nearby_drops()
	if nearby.is_empty():
		return
	var category_id: String = "bonus" if _turn_system.active else "action"
	var category_entries: Array = entries.get(category_id, []) as Array
	for dropped: DroppedInventoryItem in nearby:
		var enabled: bool = _can_fit_dropped_item(dropped)
		if _turn_system.active:
			enabled = (
				enabled
				and _turn_system.is_player_turn(player)
				and not _enemy_turn_running
				and _turn_system.bonus_action_available
			)
		category_entries.append(_entry(
			"%s%s" % [PICKUP_DROPPED_PREFIX, dropped.get_drop_id()],
			"ПОДОБРАТЬ: %s" % dropped.get_item_label().to_upper(),
			enabled,
			"Подобрать предмет и положить его в инвентарь.%s" % (
				" В бою расходует дополнительное действие." if _turn_system.active else ""
			),
			"world"
		))
	entries[category_id] = category_entries


func _registered_nearby_drops() -> Array[DroppedInventoryItem]:
	var result: Array[DroppedInventoryItem] = []
	if player == null or not player.has_method("get_nearby_interactables"):
		return result
	var value: Variant = player.call("get_nearby_interactables")
	if not value is Array:
		return result
	for target: Variant in value as Array:
		if target is DroppedInventoryItem and is_instance_valid(target as DroppedInventoryItem):
			var dropped: DroppedInventoryItem = target as DroppedInventoryItem
			if dropped.is_available_for_pickup():
				result.append(dropped)
	return result


func _nearby_drop_by_id(drop_id: String) -> DroppedInventoryItem:
	for dropped: DroppedInventoryItem in _registered_nearby_drops():
		if dropped.get_drop_id() == drop_id:
			return dropped
	return null


func _can_fit_dropped_item(dropped: DroppedInventoryItem) -> bool:
	var item_id: String = dropped.get_item_id()
	var definition: Dictionary = GameState.get_item_definition(item_id)
	if definition.is_empty():
		return false
	var maximum: int = int(definition.get("max_stack", 99)) if bool(definition.get("stackable", true)) else 1
	return GameState.get_item_count(item_id) + dropped.get_quantity() <= maxi(maximum, 1)


func _enrich_attack_entry(entries: Dictionary) -> void:
	var values: Variant = entries.get("action", [])
	if not values is Array:
		return
	var weapon: Dictionary = _class_data.get_equipped_weapon(GameState.player_character)
	var resource_id: String = str(weapon.get("ammunition_id", ""))
	var properties_value: Variant = weapon.get("properties", [])
	if resource_id.is_empty() and properties_value is Array and "thrown" in (properties_value as Array):
		resource_id = str(weapon.get("id", ""))
	for value: Variant in values as Array:
		if not value is Dictionary:
			continue
		var entry: Dictionary = value as Dictionary
		if str(entry.get("id", "")) != "attack":
			continue
		if not resource_id.is_empty():
			var count: int = GameState.get_inventory_available_count(resource_id)
			var resource: Dictionary = GameState.get_item_definition(resource_id)
			entry["description"] = "%s Осталось: %d %s." % [
				str(entry.get("description", "")),
				count,
				str(resource.get("name", resource_id)).to_lower()
			]
			if count <= 0:
				entry["enabled"] = false
		break


func _weapon_consumable_item_id(
	weapon: Dictionary,
	ammo_id: String,
	distance: int
) -> String:
	if not ammo_id.is_empty():
		return ammo_id
	if _is_recoverable_thrown_attack(weapon, distance):
		return str(weapon.get("id", ""))
	return ""


func _is_recoverable_thrown_attack(weapon: Dictionary, distance: int) -> bool:
	var properties_value: Variant = weapon.get("properties", [])
	return (
		properties_value is Array
		and "thrown" in (properties_value as Array)
		and DistanceSystem.is_ranged_attack(weapon, distance)
		and not str(weapon.get("id", "")).is_empty()
	)


func _thrown_landing_position(target_position: Vector2, hit: bool) -> Vector2:
	if hit:
		return target_position
	var direction: Vector2 = target_position - player.global_position
	if direction.length_squared() <= 0.0001:
		direction = Vector2.RIGHT
	direction = direction.normalized()
	return target_position + direction * 12.0 + direction.orthogonal() * 28.0


func _ensure_dropped_inventory_manager() -> void:
	if _dropped_inventory_manager != null and is_instance_valid(_dropped_inventory_manager):
		return
	_dropped_inventory_manager = get_node_or_null("DroppedInventoryItemManager") as DroppedInventoryItemManager
	if _dropped_inventory_manager != null:
		return
	_dropped_inventory_manager = (
		DROPPED_ITEM_MANAGER_SCRIPT.new() as DroppedInventoryItemManager
	)
	_dropped_inventory_manager.name = "DroppedInventoryItemManager"
	add_child(_dropped_inventory_manager)


func get_dropped_inventory_manager_for_testing() -> DroppedInventoryItemManager:
	_ensure_dropped_inventory_manager()
	return _dropped_inventory_manager
