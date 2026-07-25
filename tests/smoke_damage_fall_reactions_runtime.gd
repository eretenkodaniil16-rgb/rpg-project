extends SceneTree

var _finished: bool = false


func _init() -> void:
	call_deferred("_run")
	call_deferred("_watchdog")


func _fail(message: String) -> void:
	_finished = true
	push_error(message)
	quit(1)


func _watchdog() -> void:
	await create_timer(60.0).timeout
	if not _finished:
		_fail("Damage and fall reaction runtime smoke test timed out after 60 seconds.")


func _wait_for_prompt(prompt: ReactionChoicePrompt) -> bool:
	for _frame: int in range(360):
		if prompt != null and prompt.is_waiting_for_decision() and prompt.is_visible_in_tree():
			return true
		await process_frame
	return false


func _wait_for_prompt_closed(prompt: ReactionChoicePrompt) -> bool:
	for _frame: int in range(360):
		if prompt != null and not prompt.is_waiting_for_decision() and not prompt.visible:
			return true
		await process_frame
	return false


func _make_warlock() -> PlayerCharacter:
	var character := PlayerCharacter.new()
	character.character_name = "Мстительный колдун"
	character.character_class_id = "warlock"
	character.character_class_name = "Колдун"
	character.race_name = "Человек"
	character.level = 1
	character.maximum_health = 60
	character.current_health = 60
	character.abilities["charisma"] = 18
	character.base_abilities["charisma"] = 18
	character.abilities["dexterity"] = 14
	character.base_abilities["dexterity"] = 14
	character.starter_loadout_granted = true
	var spellcasting := SpellcastingSystem.new()
	spellcasting.ensure_character(character, true)
	character.class_resources[SpellcastingSystem.PREPARED_SPELLS_STATE_KEY] = [DamageFallReactionSystem.HELLISH_REBUKE_SPELL_ID]
	return character


func _make_monk() -> PlayerCharacter:
	var character := PlayerCharacter.new()
	character.character_name = "Монах над пропастью"
	character.character_class_id = "monk"
	character.character_class_name = "Монах"
	character.race_name = "Человек"
	character.level = 4
	character.maximum_health = 50
	character.current_health = 50
	character.abilities["dexterity"] = 18
	character.base_abilities["dexterity"] = 18
	character.abilities["wisdom"] = 16
	character.base_abilities["wisdom"] = 16
	character.starter_loadout_granted = true
	return character


func _instantiate_game(character: PlayerCharacter) -> Dictionary:
	var game_state: Node = root.get_node_or_null("GameState")
	if game_state == null:
		return {}
	game_state.call("new_game")
	game_state.set("player_character", character)
	var game_scene: PackedScene = load("res://scenes/game/game.tscn") as PackedScene
	if game_scene == null:
		return {}
	var game: Node = game_scene.instantiate()
	root.add_child(game)
	for _frame: int in range(18):
		await process_frame
	return {
		"game": game,
		"prompt": game.call("get_reaction_choice_prompt_for_testing") as ReactionChoicePrompt,
		"construct": game.call("get_rune_training_construct_for_testing") as RuneTrainingConstruct,
		"player": get_first_node_in_group("player") as Node2D,
		"turns": game.get("_turn_system") as TurnBasedCombatSystem
	}


