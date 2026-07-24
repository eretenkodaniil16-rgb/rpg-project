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
var _progression: SpellcastingProgressionSystem = SpellcastingProgressionSystem.new()


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
		var fallback_limit: int = maxi(int(profile.get("prepared_limit", 0)), 0)
		var prepared_limit: int = _progression.get_prepared_limit(character.character_class_id, character.level, fallback_limit)
		if int(character.class_resources.get(PREPARED_LIMIT_STATE_KEY, -1)) != prepared_limit:
			character.class_resources[PREPARED_LIMIT_STATE_KEY] = prepared_limit
			changed = true
		for spell_id: String in _string_array(profile.get("starting_spells", [])):
			changed = _append_unique(character.known_features, spell_id) or changed
		var had_prepared_state: bool = character.class_resources.has(PREPARED_SPELLS_STATE_KEY)
		var profile_prepared: Array[String] = get_prepared_spell_ids(character)
		if not had_prepared_state:
			for spell_id: String in _string_array(profile.get("starting_prepared", [])):
				if spell_id not in profile_prepared:
					profile_prepared.append(spell_id)
					changed = true
		_store_prepared_spell_ids(character, profile_prepared)
		changed = changed or not had_prepared_state
		var maximums: Dictionary = _slot_maximums(character, profile)
		changed = _sync_slot_resources(character, profile, maximums, refill_slots) or changed
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
		for level_value: Variant in _slot_maximums(character, profile).keys():
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


func can_cast_spell(character: PlayerCharacter, spell: Dictionary, as_ritual: bool = false, in_combat: bool = false, slot_level: int = 0, casting_context: Dictionary = {}) -> bool:
	if character == null or spell.is_empty() or not is_spell_definition(spell):
		return false
	if not bool(check_spell_components(spell, casting_context).get("success", false)):
		return false
	var spell_id: String = str(spell.get("id", ""))
	if spell_id.is_empty() or spell_id not in get_known_spell_ids(character):
		return false
	var level: int = maxi(int(spell.get("spell_level", 0)), 0)
	var prepared: bool = is_prepared(character, spell_id)
	if as_ritual:
		var wizard_ritual_adept: bool = character.character_class_id == "wizard" and "ritual_adept" in character.known_features
		return level > 0 and bool(spell.get("ritual", false)) and not in_combat and (prepared or wizard_ritual_adept)
	if not prepared:
		return false
	if level == 0:
		return true
	var special_key: String = _available_special_resource_key(character, spell)
	if not special_key.is_empty():
		return true
	if _has_special_resource_contract(spell) and str(spell.get("fallback_resource_key", "")).is_empty():
		return false
	if _turn_slot_rule_blocked(character, casting_context):
		return false
	return resolve_slot_level(character, spell, slot_level) > 0


func consume_spell_cost(character: PlayerCharacter, spell: Dictionary, slot_level: int = 0) -> bool:
	return bool(consume_spell_cost_detailed(character, spell, slot_level).get("success", false))


func active_resource_key(character: PlayerCharacter, spell: Dictionary) -> String:
	if character == null or spell.is_empty():
		return ""
	var level: int = maxi(int(spell.get("spell_level", 0)), 0)
	if level == 0:
		return "unlimited"
	var special_key: String = _available_special_resource_key(character, spell)
	if not special_key.is_empty():
		return special_key
	var selected_level: int = resolve_slot_level(character, spell, 0)
	return slot_resource_key(character, selected_level if selected_level > 0 else level)


func slot_resource_key(character: PlayerCharacter, level: int) -> String:
	var profile: Dictionary = get_spellcasting_profile(character.character_class_id if character != null else "")
	var prefix: String = str(profile.get("slot_resource_prefix", "spell_slots"))
	if character != null and _progression.uses_pact_magic(character.character_class_id):
		var pact_level: int = _progression.get_pact_slot_level(character.character_class_id, character.level)
		return "%s_%d" % [prefix, maxi(pact_level, 1)]
	return "%s_%d" % [prefix, maxi(level, 1)]


func cast_ritual(character: PlayerCharacter, spell_id: String, current_world_minutes: int, in_combat: bool = false) -> Dictionary:
	var spell: Dictionary = get_spell_definition(spell_id)
	if not can_cast_spell(character, spell, true, in_combat):
		return _failure("Ритуал недоступен: нужен известный Ritual-спелл; обычно он должен быть подготовлен. Волшебник с Мастером ритуалов может читать его из книги без подготовки. В бою ритуалы запрещены.")
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


