class_name SpellcastingSystem
extends RefCounted

const ABILITIES_PATH: String = "res://data/abilities/abilities.json"
const CLASSES_PATH: String = "res://data/classes/classes.json"
const RITUAL_EXTRA_MINUTES: int = 10

const PREPARED_SPELLS_STATE_KEY: String = "_prepared_spell_ids"
const SPELLCASTING_ABILITY_STATE_KEY: String = "_spellcasting_ability_id"
const PREPARED_LIMIT_STATE_KEY: String = "_prepared_spell_limit"
const CONCENTRATION_STATE_KEY: String = "_concentration_spell_id"

const DETECT_MAGIC_UNTIL_KEY: String = "detect_magic_until_minute"
const COMPREHEND_LANGUAGES_UNTIL_KEY: String = "comprehend_languages_until_minute"

var _abilities: Dictionary = {}
var _classes: Dictionary = {}


func _init() -> void:
	_load_databases()


func ensure_character(character: PlayerCharacter, refill_slots: bool = false) -> bool:
	if character == null:
		return false
	var profile: Dictionary = get_spellcasting_profile(character.character_class_id)
	var changed: bool = false
	if not profile.is_empty():
		var ability_id: String = str(profile.get("ability", ""))
		if str(character.class_resources.get(SPELLCASTING_ABILITY_STATE_KEY, "")) != ability_id:
			character.class_resources[SPELLCASTING_ABILITY_STATE_KEY] = ability_id
			changed = true
		var prepared_limit: int = maxi(int(profile.get("prepared_limit", 0)), 0)
		if int(character.class_resources.get(PREPARED_LIMIT_STATE_KEY, -1)) != prepared_limit:
			character.class_resources[PREPARED_LIMIT_STATE_KEY] = prepared_limit
			changed = true
		for spell_id: String in _string_array(profile.get("starting_spells", [])):
			changed = _append_unique(character.known_features, spell_id) or changed
		var profile_prepared: Array[String] = get_prepared_spell_ids(character)
		for spell_id: String in _string_array(profile.get("starting_prepared", [])):
			if spell_id not in profile_prepared:
				profile_prepared.append(spell_id)
				changed = true
		_store_prepared_spell_ids(character, profile_prepared)
		var slot_maximums_value: Variant = profile.get("slot_maximums", {})
		if slot_maximums_value is Dictionary:
			for level_value: Variant in (slot_maximums_value as Dictionary).keys():
				var level: int = maxi(int(str(level_value)), 1)
				var maximum: int = maxi(int((slot_maximums_value as Dictionary)[level_value]), 0)
				var resource_key: String = slot_resource_key(character, level)
				var had_maximum: bool = character.class_resource_maximums.has(resource_key)
				var current: int = character.get_resource(resource_key)
				character.class_resource_maximums[resource_key] = maximum
				if refill_slots or not had_maximum:
					character.class_resources[resource_key] = maximum
				else:
					character.class_resources[resource_key] = clampi(current, 0, maximum)
				changed = changed or not had_maximum
	for feature_id: String in character.known_features.duplicate():
		var spell: Dictionary = get_spell_definition(feature_id)
		if spell.is_empty() or not bool(spell.get("always_prepared", false)):
			continue
		var always_prepared_ids: Array[String] = get_prepared_spell_ids(character)
		if feature_id not in always_prepared_ids:
			always_prepared_ids.append(feature_id)
			_store_prepared_spell_ids(character, always_prepared_ids)
			changed = true
	return changed


func recover_after_rest(character: PlayerCharacter, long_rest: bool) -> bool:
	if character == null:
		return false
	ensure_character(character, false)
	var profile: Dictionary = get_spellcasting_profile(character.character_class_id)
	if profile.is_empty():
		if long_rest:
			end_concentration(character)
		return false
	var recovery: String = str(profile.get("slot_recovery", "long_rest"))
	var should_refill: bool = long_rest or recovery == "short_rest"
	var changed: bool = false
	if should_refill:
		var slot_maximums_value: Variant = profile.get("slot_maximums", {})
		if slot_maximums_value is Dictionary:
			for level_value: Variant in (slot_maximums_value as Dictionary).keys():
				var level: int = maxi(int(str(level_value)), 1)
				var resource_key: String = slot_resource_key(character, level)
				var maximum: int = maxi(character.get_resource_maximum(resource_key), 0)
				if character.get_resource(resource_key) != maximum:
					character.class_resources[resource_key] = maximum
					changed = true
	if long_rest and not get_concentration_spell_id(character).is_empty():
		end_concentration(character)
		changed = true
	return changed


