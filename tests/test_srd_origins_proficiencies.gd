extends SceneTree

const BACKGROUNDS_PATH: String = "res://data/origins/backgrounds.json"
const RACES_PATH: String = "res://data/races/races.json"
const CLASSES_PATH: String = "res://data/classes/classes.json"


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _init() -> void:
	_test_background_catalog()
	_test_ability_bonus_validation()
	_test_background_application()
	_test_proficiency_progression()
	_test_skill_and_save_modifiers()
	_test_serialization_and_legacy_migration()
	_test_species_have_no_ability_bonuses()
	print("SRD 5.2.1 origins and proficiency tests passed.")
	quit(0)


func _test_background_catalog() -> void:
	if not FileAccess.file_exists(BACKGROUNDS_PATH):
		_fail("Background data file is missing.")
		return
	var system := OriginDataSystem.new()
	var backgrounds: Array[Dictionary] = system.get_backgrounds()
	if backgrounds.size() != 4:
		_fail("Expected four SRD backgrounds, got %d." % backgrounds.size())
		return
	var required_ids: Array[String] = ["acolyte", "criminal", "sage", "soldier"]
	var seen: Dictionary = {}
	for background: Dictionary in backgrounds:
		var background_id: String = str(background.get("id", ""))
		if background_id not in required_ids or seen.has(background_id):
			_fail("Invalid or duplicate background id: %s." % background_id)
			return
		seen[background_id] = true
		if (background.get("ability_options", []) as Array).size() != 3:
			_fail("Background %s must expose exactly three ability options." % background_id)
			return
		if (background.get("skill_proficiencies", []) as Array).size() != 2:
			_fail("Background %s must grant exactly two skills." % background_id)
			return
		if (background.get("tool_proficiencies", []) as Array).size() != 1:
			_fail("Background %s must grant exactly one tool proficiency." % background_id)
			return
		if str(background.get("origin_feat_id", "")).is_empty():
			_fail("Background %s has no Origin feat." % background_id)
			return
	for background_id: String in required_ids:
		if not seen.has(background_id):
			_fail("Required background %s is missing." % background_id)
			return


func _test_ability_bonus_validation() -> void:
	var system := OriginDataSystem.new()
	var abilities: Dictionary = {
		"strength": 18,
		"dexterity": 14,
		"constitution": 14,
		"intelligence": 10,
		"wisdom": 10,
		"charisma": 10
	}
	if not bool(system.validate_ability_bonuses("soldier", {"strength": 2, "constitution": 1}, abilities).get("success", false)):
		_fail("Valid +2/+1 background allocation was rejected.")
		return
	if not bool(system.validate_ability_bonuses("soldier", {"strength": 1, "dexterity": 1, "constitution": 1}, abilities).get("success", false)):
		_fail("Valid +1/+1/+1 background allocation was rejected.")
		return
	if bool(system.validate_ability_bonuses("soldier", {"strength": 3}, abilities).get("success", false)):
		_fail("Invalid +3 allocation was accepted.")
		return
	if bool(system.validate_ability_bonuses("soldier", {"wisdom": 2, "strength": 1}, abilities).get("success", false)):
		_fail("Background accepted an ability outside its three options.")
		return
	var capped: Dictionary = abilities.duplicate(true)
	capped["strength"] = 19
	if bool(system.validate_ability_bonuses("soldier", {"strength": 2, "constitution": 1}, capped).get("success", false)):
		_fail("Background allocation exceeded the score cap of 20.")
		return


func _test_background_application() -> void:
	var system := OriginDataSystem.new()
	var character := _fighter()
	var result: Dictionary = system.apply_background(
		character,
		"soldier",
		{"strength": 2, "constitution": 1},
		["dwarvish", "orc"]
	)
	if not bool(result.get("success", false)):
		_fail("Soldier background could not be applied: %s" % str(result.get("message", "")))
		return
	if character.get_ability_score("strength") != 16 or character.get_ability_score("constitution") != 15:
		_fail("Background ability increases were not applied to the stored base scores.")
		return
	if character.background_id != "soldier" or character.origin_feat_id != "savage_attacker":
		_fail("Background identity or Origin feat was not persisted.")
		return
	if character.skill_proficiencies != ["athletics", "intimidation"]:
		_fail("Soldier skill proficiencies are incorrect.")
		return
	if character.tool_proficiencies != ["gaming_set_choice"]:
		_fail("Soldier tool proficiency is incorrect.")
		return
	if character.language_proficiencies != ["common", "dwarvish", "orc"]:
		_fail("Common plus two selected languages were not stored.")
		return
	if bool(system.apply_background(character, "soldier", {"strength": 2, "constitution": 1}, ["dwarvish", "orc"]).get("success", false)):
		_fail("Origin ability increases were applied more than once.")
		return
	var class_data: Dictionary = _fighter_class_data()
	system.apply_class_proficiencies(character, class_data)
	if character.saving_throw_proficiencies != ["strength", "constitution"]:
		_fail("Fighter saving throw proficiencies were not applied from class data.")
		return


