class_name SpellSelectionSystem
extends RefCounted

const RULES_PATH: String = "res://data/rules/spell_selection.json"
const ABILITIES_PATH: String = "res://data/abilities/abilities.json"
const CLASSES_PATH: String = "res://data/classes/classes.json"

const SOURCE_CLASS: String = "class"
const SOURCE_MAGIC_INITIATE: String = "magic_initiate"
const CANTRIP_IDS_KEY: String = "cantrip_ids"
const SPELL_IDS_KEY: String = "spell_ids"
const PREPARED_IDS_KEY: String = "prepared_ids"
const ALWAYS_KNOWN_IDS_KEY: String = "always_known_ids"
const ALWAYS_PREPARED_IDS_KEY: String = "always_prepared_ids"
const SELECTION_VERSION: int = 1
const VALID_ABILITY_IDS: Array[String] = [
	"strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"
]

var _rules: Dictionary = {}
var _abilities: Dictionary = {}
var _classes: Dictionary = {}


func _init() -> void:
	_rules = _load_json(RULES_PATH)
	_abilities = _load_json(ABILITIES_PATH)
	var classes_root: Dictionary = _load_json(CLASSES_PATH)
	var classes_value: Variant = classes_root.get("classes", [])
	if classes_value is Array:
		for class_value: Variant in classes_value:
			if class_value is Dictionary:
				var class_data: Dictionary = class_value as Dictionary
				var class_id: String = str(class_data.get("id", ""))
				if not class_id.is_empty():
					_classes[class_id] = class_data.duplicate(true)