func get_spellcasting_profile(class_id: String) -> Dictionary:
	var class_value: Variant = _classes.get(class_id, {})
	if not class_value is Dictionary:
		return {}
	var profile_value: Variant = (class_value as Dictionary).get("spellcasting", {})
	return (profile_value as Dictionary).duplicate(true) if profile_value is Dictionary else {}


func get_spell_definition(spell_id: String) -> Dictionary:
	var value: Variant = _abilities.get(spell_id, {})
	if not value is Dictionary:
		return {}
	var definition: Dictionary = (value as Dictionary).duplicate(true)
	return definition if is_spell_definition(definition) else {}


func is_spell_definition(definition: Dictionary) -> bool:
	if bool(definition.get("is_spell", false)):
		return true
	return str(definition.get("effect", "")) in [
		"spell_attack", "saving_throw_spell", "auto_hit_spell", "heal_2d8_wisdom",
		"origin_heal", "hunters_mark", "utility_detect_magic", "utility_comprehend_languages"
	]


func get_known_spell_ids(character: PlayerCharacter) -> Array[String]:
	var result: Array[String] = []
	if character == null:
		return result
	for feature_id: String in character.known_features:
		if not get_spell_definition(feature_id).is_empty() and feature_id not in result:
			result.append(feature_id)
	return result


func get_prepared_spell_ids(character: PlayerCharacter) -> Array[String]:
	if character == null:
		return []
	return _string_array(character.class_resources.get(PREPARED_SPELLS_STATE_KEY, []))


func get_prepared_limit(character: PlayerCharacter) -> int:
	return 0 if character == null else maxi(int(character.class_resources.get(PREPARED_LIMIT_STATE_KEY, 0)), 0)


func get_spellcasting_ability(character: PlayerCharacter, spell: Dictionary = {}) -> String:
	if not spell.is_empty() and not str(spell.get("ability", "")).is_empty():
		return str(spell.get("ability", ""))
	return "" if character == null else str(character.class_resources.get(SPELLCASTING_ABILITY_STATE_KEY, ""))


func get_spell_attack_bonus(character: PlayerCharacter, spell: Dictionary = {}) -> int:
	if character == null:
		return 0
	var ability_id: String = get_spellcasting_ability(character, spell)
	return character.get_proficiency_bonus() + character.get_ability_modifier(ability_id)


func get_spell_save_dc(character: PlayerCharacter, spell: Dictionary = {}) -> int:
	return 8 + get_spell_attack_bonus(character, spell)


func is_prepared(character: PlayerCharacter, spell_id: String) -> bool:
	var spell: Dictionary = get_spell_definition(spell_id)
	if character == null or spell.is_empty() or spell_id not in get_known_spell_ids(character):
		return false
	return int(spell.get("spell_level", 0)) == 0 or bool(spell.get("always_prepared", false)) or spell_id in get_prepared_spell_ids(character)


func prepare_spell(character: PlayerCharacter, spell_id: String) -> Dictionary:
	var spell: Dictionary = get_spell_definition(spell_id)
	if character == null or spell.is_empty() or spell_id not in get_known_spell_ids(character):
		return _failure("Заклинание не изучено.")
	if int(spell.get("spell_level", 0)) == 0 or bool(spell.get("always_prepared", false)):
		return _success("Это заклинание всегда подготовлено.")
	var prepared: Array[String] = get_prepared_spell_ids(character)
	if spell_id in prepared:
		return _success("Заклинание уже подготовлено.")
	var counted: int = _count_changeable_prepared(character, prepared)
	var limit: int = get_prepared_limit(character)
	if limit <= 0 or counted >= limit:
		return _failure("Достигнут предел подготовленных заклинаний: %d." % limit)
	prepared.append(spell_id)
	_store_prepared_spell_ids(character, prepared)
	return _success("Заклинание подготовлено.")