func _run() -> void:
	var warlock: PlayerCharacter = _make_warlock()
	var first: Dictionary = await _instantiate_game(warlock)
	var game: Node = first.get("game") as Node
	var prompt: ReactionChoicePrompt = first.get("prompt") as ReactionChoicePrompt
	var construct: RuneTrainingConstruct = first.get("construct") as RuneTrainingConstruct
	var player: Node2D = first.get("player") as Node2D
	var turns: TurnBasedCombatSystem = first.get("turns") as TurnBasedCombatSystem
	if game == null or prompt == null or construct == null or player == null or turns == null:
		_fail("Warlock game, prompt, construct, player, or turn system was unavailable.")
		return
	construct.global_position = player.global_position + Vector2.RIGHT * DistanceSystem.feet_to_pixels(5)
	construct.enter_combat_hostile()
	turns.start_combat(
		player,
		[construct],
		warlock.get_ability_modifier("dexterity"),
		{player.get_instance_id(): 20, construct.get_instance_id(): 1}
	)
	game.call("set_hellish_rebuke_testing_overrides", [1], [10, 10])
	var hp_before_damage: int = warlock.current_health
	var construct_hp_before: int = construct.get_current_health()
	var slots_before: int = warlock.get_resource("pact_slots_1")
	game.call_deferred("resolve_npc_attack_for_testing", construct, 18, 12, 8, "slashing")
	if not await _wait_for_prompt(prompt):
		_fail("Creature damage did not open the universal reaction prompt for Hellish Rebuke.")
		return
	if prompt.get_option_ids() != [ReactionOpportunitySystem.OPTION_HELLISH_REBUKE]:
		_fail("The post-damage prompt did not contain exactly Hellish Rebuke.")
		return
	if warlock.current_health != hp_before_damage - 8:
		_fail("Hellish Rebuke prompt opened before the triggering damage was applied.")
		return
	if construct.get_current_health() != construct_hp_before:
		_fail("Hellish Rebuke damaged the source before the player selected the reaction.")
		return
	prompt.choose_option(ReactionOpportunitySystem.OPTION_HELLISH_REBUKE)
	if not await _wait_for_prompt_closed(prompt):
		_fail("Hellish Rebuke prompt did not close after selection.")
		return
	await create_timer(0.2).timeout
	if construct.get_current_health() != construct_hp_before - 20:
		_fail("Hellish Rebuke did not deal the deterministic 20 fire damage after selection.")
		return
	if warlock.get_resource("pact_slots_1") != slots_before - 1:
		_fail("Hellish Rebuke did not spend exactly one pact slot.")
		return
	if turns.has_reaction(player):
		_fail("Hellish Rebuke did not consume the player's reaction.")
		return
	game.queue_free()
	for _frame: int in range(6):
		await process_frame

	var monk: PlayerCharacter = _make_monk()
	var second: Dictionary = await _instantiate_game(monk)
	game = second.get("game") as Node
	prompt = second.get("prompt") as ReactionChoicePrompt
	construct = second.get("construct") as RuneTrainingConstruct
	player = second.get("player") as Node2D
	turns = second.get("turns") as TurnBasedCombatSystem
	if game == null or prompt == null or construct == null or player == null or turns == null:
		_fail("Monk game, prompt, construct, player, or turn system was unavailable.")
		return
	construct.global_position = player.global_position + Vector2.RIGHT * DistanceSystem.feet_to_pixels(10)
	turns.start_combat(
		player,
		[construct],
		monk.get_ability_modifier("dexterity"),
		{player.get_instance_id(): 20, construct.get_instance_id(): 1}
	)
	var hp_before_fall: int = monk.current_health
	game.call_deferred("resolve_player_fall_for_testing", 40, [6, 6, 6, 6])
	if not await _wait_for_prompt(prompt):
		_fail("Potential falling damage did not open the universal reaction prompt for Slow Fall.")
		return
	if prompt.get_option_ids() != [ReactionOpportunitySystem.OPTION_SLOW_FALL]:
		_fail("The fall prompt did not contain exactly Slow Fall.")
		return
	if monk.current_health != hp_before_fall:
		_fail("Falling damage was applied before the Slow Fall decision.")
		return
	prompt.choose_option(ReactionOpportunitySystem.OPTION_SLOW_FALL)
	if not await _wait_for_prompt_closed(prompt):
		_fail("Slow Fall prompt did not close after selection.")
		return
	await create_timer(0.2).timeout
	if monk.current_health != hp_before_fall - 4:
		_fail("Level-four Slow Fall did not reduce deterministic 24 falling damage to 4.")
		return
	if turns.has_reaction(player):
		_fail("Slow Fall did not consume the player's reaction.")
		return
	var player_state: CombatantState = game.get("_player_combat_state") as CombatantState
	if player_state == null or not player_state.has_condition("prone"):
		_fail("The Monk did not land prone after still taking falling damage.")
		return

	_finished = true
	game.queue_free()
	print("Hellish Rebuke triggers after HP loss and retaliates through the shared prompt; Slow Fall pauses before landing and applies 5x-level reduction.")
	quit(0)
