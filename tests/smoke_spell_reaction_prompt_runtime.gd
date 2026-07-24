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
		_fail("Counterspell runtime prompt smoke test timed out after 45 seconds.")


func _wait_for_prompt(prompt: SpellReactionPrompt) -> bool:
	for _frame: int in range(180):
		if prompt != null and prompt.is_waiting_for_decision() and prompt.is_visible_in_tree():
			return true
		await process_frame
	return false


func _start_enemy_turn(game: Node, player: Node, construct: RuneTrainingConstruct) -> void:
	var turns: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	turns.start_combat(
		player,
		[construct],
		0,
		{player.get_instance_id(): 1, construct.get_instance_id(): 20}
	)
	construct.enter_combat_hostile()
	game.call("_begin_current_turn")


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
	wizard.maximum_health = 40
	wizard.current_health = 40
	wizard.abilities["intelligence"] = 18
	wizard.base_abilities["intelligence"] = 18
	wizard.abilities["constitution"] = 14
	wizard.base_abilities["constitution"] = 14
	var spells := SpellcastingSystem.new()
	spells.ensure_character(wizard, false)
	var preparation: Dictionary = spells.prepare_spell(wizard, "counterspell")
	if not bool(preparation.get("success", false)):
		_fail("Counterspell could not be prepared for the runtime smoke test.")
		return
	game_state.set("player_character", wizard)

	var game_scene: PackedScene = load("res://scenes/game/game.tscn") as PackedScene
	if game_scene == null:
		_fail("Game scene could not be loaded.")
		return
	var game: Node = game_scene.instantiate()
	root.add_child(game)
	for _frame: int in range(10):
		await process_frame

	var prompt: SpellReactionPrompt = game.call("get_spell_reaction_prompt") as SpellReactionPrompt
	var construct: RuneTrainingConstruct = game.call("get_rune_training_construct") as RuneTrainingConstruct
	var player: Node = get_first_node_in_group("player")
	if prompt == null or construct == null or player == null:
		_fail("Counterspell prompt, rune construct, or player was not created by the game runtime.")
		return
	if construct.get_combat_spell_id() != "burning_hands":
		_fail("Rune construct did not expose its training spell.")
		return

	construct.counterspell_save_roll_override = 1
	var player_slot_before: int = wizard.get_resource("spell_slots_3")
	var enemy_slot_before: int = construct.spell_slots_level_1
	var hp_before: int = wizard.current_health
	_start_enemy_turn(game, player, construct)
	if not await _wait_for_prompt(prompt):
		_fail("Enemy casting did not pause on the Counterspell prompt.")
		return
	prompt.choose_counterspell()
	await create_timer(1.2).timeout
	if prompt.visible or prompt.is_waiting_for_decision():
		_fail("Counterspell prompt remained open after the decision.")
		return
	if wizard.get_resource("spell_slots_3") != player_slot_before - 1:
		_fail("Runtime Counterspell did not consume exactly one level-three player slot.")
		return
	if construct.spell_slots_level_1 != enemy_slot_before:
		_fail("A countered enemy spell incorrectly consumed its original slot.")
		return
	if wizard.current_health != hp_before:
		_fail("A successfully countered enemy spell still damaged the player.")
		return

	game.call("_stop_turn_based_combat", "Сброс smoke-test.")
	await process_frame
	construct.reset_for_testing()
	wizard.current_health = wizard.maximum_health
	construct.counterspell_save_roll_override = 20
	var skip_player_slot_before: int = wizard.get_resource("spell_slots_3")
	var skip_enemy_slot_before: int = construct.spell_slots_level_1
	var skip_hp_before: int = wizard.current_health
	_start_enemy_turn(game, player, construct)
	if not await _wait_for_prompt(prompt):
		_fail("Second enemy casting did not reopen the Counterspell prompt.")
		return
	prompt.skip_reaction()
	await create_timer(1.2).timeout
	if wizard.get_resource("spell_slots_3") != skip_player_slot_before:
		_fail("Skipping Counterspell consumed a player spell slot.")
		return
	if construct.spell_slots_level_1 != skip_enemy_slot_before - 1:
		_fail("Skipping the reaction did not consume the enemy spell slot.")
		return
	if wizard.current_health >= skip_hp_before:
		_fail("The enemy spell did not resolve after Counterspell was skipped.")
		return

	_finished = true
	game.queue_free()
	print("Counterspell runtime prompt, paused enemy casting, original-slot preservation, and skip resolution smoke test passed.")
	quit(0)