func unprepare_spell(character: PlayerCharacter, spell_id: String) -> Dictionary:
	var spell: Dictionary = get_spell_definition(spell_id)
	if character == null or spell.is_empty():
		return _failure("Заклинание не найдено.")
	if int(spell.get("spell_level", 0)) == 0 or bool(spell.get("always_prepared", false)):
		return _failure("Это заклинание нельзя снять с подготовки.")
	var prepared: Array[String] = get_prepared_spell_ids(character)
	if spell_id not in prepared:
		return _failure("Заклинание не подготовлено.")
	prepared.erase(spell_id)
	_store_prepared_spell_ids(character, prepared)
	return _success("Заклинание снято с подготовки.")


func can_cast_spell(character: PlayerCharacter, spell: Dictionary, as_ritual: bool = false, in_combat: bool = false, slot_level: int = 0) -> bool:
	if character == null or spell.is_empty() or not is_spell_definition(spell):
		return false
	var spell_id: String = str(spell.get("id", ""))
	if spell_id.is_empty() or spell_id not in get_known_spell_ids(character) or not is_prepared(character, spell_id):
		return false
	var level: int = maxi(int(spell.get("spell_level", 0)), 0)
	if as_ritual:
		return level > 0 and bool(spell.get("ritual", false)) and not in_combat
	if level == 0:
		return true
	var resource_key: String = str(spell.get("resource_key", ""))
	if not resource_key.is_empty() and resource_key != "unlimited" and not resource_key.begins_with("spell_slots_"):
		if character.get_resource(resource_key) > 0:
			return true
		var fallback_key: String = str(spell.get("fallback_resource_key", ""))
		if not fallback_key.is_empty() and character.get_resource(_mapped_resource_key(character, fallback_key)) > 0:
			return true
		return false
	return _find_available_slot_level(character, maxi(slot_level, level), level) > 0


func consume_spell_cost(character: PlayerCharacter, spell: Dictionary, slot_level: int = 0) -> bool:
	if character == null or spell.is_empty():
		return false
	var level: int = maxi(int(spell.get("spell_level", 0)), 0)
	if level == 0:
		return true
	var resource_key: String = str(spell.get("resource_key", ""))
	if not resource_key.is_empty() and resource_key != "unlimited" and not resource_key.begins_with("spell_slots_"):
		if character.consume_resource(resource_key, 1):
			return true
		var fallback_key: String = str(spell.get("fallback_resource_key", ""))
		return not fallback_key.is_empty() and character.consume_resource(_mapped_resource_key(character, fallback_key), 1)
	var selected_level: int = _find_available_slot_level(character, maxi(slot_level, level), level)
	return selected_level > 0 and character.consume_resource(slot_resource_key(character, selected_level), 1)


func active_resource_key(character: PlayerCharacter, spell: Dictionary) -> String:
	var level: int = maxi(int(spell.get("spell_level", 0)), 0)
	if level == 0:
		return "unlimited"
	var resource_key: String = str(spell.get("resource_key", ""))
	if not resource_key.is_empty() and resource_key != "unlimited" and not resource_key.begins_with("spell_slots_"):
		if character.get_resource(resource_key) > 0:
			return resource_key
		var fallback_key: String = str(spell.get("fallback_resource_key", ""))
		return _mapped_resource_key(character, fallback_key) if not fallback_key.is_empty() else resource_key
	var selected_level: int = _find_available_slot_level(character, level, level)
	return slot_resource_key(character, selected_level) if selected_level > 0 else slot_resource_key(character, level)


func slot_resource_key(character: PlayerCharacter, level: int) -> String:
	var profile: Dictionary = get_spellcasting_profile(character.character_class_id if character != null else "")
	var prefix: String = str(profile.get("slot_resource_prefix", "spell_slots"))
	return "%s_%d" % [prefix, maxi(level, 1)]