func consume_spell_cost_detailed(character: PlayerCharacter, spell: Dictionary, slot_level: int = 0, casting_context: Dictionary = {}) -> Dictionary:
	if character == null or spell.is_empty():
		return _failure("Заклинание не найдено.")
	var component_result: Dictionary = check_spell_components(spell, casting_context)
	if not bool(component_result.get("success", false)):
		return component_result
	var level: int = maxi(int(spell.get("spell_level", 0)), 0)
	if level == 0:
		return {"success": true, "message": "Заговор не расходует ячейку.", "slot_level": 0, "resource_key": "unlimited", "expended_slot": false}
	var special_key: String = _available_special_resource_key(character, spell)
	if not special_key.is_empty():
		if not character.consume_resource(special_key, 1):
			return _failure("Не удалось израсходовать бесплатное применение.")
		return {"success": true, "message": "Использовано специальное применение.", "slot_level": level, "resource_key": special_key, "expended_slot": false}
	if _turn_slot_rule_blocked(character, casting_context):
		return _failure("На этом ходу уже была потрачена ячейка на другое заклинание.")
	var selected_level: int = resolve_slot_level(character, spell, slot_level)
	if selected_level <= 0:
		return _failure("Нет доступной ячейки подходящего уровня.")
	var resource_key: String = slot_resource_key(character, selected_level)
	if not character.consume_resource(resource_key, 1):
		return _failure("Не удалось израсходовать выбранную ячейку.")
	_mark_slot_expended(character, casting_context)
	return {"success": true, "message": "Израсходована ячейка %d уровня." % selected_level, "slot_level": selected_level, "resource_key": resource_key, "expended_slot": true}


func get_available_slot_levels(character: PlayerCharacter, minimum_level: int = 1, require_remaining: bool = true) -> Array[int]:
	var result: Array[int] = []
	if character == null:
		return result
	var profile: Dictionary = get_spellcasting_profile(character.character_class_id)
	var maximums: Dictionary = _slot_maximums(character, profile)
	for level_value: Variant in maximums.keys():
		var level: int = maxi(int(str(level_value)), 1)
		if level < minimum_level:
			continue
		var key: String = slot_resource_key(character, level)
		if not require_remaining or character.get_resource(key) > 0:
			if level not in result:
				result.append(level)
	result.sort()
	return result


func resolve_slot_level(character: PlayerCharacter, spell: Dictionary, requested_level: int = 0) -> int:
	if character == null or spell.is_empty():
		return 0
	var minimum: int = maxi(int(spell.get("spell_level", 0)), 1)
	var chosen: int = requested_level
	if chosen <= 0:
		chosen = get_selected_slot_level(character, str(spell.get("id", "")))
	var available: Array[int] = get_available_slot_levels(character, minimum, true)
	if chosen > 0:
		return chosen if chosen in available else 0
	return available[0] if not available.is_empty() else 0


func set_selected_slot_level(character: PlayerCharacter, spell_id: String, slot_level: int) -> Dictionary:
	var spell: Dictionary = get_spell_definition(spell_id)
	if character == null or spell.is_empty() or int(spell.get("spell_level", 0)) <= 0:
		return _failure("Для этого заклинания уровень ячейки не выбирается.")
	var selectable: Array[int] = get_available_slot_levels(character, int(spell.get("spell_level", 1)), false)
	if slot_level not in selectable:
		return _failure("Ячейка %d уровня недоступна этому персонажу." % slot_level)
	var choices_value: Variant = character.class_resources.get("_selected_spell_slot_levels", {})
	var choices: Dictionary = (choices_value as Dictionary).duplicate(true) if choices_value is Dictionary else {}
	choices[spell_id] = slot_level
	character.class_resources["_selected_spell_slot_levels"] = choices
	return _success("Выбрана ячейка %d уровня." % slot_level)


func get_selected_slot_level(character: PlayerCharacter, spell_id: String) -> int:
	if character == null:
		return 0
	var choices_value: Variant = character.class_resources.get("_selected_spell_slot_levels", {})
	if not choices_value is Dictionary:
		return 0
	return maxi(int((choices_value as Dictionary).get(spell_id, 0)), 0)


