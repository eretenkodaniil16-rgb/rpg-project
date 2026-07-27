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
	await create_timer(35.0).timeout
	if not _finished:
		_fail("Readied-action reaction prompt smoke test timed out after 35 seconds.")


func _wait_for_prompt(prompt: ReactionChoicePrompt) -> bool:
	for _frame: int in range(180):
		if prompt != null and prompt.is_waiting_for_decision() and prompt.is_visible_in_tree():
			return true
		await process_frame
	return false


func _wait_for_prompt_closed(prompt: ReactionChoicePrompt) -> bool:
	for _frame: int in range(240):
		if prompt != null and not prompt.is_waiting_for_decision() and not prompt.visible:
			return true
		await process_frame
	return false


func _run() -> void:
	var game_state: Node = root.get_node_or_null("GameState")
	if game_state == null:
		_fail("GameState autoload was unavailable.")
		return
	game_state.call("new_game")
	var fighter := PlayerCharacter.new()
	fighter.character_name = "Дозорный"
	fighter.character_class_id = "fighter"
	fighter.character_class_name = "Воин"
	fighter.race_name = "Человек"
	fighter.level = 1
	fighter.maximum_health = 30
	fighter.current_health = 30
	fighter.abilities["strength"] = 18
	fighter.base_abilities["strength"] = 18
	fighter.abilities["dexterity"] = 14
	fighter.base_abilities["dexterity"] = 14
	game_state.set("player_character", fighter)

	var game_scene: PackedScene = load("res://scenes/game/game.tscn") as PackedScene
	if game_scene == null:
		_fail("Game scene could not be loaded.")
		return
	var game: Node = game_scene.instantiate()
	root.add_child(game)
	for _frame: int in range(12):
		await process_frame

	var prompt: ReactionChoicePrompt = game.call("get_reaction_choice_prompt_for_testing") as ReactionChoicePrompt
	var construct: RuneTrainingConstruct = game.call("get_rune_training_construct_for_testing") as RuneTrainingConstruct
	var player: Node2D = get_first_node_in_group("player") as Node2D
	var turns: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	var player_state: CombatantState = game.call("get_player_combat_state") as CombatantState
	if prompt == null or construct == null or player == null or turns == null or player_state == null:
		_fail("Reaction prompt, construct, player, turn system, or player combat state was unavailable.")
		return

	construct.global_position = player.global_position + Vector2.RIGHT * DistanceSystem.feet_to_pixels(5)
	construct.enter_combat_hostile()
	turns.start_combat(
		player,
		[construct],
		fighter.get_ability_modifier("dexterity"),
		{player.get_instance_id(): 20, construct.get_instance_id(): 1}
	)
	player_state.readied_attack = true
	game.call_deferred("_trigger_readied_attack_if_possible", construct)
	if not await _wait_for_prompt(prompt):
		_fail("A matching readied-action trigger did not open the reaction list.")
		return
	if prompt.get_option_count() != 1 or ReactionOpportunitySystem.OPTION_READIED_ATTACK not in prompt.get_option_ids():
		_fail("Readied-action reaction list did not contain the prepared attack.")
		return
	prompt.skip_reaction()
	if not await _wait_for_prompt_closed(prompt):
		_fail("Readied-action reaction list did not close after Skip.")
		return
	if not turns.has_reaction(player) or not player_state.readied_attack:
		_fail("Skipping a readied-action trigger consumed the reaction or erased the prepared action.")
		return

	game.call_deferred("_trigger_readied_attack_if_possible", construct)
	if not await _wait_for_prompt(prompt):
		_fail("The saved prepared action was not offered on the next matching trigger.")
		return
	prompt.choose_option(ReactionOpportunitySystem.OPTION_READIED_ATTACK)
	if not await _wait_for_prompt_closed(prompt):
		_fail("Readied-action reaction list did not close after choosing the attack.")
		return
	await create_timer(0.5).timeout
	if turns.has_reaction(player):
		_fail("Executing the prepared attack did not spend the player's reaction.")
		return
	if player_state.readied_attack:
		_fail("Executing the prepared attack did not clear the prepared action.")
		return

	_finished = true
	game.queue_free()
	print("Readied-action reaction prompt preserves reaction and preparation on Skip, then spends both correctly when selected.")
	quit(0)
