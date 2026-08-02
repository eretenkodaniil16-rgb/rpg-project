extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	state.call("new_game")
	state.set("player_character", _make_hero())

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	var game: Node = packed.instantiate() if packed != null else null
	if game == null:
		_fail("Game scene could not be instantiated.")
		return
	root.add_child(game)
	for _frame: int in range(20):
		await process_frame

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var room: GuardPostTwoRoomVisibility = game.get_node_or_null("StealthTestRoom") as GuardPostTwoRoomVisibility
	var guard: Node = room.get_patrol_observer() if room != null else null
	var west_door: StealthDoor = room.get_test_door() if room != null else null
	var catalog: ActionCatalogUI = game.get_node_or_null("Interface/ActionCatalogUI") as ActionCatalogUI
	if player == null or guard == null or west_door == null or catalog == null:
		_fail("Pursuit test fixtures are incomplete.")
		return

	var last_known := Vector2(620.0, 180.0)
	player.global_position = last_known
	state.set("player_position", player.global_position)
	(guard as Node2D).global_position = Vector2(760.0, 180.0)
	guard.call("set_facing_direction", Vector2.LEFT)
	game.call("_start_turn_based_combat", guard)
	game.call("force_player_turn_for_testing")
	await process_frame
	if not bool(game.call("is_turn_based_combat_active")):
		_fail("Combat did not start for the pursuit transition test.")
		return

	catalog.call("toggle_catalog")
	if not catalog.is_catalog_open():
		_fail("Action catalog did not open on the player turn.")
		return

	# Model a valid successful Hide: the hero leaves the observer's line of sight
	# behind the closed service door while the guard retains the previous position.
	west_door.set_door_state("closed", false)
	player.global_position = Vector2(100.0, 110.0)
	state.set("player_position", player.global_position)
	var combat_state: CombatantState = game.get("_player_combat_state") as CombatantState
	combat_state.hidden = true
	var observers: Array[Node] = [guard]
	game.call("_suspend_combat_for_hidden_pursuit", observers, last_known)
	await process_frame
	if bool(game.call("is_turn_based_combat_active")):
		_fail("Successful hiding did not end turn-based initiative.")
		return
	if catalog.is_catalog_open():
		_fail("Action catalog remained visible during the combat-to-search transition.")
		return
	if not bool(game.call("is_exploration_hidden_for_testing")):
		_fail("Combat hiding was not transferred to exploration hidden state.")
		return
	if bool(guard.call("is_hostile")):
		_fail("Searching guard remained in real-time hostile attack mode outside initiative.")
		return
	var record: Dictionary = state.call("get_stealth_alert_record", "service_guard") as Dictionary
	if str(record.get("state", "")) != StealthAlertSystem.STATE_INVESTIGATING:
		_fail("Guard did not continue as an exploration investigator.")
		return
	var stored_last_known: Vector2 = StealthAlertSystem.new().vector_from_value(record.get("last_known_position", []))
	if stored_last_known.distance_to(last_known) > 0.5:
		_fail("Last known player position was lost when initiative ended.")
		return

	var before_search_move: Vector2 = (guard as Node2D).global_position
	game.call("force_exploration_alert_tick_for_testing", 0.5)
	if (guard as Node2D).global_position.distance_to(before_search_move) <= 0.1:
		_fail("Guard patrol/search did not continue toward the last known position.")
		return

	# Leaving concealment and being seen again starts a new initiative. No
	# unconditional advantage is granted here; visibility and the normal SRD
	# combat rules determine any advantage later.
	west_door.set_door_state("open", false)
	game.call("_break_exploration_hidden", "")
	player.global_position = Vector2(690.0, 180.0)
	state.set("player_position", player.global_position)
	(guard as Node2D).global_position = Vector2(760.0, 180.0)
	guard.call("set_facing_direction", Vector2.LEFT)
	game.call("force_exploration_alert_tick_for_testing", 1.0)
	await process_frame
	if not bool(game.call("is_turn_based_combat_active")):
		_fail("Reacquiring the hidden hero did not restart initiative.")
		return

	print("Successful hide suspension, exploration pursuit, closed action catalog and combat reacquisition smoke test passed.")
	game.queue_free()
	await process_frame
	quit(0)


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.create_legacy_default()
	hero.character_name = "Лазутчик"
	hero.abilities["dexterity"] = 18
	hero.base_abilities["dexterity"] = 18
	hero.skill_proficiencies.append("stealth")
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
