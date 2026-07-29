class_name LevelChoiceSystem
extends RefCounted

const DATA_PATH: String = "res://data/rules/level_choices.json"
const CHOICE_SUBCLASS: String = "subclass"
const CHOICE_ADVANCEMENT: String = "advancement"
const ADVANCEMENT_PLUS_TWO: String = "ability_plus_two"
const ADVANCEMENT_SPLIT: String = "ability_plus_one_each"
const ADVANCEMENT_FEAT: String = "feat"
const LEGACY_PRESERVED: String = "legacy_preserved"
const ABILITY_ORDER: Array[String] = [
	"strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"
]

var _data: Dictionary = {}


func _init() -> void:
	_load_data()


func get_choice_definitions(character: PlayerCharacter, target_level: int) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	if character == null or target_level <= 0:
		return result
	var global_levels: Dictionary = _dictionary(_data.get("global_level_choices", {}))
	_append_choice_definitions(result, global_levels.get(str(target_level), []))
	var class_levels: Dictionary = _dictionary(_data.get("class_level_choices", {}))
	var class_choices: Dictionary = _dictionary(class_levels.get(character.character_class_id, {}))
	_append_choice_definitions(result, class_choices.get(str(target_level), []))
	return result


func get_choice_definition(
	character: PlayerCharacter,
	target_level: int,
	choice_id: String
) -> Dictionary:
	for definition: Dictionary in get_choice_definitions(character, target_level):
		if str(definition.get("choice_id", "")) == choice_id:
			return definition
	return {}


func get_selection(transaction: Dictionary, choice_id: String) -> Dictionary:
	var choices: Dictionary = _dictionary(transaction.get("level_choices", {}))
	return _dictionary(choices.get(choice_id, {})).duplicate(true)


func set_selection(
	character: PlayerCharacter,
	transaction: Dictionary,
	choice_id: String,
	selection: Dictionary
) -> Dictionary:
	var target_level: int = int(transaction.get("target_level", 0))
	var definition: Dictionary = get_choice_definition(character, target_level, choice_id)
	if definition.is_empty():
		return {
			"success": false,
			"message": "Выбор уровня не найден.",
			"transaction": transaction.duplicate(true)
		}
	var updated: Dictionary = transaction.duplicate(true)
	var choices: Dictionary = _dictionary(updated.get("level_choices", {})).duplicate(true)
	choices[choice_id] = selection.duplicate(true)
	updated["level_choices"] = choices
	return {
		"success": true,
		"message": "Выбор сохранён.",
		"transaction": updated
	}


func validate_choices(
	character: PlayerCharacter,
	target_level: int,
	transaction: Dictionary
) -> Dictionary:
	if character == null:
		return _failure("Персонаж недоступен.")
	for definition: Dictionary in get_choice_definitions(character, target_level):
		var choice_id: String = str(definition.get("choice_id", ""))
		var title: String = str(definition.get("title", choice_id))
		var required: bool = bool(definition.get("required", true))
		var selection: Dictionary = get_selection(transaction, choice_id)
		if selection.is_empty():
			if required:
				return _failure("Заполните обязательный выбор: %s." % title, choice_id)
			continue
		var choice_type: String = str(definition.get("type", ""))
		var error: String = ""
		match choice_type:
			CHOICE_SUBCLASS:
				error = _validate_subclass(character, definition, selection)
			CHOICE_ADVANCEMENT:
				error = _validate_advancement(character, selection)
			_:
				error = "Неизвестный тип выбора: %s." % choice_type
		if not error.is_empty():
			return _failure(error, choice_id)
	return {
		"success": true,
		"message": "Все обязательные решения заполнены.",
		"invalid_choice_id": ""
	}


