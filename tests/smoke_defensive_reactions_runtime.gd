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
	await create_timer(50.0).timeout
	if not _finished:
		_fail("Defensive reaction runtime smoke test timed out after 50 seconds.")


func _wait_for_prompt(prompt: ReactionChoicePrompt) -> bool:
	for _frame: int in range(300):
		if prompt != null and prompt.is_waiting_for_decision() and prompt.is_visible_in_tree():
			return true
		await process_frame
	return false


func _wait_for_prompt_closed(prompt: ReactionChoicePrompt) -> bool:
	for _frame: int in range(300):
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

	var wizard := PlayerCharacter.new()
	wizard.character_name = "Реактивный защитник"
	wizard.character_class_id = "wizard"
	wizard.character_class_name = "Волшебник"
	wizard.race_name = "Человек"
	wizard.level = 3
	wizard.maximum_health = 60
	wizard.current_health = 60
	wizard.abilities["intelligence"] = 18
	wizard.base_abilities["intelligence"] = 18
	wizard.abilities["dexterity"] = 14
	wizard.base_abilities["dexterity"] = 14
	wizard.starter_loadout_granted = true
	var spellcasting := SpellcastingSystem.new()
	spellcasting.ensure_character(wizard, true)
	wizard.class_resources[SpellcastingSystem.PREPARED_SPELLS_STATE_KEY] = [
		DefensiveReactionSystem.SHIELD_SPELL_ID,
		DefensiveReactionSystem.ABSORB_ELEMENTS_SPELL_ID
	]
	game_state.set("player_character", wizard)

	var game_scene: PackedScene = load("res://scenes/game/game.tscn") as PackedScene
	if game_scene == null:
		_fail("Game scene could not be loaded.")
		return
	var game: Node = game_scene.instantiate()
	root.add_child(game)
	for _frame: int in range(16):
		await process_frame

	var prompt: ReactionChoicePrompt = game.call("get_reaction_choice_prompt_for_testing") as ReactionChoicePrompt
	var construct: RuneTrainingConstruct = game.call("get_rune_training_construct_for_testing") as RuneTrainingConstruct
	var player: Node2D = get_first_node_in_group("player") as Node2D
	var turns: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	if prompt == null or construct == null or player == null or turns == null:
		_fail("Reaction prompt, construct, player, or turn system was not available.")
		return

	construct.global_position = player.global_position + Vector2.RIGHT * DistanceSystem.feet_to_pixels(5)
	construct.enter_combat_hostile()
	turns.start_combat(
		player,
		[construct],
		wizard.get_ability_modifier("dexterity"),
		{player.get_instance_id(): 1, construct.get_instance_id(): 20}
	)

	var hp_before_shield: int = wizard.current_health
	var slots_before_shield: int = wizard.get_resource("spell_slots_1")
	game.call_deferred("resolve_npc_attack_for_testing", construct, 15, 12, 8, "slashing")
	if not await _wait_for_prompt(prompt):
		_fail("A hit did not open the universal reaction prompt for Shield.")
		return
	if prompt.get_option_ids() != [ReactionOpportunitySystem.OPTION_SHIELD]:
		_fail("The attack-hit prompt did not contain exactly the Shield option.")
		return
	await create_timer(0.15).timeout
	if wizard.current_health != hp_before_shield:
		_fail("Damage was applied before the Shield decision.")
		return
	prompt.choose_option(ReactionOpportunitySystem.OPTION_SHIELD)
	if not await _wait_for_prompt_closed(prompt):
		_fail("Shield prompt did not close after selection.")
		return
	await create_timer(0.15).timeout
	if wizard.current_health != hp_before_shield:
		_fail("Shield failed to turn the triggering hit into a miss.")
		return
	if wizard.get_resource("spell_slots_1") != slots_before_shield - 1:
		_fail("Shield did not spend exactly one level-one slot.")
		return
	if not bool(game.call("is_shield_active_for_testing")) or int(game.call("get_shield_ac_bonus_for_testing")) != 5:
		_fail("Shield did not remain active with +5 AC.")
		return
	if turns.has_reaction(player):
		_fail("Shield did not consume the player's reaction.")
		return

	var hp_before_missile: int = wizard.current_health
	var missile_result: Dictionary = await game.call("resolve_magic_missile_damage_for_testing", 12, construct)
	if not bool(missile_result.get("blocked", false)) or int(missile_result.get("applied", -1)) != 0:
		_fail("An already active Shield did not fully block Magic Missile.")
		return
	if wizard.current_health != hp_before_missile:
		_fail("Magic Missile damaged the player through an active Shield.")
		return

	game.call("_expire_shield_at_start_of_turn")
	turns.force_current_actor_for_testing(player)
	turns.advance_turn()
	if turns.current_actor() != construct or not turns.has_reaction(player):
		_fail("The next enemy turn did not restore the player's reaction.")
		return
	var hp_before_absorb: int = wizard.current_health
	var slots_before_absorb: int = wizard.get_resource("spell_slots_1")
	game.call_deferred("apply_elemental_damage_for_testing", 10, "fire", construct)
	if not await _wait_for_prompt(prompt):
		_fail("Fire damage did not open the universal reaction prompt for Absorb Elements.")
		return
	if prompt.get_option_ids() != [ReactionOpportunitySystem.OPTION_ABSORB_ELEMENTS]:
		_fail("The elemental-damage prompt did not contain exactly Absorb Elements.")
		return
	await create_timer(0.15).timeout
	if wizard.current_health != hp_before_absorb:
		_fail("Elemental damage was applied before the reaction decision.")
		return
	prompt.choose_option(ReactionOpportunitySystem.OPTION_ABSORB_ELEMENTS)
	if not await _wait_for_prompt_closed(prompt):
		_fail("Absorb Elements prompt did not close after selection.")
		return
	await create_timer(0.15).timeout
	if wizard.current_health != hp_before_absorb - 5:
		_fail("Absorb Elements did not halve 10 fire damage to 5.")
		return
	if wizard.get_resource("spell_slots_1") != slots_before_absorb - 1:
		_fail("Absorb Elements did not spend exactly one level-one slot.")
		return
	if str(game.call("get_absorb_resistance_type_for_testing")) != "fire":
		_fail("Absorb Elements did not store fire resistance.")
		return
	if not bool(game.call("is_absorb_bonus_pending_for_testing")):
		_fail("Absorb Elements did not charge its next-turn melee bonus.")
		return
	if turns.has_reaction(player):
		_fail("Absorb Elements did not consume the player's reaction.")
		return

	turns.force_current_actor_for_testing(player)
	game.call("_begin_current_turn")
	if not str(game.call("get_absorb_resistance_type_for_testing")).is_empty():
		_fail("Absorb Elements resistance did not end at the start of the player's next turn.")
		return
	if not bool(game.call("is_absorb_bonus_ready_for_testing")):
		_fail("Absorb Elements bonus was not made ready on the player's next turn.")
		return

	_finished = true
	game.queue_free()
	print("Shield pauses a hit, changes AC, blocks Magic Missile, and Absorb Elements halves elemental damage then charges the next-turn melee bonus.")
	quit(0)
