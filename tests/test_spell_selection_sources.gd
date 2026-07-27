extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var selections := SpellSelectionSystem.new()
	var spells := SpellcastingSystem.new()
	var class_ids: Array[String] = [
		"bard", "cleric", "druid", "paladin", "ranger", "sorcerer", "warlock", "wizard"
	]
	for class_id: String in class_ids:
		var catalog_error: String = _catalog_error(selections.get_class_profile(class_id), spells)
		if not catalog_error.is_empty():
			_fail("%s class profile: %s" % [class_id, catalog_error])
			return
		var defaults: Dictionary = selections.create_default_sources(class_id, "")
		var validation: Dictionary = selections.validate_sources(class_id, "", defaults)
		if not bool(validation.get("success", false)):
			_fail("Default spell selection is invalid for %s: %s" % [class_id, str(validation.get("message", ""))])
			return
	for feat_id: String in [
		OriginFeatSystem.MAGIC_INITIATE_CLERIC_FEAT_ID,
		OriginFeatSystem.MAGIC_INITIATE_WIZARD_FEAT_ID
	]:
		var feat_catalog_error: String = _catalog_error(selections.get_magic_initiate_profile(feat_id), spells)
		if not feat_catalog_error.is_empty():
			_fail("%s feat profile: %s" % [feat_id, feat_catalog_error])
			return

	var wizard_sources: Dictionary = selections.create_default_sources(
		"wizard",
		OriginFeatSystem.MAGIC_INITIATE_CLERIC_FEAT_ID
	)
	var wizard_source: Dictionary = wizard_sources.get(SpellSelectionSystem.SOURCE_CLASS, {}) as Dictionary
	if (wizard_source.get(SpellSelectionSystem.CANTRIP_IDS_KEY, []) as Array).size() != 3:
		_fail("Wizard did not receive three cantrip choices.")
		return
	if (wizard_source.get(SpellSelectionSystem.SPELL_IDS_KEY, []) as Array).size() != 6:
		_fail("Wizard spellbook did not receive six level-one spell choices.")
		return
	if (wizard_source.get(SpellSelectionSystem.PREPARED_IDS_KEY, []) as Array).size() != 4:
		_fail("Wizard did not prepare four of the six spellbook spells.")
		return
	var feat_source: Dictionary = wizard_sources.get(SpellSelectionSystem.SOURCE_MAGIC_INITIATE, {}) as Dictionary
	feat_source["ability_id"] = "charisma"
	wizard_sources[SpellSelectionSystem.SOURCE_MAGIC_INITIATE] = feat_source

	var wizard := PlayerCharacter.new()
	wizard.character_name = "Источник"
	wizard.character_class_id = "wizard"
	wizard.character_class_name = "Волшебник"
	wizard.origin_feat_id = OriginFeatSystem.MAGIC_INITIATE_CLERIC_FEAT_ID
	wizard.abilities["intelligence"] = 16
	wizard.base_abilities["intelligence"] = 16
	wizard.abilities["charisma"] = 14
	wizard.base_abilities["charisma"] = 14
	var apply_result: Dictionary = selections.apply_sources(wizard, wizard_sources)
	if not bool(apply_result.get("success", false)):
		_fail("Valid source-oriented selection was rejected: %s" % str(apply_result.get("message", "")))
		return
	OriginFeatSystem.new().initialize_character(wizard, true)
	spells.ensure_character(wizard, true)
	if "cure_wounds" not in spells.get_known_spell_ids(wizard) or not spells.is_prepared(wizard, "cure_wounds"):
		_fail("Selected Magic Initiate spell was not known and always prepared.")
		return
	var cure_wounds: Dictionary = spells.get_spell_definition("cure_wounds")
	if spells.get_spellcasting_ability(wizard, cure_wounds) != "charisma":
		_fail("Magic Initiate did not use the explicitly selected Charisma source.")
		return
	if wizard.get_resource("magic_initiate_cleric_1") != 1:
		_fail("Magic Initiate free-use resource was not initialized.")
		return
	if spells.active_resource_key(wizard, cure_wounds) != "magic_initiate_cleric_1":
		_fail("Selected Magic Initiate spell did not prefer its free use.")
		return
	var free_payment: Dictionary = spells.consume_spell_cost_detailed(wizard, cure_wounds)
	if not bool(free_payment.get("success", false)) or bool(free_payment.get("expended_slot", true)):
		_fail("Magic Initiate free use was not consumed as a source resource.")
		return
	var slots_before: int = wizard.get_resource("spell_slots_1")
	var slot_payment: Dictionary = spells.consume_spell_cost_detailed(wizard, cure_wounds)
	if not bool(slot_payment.get("success", false)) or not bool(slot_payment.get("expended_slot", false)):
		_fail("Magic Initiate did not fall back to the Wizard spell slots.")
		return
	if wizard.get_resource("spell_slots_1") != slots_before - 1:
		_fail("Magic Initiate fallback did not consume exactly one spell slot.")
		return

	var restored: PlayerCharacter = PlayerCharacter.from_dict(wizard.to_dict())
	if restored.spell_sources != wizard.spell_sources:
		_fail("Spell sources were not preserved by PlayerCharacter save round-trip.")
		return
	if selections.get_spellcasting_ability(restored, "cure_wounds") != "charisma":
		_fail("Restored Magic Initiate source lost its selected spellcasting ability.")
		return
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload was unavailable for the version-four save migration.")
		return
	var version_four_character: Dictionary = wizard.to_dict()
	version_four_character.erase("spell_sources")
	var migrated_save: Dictionary = state.call(
		"_migrate_version_4_to_5",
		{"version": 4, "player_character": version_four_character}
	) as Dictionary
	var migrated_character: Dictionary = migrated_save.get("player_character", {}) as Dictionary
	if int(migrated_save.get("version", 0)) != 5 or not migrated_character.has("spell_sources"):
		_fail("Version-four saves were not upgraded with the spell source field.")
		return

	var sorcerer := PlayerCharacter.new()
	sorcerer.character_class_id = "sorcerer"
	sorcerer.abilities["charisma"] = 16
	sorcerer.base_abilities["charisma"] = 16
	var sorcerer_sources: Dictionary = selections.create_default_sources("sorcerer", "")
	if not bool(selections.apply_sources(sorcerer, sorcerer_sources).get("success", false)):
		_fail("Sorcerer source selection could not be applied.")
		return
	spells.ensure_character(sorcerer, true)
	if spells.get_spellcasting_ability(sorcerer, spells.get_spell_definition("fire_bolt")) != "charisma":
		_fail("Class source did not override the legacy Intelligence field on Fire Bolt.")
		return

	var legacy_origin := PlayerCharacter.new()
	legacy_origin.character_class_id = "fighter"
	legacy_origin.origin_feat_id = OriginFeatSystem.MAGIC_INITIATE_WIZARD_FEAT_ID
	OriginFeatSystem.new().initialize_character(legacy_origin, true)
	var legacy_feat_source: Dictionary = selections.get_source(legacy_origin, SpellSelectionSystem.SOURCE_MAGIC_INITIATE)
	if not bool(legacy_feat_source.get("legacy", false)):
		_fail("A pre-selection Magic Initiate character did not receive a legacy source.")
		return
	for legacy_spell_id: String in ["fire_bolt", "poison_spray", "origin_magic_missile"]:
		if legacy_spell_id not in legacy_origin.known_features:
			_fail("Legacy Magic Initiate package lost %s." % legacy_spell_id)
			return

	var legacy_wizard := PlayerCharacter.new()
	legacy_wizard.character_class_id = "wizard"
	spells.ensure_character(legacy_wizard, false)
	var legacy_class_source: Dictionary = selections.get_source(legacy_wizard, SpellSelectionSystem.SOURCE_CLASS)
	if not bool(legacy_class_source.get("legacy", false)) or "absorb_elements" not in legacy_wizard.known_features:
		_fail("Legacy class starting package was not preserved during source migration.")
		return

	var invalid_sources: Dictionary = selections.create_default_sources("wizard", "")
	var invalid_class: Dictionary = invalid_sources.get(SpellSelectionSystem.SOURCE_CLASS, {}) as Dictionary
	var invalid_cantrips: Array = invalid_class.get(SpellSelectionSystem.CANTRIP_IDS_KEY, []) as Array
	invalid_cantrips.pop_back()
	invalid_class[SpellSelectionSystem.CANTRIP_IDS_KEY] = invalid_cantrips
	invalid_sources[SpellSelectionSystem.SOURCE_CLASS] = invalid_class
	if bool(selections.validate_sources("wizard", "", invalid_sources).get("success", true)):
		_fail("Incomplete Wizard cantrip selection passed validation.")
		return

	print("Class spell selection, Wizard spellbook preparation, source abilities, Magic Initiate free use and legacy migrations passed.")
	quit(0)


func _catalog_error(profile: Dictionary, spells: SpellcastingSystem) -> String:
	for spell_id: String in _string_array(profile.get("cantrip_options", [])):
		var cantrip: Dictionary = spells.get_spell_definition(spell_id)
		if cantrip.is_empty():
			return "unknown cantrip option %s" % spell_id
		if int(cantrip.get("spell_level", -1)) != 0:
			return "cantrip option %s is not level zero" % spell_id
	for spell_id: String in _string_array(profile.get("spell_options", [])):
		var spell: Dictionary = spells.get_spell_definition(spell_id)
		if spell.is_empty():
			return "unknown level-one option %s" % spell_id
		if int(spell.get("spell_level", -1)) != 1:
			return "spell option %s is not level one" % spell_id
	return ""


func _string_array(value: Variant) -> Array[String]:
	var result: Array[String] = []
	if value is Array:
		for item: Variant in value:
			result.append(str(item))
	return result