func check_spell_components(spell: Dictionary, casting_context: Dictionary = {}) -> Dictionary:
	var components: Array[String] = _string_array(spell.get("components", []))
	if "v" in components and not bool(casting_context.get("can_speak", true)):
		return _failure("Для вербального компонента требуется нормальная речь.")
	if not bool(casting_context.get("armor_trained", true)):
		return _failure("Нельзя сотворять заклинание в доспехе без соответствующего обучения.")
	var free_hands: int = maxi(int(casting_context.get("free_hands", 1)), 0)
	var focus_in_hand: bool = bool(casting_context.get("focus_in_hand", true))
	var has_pouch: bool = bool(casting_context.get("has_component_pouch", true))
	var has_material: bool = bool(casting_context.get("has_required_material", true))
	var has_m: bool = "m" in components
	if has_m:
		var costly_or_consumed: bool = int(spell.get("material_cost_gp", 0)) > 0 or bool(spell.get("material_consumed", false))
		if costly_or_consumed:
			if not has_material or free_hands <= 0:
				return _failure("Нужен указанный материальный компонент и свободная рука.")
		elif not focus_in_hand and not (has_pouch and free_hands > 0):
			return _failure("Нужен магический фокус в руке или сумка компонентов со свободной рукой.")
	if "s" in components and free_hands <= 0 and not (has_m and focus_in_hand):
		return _failure("Для соматического компонента требуется свободная рука.")
	return _success("Компоненты доступны.")


func scale_dice_for_slot(spell: Dictionary, base_dice: Array[int], slot_level: int, kind: String) -> Array[int]:
	var result: Array[int] = [maxi(base_dice[0] if base_dice.size() > 0 else 1, 1), maxi(base_dice[1] if base_dice.size() > 1 else 6, 2)]
	var base_level: int = maxi(int(spell.get("spell_level", 0)), 0)
	var extra_levels: int = maxi(slot_level - base_level, 0)
	if extra_levels <= 0:
		return result
	var upcast_value: Variant = spell.get("upcast", {})
	if not upcast_value is Dictionary:
		return result
	var field: String = "%s_dice_per_level" % kind
	var pair_value: Variant = (upcast_value as Dictionary).get(field, [])
	if pair_value is Array and (pair_value as Array).size() >= 2:
		result[0] += maxi(int((pair_value as Array)[0]), 0) * extra_levels
		result[1] = maxi(int((pair_value as Array)[1]), 2)
	return result


func damage_bonus_for_slot(spell: Dictionary, slot_level: int) -> int:
	var base_bonus: int = int(spell.get("damage_bonus", 0))
	var extra_levels: int = maxi(slot_level - maxi(int(spell.get("spell_level", 0)), 0), 0)
	var upcast_value: Variant = spell.get("upcast", {})
	var per_level: int = int((upcast_value as Dictionary).get("damage_bonus_per_level", 0)) if upcast_value is Dictionary else 0
	return base_bonus + per_level * extra_levels


func ritual_casting_minutes(spell: Dictionary) -> int:
	return RITUAL_EXTRA_MINUTES + maxi(int(spell.get("casting_time_minutes", 0)), 0)


func begin_concentration(character: PlayerCharacter, spell_id: String) -> String:
	if character == null:
		return ""
	var previous: String = str(character.class_resources.get(CONCENTRATION_STATE_KEY, ""))
	if not previous.is_empty() and previous != spell_id:
		_clear_concentration_bound_effect(character, previous)
	character.class_resources[CONCENTRATION_STATE_KEY] = spell_id
	return previous


func end_concentration(character: PlayerCharacter) -> String:
	if character == null:
		return ""
	var previous: String = str(character.class_resources.get(CONCENTRATION_STATE_KEY, ""))
	character.class_resources.erase(CONCENTRATION_STATE_KEY)
	_clear_concentration_bound_effect(character, previous)
	return previous


func get_concentration_spell_id(character: PlayerCharacter) -> String:
	return "" if character == null else str(character.class_resources.get(CONCENTRATION_STATE_KEY, ""))


func sync_concentration_to_combat_state(character: PlayerCharacter, combat_state: CombatantState, source_id: int = 0) -> void:
	if combat_state == null:
		return
	var spell_id: String = get_concentration_spell_id(character)
	if spell_id.is_empty():
		combat_state.clear_concentration()
	else:
		combat_state.set_concentration(spell_id, source_id)


func _clear_concentration_bound_effect(character: PlayerCharacter, spell_id: String) -> void:
	if character == null or spell_id.is_empty():
		return
	match spell_id:
		"detect_magic":
			character.active_effects.erase(DETECT_MAGIC_UNTIL_KEY)
		"hunters_mark":
			character.active_effects.erase("hunters_mark_hits")


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
	if not is_prepared(character, str(spell.get("id", ""))) and character.character_class_id == "wizard" and "ritual_adept" in character.known_features and bool(spell.get("ritual", false)):
		prepared_text += " · доступно как ритуал из книги"
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
	var available: Array[int] = get_available_slot_levels(character, minimum_level, true)
	if preferred_level in available:
		return preferred_level
	for level: int in available:
		if level >= preferred_level:
			return level
	return available[0] if not available.is_empty() else 0


