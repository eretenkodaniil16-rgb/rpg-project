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
	await create_timer(45.0).timeout
	if not _finished:
		_fail("Spell reaction prompt smoke test timed out after 45 seconds.")


func _wait_for_prompt(prompt: SpellReactionPrompt) -> bool:
	for _frame: int in range(240):
		if prompt != null and prompt.is_waiting_for_decision() and prompt.is_visible_in_tree():
			return true
		await process_frame
	return false


func _wait_for_enemy_turn(game: Node, expected_running: bool) -> bool:
	for _frame: int in range(300):
		if bool(game.get("_enemy_turn_running")) == expected_running:
			return true
		await process_frame
	return false


func _run() -> void:
	var game_state: Node = root.get_node_or_null("GameState")
	if game_state == null:
		_fail("GameState autoload was unavailable.")
		return
	game_state.call("new_game")

	var wizard := PlayerCharacter.new()
	wizard.character_name = "Контрмаг"
	wizard.character_class_id = "wizard"
	wizard.character_class_name = "Волшебник"
	wizard.race_name = "Человек"
	wizard.level = 5
	wizard.maximum_health = 60
	wizard.current_health = 60
	wizard.abilities["intelligence"] = 18
	wizard.base_abilities["intelligence"] = 18
	wizard.abilities["dexterity"] = 14
	wizard.base_abilities["dexterity"] = 14
	wizard.starter_loadout_granted = true
	var spellcasting := SpellcastingSystem.new()
	spellcasting.ensure_character(wizard, true)
	var prepared: Dictionary = spellcasting.prepare_spell(wizard, "counterspell")
	if not bool(prepared.get("success", false)) or not spellcasting.is_prepared(wizard, "counterspell"):
		_fail("Level-five Wizard could not prepare Counterspell for the runtime smoke test.")
		return
	game_state.set("player_character", wizard)

	var game_scene: PackedScene = load("res://scenes/game/game.tscn") as PackedScene
	if game_scene == null:
		_fail("Game scene could not be loaded.")
		return
	var game: Node = game_scene.instantiate()
	root.add_child(game)
	for _frame: int in range(12):
		await process_frame

	var prompt: SpellReactionPrompt = game.call("get_spell_reaction_prompt_for_testing") as SpellReactionPrompt
	var construct: RuneTrainingConstruct = game.call("get_rune_training_construct_for_testing") as RuneTrainingConstruct
	var player: Node2D = get_first_node_in_group("player") as Node2D
	var turns: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	if prompt == null or construct == null or player == null or turns == null:
		_fail("Reaction prompt, rune construct, player, or turn system was not constructed.")
		return
	var cast_button: Button = prompt.find_child("CounterspellButton", true, false) as Button
	var skip_button: Button = prompt.find_child("SkipReactionButton", true, false) as Button
	if cast_button == null or skip_button == null:
		_fail("Mobile Counterspell and Skip buttons were not present in the runtime prompt.")
		return

	construct.global_position = player.global_position + Vector2.RIGHT * DistanceSystem.feet_to_pixels(10)
	construct.enter_combat_hostile()
	turns.start_combat(
		player,
		[construct],
		wizard.get_ability_modifier("dexterity"),
		{player.get_instance_id(): 1, construct.get_instance_id(): 20}
	)
	var enemy_slots_before_skip: int = construct.get_combat_spell_slot_count(1)
	var wizard_slots_before_skip: int = wizard.get_resource("spell_slots_3")
	var hp_before_skip: int = wizard.current_health
	game.call_deferred("_run_enemy_turn", construct)
	var first_prompt_opened: bool = await _wait_for_prompt(prompt)
	if not first_prompt_opened:
		_fail("Enemy spellcasting did not open the Counterspell decision prompt.")
		return
	if cast_button.text != "КОНТРЗАКЛИНАНИЕ" or skip_button.text != "ПРОПУСТИТЬ":
		_fail("Reaction prompt mobile button labels were incorrect.")
		return
	await create_timer(0.2).timeout
	if construct.get_combat_spell_slot_count(1) != enemy_slots_before_skip or wizard.current_health != hp_before_skip:
		_fail("Enemy casting was not paused before the reaction decision.")
		return
	prompt.skip_reaction()
	var first_turn_finished: bool = await _wait_for_enemy_turn(game, false)
	if not first_turn_finished:
		_fail("Enemy turn did not resume after skipping Counterspell.")
		return
	if construct.get_combat_spell_slot_count(1) != enemy_slots_before_skip - 1:
		_fail("Skipping Counterspell did not allow the original enemy slot to be expended exactly once.")
		return
	if wizard.get_resource("spell_slots_3") != wizard_slots_before_skip:
		_fail("Skipping the reaction incorrectly spent a Counterspell slot.")
		return
	if wizard.current_health >= hp_before_skip:
		_fail("Skipping Counterspell did not allow Burning Hands to resolve against the player.")
		return
	if not turns.has_reaction(player):
		_fail("Skipping Counterspell incorrectly consumed the player's reaction.")
		return

	turns.force_current_actor_for_testing(construct)
	construct.counterspell_save_roll_override = 1
	var enemy_slots_before_counter: int = construct.get_combat_spell_slot_count(1)
	var wizard_slots_before_counter: int = wizard.get_resource("spell_slots_3")
	var hp_before_counter: int = wizard.current_health
	game.call_deferred("_run_enemy_turn", construct)
	var second_prompt_opened: bool = await _wait_for_prompt(prompt)
	if not second_prompt_opened:
		_fail("Second enemy casting did not reopen the Counterspell decision prompt.")
		return
	await create_timer(0.2).timeout
	if construct.get_combat_spell_slot_count(1) != enemy_slots_before_counter or wizard.current_health != hp_before_counter:
		_fail("Second enemy casting advanced before the player answered the reaction prompt.")
		return
	prompt.choose_counterspell()
	var second_turn_finished: bool = await _wait_for_enemy_turn(game, false)
	if not second_turn_finished:
		_fail("Enemy turn did not finish after resolving Counterspell.")
		return
	if construct.get_combat_spell_slot_count(1) != enemy_slots_before_counter:
		_fail("A countered enemy spell incorrectly spent its original spell slot.")
		return
	if wizard.get_resource("spell_slots_3") != wizard_slots_before_counter - 1:
		_fail("Counterspell did not spend exactly one level-three player slot.")
		return
	if wizard.current_health != hp_before_counter:
		_fail("A countered Burning Hands still damaged the player.")
		return
	if turns.current_actor() != player or not turns.has_reaction(player):
		_fail("The enemy turn did not advance to the player or reset the reaction at the start of that turn.")
		return
	if prompt.visible or prompt.is_waiting_for_decision():
		_fail("Reaction prompt remained open after Counterspell resolved.")
		return

	_finished = true
	game.queue_free()
	print("Mobile Counterspell prompt pauses enemy casting, Skip resumes it, Counterspell preserves the enemy slot, and the reaction resets on the player's next turn.")
	quit(0)