func build_application(
	character: PlayerCharacter,
	target_level: int,
	transaction: Dictionary
) -> Dictionary:
	var validation: Dictionary = validate_choices(character, target_level, transaction)
	if not bool(validation.get("success", false)):
		return validation

	var next_abilities: Dictionary = character.abilities.duplicate(true)
	var next_level_bonuses: Dictionary = character.level_ability_bonuses.duplicate(true)
	var next_level_feats: Array[String] = character.level_feat_ids.duplicate()
	var next_known_features: Array[String] = character.known_features.duplicate()
	var next_history: Dictionary = character.level_choice_history.duplicate(true)
	var next_subclass_id: String = character.subclass_id
	var next_subclass_name: String = character.subclass_name
	var applied_choices: Array[Dictionary] = []

	for definition: Dictionary in get_choice_definitions(character, target_level):
		var choice_id: String = str(definition.get("choice_id", ""))
		var choice_type: String = str(definition.get("type", ""))
		var selection: Dictionary = get_selection(transaction, choice_id)
		if selection.is_empty():
			continue
		var history_entry: Dictionary = selection.duplicate(true)
		history_entry["choice_id"] = choice_id
		history_entry["type"] = choice_type
		history_entry["target_level"] = target_level
		history_entry["migrated"] = false

		match choice_type:
			CHOICE_SUBCLASS:
				var subclass_id: String = str(selection.get("option_id", ""))
				var subclass: Dictionary = get_subclass_definition(subclass_id)
				next_subclass_id = subclass_id
				next_subclass_name = str(subclass.get("name", subclass_id))
			CHOICE_ADVANCEMENT:
				var mode: String = str(selection.get("mode", ""))
				if mode == ADVANCEMENT_PLUS_TWO:
					_apply_ability_increase(
						next_abilities,
						next_level_bonuses,
						str(selection.get("primary_ability_id", "")),
						2
					)
				elif mode == ADVANCEMENT_SPLIT:
					_apply_ability_increase(
						next_abilities,
						next_level_bonuses,
						str(selection.get("primary_ability_id", "")),
						1
					)
					_apply_ability_increase(
						next_abilities,
						next_level_bonuses,
						str(selection.get("secondary_ability_id", "")),
						1
					)
				elif mode == ADVANCEMENT_FEAT:
					var feat_id: String = str(selection.get("feat_id", ""))
					_append_unique(next_level_feats, feat_id)
					_append_unique(next_known_features, feat_id)

		next_history[_history_key(target_level, choice_id)] = history_entry
		applied_choices.append(history_entry)

	return {
		"success": true,
		"message": "Выборы готовы к применению.",
		"abilities": next_abilities,
		"level_ability_bonuses": next_level_bonuses,
		"level_feat_ids": next_level_feats,
		"known_features": next_known_features,
		"level_choice_history": next_history,
		"subclass_id": next_subclass_id,
		"subclass_name": next_subclass_name,
		"applied_choices": applied_choices
	}


func apply_application(character: PlayerCharacter, application: Dictionary) -> void:
	if character == null or not bool(application.get("success", false)):
		return
	character.abilities = _dictionary(application.get("abilities", character.abilities)).duplicate(true)
	character.level_ability_bonuses = _dictionary(
		application.get("level_ability_bonuses", character.level_ability_bonuses)
	).duplicate(true)
	character.level_feat_ids = _unique_string_array(
		application.get("level_feat_ids", character.level_feat_ids)
	)
	character.known_features = _unique_string_array(
		application.get("known_features", character.known_features)
	)
	character.level_choice_history = _dictionary(
		application.get("level_choice_history", character.level_choice_history)
	).duplicate(true)
	character.subclass_id = str(application.get("subclass_id", character.subclass_id))
	character.subclass_name = str(application.get("subclass_name", character.subclass_name))


