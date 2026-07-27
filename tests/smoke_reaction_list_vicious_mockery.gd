extends SceneTree

var _finished: bool = false
var _selected_option_id: String = ""


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
		_fail("Reaction list and Vicious Mockery runtime smoke test timed out after 45 seconds.")


func _wait_for_prompt(prompt: ReactionChoicePrompt) -> bool:
	for _frame: int in range(240):
		if prompt != null and prompt.is_waiting_for_decision() and prompt.is_visible_in_tree():
			return true
		await process_frame
	return false


func _capture_choice(option_id: String) -> void:
	_selected_option_id = option_id


func _run() -> void:
	var game_state: Node = root.get_node_or_null("GameState")
	if game_state == null:
		_fail("GameState autoload was unavailable.")
		return
	game_state.call("new_game")

	var bard := PlayerCharacter.new()
	bard.character_name = "Остроязыкий"
	bard.character_class_id = "bard"
	bard.character_class_name = "Бард"
	bard.race_name = "Человек"
	bard.level = 5
	bard.maximum_health = 48
	bard.current_health = 48
	bard.abilities["charisma"] = 18
	bard.base_abilities["charisma"] = 18
	bard.abilities["dexterity"] = 14
	bard.base_abilities["dexterity"] = 14
	bard.starter_loadout_granted = true
	var spellcasting := SpellcastingSystem.new()
	spellcasting.ensure_character(bard, true)
	game_state.set("player_character", bard)

	var game_scene: PackedScene = load("res://scenes/game/game.tscn") as PackedScene
	if game_scene == null:
		_fail("Game scene could not be loaded.")
		return
	var game: Node = game_scene.instantiate()
	root.add_child(game)
	for _frame: int in range(12):
		await process_frame

	var prompt: ReactionChoicePrompt = game.call("get_reaction_choice_prompt_for_testing") as ReactionChoicePrompt
	var mockery_button: Button = game.call("get_vicious_mockery_button_for_testing") as Button
	var construct: RuneTrainingConstruct = game.call("get_rune_training_construct_for_testing") as RuneTrainingConstruct
	var player: Node2D = get_first_node_in_group("player") as Node2D
	if prompt == null or mockery_button == null or construct == null or player == null:
		_fail("Reaction prompt, Vicious Mockery control, construct, or player was not created.")
		return
	if mockery_button.text != "ЗЛАЯ НАСМЕШКА" or not mockery_button.visible:
		_fail("Bard did not receive the mobile Vicious Mockery control.")
		return
	if prompt.option_selected.is_connected(_capture_choice):
		prompt.option_selected.disconnect(_capture_choice)
	prompt.option_selected.connect(_capture_choice)

	var synthetic_options: Array[Dictionary] = [
		{
			"id": ReactionOpportunitySystem.OPTION_READIED_ATTACK,
			"label": "ВЫПОЛНИТЬ ПОДГОТОВЛЕННОЕ",
			"description": "Синтетический вариант подготовленного действия.",
			"resource_text": "Реакция",
			"priority": 90
		},
		{
			"id": ReactionOpportunitySystem.OPTION_OPPORTUNITY_ATTACK,
			"label": "АТАКА ПО ВОЗМОЖНОСТИ",
			"description": "Синтетический вариант атаки по возможности.",
			"resource_text": "Реакция",
			"priority": 80
		}
	]
	prompt.call_deferred(
		"request_reaction",
		"ВОЗМОЖНОСТЬ РЕАКЦИИ",
		"Одновременно доступны две законные реакции.",
		synthetic_options
	)
	if not await _wait_for_prompt(prompt):
		_fail("Generic reaction list did not open for multiple available actions.")
		return
	if prompt.get_option_count() != 2:
		_fail("Generic reaction list did not display every available action.")
		return
	if ReactionOpportunitySystem.OPTION_READIED_ATTACK not in prompt.get_option_ids() or ReactionOpportunitySystem.OPTION_OPPORTUNITY_ATTACK not in prompt.get_option_ids():
		_fail("Generic reaction list lost one of the available action identifiers.")
		return
	prompt.choose_option(ReactionOpportunitySystem.OPTION_OPPORTUNITY_ATTACK)
	await process_frame
	if _selected_option_id != ReactionOpportunitySystem.OPTION_OPPORTUNITY_ATTACK:
		_fail("Generic reaction list returned the wrong selected action.")
		return
	if prompt.visible or prompt.is_waiting_for_decision():
		_fail("Generic reaction list remained open after a selection.")
		return

	construct.global_position = player.global_position + Vector2.RIGHT * DistanceSystem.feet_to_pixels(5)
	construct.enter_combat_hostile()
	game.call("apply_vicious_mockery_effect_for_testing", construct)
	if not bool(game.call("has_vicious_mockery_effect_for_testing", construct)):
		_fail("Vicious Mockery disadvantage rider was not stored on the target.")
		return
	game.call("resolve_npc_attack", construct, 3, 6, 1, "force")
	for _frame: int in range(3):
		await process_frame
	if bool(game.call("has_vicious_mockery_effect_for_testing", construct)):
		_fail("Vicious Mockery disadvantage was not removed after the next attack roll.")
		return

	_finished = true
	game.queue_free()
	print("Bard Vicious Mockery control, multi-option reaction list, selected-action return, and next-attack disadvantage runtime smoke test passed.")
	quit(0)