func _test_proficiency_progression() -> void:
	var character := _fighter()
	var expected: Dictionary = {1: 2, 4: 2, 5: 3, 8: 3, 9: 4, 13: 5, 17: 6, 20: 6}
	for level_value: Variant in expected.keys():
		character.level = int(level_value)
		if character.get_proficiency_bonus() != int(expected[level_value]):
			_fail("Incorrect Proficiency Bonus at level %d." % character.level)
			return


func _test_skill_and_save_modifiers() -> void:
	var character := _fighter()
	character.level = 5
	character.skill_proficiencies = ["athletics", "perception"]
	character.expertise_skills = ["athletics"]
	character.saving_throw_proficiencies = ["strength", "constitution"]
	if character.get_skill_modifier("athletics") != 8:
		_fail("Expertise did not add Proficiency Bonus twice.")
		return
	if character.get_skill_modifier("perception") != 4:
		_fail("Skill proficiency modifier is incorrect.")
		return
	if character.get_passive_skill("perception") != 14:
		_fail("Passive skill score is incorrect.")
		return
	if character.get_saving_throw_modifier("constitution") != 5:
		_fail("Saving throw proficiency modifier is incorrect.")
		return
	if character.get_saving_throw_modifier("wisdom") != 1:
		_fail("Untrained saving throw incorrectly received Proficiency Bonus.")
		return


func _test_serialization_and_legacy_migration() -> void:
	var system := OriginDataSystem.new()
	var character := _fighter()
	var applied: Dictionary = system.apply_background(character, "sage", {"intelligence": 2, "wisdom": 1}, ["elvish", "gnomish"])
	if not bool(applied.get("success", false)):
		_fail("Sage background setup failed.")
		return
	system.apply_class_proficiencies(character, _fighter_class_data())
	var restored: PlayerCharacter = PlayerCharacter.from_dict(character.to_dict())
	if restored.background_id != "sage" or restored.base_abilities != character.base_abilities or restored.abilities != character.abilities:
		_fail("Origin data did not survive serialization round-trip.")
		return
	if restored.skill_proficiencies != character.skill_proficiencies or restored.saving_throw_proficiencies != character.saving_throw_proficiencies:
		_fail("Proficiencies did not survive serialization round-trip.")
		return
	var legacy_data: Dictionary = {
		"name": "Старый герой",
		"class_id": "fighter",
		"class_name": "Воин",
		"abilities": {"strength": 17, "dexterity": 12, "constitution": 14, "intelligence": 10, "wisdom": 11, "charisma": 8},
		"maximum_health": 12,
		"current_health": 12
	}
	var legacy: PlayerCharacter = PlayerCharacter.from_dict(legacy_data)
	var before: Dictionary = legacy.abilities.duplicate(true)
	system.ensure_legacy_origin(legacy)
	if legacy.background_id != OriginDataSystem.LEGACY_BACKGROUND_ID or not legacy.origin_applied:
		_fail("Legacy character did not receive a migration marker.")
		return
	if legacy.abilities != before or legacy.base_abilities != before:
		_fail("Legacy migration unexpectedly changed ability scores.")
		return


func _test_species_have_no_ability_bonuses() -> void:
	if not FileAccess.file_exists(RACES_PATH):
		_fail("Species data file is missing.")
		return
	var file: FileAccess = FileAccess.open(RACES_PATH, FileAccess.READ)
	var parsed: Variant = JSON.parse_string(file.get_as_text()) if file != null else null
	if not parsed is Dictionary:
		_fail("Species data is invalid JSON.")
		return
	if str((parsed as Dictionary).get("ruleset_id", "")) != PlayerCharacter.DEFAULT_RULESET_ID:
		_fail("Species data is not pinned to SRD 5.2.1.")
		return
	var races_value: Variant = (parsed as Dictionary).get("races", [])
	if not races_value is Array:
		_fail("Species collection is not an array.")
		return
	for value: Variant in races_value:
		if not value is Dictionary:
			_fail("Species entry is invalid.")
			return
		var species: Dictionary = value as Dictionary
		if species.has("ability_bonuses") or species.has("ability_bonus_description"):
			_fail("Species %s still contains obsolete ability increases." % str(species.get("id", "")))
			return


func _fighter() -> PlayerCharacter:
	var character := PlayerCharacter.new()
	character.character_name = "Тест"
	character.character_class_id = "fighter"
	character.character_class_name = "Воин"
	character.level = 1
	character.base_abilities = {
		"strength": 14,
		"dexterity": 12,
		"constitution": 14,
		"intelligence": 10,
		"wisdom": 12,
		"charisma": 10
	}
	character.abilities = character.base_abilities.duplicate(true)
	return character


func _fighter_class_data() -> Dictionary:
	if not FileAccess.file_exists(CLASSES_PATH):
		return {}
	var file: FileAccess = FileAccess.open(CLASSES_PATH, FileAccess.READ)
	var parsed: Variant = JSON.parse_string(file.get_as_text()) if file != null else null
	if not parsed is Dictionary:
		return {}
	var classes_value: Variant = (parsed as Dictionary).get("classes", [])
	if classes_value is Array:
		for value: Variant in classes_value:
			if value is Dictionary and str((value as Dictionary).get("id", "")) == "fighter":
				return value as Dictionary
	return {}
