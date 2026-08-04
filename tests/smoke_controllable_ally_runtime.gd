extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const ALLY_ID: String = "companion_irna_guard_01"
const STABILIZE_LABEL: String = "СТАБИЛИЗИРОВАТЬ: ИРНА"

var _stage: String = "init"
var _completed: bool = false


func _init() -> void:
	call_deferred("_run")
	call_deferred("_watchdog")


func _watchdog() -> void:
	await create_timer(25.0).timeout
	if _completed:
		return
	_fail("Controllable ally smoke watchdog timed out at stage: %s" % _stage)


func _run() -> void:
	_stage = "load_game_state"
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	state.call("new_game")
	state.set("player_character", _make_hero())
	state.set("inventory", {})
	state.call("add_item", "healers_kit", 2, false)

	_stage = "instantiate_game"
	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	var game: Node = packed.instantiate() if packed != null else null
	if game == null:
		_fail("Game scene could not be loaded.")
		return
	root.add_child(game)
	for _frame: int in range(18):
		await process_frame

	_stage = "locate_runtime_nodes"
	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var ally: ControllableAlly = game.call("get_controllable_ally_for_testing") as ControllableAlly
	if player == null or ally == null:
		_fail("Player or controllable ally was not created.")
		return
	if ally.get_actor_id() != ALLY_ID:
		_fail("The ally does not expose its stable character_id.")
		return
	if not ally.is_in_group("controllable_allies") or ally.is_in_group("combat_targets"):
		_fail("The ally group contract is invalid or permits friendly-fire target cycling.")
		return

	_stage = "locate_combat_target"
	var targets: Array[Node] = []
	for target: Node in get_nodes_in_group("combat_targets"):
		if target is Node2D and target.has_method("is_combat_active") and bool(target.call("is_combat_active")):
			targets.append(target)
	if targets.is_empty():
		_fail("No hostile fixture is available for initiative testing.")
		return
	var opponent: Node = targets[0]
	var turn_system: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	if turn_system == null:
		_fail("TurnBasedCombatSystem is missing.")
		return
	_stage = "start_initiative"
	turn_system.set_pending_player_controlled_actors([ally])
	turn_system.start_combat(
		player,
		[opponent],
		0,
		{
			player.get_instance_id(): 12,
			ally.get_instance_id(): 18,
			opponent.get_instance_id(): 6
		}
	)
	if not turn_system.is_player_controlled_actor(ally):
		_fail("The ally was not registered as a player-controlled initiative participant.")
		return
	if not turn_system.is_actor_turn(ally) or not turn_system.is_player_controlled_turn():
		_fail("The deterministic ally initiative turn was not selected.")
		return
	if not turn_system.action_available or turn_system.movement_remaining_feet != ally.get_combat_speed_feet():
		_fail("The ally turn did not receive action and movement resources.")
		return

	_stage = "natural_twenty_death_save"
	ally.enter_dying()
	var death_save: Dictionary = game.call(
		"resolve_controllable_ally_death_save_for_testing",
		20
	) as Dictionary
	if not bool(death_save.get("regained_hit_point", false)) or ally.current_health != 1:
		_fail("Natural 20 did not restore the ally to 1 HP.")
		return

	_stage = "build_stabilization_action"
	ally.enter_dying()
	ally.global_position = player.global_position + Vector2(32.0, 0.0)
	turn_system.force_current_actor_for_testing(player)
	game.call("_begin_current_turn")
	var entries: Dictionary = game.call("get_action_catalog_entries_for_testing") as Dictionary
	if not _has_action_label(entries, STABILIZE_LABEL):
		_fail("The real action catalog does not expose the Russian healer-kit action for Irna.")
		return
	_stage = "execute_stabilization"
	var stabilization: Dictionary = game.call("_stabilize_controllable_ally") as Dictionary
	if not bool(stabilization.get("success", false)):
		_fail("Healer-kit stabilization failed: %s" % stabilization)
		return
	if not ally.get_combatant_state().stable or ally.current_health != 0:
		_fail("Healer kit restored HP or failed to mark the ally stable.")
		return
	if int(state.call("get_item_count", "healers_kit")) != 1:
		_fail("Healer kit was not consumed exactly once.")
		return
	if turn_system.action_available:
		_fail("Stabilization in combat did not consume the primary action.")
		return

	_stage = "stop_combat"
	game.call("_stop_turn_based_combat", "Тестовый бой завершён.")
	await process_frame
	_stage = "save_world_snapshot"
	if not bool(state.call("save_game")):
		_fail("Stable world save failed after ally combat.")
		return
	var stored: Dictionary = state.call("get_world_entity_state", ALLY_ID) as Dictionary
	if stored.is_empty():
		_fail("The ally was not written to world_snapshot.entities.")
		return
	if int(stored.get("current_health", -1)) != 0:
		_fail("The saved ally HP does not match the stabilized state.")
		return
	var combat_state_value: Variant = stored.get("combat_state", {})
	if not combat_state_value is Dictionary or not bool((combat_state_value as Dictionary).get("stable", false)):
		_fail("The ally death-save state was not persisted.")
		return

	_stage = "cleanup"
	game.queue_free()
	await process_frame
	_completed = true
	print("Controllable ally initiative, death save, healer-kit and save smoke test passed.")
	quit(0)


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель союзника"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.maximum_health = 14
	hero.current_health = 14
	hero.starter_loadout_granted = true
	return hero


func _has_action_label(entries: Dictionary, expected: String) -> bool:
	for category_id: String in ["action", "bonus", "free", "reaction"]:
		var values: Variant = entries.get(category_id, [])
		if not values is Array:
			continue
		for value: Variant in values as Array:
			if value is Dictionary and str((value as Dictionary).get("label", "")) == expected:
				return true
	return false


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
