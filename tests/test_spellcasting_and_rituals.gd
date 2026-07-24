extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var spells := SpellcastingSystem.new()
	var time := WorldTimeSystem.new()
	var wizard := PlayerCharacter.new()
	wizard.character_class_id = "wizard"
	wizard.character_class_name = "Волшебник"
	wizard.abilities["intelligence"] = 16
	wizard.base_abilities["intelligence"] = 16
	wizard.known_features.append("ritual_adept")

	if not spells.ensure_character(wizard, false):
		_fail("Wizard spellcasting profile was not initialized.")
		return
	if wizard.get_resource("spell_slots_1") != 2 or wizard.get_resource_maximum("spell_slots_1") != 2:
		_fail("Wizard level-one spell slots were not initialized to 2/2.")
		return
	for spell_id: String in ["fire_bolt", "magic_missile", "detect_magic", "comprehend_languages"]:
		if spell_id not in spells.get_known_spell_ids(wizard):
			_fail("Wizard did not learn starting spell: %s" % spell_id)
			return
	if not spells.is_prepared(wizard, "fire_bolt") or not spells.is_prepared(wizard, "detect_magic"):
		_fail("Cantrip or starting ritual was not prepared.")
		return
	if spells.get_spell_attack_bonus(wizard) != 5 or spells.get_spell_save_dc(wizard) != 13:
		_fail("Spell attack bonus or spell save DC is incorrect.")
		return

	var magic_missile: Dictionary = spells.get_spell_definition("magic_missile")
	if not spells.can_cast_spell(wizard, magic_missile):
		_fail("Prepared Magic Missile was rejected despite available slots.")
		return
	if not spells.consume_spell_cost(wizard, magic_missile) or wizard.get_resource("spell_slots_1") != 1:
		_fail("Casting a level-one spell did not consume one slot.")
		return
	spells.ensure_character(wizard, false)
	if wizard.get_resource("spell_slots_1") != 1:
		_fail("Loading/ensuring spellcasting incorrectly refilled a spent slot.")
		return
	spells.recover_after_rest(wizard, false)
	if wizard.get_resource("spell_slots_1") != 1:
		_fail("A short rest incorrectly restored ordinary Wizard spell slots.")
		return
	spells.recover_after_rest(wizard, true)
	if wizard.get_resource("spell_slots_1") != 2:
		_fail("Long-rest recovery did not restore ordinary spell slots.")
		return

	var unprepare_result: Dictionary = spells.unprepare_spell(wizard, "magic_missile")
	if not bool(unprepare_result.get("success", false)) or spells.is_prepared(wizard, "magic_missile"):
		_fail("Prepared spell could not be removed from preparation.")
		return
	spells.ensure_character(wizard, false)
	if spells.is_prepared(wizard, "magic_missile"):
		_fail("Starting preparation was incorrectly re-applied after an explicit unprepare.")
		return
	if spells.can_cast_spell(wizard, magic_missile):
		_fail("Unprepared level-one spell remained castable.")
		return
	var prepare_result: Dictionary = spells.prepare_spell(wizard, "magic_missile")
	if not bool(prepare_result.get("success", false)) or not spells.is_prepared(wizard, "magic_missile"):
		_fail("Known spell could not be prepared again.")
		return

	var detect_magic: Dictionary = spells.get_spell_definition("detect_magic")
	var unprepare_ritual_result: Dictionary = spells.unprepare_spell(wizard, "detect_magic")
	if not bool(unprepare_ritual_result.get("success", false)) or spells.is_prepared(wizard, "detect_magic"):
		_fail("Wizard ritual could not be removed from preparation for the Ritual Adept test.")
		return
	if spells.can_cast_spell(wizard, detect_magic, false, false):
		_fail("Unprepared Wizard ritual remained castable as a normal spell.")
		return
	if not spells.can_cast_spell(wizard, detect_magic, true, false, 0, {"has_spellbook": true}):
		_fail("Wizard Ritual Adept could not cast a known spellbook ritual without preparing it.")
		return

	var slot_before_ritual: int = wizard.get_resource("spell_slots_1")
	var ritual_result: Dictionary = spells.cast_ritual(wizard, "detect_magic", 480, false, {"has_spellbook": true})
	if not bool(ritual_result.get("success", false)) or int(ritual_result.get("advance_minutes", 0)) != 10:
		_fail("Detect Magic ritual did not complete in ten extra minutes.")
		return
	if wizard.get_resource("spell_slots_1") != slot_before_ritual:
		_fail("Ritual casting consumed a spell slot.")
		return
	if not spells.has_detect_magic(wizard, 499) or spells.has_detect_magic(wizard, 500):
		_fail("Detect Magic ritual duration did not begin after ritual completion.")
		return
	if spells.get_concentration_spell_id(wizard) != "detect_magic":
		_fail("Detect Magic did not start concentration.")
		return
	if bool(spells.cast_ritual(wizard, "detect_magic", 500, true, {"has_spellbook": true}).get("success", false)):
		_fail("Ritual casting was allowed during combat.")
		return
	spells.cleanup_expired_effects(wizard, 500)
	if not spells.get_concentration_spell_id(wizard).is_empty():
		_fail("Expired concentration ritual was not cleaned up.")
		return

	wizard.active_effects[SpellcastingSystem.DETECT_MAGIC_UNTIL_KEY] = 520
	spells.begin_concentration(wizard, "detect_magic")
	var combat_state := CombatantState.new()
	spells.sync_concentration_to_combat_state(wizard, combat_state, 77)
	if combat_state.concentrating_on != "detect_magic" or combat_state.concentration_source_id != 77:
		_fail("Saved ritual concentration was not synchronized to CombatantState.")
		return
	spells.end_concentration(wizard)
	if spells.has_detect_magic(wizard, 501):
		_fail("Ending concentration did not remove the concentration-bound Detect Magic effect.")
		return

	var comprehend: Dictionary = spells.get_spell_definition("comprehend_languages")
	var normal_result: Dictionary = spells.cast_utility_spell(wizard, comprehend, 600, false)
	if not bool(normal_result.get("success", false)) or wizard.get_resource("spell_slots_1") != slot_before_ritual - 1:
		_fail("Normal utility spell did not spend a spell slot.")
		return
	if not spells.comprehends_all_languages(wizard, 659) or spells.comprehends_all_languages(wizard, 660):
		_fail("Comprehend Languages duration is incorrect.")
		return

	var origin_character := PlayerCharacter.new()
	origin_character.character_class_id = "fighter"
	origin_character.origin_feat_id = "magic_initiate_wizard"
	OriginFeatSystem.new().initialize_character(origin_character, true)
	spells.ensure_character(origin_character, false)
	if not spells.is_prepared(origin_character, "origin_magic_missile"):
		_fail("Magic Initiate level-one spell was not always prepared.")
		return
	if not spells.can_cast_spell(origin_character, spells.get_spell_definition("origin_magic_missile")):
		_fail("Magic Initiate free casting was unavailable.")
		return

	var warlock := PlayerCharacter.new()
	warlock.character_class_id = "warlock"
	spells.ensure_character(warlock, false)
	if warlock.get_resource("pact_slots_1") != 1 or spells.slot_resource_key(warlock, 1) != "pact_slots_1":
		_fail("Warlock pact slot profile was not isolated from ordinary spell slots.")
		return
	warlock.consume_resource("pact_slots_1", 1)
	if warlock.get_resource("pact_slots_1") != 0:
		_fail("Warlock pact slot could not be spent.")
		return
	spells.recover_after_rest(warlock, false)
	if warlock.get_resource("pact_slots_1") != 1:
		_fail("Warlock pact slot was not restored by a short rest.")
		return

	spells.begin_concentration(wizard, "detect_magic")
	spells.recover_after_rest(wizard, true)
	if not spells.get_concentration_spell_id(wizard).is_empty():
		_fail("Long rest did not end concentration.")
		return

	if time.format_time(480) != "День 1, 08:00" or time.format_time(1500) != "День 2, 01:00":
		_fail("World time formatting is incorrect.")
		return

	print("Spellcasting, concentration, rituals, Ritual Adept, rest recovery and world time tests passed.")
	quit(0)
