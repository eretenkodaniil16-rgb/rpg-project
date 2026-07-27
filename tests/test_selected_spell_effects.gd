extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is required for selected spell effects.")
		return
	state.call("new_game")
	var selections := SpellSelectionSystem.new()
	var spells := SpellcastingSystem.new()
	var abilities := ClassAbilitySystem.new()
	var classes := ClassDataSystem.new()

	var cleric := PlayerCharacter.new()
	cleric.character_class_id = "cleric"
	cleric.abilities["wisdom"] = 16
	cleric.base_abilities["wisdom"] = 16
	cleric.abilities["dexterity"] = 10
	cleric.base_abilities["dexterity"] = 10
	if not bool(selections.apply_sources(cleric, selections.create_default_sources("cleric", "")).get("success", false)):
		_fail("Default Cleric spell choices could not be applied.")
		return
	spells.ensure_character(cleric, true)
	state.set("player_character", cleric)
	var armor_class_before: int = classes.get_armor_class(cleric)
	var shield_result: Dictionary = abilities.use_self_ability(
		cleric,
		spells.get_spell_definition("shield_of_faith")
	)
	if not bool(shield_result.get("success", false)):
		_fail("Selected Shield of Faith could not be cast.")
		return
	if classes.get_armor_class(cleric) != armor_class_before + 2:
		_fail("Shield of Faith did not add exactly +2 Armor Class.")
		return
	if spells.get_concentration_spell_id(cleric) != "shield_of_faith":
		_fail("Shield of Faith did not start concentration.")
		return
	var guidance_result: Dictionary = abilities.use_self_ability(
		cleric,
		spells.get_spell_definition("guidance")
	)
	if not bool(guidance_result.get("success", false)) or not spells.has_guidance(cleric):
		_fail("Selected Guidance could not be activated.")
		return
	if spells.get_concentration_spell_id(cleric) != "guidance":
		_fail("Guidance did not replace the previous concentration spell.")
		return
	if classes.get_armor_class(cleric) != armor_class_before:
		_fail("Replacing Shield of Faith concentration did not remove its Armor Class bonus.")
		return

	var druid := PlayerCharacter.new()
	druid.character_class_id = "druid"
	druid.abilities["wisdom"] = 16
	druid.base_abilities["wisdom"] = 16
	var druid_sources: Dictionary = selections.create_default_sources("druid", "")
	var druid_source: Dictionary = druid_sources.get(SpellSelectionSystem.SOURCE_CLASS, {}) as Dictionary
	var druid_cantrips: Array = druid_source.get(SpellSelectionSystem.CANTRIP_IDS_KEY, []) as Array
	druid_cantrips[0] = "starry_wisp"
	druid_source[SpellSelectionSystem.CANTRIP_IDS_KEY] = druid_cantrips
	druid_sources[SpellSelectionSystem.SOURCE_CLASS] = druid_source
	if not bool(selections.apply_sources(druid, druid_sources).get("success", false)):
		_fail("Druid choices with Starry Wisp could not be applied.")
		return
	spells.ensure_character(druid, true)
	if not spells.is_prepared(druid, "speak_with_animals"):
		_fail("Druid did not retain always-prepared Speak with Animals.")
		return

	var failed_target := Node.new()
	failed_target.name = "FailedSaveTarget"
	root.add_child(failed_target)
	var successful_target := Node.new()
	successful_target.name = "SuccessfulSaveTarget"
	root.add_child(successful_target)
	var thunderwave_result: Dictionary = abilities.perform_area_spell(
		druid,
		spells.get_spell_definition("thunderwave"),
		[
			{
				"target": failed_target,
				"target_name": "Провал",
				"defender_state": CombatantState.new(),
				"save_rolls_override": [1]
			},
			{
				"target": successful_target,
				"target_name": "Успех",
				"defender_state": CombatantState.new(),
				"save_rolls_override": [20]
			}
		],
		{},
		[4, 4]
	)
	if not bool(thunderwave_result.get("success", false)):
		_fail("Selected Thunderwave could not be resolved.")
		return
	var resolutions: Array = thunderwave_result.get("resolutions", []) as Array
	if resolutions.size() != 2:
		_fail("Thunderwave did not resolve both targets.")
		return
	var failed_resolution: Dictionary = resolutions[0] as Dictionary
	var successful_resolution: Dictionary = resolutions[1] as Dictionary
	var failed_attack: AttackResult = failed_resolution.get("result") as AttackResult
	var successful_attack: AttackResult = successful_resolution.get("result") as AttackResult
	if int(failed_resolution.get("push_feet", 0)) != 10 or failed_attack.damage != 8:
		_fail("Failed Thunderwave save did not preserve full damage and ten-foot push metadata.")
		return
	if int(successful_resolution.get("push_feet", -1)) != 0 or successful_attack.damage != 4:
		_fail("Successful Thunderwave save did not preserve half damage and prevent the push.")
		return

	var invisible_target := CombatantState.new()
	invisible_target.add_condition("invisible")
	var starry_result: AttackResult = abilities.perform_offensive_ability(
		druid,
		spells.get_spell_definition("starry_wisp"),
		12,
		10,
		[5],
		{"distance_feet": 30, "defender_state": invisible_target}
	)
	if not starry_result.hit or starry_result.damage != 5 or invisible_target.has_condition("invisible"):
		_fail("Starry Wisp did not damage and reveal an invisible target on hit.")
		return

	var sorcerer := PlayerCharacter.new()
	sorcerer.character_class_id = "sorcerer"
	sorcerer.abilities["charisma"] = 16
	sorcerer.base_abilities["charisma"] = 16
	var sorcerer_sources: Dictionary = selections.create_default_sources("sorcerer", "")
	var sorcerer_source: Dictionary = sorcerer_sources.get(SpellSelectionSystem.SOURCE_CLASS, {}) as Dictionary
	var sorcerer_spells: Array = sorcerer_source.get(SpellSelectionSystem.SPELL_IDS_KEY, []) as Array
	var sorcerer_prepared: Array = sorcerer_source.get(SpellSelectionSystem.PREPARED_IDS_KEY, []) as Array
	sorcerer_spells[0] = "ray_of_sickness"
	sorcerer_prepared[0] = "ray_of_sickness"
	sorcerer_source[SpellSelectionSystem.SPELL_IDS_KEY] = sorcerer_spells
	sorcerer_source[SpellSelectionSystem.PREPARED_IDS_KEY] = sorcerer_prepared
	sorcerer_sources[SpellSelectionSystem.SOURCE_CLASS] = sorcerer_source
	if not bool(selections.apply_sources(sorcerer, sorcerer_sources).get("success", false)):
		_fail("Sorcerer choices with Ray of Sickness could not be applied.")
		return
	spells.ensure_character(sorcerer, true)
	var poisoned_target := CombatantState.new()
	var ray_result: AttackResult = abilities.perform_offensive_ability(
		sorcerer,
		spells.get_spell_definition("ray_of_sickness"),
		12,
		10,
		[4, 4],
		{"distance_feet": 30, "defender_state": poisoned_target}
	)
	if not ray_result.hit or ray_result.damage != 8 or not poisoned_target.has_condition("poisoned"):
		_fail("Ray of Sickness did not deal 2d8 poison damage and apply Poisoned on hit.")
		return

	print("Selected spell effects, concentration replacement, area push metadata and condition riders passed.")
	failed_target.queue_free()
	successful_target.queue_free()
	quit(0)
