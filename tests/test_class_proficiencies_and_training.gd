extends SceneTree

const CLASS_IDS: Array[String] = [
	"barbarian", "bard", "cleric", "druid", "fighter", "monk",
	"paladin", "ranger", "rogue", "sorcerer", "warlock", "wizard"
]
const SKILL_COUNTS: Dictionary = {
	"barbarian": 2, "bard": 3, "cleric": 2, "druid": 2,
	"fighter": 2, "monk": 2, "paladin": 2, "ranger": 3,
	"rogue": 4, "sorcerer": 2, "warlock": 2, "wizard": 2
}

var _classes: ClassDataSystem = ClassDataSystem.new()
var _proficiencies: ClassProficiencySystem = ClassProficiencySystem.new()


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	if not _test_class_data_contract():
		return
	if not _test_selection_application_and_legacy_migration():
		return
	if not _test_weapon_training_rules():
		return
	if not _test_attack_bonus_and_armor_disadvantage():
		return
	if not _test_armor_and_shield_training():
		return
	if not _test_skill_check_disadvantage():
		return
	print("Class skills, weapon proficiency, and armor training tests passed.")
	quit(0)


func _test_class_data_contract() -> bool:
	var allowed_weapon_training: Array[String] = [
		ClassProficiencySystem.SIMPLE_WEAPONS,
		ClassProficiencySystem.MARTIAL_WEAPONS,
		ClassProficiencySystem.MARTIAL_LIGHT_WEAPONS,
		ClassProficiencySystem.MARTIAL_FINESSE_OR_LIGHT_WEAPONS
	]
	for class_id: String in CLASS_IDS:
		var class_data: Dictionary = _classes.get_class_definition(class_id)
		if class_data.is_empty():
			return _fail("Class definition is missing: %s." % class_id)
		var expected_count: int = int(SKILL_COUNTS[class_id])
		var options: Array[String] = _proficiencies.get_skill_options(class_data)
		if _proficiencies.get_skill_choice_count(class_data) != expected_count or options.size() < expected_count:
			return _fail("%s has an invalid class skill choice contract." % class_id)
		var defaults: Array[String] = _proficiencies.get_default_skill_choices(class_data)
		if not bool(_proficiencies.validate_skill_choices(class_data, defaults).get("success", false)):
			return _fail("%s has invalid recommended class skills." % class_id)
		var weapon_training: Variant = class_data.get("weapon_proficiencies", [])
		if not weapon_training is Array or (weapon_training as Array).is_empty():
			return _fail("%s has no weapon proficiency data." % class_id)
		for value: Variant in weapon_training:
			if str(value) not in allowed_weapon_training:
				return _fail("%s references unknown weapon training %s." % [class_id, str(value)])
	return true


func _test_selection_application_and_legacy_migration() -> bool:
	var fighter_data: Dictionary = _classes.get_class_definition("fighter")
	var character: PlayerCharacter = _fighter()
	character.background_id = "soldier"
	character.skill_proficiencies = ["athletics", "intimidation"]
	var defaults: Array[String] = _proficiencies.get_default_skill_choices(
		fighter_data,
		character.skill_proficiencies
	)
	if defaults != ["perception", "acrobatics"]:
		return _fail("Fighter defaults did not avoid Soldier background skills: %s." % str(defaults))
	if bool(_proficiencies.validate_skill_choices(
		fighter_data,
		["athletics", "perception"],
		character.skill_proficiencies
	).get("success", false)):
		return _fail("A background skill was accepted as a duplicate class choice.")
	var applied: Dictionary = _proficiencies.ensure_character(character, fighter_data)
	if not bool(applied.get("success", false)) or not bool(applied.get("changed", false)):
		return _fail("Class proficiencies were not applied to a legacy character.")
	if character.class_skill_proficiencies != defaults:
		return _fail("Class skill provenance was not stored separately.")
	if character.skill_proficiencies != ["athletics", "intimidation", "perception", "acrobatics"]:
		return _fail("Background and class skills were not combined without duplication.")
	if character.saving_throw_proficiencies != ["strength", "constitution"]:
		return _fail("Class saving throw proficiencies were not applied.")
	if character.weapon_proficiencies != [
		ClassProficiencySystem.SIMPLE_WEAPONS,
		ClassProficiencySystem.MARTIAL_WEAPONS
	]:
		return _fail("Fighter weapon proficiencies were not applied.")
	if character.armor_training != ["light", "medium", "heavy", "shield"]:
		return _fail("Fighter armor training was not applied.")
	if bool(_proficiencies.ensure_character(character, fighter_data).get("changed", true)):
		return _fail("Class proficiency migration is not idempotent.")
	var restored: PlayerCharacter = PlayerCharacter.from_dict(character.to_dict())
	if restored.class_skill_proficiencies != character.class_skill_proficiencies:
		return _fail("Class skill provenance did not survive serialization.")
	if restored.weapon_proficiencies != character.weapon_proficiencies or restored.armor_training != character.armor_training:
		return _fail("Weapon or armor training did not survive serialization.")
	return true


