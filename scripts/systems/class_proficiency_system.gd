class_name ClassProficiencySystem
extends RefCounted

const SIMPLE_WEAPONS: String = "simple_weapons"
const MARTIAL_WEAPONS: String = "martial_weapons"
const MARTIAL_LIGHT_WEAPONS: String = "martial_light_weapons"
const MARTIAL_FINESSE_OR_LIGHT_WEAPONS: String = "martial_finesse_or_light_weapons"


func get_skill_choice_count(class_data: Dictionary) -> int:
	var training: Dictionary = _skill_training(class_data)
	return maxi(int(training.get("choice_count", 0)), 0)


func get_skill_options(class_data: Dictionary) -> Array[String]:
	return _unique_string_array(_skill_training(class_data).get("options", []))


func get_default_skill_choices(class_data: Dictionary, unavailable_skills: Array[String] = []) -> Array[String]:
	var required: int = get_skill_choice_count(class_data)
	var options: Array[String] = get_skill_options(class_data)
	var result: Array[String] = []
	var preferred: Array[String] = _unique_string_array(_skill_training(class_data).get("recommended", []))
	for skill_id: String in preferred + options:
		if skill_id in options and skill_id not in unavailable_skills and skill_id not in result:
			result.append(skill_id)
			if result.size() >= required:
				break
	return result


func validate_skill_choices(
	class_data: Dictionary,
	selected_skills: Array[String],
	unavailable_skills: Array[String] = []
) -> Dictionary:
	var required: int = get_skill_choice_count(class_data)
	var options: Array[String] = get_skill_options(class_data)
	var selected: Array[String] = _unique_string_array(selected_skills)
	if selected.size() != selected_skills.size():
		return {
			"success": false,
			"message": "Один классовый навык выбран несколько раз.",
			"selected": selected
		}
	for skill_id: String in selected:
		if skill_id not in options:
			return {
				"success": false,
				"message": "Навык %s недоступен выбранному классу." % skill_id,
				"selected": selected
			}
		if skill_id in unavailable_skills:
			return {
				"success": false,
				"message": "Навык %s уже получен из происхождения." % skill_id,
				"selected": selected
			}
	if selected.size() != required:
		return {
			"success": false,
			"message": "Выберите классовые навыки: %d из %d." % [selected.size(), required],
			"selected": selected
		}
	return {
		"success": true,
		"message": "Классовые навыки выбраны: %d из %d." % [selected.size(), required],
		"selected": selected
	}


func ensure_character(character: PlayerCharacter, class_data: Dictionary) -> Dictionary:
	if character == null or class_data.is_empty():
		return {"success": false, "changed": false, "message": "Не удалось определить класс персонажа."}
	var unavailable: Array[String] = _skills_from_other_sources(character)
	var selected: Array[String] = character.class_skill_proficiencies.duplicate()
	var validation: Dictionary = validate_skill_choices(class_data, selected, unavailable)
	if not bool(validation.get("success", false)):
		selected = get_default_skill_choices(class_data, unavailable)
	return apply_class_proficiencies(character, class_data, selected, false)


func apply_class_proficiencies(
	character: PlayerCharacter,
	class_data: Dictionary,
	selected_skills: Array[String] = [],
	use_defaults_if_empty: bool = true
) -> Dictionary:
	if character == null or class_data.is_empty():
		return {"success": false, "changed": false, "message": "Не удалось определить класс персонажа."}
	var before: Dictionary = {
		"skills": character.skill_proficiencies.duplicate(),
		"class_skills": character.class_skill_proficiencies.duplicate(),
		"saves": character.saving_throw_proficiencies.duplicate(),
		"weapons": character.weapon_proficiencies.duplicate(),
		"armor": character.armor_training.duplicate()
	}
	var unavailable: Array[String] = _skills_from_other_sources(character)
	var resolved_skills: Array[String] = _unique_string_array(selected_skills)
	if resolved_skills.is_empty() and use_defaults_if_empty:
		resolved_skills = get_default_skill_choices(class_data, unavailable)
	var validation: Dictionary = validate_skill_choices(class_data, resolved_skills, unavailable)
	if not bool(validation.get("success", false)):
		validation["changed"] = false
		return validation

	for previous_skill: String in character.class_skill_proficiencies:
		if previous_skill in character.skill_proficiencies and previous_skill not in unavailable:
			character.skill_proficiencies.erase(previous_skill)
	character.class_skill_proficiencies = resolved_skills.duplicate()
	for skill_id: String in resolved_skills:
		_append_unique(character.skill_proficiencies, skill_id)
	for save_id: String in _unique_string_array(class_data.get("saving_throws", [])):
		_append_unique(character.saving_throw_proficiencies, save_id)
	for weapon_training_id: String in _unique_string_array(class_data.get("weapon_proficiencies", [])):
		_append_unique(character.weapon_proficiencies, weapon_training_id)
	for armor_training_id: String in _unique_string_array(class_data.get("armor_training", [])):
		_append_unique(character.armor_training, armor_training_id)

	var changed: bool = (
		before["skills"] != character.skill_proficiencies
		or before["class_skills"] != character.class_skill_proficiencies
		or before["saves"] != character.saving_throw_proficiencies
		or before["weapons"] != character.weapon_proficiencies
		or before["armor"] != character.armor_training
	)
	return {
		"success": true,
		"changed": changed,
		"message": str(validation.get("message", "")),
		"selected": resolved_skills.duplicate()
	}


func _skills_from_other_sources(character: PlayerCharacter) -> Array[String]:
	var result: Array[String] = []
	for skill_id: String in character.skill_proficiencies:
		if skill_id not in character.class_skill_proficiencies and skill_id not in result:
			result.append(skill_id)
	return result


func _skill_training(class_data: Dictionary) -> Dictionary:
	var value: Variant = class_data.get("skill_training", {})
	return value as Dictionary if value is Dictionary else {}


func _append_unique(target: Array[String], value: String) -> void:
	if not value.is_empty() and value not in target:
		target.append(value)


func _unique_string_array(value: Variant) -> Array[String]:
	var result: Array[String] = []
	if value is Array:
		for item: Variant in value:
			var normalized: String = str(item)
			if not normalized.is_empty() and normalized not in result:
				result.append(normalized)
	return result
