extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return

	if ProgressionSystem.total_experience_for_level(2) != 300:
		_fail("Level 2 XP threshold is not the official 300 XP.")
		return
	if ProgressionSystem.total_experience_for_level(20) != 355000:
		_fail("Level 20 XP threshold is not the official 355000 XP.")
		return

	state.call("new_game")
	var fighter := _character("fighter", "Воин", 10, 14)
	state.set("player_character", fighter)
	var xp_result: Dictionary = ProgressionSystem.grant_experience(fighter, 300)
	if fighter.level != 1 or not bool(xp_result.get("level_up_available", false)):
		_fail("XP must unlock a level without applying it automatically.")
		return

	var levels := LevelUpSystem.new()
	var begin_result: Dictionary = levels.begin_transaction(fighter, state)
	if not bool(begin_result.get("success", false)):
		_fail("Level-up transaction did not start.")
		return
	if int((begin_result.get("transaction", {}) as Dictionary).get("target_level", 0)) != 2:
		_fail("The transaction did not target the next sequential level.")
		return
	var restored := LevelUpSystem.new()
	if not restored.has_pending_transaction(fighter, state):
		_fail("A new system instance did not restore the saved transaction.")
		return
	levels.choose_fixed_hp(fighter, state)
	var fixed_gain: int = levels.get_fixed_hp_gain(fighter)
	var commit_result: Dictionary = levels.commit_transaction(fighter, state)
	if not bool(commit_result.get("success", false)):
		_fail("Fixed-HP level-up did not commit.")
		return
	if fighter.level != 2 or fighter.maximum_health != 12 + fixed_gain:
		_fail("Fixed HP or level was applied incorrectly.")
		return
	if levels.has_pending_transaction(fighter, state):
		_fail("Committed transaction was not cleared.")
		return

	ProgressionSystem.grant_experience(
		fighter,
		ProgressionSystem.total_experience_for_level(3) - fighter.experience
	)
	levels.begin_transaction(fighter, state)
	var first_roll: Dictionary = levels.roll_hp_once(fighter, state, 1)
	var second_roll: Dictionary = levels.roll_hp_once(fighter, state, 10)
	var first_transaction: Dictionary = first_roll.get("transaction", {}) as Dictionary
	var second_transaction: Dictionary = second_roll.get("transaction", {}) as Dictionary
	if int(first_transaction.get("hp_roll", 0)) != 1 or int(second_transaction.get("hp_roll", 0)) != 1:
		_fail("HP roll was not irreversible inside the saved transaction.")
		return
	if not bool(levels.commit_transaction(fighter, state).get("success", false)) or fighter.level != 3:
		_fail("Rolled-HP level-up did not commit.")
		return

	state.call("new_game")
	var monk := _character("monk", "Монах", 8, 12)
	monk.level = 3
	monk.experience = ProgressionSystem.total_experience_for_level(4)
	monk.hit_dice_maximum = 3
	monk.hit_dice_current = 3
	state.set("player_character", monk)
	levels.begin_transaction(monk, state)
	levels.choose_fixed_hp(monk, state)
	if not bool(levels.commit_transaction(monk, state).get("success", false)):
		_fail("Monk level-up did not commit.")
		return
	if "slow_fall" not in monk.known_features:
		_fail("Level-specific class feature was not granted.")
		return

	state.call("new_game")
	var bard := _character("bard", "Бард", 8, 12)
	bard.origin_feat_id = OriginFeatSystem.MAGIC_INITIATE_CLERIC_FEAT_ID
	var selections := SpellSelectionSystem.new()
	var sources: Dictionary = selections.create_default_sources(
		bard.character_class_id,
		bard.origin_feat_id
	)
	if not bool(selections.apply_sources(bard, sources).get("success", false)):
		_fail("Spell sources could not be initialized for level-up test.")
		return
	OriginFeatSystem.new().initialize_character(bard, true)
	SpellcastingSystem.new().ensure_character(bard, true)
	bard.experience = ProgressionSystem.total_experience_for_level(2)
	state.set("player_character", bard)
	levels.begin_transaction(bard, state)
	levels.choose_fixed_hp(bard, state)

	var new_class_spells: Array[String] = levels.get_new_class_spell_candidates(bard)
	if new_class_spells.is_empty():
		_fail("No optional new class spell was offered from the current catalog.")
		return
	levels.set_new_class_spell(bard, state, new_class_spells[0])

	var old_magic_spells: Array[String] = levels.get_magic_initiate_spell_old_candidates(bard)
	var new_magic_spells: Array[String] = levels.get_magic_initiate_spell_new_candidates(bard)
	if old_magic_spells.is_empty() or new_magic_spells.is_empty():
		_fail("Magic Initiate spell replacement candidates are missing.")
		return
	levels.set_magic_initiate_spell_replacement(
		bard,
		state,
		old_magic_spells[0],
		new_magic_spells[0]
	)

	if not bool(levels.commit_transaction(bard, state).get("success", false)):
		_fail("Spell-choice level-up did not commit.")
		return
	var class_source: Dictionary = selections.get_source(bard, SpellSelectionSystem.SOURCE_CLASS)
	if new_class_spells[0] not in (class_source.get(SpellSelectionSystem.SPELL_IDS_KEY, []) as Array):
		_fail("New class spell was not stored in its source.")
		return
	var feat_source: Dictionary = selections.get_source(bard, SpellSelectionSystem.SOURCE_MAGIC_INITIATE)
	if new_magic_spells[0] not in (feat_source.get(SpellSelectionSystem.SPELL_IDS_KEY, []) as Array):
		_fail("New Magic Initiate spell was not stored.")
		return

	ProgressionSystem.grant_experience(
		bard,
		ProgressionSystem.total_experience_for_level(3) - bard.experience
	)
	levels.begin_transaction(bard, state)
	levels.choose_fixed_hp(bard, state)
	var old_magic_cantrips: Array[String] = levels.get_magic_initiate_cantrip_old_candidates(bard)
	var new_magic_cantrips: Array[String] = levels.get_magic_initiate_cantrip_new_candidates(bard)
	if old_magic_cantrips.is_empty() or new_magic_cantrips.is_empty():
		_fail("Magic Initiate cantrip replacement candidates are missing.")
		return
	levels.set_magic_initiate_cantrip_replacement(
		bard,
		state,
		old_magic_cantrips[0],
		new_magic_cantrips[0]
	)
	if not bool(levels.commit_transaction(bard, state).get("success", false)):
		_fail("Magic Initiate cantrip replacement did not commit.")
		return
	feat_source = selections.get_source(bard, SpellSelectionSystem.SOURCE_MAGIC_INITIATE)
	if old_magic_cantrips[0] in (feat_source.get(SpellSelectionSystem.CANTRIP_IDS_KEY, []) as Array):
		_fail("Replaced Magic Initiate cantrip remained in the source.")
		return

	state.call("new_game")
	var legacy := _character("fighter", "Воин", 10, 12)
	legacy.level = 2
	legacy.experience = 100
	state.set("player_character", legacy)
	if not levels.ensure_migrated(legacy, state):
		_fail("Legacy synthetic XP state was not migrated.")
		return
	if legacy.experience != ProgressionSystem.total_experience_for_level(2):
		_fail("Migration did not preserve the level with the official minimum XP.")
		return

	print("Official XP, saved sequential transactions, HP choice, class features and spell replacement tests passed.")
	quit(0)


func _character(
	class_id: String,
	class_name_value: String,
	hit_die: int,
	constitution: int
) -> PlayerCharacter:
	var character := PlayerCharacter.new()
	character.character_name = "Испытатель"
	character.character_class_id = class_id
	character.character_class_name = class_name_value
	character.race_id = "human"
	character.race_name = "Человек"
	character.abilities["constitution"] = constitution
	character.base_abilities["constitution"] = constitution
	character.maximum_health = 12
	character.current_health = 12
	character.hit_die_size = hit_die
	character.hit_dice_maximum = 1
	character.hit_dice_current = 1
	return character