func _slot_maximums(character: PlayerCharacter, profile: Dictionary) -> Dictionary:
	var progression_maximums: Dictionary = _progression.get_slot_maximums(character.character_class_id, character.level)
	if not progression_maximums.is_empty():
		return progression_maximums
	var fallback_value: Variant = profile.get("slot_maximums", {})
	return (fallback_value as Dictionary).duplicate(true) if fallback_value is Dictionary else {}


func _sync_slot_resources(character: PlayerCharacter, profile: Dictionary, maximums: Dictionary, refill_slots: bool) -> bool:
	if _progression.uses_pact_magic(character.character_class_id):
		return _sync_pact_slot_resources(character, profile, maximums, refill_slots)
	var prefix: String = str(profile.get("slot_resource_prefix", "spell_slots"))
	var changed: bool = false
	for level: int in range(1, 10):
		var key: String = "%s_%d" % [prefix, level]
		var maximum: int = maxi(int(maximums.get(str(level), maximums.get(level, 0))), 0)
		var had_maximum: bool = character.class_resource_maximums.has(key)
		var old_maximum: int = character.get_resource_maximum(key)
		var current: int = character.get_resource(key)
		if maximum <= 0:
			if had_maximum or character.class_resources.has(key):
				character.class_resource_maximums.erase(key)
				character.class_resources.erase(key)
				changed = true
			continue
		var spent: int = maxi(old_maximum - current, 0)
		var next_current: int = maximum if refill_slots or not had_maximum else clampi(maximum - spent, 0, maximum)
		if not had_maximum or old_maximum != maximum or current != next_current:
			changed = true
		character.class_resource_maximums[key] = maximum
		character.class_resources[key] = next_current
	return changed


func _sync_pact_slot_resources(character: PlayerCharacter, profile: Dictionary, maximums: Dictionary, refill_slots: bool) -> bool:
	var prefix: String = str(profile.get("slot_resource_prefix", "pact_slots"))
	var new_level: int = _progression.get_pact_slot_level(character.character_class_id, character.level)
	var new_maximum: int = maxi(int(maximums.get(str(new_level), maximums.get(new_level, 0))), 0)
	var old_maximum: int = 0
	var old_current: int = 0
	var changed: bool = false
	for level: int in range(1, 10):
		var key: String = "%s_%d" % [prefix, level]
		if character.class_resource_maximums.has(key) or character.class_resources.has(key):
			old_maximum = maxi(old_maximum, character.get_resource_maximum(key))
			old_current = maxi(old_current, character.get_resource(key))
			if level != new_level:
				character.class_resource_maximums.erase(key)
				character.class_resources.erase(key)
				changed = true
	var key: String = "%s_%d" % [prefix, maxi(new_level, 1)]
	var had_target: bool = character.class_resource_maximums.has(key)
	var spent: int = maxi(old_maximum - old_current, 0)
	var next_current: int = new_maximum if refill_slots or old_maximum <= 0 else clampi(new_maximum - spent, 0, new_maximum)
	if not had_target or character.get_resource_maximum(key) != new_maximum or character.get_resource(key) != next_current:
		changed = true
	character.class_resource_maximums[key] = new_maximum
	character.class_resources[key] = next_current
	character.class_resources["_pact_slot_level"] = new_level
	return changed


func _has_special_resource_contract(spell: Dictionary) -> bool:
	var resource_key: String = str(spell.get("resource_key", ""))
	return not resource_key.is_empty() and resource_key != "unlimited" and not resource_key.begins_with("spell_slots_")


func _available_special_resource_key(character: PlayerCharacter, spell: Dictionary) -> String:
	if not _has_special_resource_contract(spell):
		return ""
	var resource_key: String = str(spell.get("resource_key", ""))
	if character.get_resource(resource_key) > 0:
		return resource_key
	var fallback_key: String = str(spell.get("fallback_resource_key", ""))
	if fallback_key.is_empty():
		return ""
	var mapped: String = _mapped_resource_key(character, fallback_key)
	return mapped if character.get_resource(mapped) > 0 else ""


func _turn_slot_rule_blocked(character: PlayerCharacter, casting_context: Dictionary) -> bool:
	var turn_token: String = str(casting_context.get("turn_token", ""))
	return not turn_token.is_empty() and str(character.class_resources.get("_slot_spell_turn_token", "")) == turn_token


func _mark_slot_expended(character: PlayerCharacter, casting_context: Dictionary) -> void:
	var turn_token: String = str(casting_context.get("turn_token", ""))
	if not turn_token.is_empty():
		character.class_resources["_slot_spell_turn_token"] = turn_token


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
