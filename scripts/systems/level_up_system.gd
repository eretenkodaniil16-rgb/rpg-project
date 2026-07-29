class_name LevelUpSystem
extends RefCounted

const TRANSACTION_FLAG: String = "_level_up_transaction_v2"
const MIGRATION_FLAG: String = "_level_up_progression_migrated_v2"
const LAST_RESULT_FLAG: String = "_last_level_up_result_v2"
const TRANSACTION_VERSION: int = 2

const HP_MODE_FIXED: String = "fixed"
const HP_MODE_ROLL: String = "roll"

const CLASS_SOURCE_ID: String = SpellSelectionSystem.SOURCE_CLASS
const MAGIC_INITIATE_SOURCE_ID: String = SpellSelectionSystem.SOURCE_MAGIC_INITIATE
const NEW_CLASS_SPELL_CLASSES: Array[String] = [
	"bard", "cleric", "druid", "paladin", "ranger", "sorcerer", "warlock", "wizard"
]
const CLASS_SPELL_REPLACEMENT_CLASSES: Array[String] = [
	"bard", "ranger", "sorcerer", "warlock"
]
const AUTO_PREPARED_NEW_SPELL_CLASSES: Array[String] = [
	"bard", "cleric", "druid", "paladin", "ranger", "sorcerer", "warlock"
]

var _class_data: ClassDataSystem = ClassDataSystem.new()
var _spell_selection: SpellSelectionSystem = SpellSelectionSystem.new()
var _spellcasting: SpellcastingSystem = SpellcastingSystem.new()
var _race_data: RaceDataSystem = RaceDataSystem.new()


func ensure_migrated(character: PlayerCharacter, state: Node) -> bool:
	if character == null or state == null:
		return false
	var changed: bool = false
	var minimum_experience: int = ProgressionSystem.total_experience_for_level(character.level)
	if character.experience < minimum_experience:
		character.experience = minimum_experience
		changed = true
	var transaction: Dictionary = get_transaction(state)
	if not transaction.is_empty() and not _is_transaction_current(character, transaction):
		_state_set(state, TRANSACTION_FLAG, {})
		changed = true
	if not bool(_state_get(state, MIGRATION_FLAG, false)):
		_state_set(state, MIGRATION_FLAG, true)
		changed = true
	if _spellcasting.ensure_character(character, false):
		changed = true
	if changed:
		_save(state)
	return changed


func can_begin(character: PlayerCharacter) -> bool:
	return ProgressionSystem.can_level_up(character)


func has_pending_transaction(character: PlayerCharacter, state: Node) -> bool:
	if character == null or state == null:
		return false
	var transaction: Dictionary = get_transaction(state)
	return not transaction.is_empty() and _is_transaction_current(character, transaction)


func begin_transaction(character: PlayerCharacter, state: Node) -> Dictionary:
	if character == null or state == null:
		return _failure("Персонаж или состояние игры недоступны.")
	ensure_migrated(character, state)
	var existing: Dictionary = get_transaction(state)
	if not existing.is_empty() and _is_transaction_current(character, existing):
		return _success("Незавершённое повышение восстановлено.", existing)
	if not ProgressionSystem.can_level_up(character):
		return _failure("Недостаточно опыта для следующего уровня.")
	var target_level: int = character.level + 1
	var transaction: Dictionary = {
		"version": TRANSACTION_VERSION,
		"class_id": character.character_class_id,
		"from_level": character.level,
		"target_level": target_level,
		"experience_snapshot": character.experience,
		"hp_mode": "",
		"hp_roll": 0,
		"hp_gain": 0,
		"new_class_spell_id": "",
		"replace_class_spell_old_id": "",
		"replace_class_spell_new_id": "",
		"replace_magic_cantrip_old_id": "",
		"replace_magic_cantrip_new_id": "",
		"replace_magic_spell_old_id": "",
		"replace_magic_spell_new_id": ""
	}
	_store_transaction(state, transaction)
	return _success("Повышение уровня начато.", transaction)


