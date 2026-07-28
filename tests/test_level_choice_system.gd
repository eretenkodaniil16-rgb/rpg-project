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

	var choices := LevelChoiceSystem.new()
	var fighter := _fighter(2, ProgressionSystem.total_experience_for_level(3))
	var definitions: Array[Dictionary] = choices.get_choice_definitions(fighter, 3)
	if definitions.size() != 1 or str(definitions[0].get("choice_id", "")) != "fighter_subclass":
		_fail("Fighter level 3 subclass choice is missing from data.")
		return

	state.call("new_game")
	state.set("player_character", fighter)
	var levels := LevelUpChoiceSystem.new()
	levels.begin_transaction(fighter, state)
	levels.choose_fixed_hp(fighter, state)
	var validation: Dictionary = levels.validate_transaction(fighter, state)
	if bool(validation.get("success", false)) or str(validation.get("invalid_choice_id", "")) != "fighter_subclass":
		_fail("Required subclass choice did not block commit.")
		return
	levels.set_level_choice(
		fighter,
		state,
		"fighter_subclass",
		{"option_id": "tactical_blade"}
	)
	var restored := LevelUpChoiceSystem.new()
	var restored_selection: Dictionary = restored.get_level_choice_selection(
		state,
		"fighter_subclass"
	)
	if str(restored_selection.get("option_id", "")) != "tactical_blade":
		_fail("Saved subclass selection was not restored by a new system instance.")
		return
	var result: Dictionary = restored.commit_transaction(fighter, state)
	if not bool(result.get("success", false)) or fighter.subclass_id != "tactical_blade":
		_fail("Subclass choice was not committed.")
		return
	if not fighter.level_choice_history.has("3:fighter_subclass"):
		_fail("Subclass choice history is missing.")
		return

	var serialized: Dictionary = fighter.to_dict()
	var loaded: PlayerCharacter = PlayerCharacter.from_dict(serialized)
	if loaded.subclass_id != fighter.subclass_id or loaded.level_choice_history != fighter.level_choice_history:
		_fail("Subclass or level choice history did not survive serialization.")
		return

	state.call("new_game")
	var capped := _fighter(3, ProgressionSystem.total_experience_for_level(4))
	capped.abilities["strength"] = 19
	capped.base_abilities["strength"] = 19
	state.set("player_character", capped)
	levels.begin_transaction(capped, state)
	levels.choose_fixed_hp(capped, state)
	levels.set_level_choice(
		capped,
		state,
		"level_4_advancement",
		{
			"mode": LevelChoiceSystem.ADVANCEMENT_PLUS_TWO,
			"primary_ability_id": "strength"
		}
	)
	validation = levels.validate_transaction(capped, state)
	if bool(validation.get("success", false)):
		_fail("Ability score increase incorrectly exceeded the cap of 20.")
		return
	levels.set_level_choice(
		capped,
		state,
		"level_4_advancement",
		{
			"mode": LevelChoiceSystem.ADVANCEMENT_SPLIT,
			"primary_ability_id": "strength",
			"secondary_ability_id": "strength"
		}
	)
	if bool(levels.validate_transaction(capped, state).get("success", false)):
		_fail("Split ability increase accepted the same ability twice.")
		return
	levels.set_level_choice(
		capped,
		state,
		"level_4_advancement",
		{
			"mode": LevelChoiceSystem.ADVANCEMENT_SPLIT,
			"primary_ability_id": "strength",
			"secondary_ability_id": "constitution"
		}
	)
	if not bool(levels.commit_transaction(capped, state).get("success", false)):
		_fail("Valid split ability increase did not commit.")
		return
	if capped.get_ability_score("strength") != 20 or capped.get_ability_score("constitution") != 11:
		_fail("Split ability increase produced incorrect scores.")
		return
	if int(capped.level_ability_bonuses.get("strength", 0)) != 1:
		_fail("Level ability bonus source was not stored.")
		return

	state.call("new_game")
	var feat_hero := _fighter(3, ProgressionSystem.total_experience_for_level(4))
	feat_hero.origin_feat_id = OriginFeatSystem.SAVAGE_ATTACKER_FEAT_ID
	state.set("player_character", feat_hero)
	levels.begin_transaction(feat_hero, state)
	levels.choose_fixed_hp(feat_hero, state)
	var available_feats: Array[String] = levels.get_available_level_feat_ids(feat_hero)
	if OriginFeatSystem.SAVAGE_ATTACKER_FEAT_ID in available_feats or OriginFeatSystem.ALERT_FEAT_ID not in available_feats:
		_fail("Feat availability did not exclude an existing origin feat.")
		return
	levels.set_level_choice(
		feat_hero,
		state,
		"level_4_advancement",
		{
			"mode": LevelChoiceSystem.ADVANCEMENT_FEAT,
			"feat_id": OriginFeatSystem.ALERT_FEAT_ID
		}
	)
	if not bool(levels.commit_transaction(feat_hero, state).get("success", false)):
		_fail("Functional level feat did not commit.")
		return
	if not feat_hero.has_feat(OriginFeatSystem.ALERT_FEAT_ID):
		_fail("Level feat was not stored separately from the origin feat.")
		return
	if OriginFeatSystem.new().initiative_proficiency_bonus(feat_hero) != feat_hero.get_proficiency_bonus():
		_fail("Alert selected at level does not affect initiative.")
		return

	state.call("new_game")
	var legacy := _fighter(5, ProgressionSystem.total_experience_for_level(5))
	legacy.subclass_id = ""
	legacy.subclass_name = ""
	legacy.level_choice_history.clear()
	state.set("player_character", legacy)
	if not levels.ensure_migrated(legacy, state):
		_fail("Legacy choice state was not migrated.")
		return
	if legacy.subclass_id != "guardian_vanguard":
		_fail("Legacy fighter did not receive the documented subclass fallback.")
		return
	if str((legacy.level_choice_history.get("4:level_4_advancement", {}) as Dictionary).get("mode", "")) != LevelChoiceSystem.LEGACY_PRESERVED:
		_fail("Legacy level 4 advancement was not marked as preserved.")
		return

	state.call("new_game")
	var pending := _fighter(2, ProgressionSystem.total_experience_for_level(3))
	state.set("player_character", pending)
	state.call("set_flag", LevelUpSystem.TRANSACTION_FLAG, {
		"version": LevelUpSystem.TRANSACTION_VERSION,
		"class_id": "fighter",
		"from_level": 2,
		"target_level": 3,
		"experience_snapshot": pending.experience,
		"hp_mode": LevelUpSystem.HP_MODE_ROLL,
		"hp_roll": 4,
		"hp_gain": 6,
		"new_class_spell_id": "",
		"replace_class_spell_old_id": "",
		"replace_class_spell_new_id": "",
		"replace_magic_cantrip_old_id": "",
		"replace_magic_cantrip_new_id": "",
		"replace_magic_spell_old_id": "",
		"replace_magic_spell_new_id": ""
	})
	levels.ensure_migrated(pending, state)
	var migrated_transaction: Dictionary = levels.get_transaction(state)
	if int(migrated_transaction.get("hp_roll", 0)) != 4:
		_fail("Pending HP roll was lost during choice migration.")
		return
	if not migrated_transaction.has("level_choices"):
		_fail("Pending transaction did not receive the universal choice container.")
		return

	print("Universal subclass, advancement, feat, serialization and migration tests passed.")
	quit(0)


func _fighter(level_value: int, experience_value: int) -> PlayerCharacter:
	var character := PlayerCharacter.new()
	character.character_name = "Испытатель"
	character.character_class_id = "fighter"
	character.character_class_name = "Воин"
	character.race_id = "human"
	character.race_name = "Человек"
	character.level = level_value
	character.experience = experience_value
	character.maximum_health = 12
	character.current_health = 12
	character.hit_die_size = 10
	character.hit_dice_maximum = maxi(level_value, 1)
	character.hit_dice_current = character.hit_dice_maximum
	return character