func cast_ritual(character: PlayerCharacter, spell_id: String, current_world_minutes: int, in_combat: bool = false) -> Dictionary:
	var spell: Dictionary = get_spell_definition(spell_id)
	if not can_cast_spell(character, spell, true, in_combat):
		return _failure("Ритуал недоступен: заклинание должно быть изучено, подготовлено и иметь тег «Ритуал»; в бою ритуалы запрещены.")
	var casting_minutes: int = ritual_casting_minutes(spell)
	var completion_minute: int = maxi(current_world_minutes, 0) + casting_minutes
	var effect_result: Dictionary = _apply_utility_effect(character, spell, completion_minute)
	if not bool(effect_result.get("success", false)):
		return effect_result
	if bool(spell.get("concentration", false)):
		begin_concentration(character, spell_id)
	return {
		"success": true,
		"message": "%s сотворено как ритуал без расхода ячейки. Затрачено %d мин." % [str(spell.get("name", "Заклинание")), casting_minutes],
		"advance_minutes": casting_minutes,
		"spell_id": spell_id,
		"ritual": true
	}


func cast_utility_spell(character: PlayerCharacter, spell: Dictionary, current_world_minutes: int, in_combat: bool = false) -> Dictionary:
	if not can_cast_spell(character, spell, false, in_combat):
		return _failure("Заклинание не подготовлено или нет доступной ячейки.")
	if not consume_spell_cost(character, spell):
		return _failure("Не удалось израсходовать ячейку заклинания.")
	var result: Dictionary = _apply_utility_effect(character, spell, maxi(current_world_minutes, 0))
	if bool(result.get("success", false)) and bool(spell.get("concentration", false)):
		begin_concentration(character, str(spell.get("id", "")))
	return result


func ritual_casting_minutes(spell: Dictionary) -> int:
	return RITUAL_EXTRA_MINUTES + maxi(int(spell.get("casting_time_minutes", 0)), 0)


func begin_concentration(character: PlayerCharacter, spell_id: String) -> String:
	if character == null:
		return ""
	var previous: String = str(character.class_resources.get(CONCENTRATION_STATE_KEY, ""))
	character.class_resources[CONCENTRATION_STATE_KEY] = spell_id
	return previous


func end_concentration(character: PlayerCharacter) -> String:
	if character == null:
		return ""
	var previous: String = str(character.class_resources.get(CONCENTRATION_STATE_KEY, ""))
	character.class_resources.erase(CONCENTRATION_STATE_KEY)
	return previous


func get_concentration_spell_id(character: PlayerCharacter) -> String:
	return "" if character == null else str(character.class_resources.get(CONCENTRATION_STATE_KEY, ""))


func cleanup_expired_effects(character: PlayerCharacter, current_world_minutes: int) -> void:
	if character == null:
		return
	for key: String in [DETECT_MAGIC_UNTIL_KEY, COMPREHEND_LANGUAGES_UNTIL_KEY]:
		if int(character.active_effects.get(key, -1)) >= 0 and int(character.active_effects.get(key, -1)) <= current_world_minutes:
			character.active_effects.erase(key)
	if get_concentration_spell_id(character) == "detect_magic" and not has_detect_magic(character, current_world_minutes):
		end_concentration(character)


func has_detect_magic(character: PlayerCharacter, current_world_minutes: int) -> bool:
	return character != null and int(character.active_effects.get(DETECT_MAGIC_UNTIL_KEY, -1)) > current_world_minutes


func comprehends_all_languages(character: PlayerCharacter, current_world_minutes: int) -> bool:
	return character != null and int(character.active_effects.get(COMPREHEND_LANGUAGES_UNTIL_KEY, -1)) > current_world_minutes