func get_transaction(state: Node) -> Dictionary:
	if state == null:
		return {}
	var value: Variant = _state_get(state, TRANSACTION_FLAG, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func get_fixed_hp_gain(character: PlayerCharacter) -> int:
	if character == null:
		return 1
	var fixed_die_value: int = floori(float(maxi(character.hit_die_size, 2)) / 2.0) + 1
	return _final_hp_gain(character, fixed_die_value)


func choose_fixed_hp(character: PlayerCharacter, state: Node) -> Dictionary:
	var transaction_result: Dictionary = begin_transaction(character, state)
	if not bool(transaction_result.get("success", false)):
		return transaction_result
	var transaction: Dictionary = transaction_result.get("transaction", {}) as Dictionary
	transaction["hp_mode"] = HP_MODE_FIXED
	transaction["hp_gain"] = get_fixed_hp_gain(character)
	_store_transaction(state, transaction)
	return _success("Выбран фиксированный прирост здоровья.", transaction)


func roll_hp_once(character: PlayerCharacter, state: Node, roll_override: int = -1) -> Dictionary:
	var transaction_result: Dictionary = begin_transaction(character, state)
	if not bool(transaction_result.get("success", false)):
		return transaction_result
	var transaction: Dictionary = transaction_result.get("transaction", {}) as Dictionary
	var stored_roll: int = maxi(int(transaction.get("hp_roll", 0)), 0)
	if stored_roll <= 0:
		var die_size: int = maxi(character.hit_die_size, 2)
		stored_roll = clampi(roll_override, 1, die_size) if roll_override > 0 else randi_range(1, die_size)
		transaction["hp_roll"] = stored_roll
	transaction["hp_mode"] = HP_MODE_ROLL
	transaction["hp_gain"] = _final_hp_gain(character, stored_roll)
	_store_transaction(state, transaction)
	return _success("Бросок Кости Хитов сохранён и не может быть повторён.", transaction)


func set_new_class_spell(character: PlayerCharacter, state: Node, spell_id: String) -> Dictionary:
	return _set_choice(character, state, "new_class_spell_id", spell_id)


func set_class_spell_replacement(
	character: PlayerCharacter,
	state: Node,
	old_spell_id: String,
	new_spell_id: String
) -> Dictionary:
	var result: Dictionary = _set_choice(character, state, "replace_class_spell_old_id", old_spell_id)
	if not bool(result.get("success", false)):
		return result
	return _set_choice(character, state, "replace_class_spell_new_id", new_spell_id)


func set_magic_initiate_cantrip_replacement(
	character: PlayerCharacter,
	state: Node,
	old_spell_id: String,
	new_spell_id: String
) -> Dictionary:
	var result: Dictionary = _set_choice(character, state, "replace_magic_cantrip_old_id", old_spell_id)
	if not bool(result.get("success", false)):
		return result
	return _set_choice(character, state, "replace_magic_cantrip_new_id", new_spell_id)


func set_magic_initiate_spell_replacement(
	character: PlayerCharacter,
	state: Node,
	old_spell_id: String,
	new_spell_id: String
) -> Dictionary:
	var result: Dictionary = _set_choice(character, state, "replace_magic_spell_old_id", old_spell_id)
	if not bool(result.get("success", false)):
		return result
	return _set_choice(character, state, "replace_magic_spell_new_id", new_spell_id)


func get_level_features(character: PlayerCharacter, target_level: int = 0) -> Array[String]:
	var result: Array[String] = []
	if character == null:
		return result
	var level_value: int = target_level if target_level > 0 else character.level + 1
	var class_definition: Dictionary = _class_data.get_class_definition(character.character_class_id)
	var level_features_value: Variant = class_definition.get("level_features", {})
	if not level_features_value is Dictionary:
		return result
	for feature_id: String in _string_array((level_features_value as Dictionary).get(str(level_value), [])):
		if not feature_id.is_empty() and feature_id not in result:
			result.append(feature_id)
	return result


func get_new_class_spell_candidates(character: PlayerCharacter) -> Array[String]:
	if character == null or character.character_class_id not in NEW_CLASS_SPELL_CLASSES:
		return []
	var profile: Dictionary = _spell_selection.get_class_profile(character.character_class_id)
	var source: Dictionary = _spell_selection.get_source(character, CLASS_SOURCE_ID)
	var current: Array[String] = _string_array(source.get(SpellSelectionSystem.SPELL_IDS_KEY, []))
	return _available_options(profile.get("spell_options", []), current)


func get_class_spell_replacement_old_candidates(character: PlayerCharacter) -> Array[String]:
	if character == null or character.character_class_id not in CLASS_SPELL_REPLACEMENT_CLASSES:
		return []
	var source: Dictionary = _spell_selection.get_source(character, CLASS_SOURCE_ID)
	return _string_array(source.get(SpellSelectionSystem.SPELL_IDS_KEY, []))


func get_class_spell_replacement_new_candidates(character: PlayerCharacter) -> Array[String]:
	if character == null or character.character_class_id not in CLASS_SPELL_REPLACEMENT_CLASSES:
		return []
	return get_new_class_spell_candidates(character)


func get_magic_initiate_cantrip_old_candidates(character: PlayerCharacter) -> Array[String]:
	if character == null:
		return []
	var source: Dictionary = _spell_selection.get_source(character, MAGIC_INITIATE_SOURCE_ID)
	return _string_array(source.get(SpellSelectionSystem.CANTRIP_IDS_KEY, []))


func get_magic_initiate_cantrip_new_candidates(character: PlayerCharacter) -> Array[String]:
	if character == null:
		return []
	var profile: Dictionary = _spell_selection.get_magic_initiate_profile(character.origin_feat_id)
	var source: Dictionary = _spell_selection.get_source(character, MAGIC_INITIATE_SOURCE_ID)
	var current: Array[String] = _string_array(source.get(SpellSelectionSystem.CANTRIP_IDS_KEY, []))
	return _available_options(profile.get("cantrip_options", []), current)


func get_magic_initiate_spell_old_candidates(character: PlayerCharacter) -> Array[String]:
	if character == null:
		return []
	var source: Dictionary = _spell_selection.get_source(character, MAGIC_INITIATE_SOURCE_ID)
	return _string_array(source.get(SpellSelectionSystem.SPELL_IDS_KEY, []))


func get_magic_initiate_spell_new_candidates(character: PlayerCharacter) -> Array[String]:
	if character == null:
		return []
	var profile: Dictionary = _spell_selection.get_magic_initiate_profile(character.origin_feat_id)
	var source: Dictionary = _spell_selection.get_source(character, MAGIC_INITIATE_SOURCE_ID)
	var current: Array[String] = _string_array(source.get(SpellSelectionSystem.SPELL_IDS_KEY, []))
	return _available_options(profile.get("spell_options", []), current)


func describe_feature(feature_id: String) -> String:
	var feature: Dictionary = _class_data.get_ability_definition(feature_id)
	if feature.is_empty():
		return feature_id
	return "%s — %s" % [
		str(feature.get("name", feature_id)),
		str(feature.get("description", ""))
	]


func spell_name(spell_id: String) -> String:
	return _spell_selection.get_spell_name(spell_id)


func validate_transaction(character: PlayerCharacter, state: Node) -> Dictionary:
	if character == null or state == null:
		return _failure("Персонаж или состояние игры недоступны.")
	var transaction: Dictionary = get_transaction(state)
	if transaction.is_empty() or not _is_transaction_current(character, transaction):
		return _failure("Незавершённое повышение не найдено.")
	if not ProgressionSystem.can_level_up(character):
		return _failure("Опыт больше не позволяет повысить уровень.")
	var hp_mode: String = str(transaction.get("hp_mode", ""))
	if hp_mode not in [HP_MODE_FIXED, HP_MODE_ROLL] or int(transaction.get("hp_gain", 0)) <= 0:
		return _failure("Выберите фиксированное здоровье или выполните один бросок Кости Хитов.")
	if hp_mode == HP_MODE_ROLL and int(transaction.get("hp_roll", 0)) <= 0:
		return _failure("Результат броска здоровья отсутствует.")
	var validation_error: String = _validate_spell_choices(character, transaction)
	if not validation_error.is_empty():
		return _failure(validation_error)
	return _success("Повышение готово к подтверждению.", transaction)


func commit_transaction(character: PlayerCharacter, state: Node) -> Dictionary:
	var validation: Dictionary = validate_transaction(character, state)
	if not bool(validation.get("success", false)):
		return validation
	var transaction: Dictionary = validation.get("transaction", {}) as Dictionary
	var target_level: int = int(transaction.get("target_level", character.level + 1))
	var hp_gain: int = maxi(int(transaction.get("hp_gain", 0)), 1)

	var next_features: Array[String] = _string_array(character.known_features)
	for feature_id: String in get_level_features(character, target_level):
		_append_unique(next_features, feature_id)

	var next_sources: Dictionary = character.spell_sources.duplicate(true)
	_apply_spell_choices(character, transaction, next_sources)

	character.level = target_level
	character.maximum_health += hp_gain
	character.current_health = mini(character.current_health + hp_gain, character.maximum_health)
	var racial_hp_gain: int = _racial_hp_gain(character)
	character.applied_racial_hit_point_bonus += racial_hp_gain
	character.hit_dice_maximum = maxi(character.level, 1)
	character.hit_dice_current = clampi(
		character.hit_dice_current + 1,
		0,
		character.hit_dice_maximum
	)
	character.known_features = next_features
	character.spell_sources = next_sources
	_sync_known_spell_membership(character, transaction)
	_synchronize_feature_resources(character)
	_spell_selection.sync_known_spells(character)
	_spellcasting.ensure_character(character, false)
	_race_data.ensure_character_race(character)

	var result: Dictionary = {
		"success": true,
		"from_level": target_level - 1,
		"level": target_level,
		"hp_gain": hp_gain,
		"maximum_health": character.maximum_health,
		"features": get_level_features(character, target_level),
		"remaining_level_ups": ProgressionSystem.pending_level_count(character)
	}
	_state_set(state, TRANSACTION_FLAG, {})
	_state_set(state, LAST_RESULT_FLAG, result.duplicate(true))
	_save(state)
	return result


func cancel_transaction(state: Node) -> void:
	if state == null:
		return
	_state_set(state, TRANSACTION_FLAG, {})
	_save(state)


func _set_choice(
	character: PlayerCharacter,
	state: Node,
	key: String,
	value: String
) -> Dictionary:
	var transaction_result: Dictionary = begin_transaction(character, state)
	if not bool(transaction_result.get("success", false)):
		return transaction_result
	var transaction: Dictionary = transaction_result.get("transaction", {}) as Dictionary
	transaction[key] = value
	_store_transaction(state, transaction)
	return _success("Выбор сохранён.", transaction)


func _validate_spell_choices(character: PlayerCharacter, transaction: Dictionary) -> String:
	var new_class_spell_id: String = str(transaction.get("new_class_spell_id", ""))
	if not new_class_spell_id.is_empty() and new_class_spell_id not in get_new_class_spell_candidates(character):
		return "Новое классовое заклинание недоступно."

	var replace_class_old: String = str(transaction.get("replace_class_spell_old_id", ""))
	var replace_class_new: String = str(transaction.get("replace_class_spell_new_id", ""))
	if replace_class_old.is_empty() != replace_class_new.is_empty():
		return "Для замены классового заклинания выберите старое и новое заклинание."
	if not replace_class_old.is_empty():
		if replace_class_old not in get_class_spell_replacement_old_candidates(character):
			return "Заменяемое классовое заклинание не найдено."
		if replace_class_new not in get_class_spell_replacement_new_candidates(character):
			return "Новое классовое заклинание для замены недоступно."
		if not new_class_spell_id.is_empty() and replace_class_new == new_class_spell_id:
			return "Новое и заменяющее классовые заклинания должны различаться."

	var magic_cantrip_old: String = str(transaction.get("replace_magic_cantrip_old_id", ""))
	var magic_cantrip_new: String = str(transaction.get("replace_magic_cantrip_new_id", ""))
	if magic_cantrip_old.is_empty() != magic_cantrip_new.is_empty():
		return "Для замены заговора Magic Initiate выберите старый и новый заговор."
	if not magic_cantrip_old.is_empty():
		if magic_cantrip_old not in get_magic_initiate_cantrip_old_candidates(character):
			return "Заменяемый заговор Magic Initiate не найден."
		if magic_cantrip_new not in get_magic_initiate_cantrip_new_candidates(character):
			return "Новый заговор Magic Initiate недоступен."

	var magic_spell_old: String = str(transaction.get("replace_magic_spell_old_id", ""))
	var magic_spell_new: String = str(transaction.get("replace_magic_spell_new_id", ""))
	if magic_spell_old.is_empty() != magic_spell_new.is_empty():
		return "Для замены заклинания Magic Initiate выберите старое и новое заклинание."
	if not magic_spell_old.is_empty():
		if magic_spell_old not in get_magic_initiate_spell_old_candidates(character):
			return "Заменяемое заклинание Magic Initiate не найдено."
		if magic_spell_new not in get_magic_initiate_spell_new_candidates(character):
			return "Новое заклинание Magic Initiate недоступно."
	if not magic_cantrip_old.is_empty() and not magic_spell_old.is_empty():
		return "При одном повышении можно заменить только одно заклинание черты «Посвящённый в магию»."
	return ""


func _apply_spell_choices(
	character: PlayerCharacter,
	transaction: Dictionary,
	sources: Dictionary
) -> void:
	var class_source: Dictionary = _dictionary(sources.get(CLASS_SOURCE_ID, {}))
	if not class_source.is_empty():
		var class_spells: Array[String] = _string_array(class_source.get(SpellSelectionSystem.SPELL_IDS_KEY, []))
		var class_prepared: Array[String] = _string_array(class_source.get(SpellSelectionSystem.PREPARED_IDS_KEY, []))
		var new_class_spell_id: String = str(transaction.get("new_class_spell_id", ""))
		if not new_class_spell_id.is_empty():
			_append_unique(class_spells, new_class_spell_id)
			if character.character_class_id in AUTO_PREPARED_NEW_SPELL_CLASSES:
				_append_unique(class_prepared, new_class_spell_id)
		var replace_class_old: String = str(transaction.get("replace_class_spell_old_id", ""))
		var replace_class_new: String = str(transaction.get("replace_class_spell_new_id", ""))
		if not replace_class_old.is_empty() and not replace_class_new.is_empty():
			var was_prepared: bool = replace_class_old in class_prepared
			class_spells.erase(replace_class_old)
			_append_unique(class_spells, replace_class_new)
			class_prepared.erase(replace_class_old)
			if was_prepared or character.character_class_id in AUTO_PREPARED_NEW_SPELL_CLASSES:
				_append_unique(class_prepared, replace_class_new)
		class_source[SpellSelectionSystem.SPELL_IDS_KEY] = class_spells
		class_source[SpellSelectionSystem.PREPARED_IDS_KEY] = class_prepared
		sources[CLASS_SOURCE_ID] = class_source

	var feat_source: Dictionary = _dictionary(sources.get(MAGIC_INITIATE_SOURCE_ID, {}))
	if feat_source.is_empty():
		return
	var feat_cantrips: Array[String] = _string_array(feat_source.get(SpellSelectionSystem.CANTRIP_IDS_KEY, []))
	var feat_spells: Array[String] = _string_array(feat_source.get(SpellSelectionSystem.SPELL_IDS_KEY, []))
	var feat_prepared: Array[String] = _string_array(feat_source.get(SpellSelectionSystem.PREPARED_IDS_KEY, []))
	var feat_always_prepared: Array[String] = _string_array(feat_source.get(SpellSelectionSystem.ALWAYS_PREPARED_IDS_KEY, []))
	var magic_cantrip_old: String = str(transaction.get("replace_magic_cantrip_old_id", ""))
	var magic_cantrip_new: String = str(transaction.get("replace_magic_cantrip_new_id", ""))
	if not magic_cantrip_old.is_empty() and not magic_cantrip_new.is_empty():
		feat_cantrips.erase(magic_cantrip_old)
		_append_unique(feat_cantrips, magic_cantrip_new)
	var magic_spell_old: String = str(transaction.get("replace_magic_spell_old_id", ""))
	var magic_spell_new: String = str(transaction.get("replace_magic_spell_new_id", ""))
	if not magic_spell_old.is_empty() and not magic_spell_new.is_empty():
		feat_spells.erase(magic_spell_old)
		feat_prepared.erase(magic_spell_old)
		feat_always_prepared.erase(magic_spell_old)
		_append_unique(feat_spells, magic_spell_new)
		_append_unique(feat_prepared, magic_spell_new)
		_append_unique(feat_always_prepared, magic_spell_new)
	feat_source[SpellSelectionSystem.CANTRIP_IDS_KEY] = feat_cantrips
	feat_source[SpellSelectionSystem.SPELL_IDS_KEY] = feat_spells
	feat_source[SpellSelectionSystem.PREPARED_IDS_KEY] = feat_prepared
	feat_source[SpellSelectionSystem.ALWAYS_PREPARED_IDS_KEY] = feat_always_prepared
	sources[MAGIC_INITIATE_SOURCE_ID] = feat_source


func _sync_known_spell_membership(character: PlayerCharacter, transaction: Dictionary) -> void:
	var current_spell_ids: Array[String] = _spell_selection.get_all_spell_ids(character)
	for key: String in [
		"replace_class_spell_old_id",
		"replace_magic_cantrip_old_id",
		"replace_magic_spell_old_id"
	]:
		var old_spell_id: String = str(transaction.get(key, ""))
		if old_spell_id.is_empty() or old_spell_id in current_spell_ids:
			continue
		var definition: Dictionary = _class_data.get_ability_definition(old_spell_id)
		if bool(definition.get("is_spell", false)):
			character.known_features.erase(old_spell_id)


func _synchronize_feature_resources(character: PlayerCharacter) -> void:
	for feature_id: String in character.known_features:
		var feature: Dictionary = _class_data.get_ability_definition(feature_id)
		if feature.is_empty() or bool(feature.get("is_spell", false)):
			continue
		var resource_key: String = str(feature.get("resource_key", ""))
		if resource_key.is_empty() or resource_key == "unlimited":
			continue
		var maximum: int = _resource_maximum(character, feature)
		if maximum <= 0:
			continue
		var had_resource: bool = character.class_resource_maximums.has(resource_key)
		var old_maximum: int = character.get_resource_maximum(resource_key)
		var spent: int = maxi(old_maximum - character.get_resource(resource_key), 0)
		var current: int = maximum if not had_resource else clampi(maximum - spent, 0, maximum)
		character.set_resource(resource_key, current, maximum)


func _resource_maximum(character: PlayerCharacter, feature: Dictionary) -> int:
	var maximum: int = maxi(int(feature.get("max_uses", 0)), 0)
	match str(feature.get("max_uses_formula", "")):
		"charisma_modifier_min_1":
			maximum = maxi(character.get_ability_modifier("charisma"), 1)
		"wisdom_modifier_min_1":
			maximum = maxi(character.get_ability_modifier("wisdom"), 1)
		"proficiency_bonus":
			maximum = character.get_proficiency_bonus()
		"level":
			maximum = character.level
		"half_level_round_up":
			maximum = ceili(float(character.level) / 2.0)
	return maxi(maximum, 0)


func _racial_hp_gain(character: PlayerCharacter) -> int:
	if character == null:
		return 0
	var race: Dictionary = _race_data.get_race(character.race_id)
	return maxi(int(race.get("hp_bonus_per_level", 0)), 0) if not race.is_empty() else 0


func _final_hp_gain(character: PlayerCharacter, die_value: int) -> int:
	return maxi(
		die_value + character.get_ability_modifier("constitution") + _racial_hp_gain(character),
		1
	)


func _available_options(options_value: Variant, current: Array[String]) -> Array[String]:
	var result: Array[String] = []
	for option_id: String in _string_array(options_value):
		if not option_id.is_empty() and option_id not in current and option_id not in result:
			result.append(option_id)
	return result


func _is_transaction_current(
	character: PlayerCharacter,
	transaction: Dictionary
) -> bool:
	return (
		int(transaction.get("version", 0)) == TRANSACTION_VERSION
		and str(transaction.get("class_id", "")) == character.character_class_id
		and int(transaction.get("from_level", 0)) == character.level
		and int(transaction.get("target_level", 0)) == character.level + 1
		and ProgressionSystem.can_level_up(character)
	)


func _store_transaction(state: Node, transaction: Dictionary) -> void:
	_state_set(state, TRANSACTION_FLAG, transaction.duplicate(true))
	_save(state)


func _state_get(state: Node, key: String, default_value: Variant) -> Variant:
	return state.call("get_flag", key, default_value) if state.has_method("get_flag") else default_value


func _state_set(state: Node, key: String, value: Variant) -> void:
	if state.has_method("set_flag"):
		state.call("set_flag", key, value)


func _save(state: Node) -> void:
	if state.has_method("save_game"):
		state.call("save_game")


func _success(message: String, transaction: Dictionary = {}) -> Dictionary:
	return {
		"success": true,
		"message": message,
		"transaction": transaction.duplicate(true)
	}


func _failure(message: String) -> Dictionary:
	return {
		"success": false,
		"message": message,
		"transaction": {}
	}


static func _dictionary(value: Variant) -> Dictionary:
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


static func _string_array(value: Variant) -> Array[String]:
	var result: Array[String] = []
	if value is Array:
		for item: Variant in value:
			result.append(str(item))
	return result


static func _append_unique(values: Array[String], value: String) -> void:
	if not value.is_empty() and value not in values:
		values.append(value)
