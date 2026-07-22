class_name OriginDataSystem
extends RefCounted

const BACKGROUNDS_PATH: String = "res://data/origins/backgrounds.json"
const LANGUAGES_PATH: String = "res://data/origins/languages.json"
const DEFAULT_BACKGROUND_ID: String = "soldier"
const COMMON_LANGUAGE_ID: String = "common"
const LEGACY_BACKGROUND_ID: String = "legacy_origin"

var _backgrounds: Dictionary = {}
var _standard_languages: Array[Dictionary] = []


func _init() -> void:
	_load_databases()


func get_backgrounds() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for value: Variant in _backgrounds.values():
		if value is Dictionary:
			result.append((value as Dictionary).duplicate(true))
	result.sort_custom(func(left: Dictionary, right: Dictionary) -> bool: return str(left.get("name", "")) < str(right.get("name", "")))
	return result


func get_background(background_id: String) -> Dictionary:
	var value: Variant = _backgrounds.get(background_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func get_standard_languages() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for language: Dictionary in _standard_languages:
		result.append(language.duplicate(true))
	return result


func default_ability_bonuses(background_id: String) -> Dictionary:
	var background: Dictionary = get_background(background_id)
	var options: Array[String] = _string_array(background.get("ability_options", []))
	if options.size() < 2:
		return {}
	return {options[0]: 2, options[1]: 1}


func default_languages() -> Array[String]:
	var result: Array[String] = []
	for language: Dictionary in _standard_languages:
		var language_id: String = str(language.get("id", ""))
		if language_id.is_empty():
			continue
		result.append(language_id)
		if result.size() == 2:
			break
	return result


func validate_ability_bonuses(background_id: String, bonuses: Dictionary, base_abilities: Dictionary = {}) -> Dictionary:
	var background: Dictionary = get_background(background_id)
	if background.is_empty():
		return {"success": false, "message": "Неизвестное происхождение."}
	var allowed: Array[String] = _string_array(background.get("ability_options", []))
	var positive_values: Array[int] = []
	var total: int = 0
	for ability_value: Variant in bonuses.keys():
		var ability_id: String = str(ability_value)
		var amount: int = int(bonuses.get(ability_value, 0))
		if amount == 0:
			continue
		if ability_id not in allowed:
			return {"success": false, "message": "Бонус выбран для характеристики, недоступной этому происхождению."}
		if amount < 0 or amount > 2:
			return {"success": false, "message": "Один бонус происхождения может быть равен только +1 или +2."}
		if not base_abilities.is_empty() and int(base_abilities.get(ability_id, 10)) + amount > 20:
			return {"success": false, "message": "Бонус происхождения не может поднять характеристику выше 20."}
		positive_values.append(amount)
		total += amount
	positive_values.sort()
	var valid_split: bool = positive_values == [1, 2] or positive_values == [1, 1, 1]
	if total != 3 or not valid_split:
		return {"success": false, "message": "Распределите +2 и +1 между двумя характеристиками либо +1 между тремя."}
	return {"success": true, "message": "Бонусы происхождения распределены корректно."}


func validate_languages(language_ids: Array[String]) -> Dictionary:
	if language_ids.size() != 2:
		return {"success": false, "message": "Нужно выбрать два дополнительных языка."}
	if language_ids[0] == language_ids[1]:
		return {"success": false, "message": "Дополнительные языки не должны совпадать."}
	var available: Array[String] = []
	for language: Dictionary in _standard_languages:
		available.append(str(language.get("id", "")))
	for language_id: String in language_ids:
		if language_id not in available:
			return {"success": false, "message": "Выбран недоступный стандартный язык."}
	return {"success": true, "message": "Языки выбраны корректно."}


func apply_background(
	character: PlayerCharacter,
	background_id: String,
	bonuses: Dictionary,
	language_ids: Array[String],
	allow_reapply: bool = false
) -> Dictionary:
	if character == null:
		return {"success": false, "message": "Персонаж отсутствует."}
	if character.origin_applied and not allow_reapply:
		return {"success": false, "message": "Происхождение уже применено."}
	var background: Dictionary = get_background(background_id)
	if background.is_empty():
		return {"success": false, "message": "Неизвестное происхождение."}
	if character.base_abilities.is_empty():
		character.base_abilities = character.abilities.duplicate(true)
	var bonus_validation: Dictionary = validate_ability_bonuses(background_id, bonuses, character.base_abilities)
	if not bool(bonus_validation.get("success", false)):
		return bonus_validation
	var language_validation: Dictionary = validate_languages(language_ids)
	if not bool(language_validation.get("success", false)):
		return language_validation

	var final_abilities: Dictionary = character.base_abilities.duplicate(true)
	for ability_value: Variant in bonuses.keys():
		var ability_id: String = str(ability_value)
		final_abilities[ability_id] = int(final_abilities.get(ability_id, 10)) + int(bonuses.get(ability_value, 0))
	character.abilities = final_abilities
	character.ruleset_id = PlayerCharacter.DEFAULT_RULESET_ID
	character.background_id = background_id
	character.background_name = str(background.get("name", background_id))
	character.background_ability_bonuses = bonuses.duplicate(true)
	character.origin_feat_id = str(background.get("origin_feat_id", ""))
	character.skill_proficiencies = _string_array(background.get("skill_proficiencies", []))
	character.tool_proficiencies = _string_array(background.get("tool_proficiencies", []))
	character.language_proficiencies.clear()
	character.language_proficiencies.append(COMMON_LANGUAGE_ID)
	for language_id: String in language_ids:
		if language_id not in character.language_proficiencies:
			character.language_proficiencies.append(language_id)
	character.origin_applied = true
	return {
		"success": true,
		"message": "Происхождение применено.",
		"background_id": background_id,
		"origin_feat_id": character.origin_feat_id
	}


func apply_class_proficiencies(character: PlayerCharacter, class_data: Dictionary) -> void:
	if character == null or class_data.is_empty():
		return
	for ability_id: String in _string_array(class_data.get("saving_throws", [])):
		if ability_id not in character.saving_throw_proficiencies:
			character.saving_throw_proficiencies.append(ability_id)


func ensure_legacy_origin(character: PlayerCharacter) -> void:
	if character == null:
		return
	character.ruleset_id = PlayerCharacter.DEFAULT_RULESET_ID
	if character.base_abilities.is_empty():
		character.base_abilities = character.abilities.duplicate(true)
	if character.background_id.is_empty():
		character.background_id = LEGACY_BACKGROUND_ID
		character.background_name = "Наследие прежней версии"
		character.background_ability_bonuses.clear()
		character.origin_feat_id = ""
		character.origin_applied = true
	if character.language_proficiencies.is_empty():
		character.language_proficiencies.append(COMMON_LANGUAGE_ID)


func _load_databases() -> void:
	_backgrounds.clear()
	_standard_languages.clear()
	var background_root: Dictionary = _load_json(BACKGROUNDS_PATH)
	var backgrounds_value: Variant = background_root.get("backgrounds", [])
	if backgrounds_value is Array:
		for value: Variant in backgrounds_value:
			if value is Dictionary:
				var background: Dictionary = value as Dictionary
				var background_id: String = str(background.get("id", ""))
				if not background_id.is_empty():
					_backgrounds[background_id] = background
	var language_root: Dictionary = _load_json(LANGUAGES_PATH)
	var languages_value: Variant = language_root.get("standard_language_choices", [])
	if languages_value is Array:
		for value: Variant in languages_value:
			if value is Dictionary:
				_standard_languages.append(value as Dictionary)


func _load_json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		push_error("Файл данных происхождений не найден: %s" % path)
		return {}
	var file: FileAccess = FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_error("Не удалось открыть файл данных происхождений: %s" % path)
		return {}
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		push_error("Файл данных происхождений содержит некорректный JSON: %s" % path)
		return {}
	return parsed as Dictionary


static func _string_array(value: Variant) -> Array[String]:
	var result: Array[String] = []
	if value is Array:
		for item: Variant in value:
			result.append(str(item))
	return result