func describe_spell(character: PlayerCharacter, spell: Dictionary) -> String:
	if spell.is_empty():
		return ""
	var level: int = maxi(int(spell.get("spell_level", 0)), 0)
	var level_text: String = "Заговор" if level == 0 else "Уровень %d" % level
	var casting_text: String = str(spell.get("casting_time_text", "1 действие"))
	var range_text: String = "На себя" if str(spell.get("target", "")) == "self" else "%d футов" % maxi(int(spell.get("range_ft", 0)), 0)
	var tags: Array[String] = []
	if bool(spell.get("concentration", false)):
		tags.append("Концентрация")
	if bool(spell.get("ritual", false)):
		tags.append("Ритуал")
	var tag_text: String = "" if tags.is_empty() else " · %s" % " · ".join(tags)
	var prepared_text: String = "Подготовлено" if is_prepared(character, str(spell.get("id", ""))) else "Не подготовлено"
	return "%s · %s\nСотворение: %s · Дистанция: %s%s\n%s" % [
		level_text,
		str(spell.get("school", "Магия")),
		casting_text,
		range_text,
		tag_text,
		prepared_text
	]


func _apply_utility_effect(character: PlayerCharacter, spell: Dictionary, effect_start_minute: int) -> Dictionary:
	var effect: String = str(spell.get("effect", ""))
	var duration_minutes: int = maxi(int(spell.get("duration_minutes", 0)), 0)
	match effect:
		"utility_detect_magic":
			character.active_effects[DETECT_MAGIC_UNTIL_KEY] = effect_start_minute + duration_minutes
			return _success("Обнаружение магии активно на %d мин. Магические ауры в пределах 30 футов могут быть выявлены." % duration_minutes)
		"utility_comprehend_languages":
			character.active_effects[COMPREHEND_LANGUAGES_UNTIL_KEY] = effect_start_minute + duration_minutes
			return _success("Понимание языков активно на %d мин. Персонаж понимает буквальный смысл известных языковых форм." % duration_minutes)
		_:
			return _failure("Для этого ритуального эффекта ещё не создан исполнитель.")


func _find_available_slot_level(character: PlayerCharacter, preferred_level: int, minimum_level: int) -> int:
	var start_level: int = maxi(preferred_level, minimum_level)
	for level: int in range(start_level, 10):
		if character.get_resource(slot_resource_key(character, level)) > 0:
			return level
	return 0


func _mapped_resource_key(character: PlayerCharacter, resource_key: String) -> String:
	if resource_key.begins_with("spell_slots_"):
		return slot_resource_key(character, maxi(int(resource_key.trim_prefix("spell_slots_")), 1))
	return resource_key


func _count_changeable_prepared(character: PlayerCharacter, prepared: Array[String]) -> int:
	var result: int = 0
	for spell_id: String in prepared:
		var spell: Dictionary = get_spell_definition(spell_id)
		if spell.is_empty() or int(spell.get("spell_level", 0)) == 0 or bool(spell.get("always_prepared", false)):
			continue
		result += 1
	return result


func _store_prepared_spell_ids(character: PlayerCharacter, prepared: Array[String]) -> void:
	var unique: Array[String] = []
	for spell_id: String in prepared:
		if not spell_id.is_empty() and not get_spell_definition(spell_id).is_empty() and spell_id not in unique:
			unique.append(spell_id)
	character.class_resources[PREPARED_SPELLS_STATE_KEY] = unique


func _load_databases() -> void:
	_abilities = _load_json(ABILITIES_PATH)
	var root: Dictionary = _load_json(CLASSES_PATH)
	var classes_value: Variant = root.get("classes", [])
	if classes_value is Array:
		for class_value: Variant in classes_value:
			if class_value is Dictionary:
				var class_data: Dictionary = class_value as Dictionary
				_classes[str(class_data.get("id", ""))] = class_data


func _load_json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		push_error("Файл данных магии не найден: %s" % path)
		return {}
	var file: FileAccess = FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {}
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	return parsed as Dictionary if parsed is Dictionary else {}


func _string_array(value: Variant) -> Array[String]:
	var result: Array[String] = []
	if value is Array:
		for item: Variant in value:
			var text: String = str(item)
			if not text.is_empty() and text not in result:
				result.append(text)
	return result


func _append_unique(values: Array[String], value: String) -> bool:
	if value.is_empty() or value in values:
		return false
	values.append(value)
	return true


func _success(message: String) -> Dictionary:
	return {"success": true, "message": message}


func _failure(message: String) -> Dictionary:
	return {"success": false, "message": message}