func ensure_character(character: PlayerCharacter) -> bool:
	if character == null:
		return false
	var changed: bool = false
	var clean_feats: Array[String] = _unique_string_array(character.level_feat_ids)
	if clean_feats != character.level_feat_ids:
		character.level_feat_ids = clean_feats
		changed = true
	for feat_id: String in character.level_feat_ids:
		if feat_id not in character.known_features:
			character.known_features.append(feat_id)
			changed = true

	var clean_bonuses: Dictionary = {}
	for ability_id: String in ABILITY_ORDER:
		var value: int = maxi(int(character.level_ability_bonuses.get(ability_id, 0)), 0)
		if value > 0:
			clean_bonuses[ability_id] = value
	if clean_bonuses != character.level_ability_bonuses:
		character.level_ability_bonuses = clean_bonuses
		changed = true

	if character.character_class_id == "fighter" and character.level >= 3:
		var definition: Dictionary = get_choice_definition(character, 3, "fighter_subclass")
		if character.subclass_id.is_empty():
			var fallback_id: String = str(definition.get("migration_default", "guardian_vanguard"))
			var fallback: Dictionary = get_subclass_definition(fallback_id)
			character.subclass_id = fallback_id
			character.subclass_name = str(fallback.get("name", fallback_id))
			character.level_choice_history[_history_key(3, "fighter_subclass")] = {
				"choice_id": "fighter_subclass",
				"type": CHOICE_SUBCLASS,
				"target_level": 3,
				"option_id": fallback_id,
				"migrated": true
			}
			changed = true
		elif character.subclass_name.is_empty():
			character.subclass_name = str(
				get_subclass_definition(character.subclass_id).get("name", character.subclass_id)
			)
			changed = true

	if character.level >= 4:
		var advancement_key: String = _history_key(4, "level_4_advancement")
		if not character.level_choice_history.has(advancement_key):
			character.level_choice_history[advancement_key] = {
				"choice_id": "level_4_advancement",
				"type": CHOICE_ADVANCEMENT,
				"target_level": 4,
				"mode": LEGACY_PRESERVED,
				"migrated": true
			}
			changed = true
	return changed


func get_available_feat_ids(character: PlayerCharacter) -> Array[String]:
	var result: Array[String] = []
	var feats: Dictionary = _dictionary(_data.get("feat_options", {}))
	for feat_id_value: Variant in feats.keys():
		var feat_id: String = str(feat_id_value)
		var feat: Dictionary = _dictionary(feats.get(feat_id, {}))
		if feat_id.is_empty():
			continue
		if not bool(feat.get("repeatable", false)) and character != null and character.has_feat(feat_id):
			continue
		result.append(feat_id)
	result.sort()
	return result


func get_subclass_definition(subclass_id: String) -> Dictionary:
	var options: Dictionary = _dictionary(_data.get("subclass_options", {}))
	return _dictionary(options.get(subclass_id, {})).duplicate(true)


func get_feat_definition(feat_id: String) -> Dictionary:
	var options: Dictionary = _dictionary(_data.get("feat_options", {}))
	return _dictionary(options.get(feat_id, {})).duplicate(true)


func option_name(choice_type: String, option_id: String) -> String:
	if option_id.is_empty():
		return ""
	if choice_type == CHOICE_SUBCLASS:
		return str(get_subclass_definition(option_id).get("name", option_id))
	if choice_type == ADVANCEMENT_FEAT or choice_type == "feat":
		return str(get_feat_definition(option_id).get("name", option_id))
	return option_id


func option_description(choice_type: String, option_id: String) -> String:
	if choice_type == CHOICE_SUBCLASS:
		return str(get_subclass_definition(option_id).get("description", ""))
	if choice_type == ADVANCEMENT_FEAT or choice_type == "feat":
		return str(get_feat_definition(option_id).get("description", ""))
	return ""


func ability_name(ability_id: String) -> String:
	var names: Dictionary = _dictionary(_data.get("ability_names", {}))
	return str(names.get(ability_id, ability_id))


func ability_ids() -> Array[String]:
	return ABILITY_ORDER.duplicate()


func advancement_mode_name(mode: String) -> String:
	match mode:
		ADVANCEMENT_PLUS_TWO:
			return "+2 к одной характеристике"
		ADVANCEMENT_SPLIT:
			return "+1 к двум характеристикам"
		ADVANCEMENT_FEAT:
			return "Выбрать черту"
		LEGACY_PRESERVED:
			return "Сохранено из прежней версии"
	return ""


func history_key(target_level: int, choice_id: String) -> String:
	return _history_key(target_level, choice_id)


func _validate_subclass(
	character: PlayerCharacter,
	definition: Dictionary,
	selection: Dictionary
) -> String:
	var option_id: String = str(selection.get("option_id", ""))
	var options: Array[String] = _string_array(definition.get("options", []))
	if option_id.is_empty() or option_id not in options:
		return "Выберите доступный воинский путь."
	var option: Dictionary = get_subclass_definition(option_id)
	if option.is_empty() or str(option.get("class_id", "")) != character.character_class_id:
		return "Выбранный подкласс не принадлежит текущему классу."
	if not character.subclass_id.is_empty() and character.subclass_id != option_id:
		return "Подкласс уже зафиксирован и не может быть заменён обычным повышением."
	return ""


