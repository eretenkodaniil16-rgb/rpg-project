class_name LevelUpChoiceSystem
extends LevelUpSystem

const LEVEL_CHOICES_KEY: String = "level_choices"
const CHOICE_MIGRATION_FLAG: String = "_level_up_choices_migrated_v1"

var _choices: LevelChoiceSystem = LevelChoiceSystem.new()
var _origin_feats: OriginFeatSystem = OriginFeatSystem.new()
var _skip_choice_validation: bool = false


func ensure_migrated(character: PlayerCharacter, state: Node) -> bool:
	var changed: bool = super.ensure_migrated(character, state)
	if character == null or state == null:
		return changed
	if _choices.ensure_character(character):
		changed = true
	var transaction: Dictionary = get_transaction(state)
	if not transaction.is_empty() and super.has_pending_transaction(character, state):
		if not transaction.has(LEVEL_CHOICES_KEY) or not transaction[LEVEL_CHOICES_KEY] is Dictionary:
			transaction[LEVEL_CHOICES_KEY] = {}
			_state_set(state, TRANSACTION_FLAG, transaction.duplicate(true))
			changed = true
	if not bool(_state_get(state, CHOICE_MIGRATION_FLAG, false)):
		_state_set(state, CHOICE_MIGRATION_FLAG, true)
		changed = true
	if changed:
		_save(state)
	return changed


func begin_transaction(character: PlayerCharacter, state: Node) -> Dictionary:
	var result: Dictionary = super.begin_transaction(character, state)
	if not bool(result.get("success", false)):
		return result
	var transaction: Dictionary = result.get("transaction", {}) as Dictionary
	if not transaction.has(LEVEL_CHOICES_KEY) or not transaction[LEVEL_CHOICES_KEY] is Dictionary:
		transaction[LEVEL_CHOICES_KEY] = {}
		_store_transaction(state, transaction)
	result["transaction"] = transaction.duplicate(true)
	return result


func get_level_choice_definitions(
	character: PlayerCharacter,
	target_level: int = 0
) -> Array[Dictionary]:
	if character == null:
		return []
	var level_value: int = target_level if target_level > 0 else character.level + 1
	return _choices.get_choice_definitions(character, level_value)


func get_level_choice_selection(state: Node, choice_id: String) -> Dictionary:
	return _choices.get_selection(get_transaction(state), choice_id)


func set_level_choice(
	character: PlayerCharacter,
	state: Node,
	choice_id: String,
	selection: Dictionary
) -> Dictionary:
	var transaction_result: Dictionary = begin_transaction(character, state)
	if not bool(transaction_result.get("success", false)):
		return transaction_result
	var transaction: Dictionary = transaction_result.get("transaction", {}) as Dictionary
	var selection_result: Dictionary = _choices.set_selection(
		character,
		transaction,
		choice_id,
		selection
	)
	if not bool(selection_result.get("success", false)):
		return selection_result
	var updated: Dictionary = selection_result.get("transaction", {}) as Dictionary
	_store_transaction(state, updated)
	return {
		"success": true,
		"message": str(selection_result.get("message", "Выбор сохранён.")),
		"transaction": updated.duplicate(true)
	}


func validate_transaction(character: PlayerCharacter, state: Node) -> Dictionary:
	var base_validation: Dictionary = super.validate_transaction(character, state)
	if not bool(base_validation.get("success", false)) or _skip_choice_validation:
		return base_validation
	var transaction: Dictionary = base_validation.get("transaction", {}) as Dictionary
	var target_level: int = int(transaction.get("target_level", character.level + 1))
	var choice_validation: Dictionary = _choices.validate_choices(
		character,
		target_level,
		transaction
	)
	if not bool(choice_validation.get("success", false)):
		return {
			"success": false,
			"message": str(choice_validation.get("message", "Заполните выборы уровня.")),
			"invalid_choice_id": str(choice_validation.get("invalid_choice_id", "")),
			"transaction": transaction.duplicate(true)
		}
	return {
		"success": true,
		"message": "Повышение и все обязательные выборы готовы к подтверждению.",
		"invalid_choice_id": "",
		"transaction": transaction.duplicate(true)
	}


