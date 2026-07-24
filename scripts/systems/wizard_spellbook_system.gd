class_name WizardSpellbookSystem
extends RefCounted

const ABILITIES_PATH: String = "res://data/abilities/abilities.json"
const CLASSES_PATH: String = "res://data/classes/classes.json"
const WIZARD_CLASS_ID: String = "wizard"
const SPELLBOOK_ITEM_ID: String = "spellbook"
const GOLD_ITEM_ID: String = "gold_coin"
const COPY_COST_GP_PER_LEVEL: int = 50
const COPY_MINUTES_PER_LEVEL: int = 120
const SCROLL_CHECK_BASE_DC: int = 10

var _abilities: Dictionary = {}
var _classes: Dictionary = {}
var _progression: SpellcastingProgressionSystem = SpellcastingProgressionSystem.new()
var _skill_checks: SkillCheckSystem = SkillCheckSystem.new()
var _world_time: WorldTimeSystem = WorldTimeSystem.new()


func _init() -> void:
	_abilities = _load_json_dictionary(ABILITIES_PATH)
	var classes_root: Dictionary = _load_json_dictionary(CLASSES_PATH)
	var classes_value: Variant = classes_root.get("classes", [])
	if classes_value is Array:
		for entry_value: Variant in classes_value:
			if entry_value is Dictionary:
				var entry: Dictionary = entry_value as Dictionary
				_classes[str(entry.get("id", ""))] = entry.duplicate(true)


func ensure_character(character: PlayerCharacter) -> bool:
	if character == null or character.character_class_id != WIZARD_CLASS_ID:
		return false
	var changed: bool = false
	if not character.spellbook_initialized:
		var candidates: Array[String] = []
		for spell_id: String in character.known_features:
			_append_unique(candidates, spell_id)
		var profile: Dictionary = _spellcasting_profile(WIZARD_CLASS_ID)
		for spell_id: String in _string_array(profile.get("starting_spells", [])):
			_append_unique(candidates, spell_id)
		var level_spells_value: Variant = profile.get("level_spells", {})
		if level_spells_value is Dictionary:
			for required_level_value: Variant in (level_spells_value as Dictionary).keys():
				if character.level < maxi(int(str(required_level_value)), 1):
					continue
				for spell_id: String in _string_array((level_spells_value as Dictionary).get(required_level_value, [])):
					_append_unique(candidates, spell_id)
		for spell_id: String in candidates:
			var spell: Dictionary = get_spell_definition(spell_id)
			if int(spell.get("spell_level", 0)) <= 0 or not is_wizard_spell(spell):
				continue
			changed = _append_unique(character.spellbook_spell_ids, spell_id) or changed
		character.spellbook_initialized = true
		changed = true
	for spell_id: String in character.spellbook_spell_ids.duplicate():
		var spell: Dictionary = get_spell_definition(spell_id)
		if spell.is_empty() or int(spell.get("spell_level", 0)) <= 0 or not is_wizard_spell(spell):
			character.spellbook_spell_ids.erase(spell_id)
			changed = true
			continue
		changed = _append_unique(character.known_features, spell_id) or changed
	return changed


func get_spellbook_spell_ids(character: PlayerCharacter) -> Array[String]:
	if character == null:
		return []
	return character.spellbook_spell_ids.duplicate()


func is_in_spellbook(character: PlayerCharacter, spell_id: String) -> bool:
	return character != null and spell_id in character.spellbook_spell_ids


func has_physical_spellbook(state: Node) -> bool:
	return state != null and state.has_method("has_item") and bool(state.call("has_item", SPELLBOOK_ITEM_ID))