func get_class_profile(class_id: String) -> Dictionary:
	var profiles_value: Variant = _rules.get("class_profiles", {})
	if not profiles_value is Dictionary:
		return {}
	var value: Variant = (profiles_value as Dictionary).get(class_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func get_magic_initiate_profile(origin_feat_id: String) -> Dictionary:
	var profiles_value: Variant = _rules.get("magic_initiate_profiles", {})
	if not profiles_value is Dictionary:
		return {}
	var value: Variant = (profiles_value as Dictionary).get(origin_feat_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func has_class_choices(class_id: String) -> bool:
	return not get_class_profile(class_id).is_empty()


func has_magic_initiate_choices(origin_feat_id: String) -> bool:
	return not get_magic_initiate_profile(origin_feat_id).is_empty()


func get_spell_name(spell_id: String) -> String:
	var value: Variant = _abilities.get(spell_id, {})
	if value is Dictionary:
		return str((value as Dictionary).get("name", spell_id))
	return spell_id


func create_default_sources(class_id: String, origin_feat_id: String) -> Dictionary:
	var sources: Dictionary = {}
	var class_profile: Dictionary = get_class_profile(class_id)
	if not class_profile.is_empty():
		sources[SOURCE_CLASS] = _default_class_source(class_id, class_profile)
	var feat_profile: Dictionary = get_magic_initiate_profile(origin_feat_id)
	if not feat_profile.is_empty():
		sources[SOURCE_MAGIC_INITIATE] = _default_magic_initiate_source(origin_feat_id, feat_profile)
	return sources


func reconcile_sources(class_id: String, origin_feat_id: String, current_sources: Dictionary) -> Dictionary:
	var defaults: Dictionary = create_default_sources(class_id, origin_feat_id)
	var result: Dictionary = {}
	var default_class: Dictionary = _dictionary(defaults.get(SOURCE_CLASS, {}))
	var current_class: Dictionary = _dictionary(current_sources.get(SOURCE_CLASS, {}))
	if not default_class.is_empty():
		result[SOURCE_CLASS] = (
			_normalize_class_source(class_id, current_class, get_class_profile(class_id))
			if _source_owner_matches(current_class, class_id)
			else default_class
		)
	var default_feat: Dictionary = _dictionary(defaults.get(SOURCE_MAGIC_INITIATE, {}))
	var current_feat: Dictionary = _dictionary(current_sources.get(SOURCE_MAGIC_INITIATE, {}))
	if not default_feat.is_empty():
		result[SOURCE_MAGIC_INITIATE] = (
			_normalize_magic_initiate_source(origin_feat_id, current_feat, get_magic_initiate_profile(origin_feat_id))
			if _source_owner_matches(current_feat, origin_feat_id)
			else default_feat
		)
	return result


func validate_sources(class_id: String, origin_feat_id: String, sources: Dictionary) -> Dictionary:
	var messages: Array[String] = []
	var class_profile: Dictionary = get_class_profile(class_id)
	var class_source: Dictionary = _dictionary(sources.get(SOURCE_CLASS, {}))
	if class_profile.is_empty():
		if not class_source.is_empty():
			messages.append("У класса без магии найден лишний источник заклинаний.")
	elif class_source.is_empty():
		messages.append("Не выбран набор заклинаний класса.")
	else:
		_validate_source(
			class_source,
			class_id,
			_string_array(class_profile.get("cantrip_options", [])),
			maxi(int(class_profile.get("cantrip_choice_count", 0)), 0),
			_string_array(class_profile.get("spell_options", [])),
			maxi(int(class_profile.get("spell_choice_count", 0)), 0),
			maxi(int(class_profile.get("prepared_choice_count", 0)), 0),
			[],
			messages
		)
	var feat_profile: Dictionary = get_magic_initiate_profile(origin_feat_id)
	var feat_source: Dictionary = _dictionary(sources.get(SOURCE_MAGIC_INITIATE, {}))
	if feat_profile.is_empty():
		if not feat_source.is_empty():
			messages.append("Найден лишний источник Magic Initiate.")
	elif feat_source.is_empty():
		messages.append("Не выбран набор Magic Initiate.")
	else:
		_validate_source(
			feat_source,
			origin_feat_id,
			_string_array(feat_profile.get("cantrip_options", [])),
			maxi(int(feat_profile.get("cantrip_choice_count", 0)), 0),
			_string_array(feat_profile.get("spell_options", [])),
			maxi(int(feat_profile.get("spell_choice_count", 0)), 0),
			maxi(int(feat_profile.get("spell_choice_count", 0)), 0),
			_string_array(feat_profile.get("ability_options", [])),
			messages
		)
	if messages.is_empty():
		return {"success": true, "message": "Выбор заклинаний завершён."}
	return {"success": false, "message": "\n".join(messages)}


func apply_sources(character: PlayerCharacter, sources: Dictionary) -> Dictionary:
	if character == null:
		return {"success": false, "message": "Персонаж не определён."}
	var validation: Dictionary = validate_sources(character.character_class_id, character.origin_feat_id, sources)
	if not bool(validation.get("success", false)):
		return validation
	var previous_ids: Array[String] = get_all_spell_ids(character)
	var normalized: Dictionary = reconcile_sources(character.character_class_id, character.origin_feat_id, sources)
	character.spell_sources = normalized.duplicate(true)
	var current_ids: Array[String] = get_all_spell_ids(character)
	for spell_id: String in previous_ids:
		if spell_id not in current_ids:
			character.known_features.erase(spell_id)
	sync_known_spells(character)
	return {"success": true, "message": "Источники заклинаний сохранены."}


func ensure_character(character: PlayerCharacter) -> bool:
	if character == null:
		return false
	var before: Dictionary = character.spell_sources.duplicate(true)
	var sources: Dictionary = before.duplicate(true)
	var class_profile: Dictionary = get_class_profile(character.character_class_id)
	if class_profile.is_empty():
		sources.erase(SOURCE_CLASS)
	else:
		var class_source: Dictionary = _dictionary(sources.get(SOURCE_CLASS, {}))
		if not _source_owner_matches(class_source, character.character_class_id):
			sources[SOURCE_CLASS] = _legacy_class_source(character, character.character_class_id, class_profile)
		else:
			sources[SOURCE_CLASS] = _normalize_class_source(character.character_class_id, class_source, class_profile)
	var feat_profile: Dictionary = get_magic_initiate_profile(character.origin_feat_id)
	if feat_profile.is_empty():
		sources.erase(SOURCE_MAGIC_INITIATE)
	else:
		var feat_source: Dictionary = _dictionary(sources.get(SOURCE_MAGIC_INITIATE, {}))
		if not _source_owner_matches(feat_source, character.origin_feat_id):
			sources[SOURCE_MAGIC_INITIATE] = _legacy_magic_initiate_source(character.origin_feat_id, feat_profile)
		else:
			sources[SOURCE_MAGIC_INITIATE] = _normalize_magic_initiate_source(character.origin_feat_id, feat_source, feat_profile)
	character.spell_sources = sources
	var changed: bool = before != sources
	return sync_known_spells(character) or changed


func ensure_magic_initiate_source(character: PlayerCharacter) -> bool:
	if character == null:
		return false
	var profile: Dictionary = get_magic_initiate_profile(character.origin_feat_id)
	if profile.is_empty():
		return false
	var current: Dictionary = _dictionary(character.spell_sources.get(SOURCE_MAGIC_INITIATE, {}))
	if _source_owner_matches(current, character.origin_feat_id):
		var normalized: Dictionary = _normalize_magic_initiate_source(character.origin_feat_id, current, profile)
		var changed_existing: bool = normalized != current
		character.spell_sources[SOURCE_MAGIC_INITIATE] = normalized
		return sync_known_spells(character) or changed_existing
	character.spell_sources[SOURCE_MAGIC_INITIATE] = _legacy_magic_initiate_source(character.origin_feat_id, profile)
	sync_known_spells(character)
	return true


func sync_known_spells(character: PlayerCharacter) -> bool:
	if character == null:
		return false
	var changed: bool = false
	for source_id: String in [SOURCE_CLASS, SOURCE_MAGIC_INITIATE]:
		var source: Dictionary = get_source(character, source_id)
		for spell_id: String in get_source_spell_ids(source):
			if spell_id not in character.known_features:
				character.known_features.append(spell_id)
				changed = true
	return changed


func get_source(character: PlayerCharacter, source_id: String) -> Dictionary:
	if character == null:
		return {}
	var value: Variant = character.spell_sources.get(source_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func get_source_spell_ids(source: Dictionary) -> Array[String]:
	var result: Array[String] = []
	for key: String in [CANTRIP_IDS_KEY, SPELL_IDS_KEY, ALWAYS_KNOWN_IDS_KEY]:
		for spell_id: String in _string_array(source.get(key, [])):
			if not spell_id.is_empty() and spell_id not in result:
				result.append(spell_id)
	return result


func get_all_spell_ids(character: PlayerCharacter) -> Array[String]:
	var result: Array[String] = []
	if character == null:
		return result
	for source_id: String in [SOURCE_CLASS, SOURCE_MAGIC_INITIATE]:
		for spell_id: String in get_source_spell_ids(get_source(character, source_id)):
			if spell_id not in result:
				result.append(spell_id)
	return result


func get_source_ids_for_spell(character: PlayerCharacter, spell_id: String) -> Array[String]:
	var result: Array[String] = []
	if character == null or spell_id.is_empty():
		return result
	for source_id: String in [SOURCE_CLASS, SOURCE_MAGIC_INITIATE]:
		if spell_id in get_source_spell_ids(get_source(character, source_id)):
			result.append(source_id)
	return result


func resolve_source_id(character: PlayerCharacter, spell_id: String, requested_source_id: String = "") -> String:
	var source_ids: Array[String] = get_source_ids_for_spell(character, spell_id)
	if requested_source_id in source_ids:
		return requested_source_id
	if source_ids.size() == 1:
		return source_ids[0]
	if SOURCE_MAGIC_INITIATE in source_ids:
		var feat_contract: Dictionary = get_resource_contract(character, spell_id, SOURCE_MAGIC_INITIATE)
		var feat_resource: String = str(feat_contract.get("resource_key", ""))
		if not feat_resource.is_empty() and character.get_resource(feat_resource) > 0:
			return SOURCE_MAGIC_INITIATE
	if SOURCE_CLASS in source_ids:
		return SOURCE_CLASS
	return source_ids[0] if not source_ids.is_empty() else ""


func get_spellcasting_ability(character: PlayerCharacter, spell_id: String, requested_source_id: String = "") -> String:
	var source_id: String = resolve_source_id(character, spell_id, requested_source_id)
	if source_id.is_empty():
		return ""
	return str(get_source(character, source_id).get("ability_id", ""))


func get_initial_prepared_spell_ids(character: PlayerCharacter) -> Array[String]:
	var result: Array[String] = []
	if character == null:
		return result
	for source_id: String in [SOURCE_CLASS, SOURCE_MAGIC_INITIATE]:
		var source: Dictionary = get_source(character, source_id)
		for key: String in [PREPARED_IDS_KEY, ALWAYS_PREPARED_IDS_KEY]:
			for spell_id: String in _string_array(source.get(key, [])):
				if not spell_id.is_empty() and spell_id not in result:
					result.append(spell_id)
	return result


func is_source_always_prepared(character: PlayerCharacter, spell_id: String) -> bool:
	if character == null:
		return false
	for source_id: String in get_source_ids_for_spell(character, spell_id):
		if spell_id in _string_array(get_source(character, source_id).get(ALWAYS_PREPARED_IDS_KEY, [])):
			return true
	return false


func get_resource_contract(character: PlayerCharacter, spell_id: String, requested_source_id: String = "") -> Dictionary:
	if character == null:
		return {}
	var source_id: String = resolve_source_id(character, spell_id, requested_source_id)
	if source_id.is_empty():
		return {}
	var source: Dictionary = get_source(character, source_id)
	var resource_key: String = str(source.get("resource_key", ""))
	if resource_key.is_empty() or spell_id not in _string_array(source.get(SPELL_IDS_KEY, [])):
		return {}
	return {
		"source_id": source_id,
		"resource_key": resource_key,
		"fallback_resource_key": str(source.get("fallback_resource_key", ""))
	}


func get_selection_summary(sources: Dictionary) -> Array[String]:
	var result: Array[String] = []
	for source_id: String in [SOURCE_CLASS, SOURCE_MAGIC_INITIATE]:
		var source: Dictionary = _dictionary(sources.get(source_id, {}))
		if source.is_empty():
			continue
		var names: Array[String] = []
		for spell_id: String in get_source_spell_ids(source):
			names.append(get_spell_name(spell_id))
		var prefix: String = "Класс" if source_id == SOURCE_CLASS else "Magic Initiate"
		result.append("%s: %s" % [prefix, ", ".join(names)])
	return result


func _default_class_source(class_id: String, profile: Dictionary) -> Dictionary:
	var spells: Array[String] = _default_choices(
		_string_array(profile.get("recommended_spells", [])),
		_string_array(profile.get("spell_options", [])),
		maxi(int(profile.get("spell_choice_count", 0)), 0)
	)
	var prepared_count: int = maxi(int(profile.get("prepared_choice_count", 0)), 0)
	var prepared: Array[String] = _default_choices(
		_string_array(profile.get("recommended_prepared", profile.get("recommended_spells", []))),
		spells,
		prepared_count
	)
	return {
		"selection_version": SELECTION_VERSION,
		"source_id": SOURCE_CLASS,
		"owner_id": class_id,
		"list_id": class_id,
		"ability_id": str(profile.get("ability_id", "")),
		CANTRIP_IDS_KEY: _default_choices(
			_string_array(profile.get("recommended_cantrips", [])),
			_string_array(profile.get("cantrip_options", [])),
			maxi(int(profile.get("cantrip_choice_count", 0)), 0)
		),
		SPELL_IDS_KEY: spells,
		PREPARED_IDS_KEY: prepared,
		ALWAYS_KNOWN_IDS_KEY: _unique_string_array(profile.get("always_known_ids", [])),
		ALWAYS_PREPARED_IDS_KEY: _unique_string_array(profile.get("always_prepared_ids", [])),
		"resource_key": "",
		"fallback_resource_key": ""
	}


func _default_magic_initiate_source(origin_feat_id: String, profile: Dictionary) -> Dictionary:
	var spells: Array[String] = _default_choices(
		_string_array(profile.get("recommended_spells", [])),
		_string_array(profile.get("spell_options", [])),
		maxi(int(profile.get("spell_choice_count", 0)), 0)
	)
	return {
		"selection_version": SELECTION_VERSION,
		"source_id": SOURCE_MAGIC_INITIATE,
		"owner_id": origin_feat_id,
		"list_id": str(profile.get("list_id", "")),
		"ability_id": str(profile.get("default_ability_id", "wisdom")),
		CANTRIP_IDS_KEY: _default_choices(
			_string_array(profile.get("recommended_cantrips", [])),
			_string_array(profile.get("cantrip_options", [])),
			maxi(int(profile.get("cantrip_choice_count", 0)), 0)
		),
		SPELL_IDS_KEY: spells,
		PREPARED_IDS_KEY: spells.duplicate(),
		ALWAYS_KNOWN_IDS_KEY: [],
		ALWAYS_PREPARED_IDS_KEY: spells.duplicate(),
		"resource_key": str(profile.get("resource_key", "")),
		"fallback_resource_key": str(profile.get("fallback_resource_key", ""))
	}


func _legacy_class_source(character: PlayerCharacter, class_id: String, profile: Dictionary) -> Dictionary:
	var source: Dictionary = _default_class_source(class_id, profile)
	var class_data: Dictionary = _dictionary(_classes.get(class_id, {}))
	var spellcasting: Dictionary = _dictionary(class_data.get("spellcasting", {}))
	var cantrips: Array[String] = []
	var spells: Array[String] = []
	for spell_id: String in _string_array(spellcasting.get("starting_spells", [])):
		if _spell_level(spell_id) <= 0:
			_append_unique(cantrips, spell_id)
		else:
			_append_unique(spells, spell_id)
	for spell_id: String in _string_array(profile.get("legacy_cantrip_ids", [])):
		_append_unique(cantrips, spell_id)
	var prepared: Array[String] = []
	if character.class_resources.has("_prepared_spell_ids"):
		prepared = _unique_string_array(character.class_resources.get("_prepared_spell_ids", []))
	else:
		prepared = _unique_string_array(spellcasting.get("starting_prepared", []))
	source[CANTRIP_IDS_KEY] = cantrips
	source[SPELL_IDS_KEY] = spells
	source[PREPARED_IDS_KEY] = prepared
	source["legacy"] = true
	return source


func _legacy_magic_initiate_source(origin_feat_id: String, profile: Dictionary) -> Dictionary:
	var source: Dictionary = _default_magic_initiate_source(origin_feat_id, profile)
	var legacy_spells: Array[String] = _unique_string_array(profile.get("legacy_spell_ids", []))
	source[CANTRIP_IDS_KEY] = _unique_string_array(profile.get("legacy_cantrip_ids", []))
	source[SPELL_IDS_KEY] = legacy_spells
	source[PREPARED_IDS_KEY] = legacy_spells.duplicate()
	source[ALWAYS_PREPARED_IDS_KEY] = legacy_spells.duplicate()
	source["legacy"] = true
	return source


func _normalize_class_source(class_id: String, source: Dictionary, profile: Dictionary) -> Dictionary:
	var normalized: Dictionary = source.duplicate(true)
	normalized["selection_version"] = maxi(int(source.get("selection_version", SELECTION_VERSION)), 1)
	normalized["source_id"] = SOURCE_CLASS
	normalized["owner_id"] = class_id
	normalized["list_id"] = class_id
	normalized["ability_id"] = str(profile.get("ability_id", ""))
	normalized[CANTRIP_IDS_KEY] = _valid_spell_ids(source.get(CANTRIP_IDS_KEY, []))
	normalized[SPELL_IDS_KEY] = _valid_spell_ids(source.get(SPELL_IDS_KEY, []))
	normalized[PREPARED_IDS_KEY] = _valid_spell_ids(source.get(PREPARED_IDS_KEY, []))
	normalized[ALWAYS_KNOWN_IDS_KEY] = _unique_string_array(profile.get("always_known_ids", []))
	normalized[ALWAYS_PREPARED_IDS_KEY] = _unique_string_array(profile.get("always_prepared_ids", []))
	normalized["resource_key"] = ""
	normalized["fallback_resource_key"] = ""
	return normalized


func _normalize_magic_initiate_source(origin_feat_id: String, source: Dictionary, profile: Dictionary) -> Dictionary:
	var normalized: Dictionary = source.duplicate(true)
	normalized["selection_version"] = maxi(int(source.get("selection_version", SELECTION_VERSION)), 1)
	normalized["source_id"] = SOURCE_MAGIC_INITIATE
	normalized["owner_id"] = origin_feat_id
	normalized["list_id"] = str(profile.get("list_id", ""))
	var ability_options: Array[String] = _string_array(profile.get("ability_options", []))
	var ability_id: String = str(source.get("ability_id", profile.get("default_ability_id", "wisdom")))
	normalized["ability_id"] = ability_id if ability_id in ability_options else str(profile.get("default_ability_id", "wisdom"))
	normalized[CANTRIP_IDS_KEY] = _valid_spell_ids(source.get(CANTRIP_IDS_KEY, []))
	normalized[SPELL_IDS_KEY] = _valid_spell_ids(source.get(SPELL_IDS_KEY, []))
	normalized[PREPARED_IDS_KEY] = _valid_spell_ids(source.get(SPELL_IDS_KEY, []))
	normalized[ALWAYS_KNOWN_IDS_KEY] = []
	normalized[ALWAYS_PREPARED_IDS_KEY] = _valid_spell_ids(source.get(SPELL_IDS_KEY, []))
	normalized["resource_key"] = str(profile.get("resource_key", ""))
	normalized["fallback_resource_key"] = str(profile.get("fallback_resource_key", ""))
	return normalized


func _validate_source(
	source: Dictionary,
	expected_owner_id: String,
	cantrip_options: Array[String],
	cantrip_count: int,
	spell_options: Array[String],
	spell_count: int,
	prepared_count: int,
	ability_options: Array[String],
	messages: Array[String]
) -> void:
	if not _source_owner_matches(source, expected_owner_id):
		messages.append("Источник заклинаний принадлежит другому классу или черте.")
		return
	var cantrips: Array[String] = _unique_string_array(source.get(CANTRIP_IDS_KEY, []))
	var spells: Array[String] = _unique_string_array(source.get(SPELL_IDS_KEY, []))
	var prepared: Array[String] = _unique_string_array(source.get(PREPARED_IDS_KEY, []))
	if cantrips.size() != cantrip_count:
		messages.append("Выберите заговоры: %d из %d." % [cantrips.size(), cantrip_count])
	if spells.size() != spell_count:
		messages.append("Выберите заклинания 1 уровня: %d из %d." % [spells.size(), spell_count])
	if prepared.size() != prepared_count:
		messages.append("Подготовьте заклинания: %d из %d." % [prepared.size(), prepared_count])
	for spell_id: String in cantrips:
		if spell_id not in cantrip_options:
			messages.append("Заговор «%s» отсутствует в выбранном списке." % get_spell_name(spell_id))
	for spell_id: String in spells:
		if spell_id not in spell_options:
			messages.append("Заклинание «%s» отсутствует в выбранном списке." % get_spell_name(spell_id))
	for spell_id: String in prepared:
		if spell_id not in spells:
			messages.append("Подготовлено не выбранное заклинание «%s»." % get_spell_name(spell_id))
	if not ability_options.is_empty() and str(source.get("ability_id", "")) not in ability_options:
		messages.append("Выберите Интеллект, Мудрость или Харизму для Magic Initiate.")


func _source_owner_matches(source: Dictionary, owner_id: String) -> bool:
	return not source.is_empty() and str(source.get("owner_id", "")) == owner_id


func _default_choices(recommended: Array[String], options: Array[String], count: int) -> Array[String]:
	var result: Array[String] = []
	for spell_id: String in recommended:
		if spell_id in options and spell_id not in result and result.size() < count:
			result.append(spell_id)
	for spell_id: String in options:
		if spell_id not in result and result.size() < count:
			result.append(spell_id)
	return result


func _valid_spell_ids(value: Variant) -> Array[String]:
	var result: Array[String] = []
	for spell_id: String in _string_array(value):
		if _spell_level(spell_id) >= 0 and spell_id not in result:
			result.append(spell_id)
	return result


func _spell_level(spell_id: String) -> int:
	var value: Variant = _abilities.get(spell_id, {})
	if not value is Dictionary or not bool((value as Dictionary).get("is_spell", false)):
		return -1
	return maxi(int((value as Dictionary).get("spell_level", 0)), 0)


func _load_json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		push_error("Файл выбора заклинаний не найден: %s" % path)
		return {}
	var file: FileAccess = FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_error("Не удалось открыть файл выбора заклинаний: %s" % path)
		return {}
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		push_error("Некорректный JSON выбора заклинаний: %s" % path)
		return {}
	return (parsed as Dictionary).duplicate(true)


static func _dictionary(value: Variant) -> Dictionary:
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


static func _string_array(value: Variant) -> Array[String]:
	var result: Array[String] = []
	if value is Array:
		for item: Variant in value:
			result.append(str(item))
	return result


static func _unique_string_array(value: Variant) -> Array[String]:
	var result: Array[String] = []
	for item: String in _string_array(value):
		if not item.is_empty() and item not in result:
			result.append(item)
	return result


static func _append_unique(values: Array[String], value: String) -> void:
	if not value.is_empty() and value not in values:
		values.append(value)