func commit_transaction(character: PlayerCharacter, state: Node) -> Dictionary:
	var validation: Dictionary = validate_transaction(character, state)
	if not bool(validation.get("success", false)):
		return validation
	var transaction: Dictionary = validation.get("transaction", {}) as Dictionary
	var target_level: int = int(transaction.get("target_level", character.level + 1))
	var application: Dictionary = _choices.build_application(
		character,
		target_level,
		transaction
	)
	if not bool(application.get("success", false)):
		return application

	var snapshot: Dictionary = _snapshot_character(character)
	_choices.apply_application(character, application)
	_origin_feats.initialize_character(character, false)

	_skip_choice_validation = true
	var result: Dictionary = super.commit_transaction(character, state)
	_skip_choice_validation = false
	if not bool(result.get("success", false)):
		_restore_character(character, snapshot)
		return result

	result["level_choices"] = (application.get("applied_choices", []) as Array).duplicate(true)
	result["subclass_id"] = character.subclass_id
	result["subclass_name"] = character.subclass_name
	result["level_feat_ids"] = character.level_feat_ids.duplicate()
	result["level_ability_bonuses"] = character.level_ability_bonuses.duplicate(true)
	_state_set(state, LAST_RESULT_FLAG, result.duplicate(true))
	_save(state)
	return result


func get_available_level_feat_ids(character: PlayerCharacter) -> Array[String]:
	return _choices.get_available_feat_ids(character)


func get_level_choice_option_name(choice_type: String, option_id: String) -> String:
	return _choices.option_name(choice_type, option_id)


func get_level_choice_option_description(choice_type: String, option_id: String) -> String:
	return _choices.option_description(choice_type, option_id)


func get_ability_choice_ids() -> Array[String]:
	return _choices.ability_ids()


func get_ability_choice_name(ability_id: String) -> String:
	return _choices.ability_name(ability_id)


func get_advancement_mode_name(mode: String) -> String:
	return _choices.advancement_mode_name(mode)


func _snapshot_character(character: PlayerCharacter) -> Dictionary:
	return {
		"abilities": character.abilities.duplicate(true),
		"subclass_id": character.subclass_id,
		"subclass_name": character.subclass_name,
		"level_feat_ids": character.level_feat_ids.duplicate(),
		"level_ability_bonuses": character.level_ability_bonuses.duplicate(true),
		"level_choice_history": character.level_choice_history.duplicate(true),
		"known_features": character.known_features.duplicate(),
		"active_effects": character.active_effects.duplicate(true),
		"class_resources": character.class_resources.duplicate(true),
		"class_resource_maximums": character.class_resource_maximums.duplicate(true)
	}


func _restore_character(character: PlayerCharacter, snapshot: Dictionary) -> void:
	character.abilities = _dictionary(snapshot.get("abilities", {})).duplicate(true)
	character.subclass_id = str(snapshot.get("subclass_id", ""))
	character.subclass_name = str(snapshot.get("subclass_name", ""))
	character.level_feat_ids = _string_array(snapshot.get("level_feat_ids", []))
	character.level_ability_bonuses = _dictionary(
		snapshot.get("level_ability_bonuses", {})
	).duplicate(true)
	character.level_choice_history = _dictionary(
		snapshot.get("level_choice_history", {})
	).duplicate(true)
	character.known_features = _string_array(snapshot.get("known_features", []))
	character.active_effects = _dictionary(snapshot.get("active_effects", {})).duplicate(true)
	character.class_resources = _dictionary(snapshot.get("class_resources", {})).duplicate(true)
	character.class_resource_maximums = _dictionary(
		snapshot.get("class_resource_maximums", {})
	).duplicate(true)


func _dictionary(value: Variant) -> Dictionary:
	return value as Dictionary if value is Dictionary else {}


func _string_array(value: Variant) -> Array[String]:
	var result: Array[String] = []
	if value is Array:
		for item: Variant in value:
			var text: String = str(item)
			if not text.is_empty() and text not in result:
				result.append(text)
	return result
