extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _wizard(level: int = 1, initialize_book: bool = false) -> PlayerCharacter:
	var character := PlayerCharacter.new()
	character.character_name = "Переписчик"
	character.character_class_id = "wizard"
	character.character_class_name = "Волшебник"
	character.level = level
	character.maximum_health = 20
	character.current_health = 20
	character.abilities["intelligence"] = 16
	character.base_abilities["intelligence"] = 16
	character.skill_proficiencies.append("arcana")
	character.spellbook_initialized = initialize_book
	return character


func _reset_inventory(state: Node) -> void:
	state.set("inventory", {})


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload was unavailable.")
		return
	state.call("new_game")
	var spellbook := WizardSpellbookSystem.new()
	var spellcasting := SpellcastingSystem.new()

	var wizard: PlayerCharacter = _wizard(1, false)
	state.set("player_character", wizard)
	state.call("add_item", "spellbook", 1, false)
	if not spellcasting.ensure_character(wizard, false):
		_fail("Wizard spellcasting and spellbook were not initialized.")
		return
	if not wizard.spellbook_initialized:
		_fail("Wizard spellbook initialization marker was not stored.")
		return
	for spell_id: String in ["magic_missile", "detect_magic", "comprehend_languages", "burning_hands"]:
		if not spellbook.is_in_spellbook(wizard, spell_id):
			_fail("Starting level-one Wizard spell was absent from the spellbook: %s" % spell_id)
			return
	if spellbook.is_in_spellbook(wizard, "fire_bolt"):
		_fail("A cantrip was incorrectly stored as a levelled spellbook formula.")
		return

	var caustic: Dictionary = spellcasting.get_spell_definition("caustic_pulse")
	if caustic.is_empty() or not spellbook.is_wizard_spell(caustic):
		_fail("The executable Wizard-only scroll spell definition was unavailable.")
		return
	if bool(spellcasting.prepare_spell(wizard, "caustic_pulse").get("success", false)):
		_fail("Wizard prepared a levelled spell that was not in the spellbook.")
		return

	state.call("add_item", "gold_coin", 100, false)
	state.call("add_item", "spell_scroll_caustic_pulse", 1, false)
	var start_minutes: int = WorldTimeSystem.new().get_minutes(state)
	var inspection: Dictionary = spellbook.inspect_scroll(wizard, "spell_scroll_caustic_pulse", state)
	if not bool(inspection.get("success", false)):
		_fail("Valid Wizard scroll was rejected: %s" % str(inspection.get("message", "")))
		return
	if int(inspection.get("cost_gp", 0)) != 50 or int(inspection.get("time_minutes", 0)) != 120 or int(inspection.get("check_dc", 0)) != 11:
		_fail("Level-one scroll transcription cost, time, or Arcana DC was incorrect.")
		return
	var copied: Dictionary = spellbook.copy_scroll_to_spellbook(wizard, "spell_scroll_caustic_pulse", state, 20)
	if not bool(copied.get("success", false)) or not bool(copied.get("copied", false)):
		_fail("Successful Arcana check did not copy the scroll formula.")
		return
	if state.call("has_item", "spell_scroll_caustic_pulse") or int(state.call("get_item_count", "gold_coin")) != 50:
		_fail("Successful transcription did not consume one scroll and 50 gold.")
		return
	if WorldTimeSystem.new().get_minutes(state) != start_minutes + 120:
		_fail("Successful transcription did not advance world time by two hours.")
		return
	if not spellbook.is_in_spellbook(wizard, "caustic_pulse") or "caustic_pulse" not in wizard.known_features:
		_fail("Copied formula was not synchronized to the book and known spell list.")
		return
	if not bool(spellcasting.prepare_spell(wizard, "caustic_pulse").get("success", false)):
		_fail("Copied Wizard spell could not be prepared.")
		return
	var duplicate_gold: int = int(state.call("get_item_count", "gold_coin"))
	state.call("add_item", "spell_scroll_caustic_pulse", 1, false)
	if bool(spellbook.copy_scroll_to_spellbook(wizard, "spell_scroll_caustic_pulse", state, 20).get("success", false)):
		_fail("Duplicate spellbook formula was copied a second time.")
		return
	if int(state.call("get_item_count", "gold_coin")) != duplicate_gold or not bool(state.call("has_item", "spell_scroll_caustic_pulse")):
		_fail("Rejected duplicate transcription consumed resources.")
		return

	_reset_inventory(state)
	var failed_wizard: PlayerCharacter = _wizard(1, true)
	failed_wizard.spellbook_spell_ids = ["magic_missile"]
	failed_wizard.known_features = ["fire_bolt", "magic_missile", "ritual_adept"]
	state.set("player_character", failed_wizard)
	state.call("add_item", "spellbook", 1, false)
	state.call("add_item", "gold_coin", 100, false)
	state.call("add_item", "spell_scroll_detect_magic", 1, false)
	var failed_start_minutes: int = WorldTimeSystem.new().get_minutes(state)
	var failed: Dictionary = spellbook.copy_scroll_to_spellbook(failed_wizard, "spell_scroll_detect_magic", state, 1)
	if bool(failed.get("success", false)) or bool(failed.get("copied", false)):
		_fail("Failed Arcana check copied a spell formula.")
		return
	if bool(state.call("has_item", "spell_scroll_detect_magic")) or int(state.call("get_item_count", "gold_coin")) != 50:
		_fail("Failed transcription did not destroy the scroll and spend materials.")
		return
	if WorldTimeSystem.new().get_minutes(state) != failed_start_minutes + 120:
		_fail("Failed transcription did not consume the required time.")
		return
	if spellbook.is_in_spellbook(failed_wizard, "detect_magic"):
		_fail("Failed transcription added the spell to the book.")
		return

	_reset_inventory(state)
	state.call("add_item", "spellbook", 1, false)
	state.call("add_item", "gold_coin", 500, false)
	state.call("add_item", "spell_scroll_cure_wounds", 1, false)
	if bool(spellbook.inspect_scroll(failed_wizard, "spell_scroll_cure_wounds", state).get("success", false)):
		_fail("A non-Wizard spell was accepted for the Wizard spellbook.")
		return
	state.call("add_item", "spell_scroll_counterspell", 1, false)
	if bool(spellbook.inspect_scroll(failed_wizard, "spell_scroll_counterspell", state).get("success", false)):
		_fail("A first-level Wizard was allowed to copy a third-level spell.")
		return
	var fighter := PlayerCharacter.new()
	fighter.character_class_id = "fighter"
	if bool(spellbook.inspect_scroll(fighter, "spell_scroll_counterspell", state).get("success", false)):
		_fail("A non-Wizard character was allowed to copy a spell scroll.")
		return

	failed_wizard.spellbook_spell_ids.append("detect_magic")
	failed_wizard.known_features.append("detect_magic")
	spellcasting.ensure_character(failed_wizard, false)
	spellcasting.unprepare_spell(failed_wizard, "detect_magic")
	var ritual: Dictionary = spellcasting.get_spell_definition("detect_magic")
	if not spellcasting.can_cast_spell(failed_wizard, ritual, true, false, 0, {"has_spellbook": true}):
		_fail("Unprepared ritual in the physical Wizard spellbook was rejected.")
		return
	if spellcasting.can_cast_spell(failed_wizard, ritual, true, false, 0, {"has_spellbook": false}):
		_fail("Wizard ritual was allowed without access to the physical spellbook.")
		return

	var saved: Dictionary = failed_wizard.to_dict()
	var loaded: PlayerCharacter = PlayerCharacter.from_dict(saved)
	if not loaded.spellbook_initialized or loaded.spellbook_spell_ids != failed_wizard.spellbook_spell_ids:
		_fail("Spellbook state did not survive PlayerCharacter serialization.")
		return
	var old_character: Dictionary = failed_wizard.to_dict()
	old_character.erase("spellbook_spell_ids")
	old_character.erase("spellbook_initialized")
	var migrated: Dictionary = state.call("_migrate_version_4_to_5", {"version": 4, "player_character": old_character}) as Dictionary
	var migrated_character: Dictionary = migrated.get("player_character", {}) as Dictionary
	if int(migrated.get("version", 0)) != 5 or not migrated_character.has("spellbook_spell_ids") or bool(migrated_character.get("spellbook_initialized", true)):
		_fail("Save migration 4 to 5 did not create a safe deferred spellbook state.")
		return

	print("Wizard spellbook initialization, scroll transcription, Arcana failure, ritual access and save migration tests passed.")
	quit(0)