func _validate_advancement(character: PlayerCharacter, selection: Dictionary) -> String:
	var mode: String = str(selection.get("mode", ""))
	var cap: int = maxi(int(_data.get("ability_score_cap", 20)), 1)
	match mode:
		ADVANCEMENT_PLUS_TWO:
			var ability_id: String = str(selection.get("primary_ability_id", ""))
			if ability_id not in ABILITY_ORDER:
				return "Выберите характеристику для увеличения на 2."
			if character.get_ability_score(ability_id) + 2 > cap:
				return "%s нельзя увеличить выше %d." % [ability_name(ability_id), cap]
		ADVANCEMENT_SPLIT:
			var primary_id: String = str(selection.get("primary_ability_id", ""))
			var secondary_id: String = str(selection.get("secondary_ability_id", ""))
			if primary_id not in ABILITY_ORDER or secondary_id not in ABILITY_ORDER:
				return "Выберите две характеристики для увеличения на 1."
			if primary_id == secondary_id:
				return "Для варианта +1/+1 нужны две разные характеристики."
			if character.get_ability_score(primary_id) + 1 > cap:
				return "%s нельзя увеличить выше %d." % [ability_name(primary_id), cap]
			if character.get_ability_score(secondary_id) + 1 > cap:
				return "%s нельзя увеличить выше %d." % [ability_name(secondary_id), cap]
		ADVANCEMENT_FEAT:
			var feat_id: String = str(selection.get("feat_id", ""))
			if feat_id.is_empty() or feat_id not in get_available_feat_ids(character):
				return "Выберите доступную черту, которой у героя ещё нет."
		_:
			return "Выберите способ развития героя."
	return ""


func _apply_ability_increase(
	abilities: Dictionary,
	bonuses: Dictionary,
	ability_id: String,
	amount: int
) -> void:
	if ability_id not in ABILITY_ORDER or amount <= 0:
		return
	abilities[ability_id] = int(abilities.get(ability_id, 10)) + amount
	bonuses[ability_id] = int(bonuses.get(ability_id, 0)) + amount


func _append_choice_definitions(result: Array[Dictionary], value: Variant) -> void:
	if not value is Array:
		return
	for item: Variant in value:
		if not item is Dictionary:
			continue
		var definition: Dictionary = (item as Dictionary).duplicate(true)
		var choice_id: String = str(definition.get("choice_id", ""))
		if choice_id.is_empty():
			continue
		var already_present: bool = false
		for existing: Dictionary in result:
			if str(existing.get("choice_id", "")) == choice_id:
				already_present = true
				break
		if not already_present:
			result.append(definition)


func _history_key(target_level: int, choice_id: String) -> String:
	return "%d:%s" % [target_level, choice_id]


func _load_data() -> void:
	_data.clear()
	if not FileAccess.file_exists(DATA_PATH):
		push_error("Каталог выборов уровня не найден: %s" % DATA_PATH)
		return
	var file: FileAccess = FileAccess.open(DATA_PATH, FileAccess.READ)
	if file == null:
		push_error("Не удалось открыть каталог выборов уровня: %s" % DATA_PATH)
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		push_error("Каталог выборов уровня имеет неверный формат.")
		return
	_data = (parsed as Dictionary).duplicate(true)


func _failure(message: String, invalid_choice_id: String = "") -> Dictionary:
	return {
		"success": false,
		"message": message,
		"invalid_choice_id": invalid_choice_id
	}


func _append_unique(values: Array[String], value: String) -> void:
	if not value.is_empty() and value not in values:
		values.append(value)


func _dictionary(value: Variant) -> Dictionary:
	return value as Dictionary if value is Dictionary else {}


func _string_array(value: Variant) -> Array[String]:
	var result: Array[String] = []
	if value is Array:
		for item: Variant in value:
			result.append(str(item))
	return result


func _unique_string_array(value: Variant) -> Array[String]:
	var result: Array[String] = []
	for item: String in _string_array(value):
		if not item.is_empty() and item not in result:
			result.append(item)
	return result
