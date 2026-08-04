extends "res://scripts/game/game_guard_post_polish_runtime_base.gd"

const ITEM_USE_SYSTEM_SCRIPT: Script = preload("res://scripts/systems/item_use_system.gd")
const ITEM_USE_ACTION_PREFIX: String = "use_inventory_item:"
const HEALING_POTION_ID: String = "potion_of_healing"
const HEALERS_KIT_ID: String = "healers_kit"
const ITEM_USE_TARGET_DISTANCE_FEET: int = 5

var _item_use_system: ItemUseSystem = ITEM_USE_SYSTEM_SCRIPT.new() as ItemUseSystem
var _item_use_hub: CharacterHubInventory = null


func _ready() -> void:
	super._ready()
	_item_use_hub = find_child("CharacterHub", true, false) as CharacterHubInventory
	if _item_use_hub != null and not _item_use_hub.item_use_requested.is_connected(_on_inventory_item_use_requested):
		_item_use_hub.item_use_requested.connect(_on_inventory_item_use_requested)


func _build_catalog_entries() -> Dictionary:
	var entries: Dictionary = super._build_catalog_entries()
	_append_healing_potion_action(entries)
	_append_healers_kit_action(entries)
	return entries


func _on_feedback_catalog_action_requested(action_id: String) -> void:
	if action_id.begins_with(ITEM_USE_ACTION_PREFIX):
		_request_item_use(action_id.trim_prefix(ITEM_USE_ACTION_PREFIX))
		_refresh_action_catalog()
		return
	super._on_feedback_catalog_action_requested(action_id)


func _on_inventory_item_use_requested(item_id: String) -> void:
	if _item_use_hub != null and _item_use_hub.visible:
		_item_use_hub.close_sheet()
	_sync_exploration_hud_visibility()
	_request_item_use(item_id)


func _request_item_use(item_id: String) -> void:
	var target: Variant = _resolve_item_use_target(item_id)
	var result: Dictionary = _execute_item_use(item_id, target, {})
	show_combat_message(
		str(result.get("message", "Предмет использован.")),
		bool(result.get("success", false))
	)
	_update_status()
	_refresh_turn_interface()
	_refresh_action_catalog()
	_sync_exploration_hud_visibility()


func _execute_item_use(item_id: String, target: Variant, context: Dictionary) -> Dictionary:
	var definition: Dictionary = GameState.get_item_definition(item_id)
	if definition.is_empty():
		return {"success": false, "message": "Описание предмета отсутствует."}
	var action: Dictionary = _item_use_system.get_use_action(definition)
	if action.is_empty():
		return {"success": false, "message": "Этот предмет пока нельзя использовать."}
	if _turn_system.active and not bool(action.get("allowed_in_combat", true)):
		return {"success": false, "message": "Этот предмет нельзя использовать во время боя."}
	if _turn_system.active and not _turn_system.is_player_turn(player):
		return {"success": false, "message": "Предмет можно использовать только на своём ходу."}

	var prepared: Dictionary = _item_use_system.prepare_use(GameState, item_id, target, context)
	if not bool(prepared.get("success", false)):
		return prepared

	if _turn_system.active and not bool(context.get("ignore_combat_cost", false)):
		var combat_cost: String = str(action.get("combat_cost", "action"))
		var paid: bool = true
		match combat_cost:
			"action":
				paid = _turn_system.consume_action()
			"bonus_action":
				paid = _turn_system.consume_bonus_action()
			"none":
				paid = true
			_:
				paid = false
		if not paid:
			_item_use_system.cancel_prepared_use(GameState, prepared)
			return {"success": false, "message": _combat_cost_failure_message(combat_cost)}

	var before_health: int = GameState.player_character.current_health
	var result: Dictionary = _item_use_system.execute_prepared_use(GameState, prepared, target, context)
	if not bool(result.get("success", false)):
		return result
	if str(result.get("effect_id", "")) == ItemUseSystem.EFFECT_RESTORE_HIT_POINTS:
		if before_health <= 0 and GameState.player_character.current_health > 0:
			_player_combat_state.recover_from_zero_hit_points()
	if not _turn_system.active:
		GameState.save_game()
	return result


func use_item_for_testing(
	item_id: String,
	target: Variant = null,
	context: Dictionary = {}
) -> Dictionary:
	var test_context: Dictionary = context.duplicate(true)
	test_context["ignore_combat_cost"] = true
	return _execute_item_use(item_id, target, test_context)


func _append_healing_potion_action(entries: Dictionary) -> void:
	if GameState.get_item_count(HEALING_POTION_ID) <= 0:
		return
	var definition: Dictionary = GameState.get_item_definition(HEALING_POTION_ID)
	var action_entries: Array = entries.get("action", []) as Array
	var wounded: bool = GameState.player_character.current_health < GameState.player_character.maximum_health
	var enabled: bool = wounded and _item_action_available_now("action")
	action_entries.append(_entry(
		ITEM_USE_ACTION_PREFIX + HEALING_POTION_ID,
		_item_use_system.build_action_label(definition),
		enabled,
		"Восстановить 2к4 + 2 HP. В бою расходует основное действие.",
		"item"
	))
	entries["action"] = action_entries


func _append_healers_kit_action(entries: Dictionary) -> void:
	if GameState.get_item_count(HEALERS_KIT_ID) <= 0:
		return
	if not is_instance_valid(_selected_target) or not _selected_target is Node2D:
		return
	if not _selected_target.has_method("can_be_stabilized_with_healers_kit"):
		return
	var definition: Dictionary = GameState.get_item_definition(HEALERS_KIT_ID)
	var target_name: String = _target_name(_selected_target)
	var reachable: bool = DistanceSystem.distance_feet(
		player.global_position,
		(_selected_target as Node2D).global_position
	) <= ITEM_USE_TARGET_DISTANCE_FEET
	var needs_stabilization: bool = bool(_selected_target.call("can_be_stabilized_with_healers_kit"))
	var enabled: bool = reachable and needs_stabilization and _item_action_available_now("action")
	var action_entries: Array = entries.get("action", []) as Array
	action_entries.append(_entry(
		ITEM_USE_ACTION_PREFIX + HEALERS_KIT_ID,
		_item_use_system.build_action_label(definition, target_name),
		enabled,
		"Стабилизировать умирающее существо рядом. Расходует одно применение набора и основное действие в бою.",
		"item"
	))
	entries["action"] = action_entries


func _resolve_item_use_target(item_id: String) -> Variant:
	var definition: Dictionary = GameState.get_item_definition(item_id)
	var action: Dictionary = _item_use_system.get_use_action(definition)
	match str(action.get("target_mode", ItemUseSystem.TARGET_SELF)):
		ItemUseSystem.TARGET_SELECTED_DYING_CREATURE:
			return _selected_target
		_:
			return null


func _item_action_available_now(combat_cost: String) -> bool:
	if not _turn_system.active:
		return true
	if not _turn_system.is_player_turn(player):
		return false
	if combat_cost == "bonus_action":
		return _turn_system.bonus_action_available
	if combat_cost == "none":
		return true
	return _turn_system.action_available


func _combat_cost_failure_message(combat_cost: String) -> String:
	if combat_cost == "bonus_action":
		return "Дополнительное действие на этом ходу уже использовано."
	if combat_cost == "none":
		return "Предмет сейчас использовать нельзя."
	return "Основное действие на этом ходу уже использовано."
