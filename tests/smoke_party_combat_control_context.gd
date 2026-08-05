extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const EXPECTED_MOBILE_SCRIPT: String = "res://scripts/ui/mobile_controls_party_routing.gd"

var _completed: bool = false
var _stage: String = "init"


func _init() -> void:
	call_deferred("_run")
	call_deferred("_watchdog")


func _watchdog() -> void:
	await create_timer(35.0).timeout
	if not _completed:
		_fail("Party control smoke timed out at stage: %s" % _stage)


func _run() -> void:
	_stage = "setup"
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState is missing.")
		return
	state.call("new_game")
	state.set("player_character", _make_hero())

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	var game: Node = packed.instantiate() if packed != null else null
	if game == null:
		_fail("Game scene could not be instantiated.")
		return
	root.add_child(game)
	for _frame: int in range(18):
		await process_frame

	_stage = "locate_runtime"
	var player: Node = game.get_node_or_null("Player")
	var ally: Node = game.call("get_controllable_ally_for_testing")
	var mobile_controls: Node = game.get_node_or_null("Interface/MobileControls")
	var action_catalog: Node = game.get_node_or_null("Interface/ActionCatalogUI")
	var target_button: Button = game.get("_target_button") as Button
	var opponents: Array[Node] = _available_opponents(game)
	if player == null or ally == null or mobile_controls == null or action_catalog == null or target_button == null or opponents.size() < 2:
		_fail("Required party actors, two targets, or mobile UI nodes are missing.")
		return
	var mobile_script: Script = mobile_controls.get_script() as Script
	if mobile_script == null or mobile_script.resource_path != EXPECTED_MOBILE_SCRIPT:
		_fail("Game scene does not use the party-aware mobile controls runtime.")
		return
	mobile_controls.call("enable_for_testing")

	var first_target: Node = opponents[0]
	var second_target: Node = opponents[1]
	var turn_system: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	turn_system.set_pending_player_controlled_actors([ally])
	turn_system.start_combat(
		player,
		opponents,
		0,
		{
			player.get_instance_id(): 20,
			ally.get_instance_id(): 1,
			first_target.get_instance_id(): 1,
			second_target.get_instance_id(): 1
		}
	)
	game.call("_begin_current_turn")

	_stage = "hero_context"
	if not turn_system.is_actor_turn(player):
		_fail("The hero did not receive the deterministic first turn.")
		return
	if int(game.call("get_active_controlled_actor_instance_id_for_testing")) != player.get_instance_id():
		_fail("The hero is not the active input owner on the hero turn.")
		return
	game.call("set_party_target_for_testing", player, first_target)
	if int(game.call("get_party_target_instance_id_for_testing", player)) != first_target.get_instance_id():
		_fail("The hero target was not stored in the hero control context.")
		return
	var hero_movement_before: int = turn_system.movement_remaining_feet
	if not turn_system.action_available or hero_movement_before <= 0:
		_fail("The hero did not receive an independent action and movement budget.")
		return

	_stage = "ally_context"
	game.call("force_controllable_ally_turn_for_testing")
	await process_frame
	if int(game.call("get_active_controlled_actor_instance_id_for_testing")) != ally.get_instance_id():
		_fail("Irina is not the active input owner on her initiative turn.")
		return
	if int(game.call("get_party_target_instance_id_for_testing", ally)) != 0:
		_fail("Irina inherited the hero target instead of receiving a separate target context.")
		return
	if int(game.call("get_party_target_instance_id_for_testing", player)) != first_target.get_instance_id():
		_fail("Switching to Irina erased the hero target context.")
		return

	_stage = "real_target_button"
	target_button.emit_signal("pressed")
	await process_frame
	if int(game.call("get_party_target_instance_id_for_testing", ally)) == 0:
		_fail("The real target button did not select a target for Irina.")
		return
	game.call("set_party_target_for_testing", ally, second_target)
	if int(game.call("get_party_target_instance_id_for_testing", ally)) != second_target.get_instance_id():
		_fail("Irina could not retain her own selected target.")
		return
	if int(game.call("get_party_target_instance_id_for_testing", player)) != first_target.get_instance_id():
		_fail("Irina target selection overwrote the hero target.")
		return

	_stage = "ally_planned_movement"
	var hero_position_before: Vector2 = (player as Node2D).global_position
	var ally_position_before: Vector2 = (ally as Node2D).global_position
	var ally_movement_before: int = turn_system.movement_remaining_feet
	if not await _create_route_with_mobile_joystick(game, mobile_controls, ally):
		_fail("The mobile joystick could not create an independent route for Irina.")
		return
	if int(game.call("get_planned_movement_owner_instance_id_for_testing")) != ally.get_instance_id():
		_fail("The planned route is not owned by Irina.")
		return
	if not (ally as Node2D).global_position.is_equal_approx(ally_position_before):
		_fail("Irina moved before her route was confirmed.")
		return
	if not (player as Node2D).global_position.is_equal_approx(hero_position_before):
		_fail("Planning Irina movement changed the hero position.")
		return

	_stage = "ally_confirm_movement"
	action_catalog.emit_signal("action_requested", "confirm_move")
	for _frame: int in range(20):
		await process_frame
	if (ally as Node2D).global_position.is_equal_approx(ally_position_before):
		_fail("Confirming Irina movement did not move Irina.")
		return
	if not (player as Node2D).global_position.is_equal_approx(hero_position_before):
		_fail("Confirming Irina movement moved the hero.")
		return
	if turn_system.movement_remaining_feet >= ally_movement_before:
		_fail("Irina movement did not consume Irina's movement budget.")
		return

	_stage = "ally_action_catalog"
	game.call("force_controllable_ally_turn_for_testing")
	game.call("set_party_target_for_testing", ally, second_target)
	if not bool(game.call("place_controllable_ally_adjacent_for_testing", second_target)):
		_fail("Could not place Irina beside her selected target for the attack test.")
		return
	mobile_controls.call("simulate_actions_touch_for_testing")
	for _frame: int in range(3):
		await process_frame
	if not bool(action_catalog.call("is_catalog_open")):
		_fail("The real Actions button could not open Irina's own action catalogue.")
		return
	var entries: Dictionary = action_catalog.call("get_entries_for_testing") as Dictionary
	if _catalog_has_action(entries, "select_ally_target"):
		_fail("Irina still exposes target cycling as an action-catalog command.")
		return
	for required_action: String in ["attack", "dash", "disengage", "dodge", "end_turn"]:
		if not _catalog_has_action(entries, required_action):
			_fail("Irina's catalogue is missing action '%s': %s" % [required_action, JSON.stringify(entries)])
			return
	action_catalog.call("_emit_action", "attack", "", true)
	for _frame: int in range(4):
		await process_frame
	if turn_system.action_available:
		_fail("Irina attack did not consume Irina's primary action.")
		return

	_stage = "hero_context_restored"
	game.call("force_player_turn_for_testing")
	await process_frame
	if int(game.call("get_active_controlled_actor_instance_id_for_testing")) != player.get_instance_id():
		_fail("Control did not return to the hero on the hero initiative turn.")
		return
	if int(game.call("get_party_target_instance_id_for_testing", player)) != first_target.get_instance_id():
		_fail("The hero target was not restored after Irina's turn.")
		return
	if int(game.call("get_party_target_instance_id_for_testing", ally)) != second_target.get_instance_id():
		_fail("Irina target was lost after control returned to the hero.")
		return
	if not turn_system.action_available:
		_fail("Irina spending her action also spent the hero action.")
		return
	if turn_system.movement_remaining_feet != hero_movement_before:
		_fail("The hero did not receive a fresh movement budget on the hero turn.")
		return

	_stage = "hero_route_owner"
	var ally_position_after_turn: Vector2 = (ally as Node2D).global_position
	if not await _create_route_with_mobile_joystick(game, mobile_controls, player):
		_fail("The same mobile joystick could not create the hero's separate route.")
		return
	if int(game.call("get_planned_movement_owner_instance_id_for_testing")) != player.get_instance_id():
		_fail("The hero route is not owned by the hero.")
		return
	if not (ally as Node2D).global_position.is_equal_approx(ally_position_after_turn):
		_fail("Planning the hero route changed Irina's position.")
		return

	if turn_system.active:
		game.call("_stop_turn_based_combat", "Party control smoke complete.")
	game.queue_free()
	await process_frame
	_completed = true
	print("Independent hero and Irina initiative, movement, action and target contexts passed.")
	quit(0)


