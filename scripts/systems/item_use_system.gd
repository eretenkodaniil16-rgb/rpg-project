class_name ItemUseSystem
extends RefCounted

const TARGET_SELF: String = "self"
const TARGET_SELECTED_DYING_CREATURE: String = "selected_dying_creature"
const CONSUME_NONE: String = "none"
const CONSUME_ONE: String = "consume_one"
const EFFECT_RESTORE_HIT_POINTS: String = "restore_hit_points"
const EFFECT_STABILIZE_CREATURE: String = "stabilize_creature"
const EFFECT_SET_STORY_FLAG: String = "set_story_flag"

var _rng: RandomNumberGenerator = RandomNumberGenerator.new()


func _init() -> void:
	_rng.randomize()


func has_use_action(item_definition: Dictionary) -> bool:
	return not get_use_action(item_definition).is_empty()


func get_use_action(item_definition: Dictionary) -> Dictionary:
	var value: Variant = item_definition.get("use_action", {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func get_inventory_label(item_definition: Dictionary) -> String:
	var action: Dictionary = get_use_action(item_definition)
	return str(action.get("inventory_label", "ИСПОЛЬЗОВАТЬ"))


func build_action_label(item_definition: Dictionary, target_name: String = "") -> String:
	var action: Dictionary = get_use_action(item_definition)
	var template: String = str(action.get("action_label", "ИСПОЛЬЗОВАТЬ: {item_name}"))
	return template.replace("{item_name}", str(item_definition.get("name", "ПРЕДМЕТ")).to_upper()).replace(
		"{target_name}",
		target_name.to_upper()
	)


func prepare_use(
	state: Node,
	item_id: String,
	target: Variant = null,
	context: Dictionary = {}
) -> Dictionary:
	if state == null or item_id.is_empty() or not state.has_method("get_item_definition"):
		return _failure("Предмет недоступен.")
	var definition_value: Variant = state.call("get_item_definition", item_id)
	if not definition_value is Dictionary:
		return _failure("Описание предмета отсутствует.")
	var definition: Dictionary = definition_value as Dictionary
	var action: Dictionary = get_use_action(definition)
	if action.is_empty():
		return _failure("Этот предмет пока нельзя использовать.")
	var validation: Dictionary = _validate_effect(state, definition, action, target, context)
	if not bool(validation.get("success", false)):
		return validation

	var transaction_id: String = ""
	var consumption_mode: String = str(action.get("consumption_mode", CONSUME_NONE))
	if consumption_mode == CONSUME_ONE:
		if not state.has_method("reserve_inventory_item"):
			return _failure("Транзакции инвентаря недоступны.")
		var reservation_value: Variant = state.call(
			"reserve_inventory_item",
			item_id,
			1,
			"item_use",
			context
		)
		if not reservation_value is Dictionary:
			return _failure("Не удалось зарезервировать предмет.")
		var reservation: Dictionary = reservation_value as Dictionary
		if not bool(reservation.get("success", false)):
			return _failure("Предмет закончился или уже используется другим действием.")
		transaction_id = str(reservation.get("transaction_id", ""))

	return {
		"success": true,
		"item_id": item_id,
		"definition": definition.duplicate(true),
		"use_action": action.duplicate(true),
		"transaction_id": transaction_id,
		"context": context.duplicate(true)
	}


func cancel_prepared_use(state: Node, prepared: Dictionary) -> void:
	var transaction_id: String = str(prepared.get("transaction_id", ""))
	if transaction_id.is_empty() or state == null or not state.has_method("rollback_inventory_transaction"):
		return
	state.call("rollback_inventory_transaction", transaction_id)


func execute_prepared_use(
	state: Node,
	prepared: Dictionary,
	target: Variant = null,
	context: Dictionary = {}
) -> Dictionary:
	if state == null or not bool(prepared.get("success", false)):
		return _failure("Использование предмета не было подготовлено.")
	var definition_value: Variant = prepared.get("definition", {})
	var action_value: Variant = prepared.get("use_action", {})
	if not definition_value is Dictionary or not action_value is Dictionary:
		cancel_prepared_use(state, prepared)
		return _failure("Данные действия повреждены.")
	var definition: Dictionary = definition_value as Dictionary
	var action: Dictionary = action_value as Dictionary
	var validation: Dictionary = _validate_effect(state, definition, action, target, context)
	if not bool(validation.get("success", false)):
		cancel_prepared_use(state, prepared)
		return validation

	var transaction_id: String = str(prepared.get("transaction_id", ""))
	if not transaction_id.is_empty():
		if not state.has_method("commit_inventory_transaction"):
			cancel_prepared_use(state, prepared)
			return _failure("Транзакции инвентаря недоступны.")
		var commit_value: Variant = state.call("commit_inventory_transaction", transaction_id, false)
		if not commit_value is Dictionary or not bool((commit_value as Dictionary).get("success", false)):
			return _failure("Не удалось списать предмет. Эффект отменён.")

	var effect_id: String = str(action.get("effect_id", ""))
	var result: Dictionary
	match effect_id:
		EFFECT_RESTORE_HIT_POINTS:
			result = _restore_hit_points(state, action, context)
		EFFECT_STABILIZE_CREATURE:
			result = _stabilize_creature(target)
		EFFECT_SET_STORY_FLAG:
			result = _set_story_flag(state, action)
		_:
			result = _failure("Неизвестный эффект предмета: %s." % effect_id)
	result["item_id"] = str(prepared.get("item_id", ""))
	result["consumed"] = not transaction_id.is_empty()
	result["effect_id"] = effect_id
	return result


func _validate_effect(
	state: Node,
	_definition: Dictionary,
	action: Dictionary,
	target: Variant,
	_context: Dictionary
) -> Dictionary:
	var effect_id: String = str(action.get("effect_id", ""))
	match effect_id:
		EFFECT_RESTORE_HIT_POINTS:
			var character: Object = _player_character(state)
			if character == null:
				return _failure("Персонаж недоступен.")
			var current: int = int(character.get("current_health"))
			var maximum: int = maxi(int(character.get("maximum_health")), 1)
			if current >= maximum:
				return _failure("Здоровье уже полностью восстановлено.")
			return {"success": true}
		EFFECT_STABILIZE_CREATURE:
			if not target is Object or not is_instance_valid(target as Object):
				return _failure("Сначала выберите умирающую цель.")
			var target_object: Object = target as Object
			if not target_object.has_method("can_be_stabilized_with_healers_kit"):
				return _failure("Эту цель нельзя стабилизировать набором лекаря.")
			if not bool(target_object.call("can_be_stabilized_with_healers_kit")):
				return _failure("Цель не нуждается в стабилизации.")
			return {"success": true}
		EFFECT_SET_STORY_FLAG:
			if not state.has_method("set_flag"):
				return _failure("Сюжетное состояние недоступно.")
			return {"success": true}
		_:
			return _failure("Для предмета не задан поддерживаемый эффект.")


func _restore_hit_points(state: Node, action: Dictionary, context: Dictionary) -> Dictionary:
	var character: Object = _player_character(state)
	if character == null:
		return _failure("Персонаж недоступен.")
	var parameters: Dictionary = _effect_parameters(action)
	var rolled: int = int(context.get("healing_roll_override", 0))
	if rolled <= 0:
		rolled = maxi(int(parameters.get("flat_bonus", 0)), 0)
		var dice_count: int = maxi(int(parameters.get("dice_count", 0)), 0)
		var dice_size: int = maxi(int(parameters.get("dice_size", 0)), 1)
		for _index: int in range(dice_count):
			rolled += _rng.randi_range(1, dice_size)
	var current: int = maxi(int(character.get("current_health")), 0)
	var maximum: int = maxi(int(character.get("maximum_health")), 1)
	var updated: int = mini(current + maxi(rolled, 0), maximum)
	var applied: int = maxi(updated - current, 0)
	character.set("current_health", updated)
	return {
		"success": applied > 0,
		"amount": applied,
		"rolled": rolled,
		"message": "Восстановлено здоровья: %d. HP: %d/%d." % [applied, updated, maximum]
	}


func _stabilize_creature(target: Variant) -> Dictionary:
	if not target is Object or not is_instance_valid(target as Object):
		return _failure("Цель исчезла до применения предмета.")
	var target_object: Object = target as Object
	var value: Variant = target_object.call("stabilize_with_healers_kit")
	if value is Dictionary:
		return (value as Dictionary).duplicate(true)
	return _failure("Цель не подтвердила стабилизацию.")


func _set_story_flag(state: Node, action: Dictionary) -> Dictionary:
	var parameters: Dictionary = _effect_parameters(action)
	var flag_id: String = str(parameters.get("flag_id", ""))
	if flag_id.is_empty():
		return _failure("Для сюжетного предмета не задан флаг.")
	state.call("set_flag", flag_id, true)
	return {
		"success": true,
		"message": str(parameters.get("message", "Предмет изучен.")),
		"flag_id": flag_id
	}


func _player_character(state: Node) -> Object:
	if state == null:
		return null
	var value: Variant = state.get("player_character")
	return value as Object if value is Object else null


func _effect_parameters(action: Dictionary) -> Dictionary:
	var value: Variant = action.get("effect_parameters", {})
	return value as Dictionary if value is Dictionary else {}


func _failure(message: String) -> Dictionary:
	return {"success": false, "message": message}