func get_spell_definition(spell_id: String) -> Dictionary:
	var value: Variant = _abilities.get(spell_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary and bool((value as Dictionary).get("is_spell", false)) else {}


func is_wizard_spell(spell: Dictionary) -> bool:
	return "wizard" in _string_array(spell.get("spell_lists", []))


func get_maximum_spell_level(character: PlayerCharacter) -> int:
	if character == null:
		return 0
	var maximums: Dictionary = _progression.get_slot_maximums(character.character_class_id, character.level)
	var result: int = 0
	for level_value: Variant in maximums.keys():
		var level: int = maxi(int(str(level_value)), 0)
		if int(maximums.get(level_value, 0)) > 0:
			result = maxi(result, level)
	return result


func inspect_scroll(character: PlayerCharacter, scroll_item_id: String, state: Node) -> Dictionary:
	if character == null:
		return _failure("Персонаж не найден.")
	if character.character_class_id != WIZARD_CLASS_ID:
		return _failure("Только Волшебник может переписывать формулы в книгу заклинаний.")
	if not has_physical_spellbook(state):
		return _failure("Для переписывания нужна книга заклинаний в инвентаре.")
	if state == null or not state.has_method("has_item") or not bool(state.call("has_item", scroll_item_id)):
		return _failure("Свиток отсутствует в инвентаре.")
	var scroll: Dictionary = state.call("get_item_definition", scroll_item_id) as Dictionary
	if str(scroll.get("type", "")) != "spell_scroll":
		return _failure("Выбранный предмет не является свитком заклинания.")
	var spell_id: String = str(scroll.get("spell_id", ""))
	var spell: Dictionary = get_spell_definition(spell_id)
	if spell.is_empty():
		return _failure("Формула свитка не распознана.")
	var spell_level: int = maxi(int(spell.get("spell_level", 0)), 0)
	if spell_level <= 0:
		return _failure("Заговоры не переписываются из свитков в книгу заклинаний.")
	if not is_wizard_spell(spell):
		return _failure("Это заклинание отсутствует в списке Волшебника.")
	if spell_level > get_maximum_spell_level(character):
		return _failure("Волшебник пока не может подготавливать заклинания %d уровня." % spell_level)
	if is_in_spellbook(character, spell_id):
		return _failure("Формула уже записана в книге заклинаний.")
	var cost_gp: int = COPY_COST_GP_PER_LEVEL * spell_level
	if not bool(state.call("has_item", GOLD_ITEM_ID, cost_gp)):
		return _failure("Для переписывания требуется %d золотых монет." % cost_gp)
	return {
		"success": true,
		"message": "Формулу можно переписать.",
		"scroll_item_id": scroll_item_id,
		"spell_id": spell_id,
		"spell_name": str(spell.get("name", spell_id)),
		"spell_level": spell_level,
		"cost_gp": cost_gp,
		"time_minutes": COPY_MINUTES_PER_LEVEL * spell_level,
		"check_dc": SCROLL_CHECK_BASE_DC + spell_level
	}


func copy_scroll_to_spellbook(
	character: PlayerCharacter,
	scroll_item_id: String,
	state: Node,
	natural_roll_override: int = 0
) -> Dictionary:
	var inspection: Dictionary = inspect_scroll(character, scroll_item_id, state)
	if not bool(inspection.get("success", false)):
		return inspection
	var cost_gp: int = int(inspection.get("cost_gp", 0))
	var time_minutes: int = int(inspection.get("time_minutes", 0))
	var spell_id: String = str(inspection.get("spell_id", ""))
	if not bool(state.call("remove_item", scroll_item_id, 1, false)):
		return _failure("Не удалось израсходовать свиток.")
	if not bool(state.call("remove_item", GOLD_ITEM_ID, cost_gp, false)):
		state.call("add_item", scroll_item_id, 1, false)
		return _failure("Не удалось оплатить переписывание.")
	_world_time.advance(state, time_minutes, false)
	var intelligence_modifier: int = character.get_ability_modifier("intelligence")
	var arcana_bonus: int = character.get_skill_modifier("arcana") - intelligence_modifier
	var check: SkillCheckResult = _skill_checks.perform_check(
		character,
		"intelligence",
		int(inspection.get("check_dc", SCROLL_CHECK_BASE_DC)),
		arcana_bonus,
		natural_roll_override
	)
	var copied: bool = check.success
	if copied:
		_append_unique(character.spellbook_spell_ids, spell_id)
		_append_unique(character.known_features, spell_id)
	if state.has_method("save_game"):
		state.call("save_game")
	return {
		"success": copied,
		"copied": copied,
		"message": (
			"Формула «%s» переписана в книгу заклинаний." % str(inspection.get("spell_name", spell_id))
			if copied
			else "Проверка Магии провалена. Свиток уничтожен, время и материалы израсходованы."
		),
		"spell_id": spell_id,
		"spell_name": str(inspection.get("spell_name", spell_id)),
		"spell_level": int(inspection.get("spell_level", 0)),
		"cost_gp": cost_gp,
		"time_minutes": time_minutes,
		"check_dc": check.difficulty,
		"natural_roll": check.natural_roll,
		"check_total": check.total,
		"scroll_consumed": true
	}


func copy_formula_to_spellbook(character: PlayerCharacter, spell_id: String, state: Node) -> Dictionary:
	if character == null or character.character_class_id != WIZARD_CLASS_ID:
		return _failure("Только Волшебник может переписывать формулы.")
	if not has_physical_spellbook(state):
		return _failure("Книга заклинаний отсутствует.")
	var spell: Dictionary = get_spell_definition(spell_id)
	var level: int = maxi(int(spell.get("spell_level", 0)), 0)
	if spell.is_empty() or level <= 0 or not is_wizard_spell(spell):
		return _failure("Эту формулу нельзя записать в книгу Волшебника.")
	if level > get_maximum_spell_level(character):
		return _failure("Уровень формулы пока недоступен.")
	if is_in_spellbook(character, spell_id):
		return _failure("Формула уже находится в книге.")
	var cost_gp: int = COPY_COST_GP_PER_LEVEL * level
	if not bool(state.call("has_item", GOLD_ITEM_ID, cost_gp)):
		return _failure("Недостаточно золота: требуется %d." % cost_gp)
	state.call("remove_item", GOLD_ITEM_ID, cost_gp, false)
	_world_time.advance(state, COPY_MINUTES_PER_LEVEL * level, false)
	_append_unique(character.spellbook_spell_ids, spell_id)
	_append_unique(character.known_features, spell_id)
	if state.has_method("save_game"):
		state.call("save_game")
	return _success("Формула переписана в книгу заклинаний.")


func _spellcasting_profile(class_id: String) -> Dictionary:
	var value: Variant = _classes.get(class_id, {})
	if not value is Dictionary:
		return {}
	var profile_value: Variant = (value as Dictionary).get("spellcasting", {})
	return (profile_value as Dictionary).duplicate(true) if profile_value is Dictionary else {}


func _load_json_dictionary(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		push_error("Файл данных не найден: %s" % path)
		return {}
	var file: FileAccess = FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {}
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	return parsed as Dictionary if parsed is Dictionary else {}


static func _append_unique(values: Array[String], value: String) -> bool:
	if value.is_empty() or value in values:
		return false
	values.append(value)
	return true


static func _string_array(value: Variant) -> Array[String]:
	var result: Array[String] = []
	if value is Array:
		for item: Variant in value:
			result.append(str(item))
	return result


static func _success(message: String) -> Dictionary:
	return {"success": true, "message": message}


static func _failure(message: String) -> Dictionary:
	return {"success": false, "message": message}