func _create_route_with_mobile_joystick(game: Node, mobile_controls: Node, expected_owner: Node) -> bool:
	game.call("_clear_movement_plan")
	for direction: Vector2 in [Vector2.LEFT, Vector2.RIGHT, Vector2.UP, Vector2.DOWN]:
		mobile_controls.call("move_joystick_for_testing", direction)
		for _frame: int in range(4):
			await process_frame
		mobile_controls.call("release_joystick_for_testing")
		await process_frame
		var path: Array = game.call("get_planned_path_for_testing") as Array
		if path.size() > 1 and int(game.call("get_planned_movement_owner_instance_id_for_testing")) == expected_owner.get_instance_id():
			return true
		game.call("_clear_movement_plan")
	return false


func _available_opponents(game: Node) -> Array[Node]:
	var result: Array[Node] = []
	var available_value: Variant = game.call("_available_targets")
	if available_value is Array:
		for value: Variant in available_value as Array:
			if value is Node and is_instance_valid(value as Node):
				result.append(value as Node)
	return result


func _catalog_has_action(entries: Dictionary, action_id: String) -> bool:
	for category_value: Variant in entries.values():
		if not category_value is Array:
			continue
		for entry_value: Variant in category_value as Array:
			if entry_value is Dictionary and str((entry_value as Dictionary).get("id", "")) == action_id:
				return true
	return false


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель партийного управления"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.maximum_health = 14
	hero.current_health = 14
	hero.starter_loadout_granted = true
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
