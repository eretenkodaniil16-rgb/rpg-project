extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const AUTOSAVE_PATH: String = "user://save_slots/autosave.json"
const OPPORTUNITY_OPTION_ID: String = ReactionOpportunitySystem.OPTION_OPPORTUNITY_ATTACK


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	var save_path: String = ProjectSettings.globalize_path(AUTOSAVE_PATH)
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	state.call("new_game")
	state.set("player_character", _make_hero())

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	var game: Node = packed.instantiate() if packed != null else null
	if game == null:
		_fail("Game scene could not be loaded.")
		return
	root.add_child(game)
	for _frame: int in range(18):
		await process_frame

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var caretaker: Node = game.get_node_or_null("Caretaker")
	var guard: Node2D = game.get_node_or_null("StealthTestRoom/ServiceGuard") as Node2D
	var prompt: ReactionChoicePrompt = game.get_node_or_null("Interface/ReactionChoicePrompt") as ReactionChoicePrompt
	var turn_system: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	if player == null or caretaker == null or guard == null or prompt == null or turn_system == null:
		_fail("Combat lifecycle test nodes are incomplete.")
		return

	game.call("_start_turn_based_combat", caretaker)
	if not turn_system.active:
		_fail("Caretaker combat did not start.")
		return
	var initiative_ids: Array[String] = _initiative_actor_ids(turn_system)
	if "caretaker" not in initiative_ids or "service_guard" not in initiative_ids:
		_fail("First-room encounter roster is incomplete: %s" % JSON.stringify(initiative_ids))
		return
	game.call("_stop_turn_based_combat", "Тестовый бой остановлен.")

	guard.set("maximum_health", 999)
	guard.set("current_health", 999)
	guard.call("enter_combat_hostile")
	player.global_position = Vector2(600.0, 360.0)
	guard.global_position = Vector2(648.0, 360.0)
	var retreat_position := Vector2(744.0, 360.0)
	turn_system.start_combat(
		player,
		[guard],
		20,
		{player.get_instance_id(): 20, guard.get_instance_id(): 1}
	)
	turn_system.force_current_actor_for_testing(player)
	game.call_deferred(
		"resolve_movement_reaction_for_testing",
		guard,
		guard.global_position,
		retreat_position,
		false,
		false
	)
	if not await _wait_for_prompt(prompt):
		_fail("Voluntary NPC retreat did not open an opportunity-reaction prompt.")
		return
	if OPPORTUNITY_OPTION_ID not in prompt.get_option_ids():
		_fail("Opportunity attack option is absent: %s" % JSON.stringify(prompt.get_option_ids()))
		return
	prompt.choose_option(OPPORTUNITY_OPTION_ID)
	if not await _wait_for_prompt_to_close(prompt):
		_fail("Opportunity reaction did not resolve.")
		return
	if turn_system.has_reaction(player):
		_fail("Resolved opportunity attack did not consume the player reaction.")
		return
	if int(game.call("get_player_opportunity_offer_count_for_testing")) != 1:
		_fail("NPC movement did not pass through exactly one reaction gateway.")
		return

	turn_system.force_current_actor_for_testing(player)
	var offer_count: int = int(game.call("get_player_opportunity_offer_count_for_testing"))
	await game.call(
		"resolve_movement_reaction_for_testing",
		guard,
		guard.global_position,
		retreat_position,
		true,
		false
	)
	if int(game.call("get_player_opportunity_offer_count_for_testing")) != offer_count or not turn_system.has_reaction(player):
		_fail("Explicit Disengage did not suppress the opportunity reaction cleanly.")
		return
	await game.call(
		"resolve_movement_reaction_for_testing",
		guard,
		guard.global_position,
		retreat_position,
		false,
		true
	)
	if int(game.call("get_player_opportunity_offer_count_for_testing")) != offer_count or not turn_system.has_reaction(player):
		_fail("Forced movement incorrectly provoked an opportunity reaction.")
		return
	game.call("_stop_turn_based_combat", "Тест реакций завершён.")

	guard.set("player_in_range", player)
	var lethal := AttackResult.new()
	lethal.hit = true
	lethal.melee_attack = true
	lethal.damage = 9999
	lethal.damage_before_mitigation = 9999
	guard.call("receive_player_attack", lethal, false)
	await create_timer(0.35).timeout
	if not bool(guard.call("is_dead_body")):
		_fail("Lethal damage did not create a dead body.")
		return
	var body_visual: Polygon2D = guard.get_node_or_null("Body") as Polygon2D
	if body_visual == null or body_visual.modulate.is_equal_approx(Color.WHITE):
		_fail("Hit flash restored the dead body to an undimmed visual.")
		return
	if body_visual.modulate.r > 0.5 or body_visual.modulate.a > 0.8:
		_fail("Dead body tint is not visibly darkened: %s" % str(body_visual.modulate))
		return
	if not bool(guard.call("can_perform_world_interaction")):
		_fail("Dead body remains blocked by living-dialogue interaction policy.")
		return
	game.call("_set_selected_target", guard)
	var action_ids: Array[String] = _action_ids(game.call("_build_catalog_entries") as Dictionary)
	if "inspect_target" not in action_ids or "open_selected_body_loot" not in action_ids:
		_fail("Dead body cannot be inspected through the common loot catalogue: %s" % JSON.stringify(action_ids))
		return
	if "corpse_loot_all" in action_ids:
		_fail("Legacy corpse loot entry remained beside the common loot panel action: %s" % JSON.stringify(action_ids))
		return
	for action_id: String in action_ids:
		if action_id.begins_with("corpse_loot_item__"):
			_fail("Legacy per-item corpse entry remained beside the common loot panel action: %s" % JSON.stringify(action_ids))
			return

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Encounter roster, corpse lifecycle and symmetric opportunity reactions passed.")
	quit(0)


func _wait_for_prompt(prompt: ReactionChoicePrompt) -> bool:
	for _frame: int in range(90):
		if prompt.is_waiting_for_decision():
			return true
		await process_frame
	return false


func _wait_for_prompt_to_close(prompt: ReactionChoicePrompt) -> bool:
	for _frame: int in range(90):
		if not prompt.is_waiting_for_decision():
			return true
		await process_frame
	return false


func _initiative_actor_ids(turn_system: TurnBasedCombatSystem) -> Array[String]:
	var result: Array[String] = []
	for entry: Dictionary in turn_system.entries:
		if bool(entry.get("is_player", false)):
			continue
		var actor: Node = entry.get("node") as Node
		if is_instance_valid(actor) and actor.has_method("get_actor_id"):
			result.append(str(actor.call("get_actor_id")))
	return result


func _action_ids(entries: Dictionary) -> Array[String]:
	var result: Array[String] = []
	for value: Variant in entries.get("action", []) as Array:
		if value is Dictionary:
			result.append(str((value as Dictionary).get("id", "")))
	return result


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Проверяющий реакций"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.level = 1
	hero.maximum_health = 18
	hero.current_health = 18
	hero.hit_die_size = 10
	hero.hit_dice_maximum = 1
	hero.hit_dice_current = 1
	hero.equipped_weapon_id = "greatsword"
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