func _test_weapon_training_rules() -> bool:
	var simple_spear: Dictionary = {"id": "spear", "weapon_category": "simple", "properties": ["thrown", "versatile"]}
	var martial_longsword: Dictionary = {"id": "longsword", "weapon_category": "martial", "properties": ["versatile"]}
	var martial_shortsword: Dictionary = {"id": "shortsword", "weapon_category": "martial", "properties": ["finesse", "light"]}
	var martial_longbow: Dictionary = {"id": "longbow", "weapon_category": "martial", "properties": ["heavy", "ranged"]}
	var wizard: PlayerCharacter = PlayerCharacter.new()
	wizard.weapon_proficiencies = [ClassProficiencySystem.SIMPLE_WEAPONS]
	if not wizard.is_proficient_with_weapon_definition(simple_spear) or wizard.is_proficient_with_weapon_definition(martial_longsword):
		return _fail("Simple-only weapon training is incorrect.")
	var monk: PlayerCharacter = PlayerCharacter.new()
	monk.weapon_proficiencies = [
		ClassProficiencySystem.SIMPLE_WEAPONS,
		ClassProficiencySystem.MARTIAL_LIGHT_WEAPONS
	]
	if not monk.is_proficient_with_weapon_definition(martial_shortsword) or monk.is_proficient_with_weapon_definition(martial_longbow):
		return _fail("Monk martial Light weapon restriction is incorrect.")
	var rogue: PlayerCharacter = PlayerCharacter.new()
	rogue.weapon_proficiencies = [
		ClassProficiencySystem.SIMPLE_WEAPONS,
		ClassProficiencySystem.MARTIAL_FINESSE_OR_LIGHT_WEAPONS
	]
	if not rogue.is_proficient_with_weapon_definition(martial_shortsword) or rogue.is_proficient_with_weapon_definition(martial_longsword):
		return _fail("Rogue martial Finesse-or-Light restriction is incorrect.")
	return true


func _test_attack_bonus_and_armor_disadvantage() -> bool:
	var combat: CombatSystem = CombatSystem.new()
	var character: PlayerCharacter = _fighter()
	character.abilities["strength"] = 16
	var longsword: Dictionary = {
		"id": "longsword",
		"name": "Длинный меч",
		"weapon_category": "martial",
		"properties": ["versatile"],
		"ability": "strength",
		"damage_dice": [1, 8],
		"damage_type": "slashing",
		"reach_ft": 5
	}
	var untrained: AttackResult = combat.perform_basic_attack(character, 30, longsword, 10, [], {"distance_feet": 5})
	if untrained.proficiency_bonus != 0 or untrained.attack_bonus != 3:
		return _fail("An untrained weapon incorrectly received Proficiency Bonus.")
	character.weapon_proficiencies = [ClassProficiencySystem.MARTIAL_WEAPONS]
	var trained: AttackResult = combat.perform_basic_attack(character, 30, longsword, 10, [], {"distance_feet": 5})
	if trained.proficiency_bonus != 2 or trained.attack_bonus != 5:
		return _fail("A trained weapon did not receive Proficiency Bonus.")
	var disadvantaged: AttackResult = combat.perform_basic_attack(
		character,
		30,
		longsword,
		18,
		[],
		{"distance_feet": 5, "untrained_armor_d20_disadvantage": true, "second_roll_override": 4}
	)
	if not disadvantaged.disadvantage or disadvantaged.natural_roll != 4:
		return _fail("Untrained armor did not impose disadvantage on a Strength weapon attack.")
	return true


func _test_armor_and_shield_training() -> bool:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		return _fail("GameState autoload is missing.")
	state.call("new_game")
	var wizard: PlayerCharacter = PlayerCharacter.new()
	wizard.character_class_id = "wizard"
	wizard.abilities["dexterity"] = 14
	wizard.equipped_armor_id = "chain_mail"
	wizard.equipped_shield_id = "shield"
	state.set("player_character", wizard)
	if _classes.get_armor_class(wizard) != 16:
		return _fail("An untrained shield incorrectly granted its AC bonus.")
	var training: Dictionary = _classes.get_equipment_training_state(wizard)
	if not bool(training.get("untrained_armor", false)) or not bool(training.get("untrained_shield", false)):
		return _fail("Untrained equipped armor or shield was not detected.")
	if not _classes.has_untrained_armor_d20_disadvantage(wizard, "strength"):
		return _fail("Untrained armor did not affect Strength D20 Tests.")
	if _classes.has_untrained_armor_d20_disadvantage(wizard, "constitution"):
		return _fail("Untrained armor incorrectly affected Constitution D20 Tests.")
	var spell_context: Dictionary = _classes.get_spellcasting_context(wizard)
	if bool(spell_context.get("armor_trained", true)):
		return _fail("Spellcasting context allowed untrained heavy armor.")
	wizard.armor_training = ["heavy", "shield"]
	if _classes.get_armor_class(wizard) != 18:
		return _fail("A trained shield did not grant its AC bonus.")
	if not bool(_classes.get_spellcasting_context(wizard).get("armor_trained", false)):
		return _fail("Spellcasting context rejected trained heavy armor.")
	return true


func _test_skill_check_disadvantage() -> bool:
	var checks: SkillCheckSystem = SkillCheckSystem.new()
	var character: PlayerCharacter = PlayerCharacter.new()
	character.abilities["charisma"] = 14
	character.skill_proficiencies = ["persuasion"]
	var trained_skill: SkillCheckResult = checks.perform_skill_check(character, "persuasion", 12, 0, 8)
	if trained_skill.skill_id != "persuasion" or trained_skill.total != 12:
		return _fail("A trained class skill did not add Proficiency Bonus to its ability check.")
	var disadvantaged: SkillCheckResult = checks.perform_check(character, "dexterity", 10, 0, 17, 3, 0, true)
	if not disadvantaged.disadvantage or disadvantaged.natural_roll != 3:
		return _fail("Ability check disadvantage did not keep the lower d20.")
	character.active_effects["racial_advantage_next_d20"] = true
	var cancelled: SkillCheckResult = checks.perform_check(character, "strength", 10, 0, 17, 3, 0, true)
	if cancelled.advantage or cancelled.disadvantage or cancelled.natural_roll != 17:
		return _fail("Advantage and disadvantage did not cancel on an ability check.")
	return true


func _fighter() -> PlayerCharacter:
	var character: PlayerCharacter = PlayerCharacter.new()
	character.character_name = "Тест"
	character.character_class_id = "fighter"
	character.character_class_name = "Воин"
	character.level = 1
	return character


func _fail(message: String) -> bool:
	push_error(message)
	quit(1)
	return false
