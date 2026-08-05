extends "res://tests/smoke_party_combat_control_context.gd"

const EXPECTED_MOBILE_SCRIPT: String = "res://scripts/ui/mobile_controls_party_routing.gd"


class StableCombatTarget:
	extends Node2D

	var combat_name: String = "Контрольная цель"
	var current_health: int = 100
	var maximum_health: int = 100
	var armor_class: int = 10
	var _turn_active: bool = false
	var _targeted: bool = false

	func _ready() -> void:
		add_to_group("combat_targets")

	func get_combat_name() -> String:
		return combat_name

	func get_current_health() -> int:
		return current_health

	func get_armor_class() -> int:
		return armor_class

	func get_initiative_modifier() -> int:
		return 0

	func get_combat_speed_feet() -> int:
		return 0

	func is_combat_active() -> bool:
		return current_health > 0

	func can_take_combat_turn() -> bool:
		return current_health > 0

	func is_hostile() -> bool:
		return true

	func enter_combat_hostile() -> void:
		pass

	func set_turn_active(value: bool) -> void:
		_turn_active = value

	func set_combat_targeted(value: bool) -> void:
		_targeted = value

	func set_combat_overlay_visible(_value: bool) -> void:
		pass

	func set_turn_based_mode(_value: bool) -> void:
		pass

	func perform_combat_turn_attack() -> void:
		pass

	func perform_opportunity_attack() -> void:
		pass

	func receive_player_attack(result: AttackResult, _show_interface: bool = true) -> void:
		if result.hit:
			# Keep the fixture active so the test verifies party control rather than
			# a target reset lifecycle. Damage application is still executed.
			current_health = maxi(1, current_health - maxi(result.damage, 0))
		result.target_health_after = current_health
		result.target_max_health = maximum_health


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
	if player == null or ally == null or mobile_controls == null or action_catalog == null or target_button == null:
		_fail("Required party actors or mobile UI nodes are missing.")
		return
	var mobile_script: Script = mobile_controls.get_script() as Script
	if mobile_script == null or mobile_script.resource_path != EXPECTED_MOBILE_SCRIPT:
		_fail("Game scene does not use the party-aware mobile controls runtime.")
		return
	mobile_controls.call("enable_for_testing")

	var first_target := StableCombatTarget.new()
	first_target.name = "PartyControlTargetA"
	first_target.combat_name = "Контрольная цель А"
	first_target.global_position = Vector2(900.0, 470.0)
	game.add_child(first_target)
	var second_target := StableCombatTarget.new()
	second_target.name = "PartyControlTargetB"
	second_target.combat_name = "Контрольная цель Б"
	second_target.global_position = Vector2(1080.0, 470.0)
	game.add_child(second_target)
	await process_frame

	var opponents: Array[Node] = [first_target, second_target]
	var turn_system: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	if turn_system == null or not game.has_method("start_party_combat_for_testing"):
		_fail("Production-like party combat test entry is missing.")
		return
	game.call(
		"start_party_combat_for_testing",
		opponents,
		{
			player.get_instance_id(): 20,
			ally.get_instance_id(): 10,
			first_target.get_instance_id(): 2,
			second_target.get_instance_id(): 1
		}
	)
	await process_frame

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
		_fail("Irna is not the active input owner on her initiative turn.")
		return
	if int(game.call("get_party_target_instance_id_for_testing", ally)) != 0:
		_fail("Irna inherited the hero target instead of receiving a separate target context.")
		return
	if int(game.call("get_party_target_instance_id_for_testing", player)) != first_target.get_instance_id():
		_fail("Switching to Irna erased the hero target context.")
		return

	_stage = "real_target_button"
	target_button.emit_signal("pressed")
	await process_frame
	if int(game.call("get_party_target_instance_id_for_testing", ally)) == 0:
		_fail("The real target button did not select a target for Irna.")
		return
	game.call("set_party_target_for_testing", ally, second_target)
	if int(game.call("get_party_target_instance_id_for_testing", ally)) != second_target.get_instance_id():
		_fail("Irna could not retain her own selected target.")
		return
	if int(game.call("get_party_target_instance_id_for_testing", player)) != first_target.get_instance_id():
		_fail("Irna target selection overwrote the hero target.")
		return

	_stage = "ally_planned_movement"
	var hero_position_before: Vector2 = (player as Node2D).global_position
	var ally_position_before: Vector2 = (ally as Node2D).global_position
	var ally_movement_before: int = turn_system.movement_remaining_feet
	if not await _create_route_with_mobile_joystick(game, mobile_controls, ally):
		_fail("The mobile joystick could not create an independent route for Irna.")
		return
	if int(game.call("get_planned_movement_owner_instance_id_for_testing")) != ally.get_instance_id():
		_fail("The planned route is not owned by Irna.")
		return
	if not (ally as Node2D).global_position.is_equal_approx(ally_position_before):
		_fail("Irna moved before her route was confirmed.")
		return
	if not (player as Node2D).global_position.is_equal_approx(hero_position_before):
		_fail("Planning Irna movement changed the hero position.")
		return

	_stage = "ally_confirm_movement"
	action_catalog.emit_signal("action_requested", "confirm_move")
	for _frame: int in range(20):
		await process_frame
	if (ally as Node2D).global_position.is_equal_approx(ally_position_before):
		_fail("Confirming Irna movement did not move Irna.")
		return
	if not (player as Node2D).global_position.is_equal_approx(hero_position_before):
		_fail("Confirming Irna movement moved the hero.")
		return
	if turn_system.movement_remaining_feet >= ally_movement_before:
		_fail("Irna movement did not consume Irna's movement budget.")
		return

	_stage = "ally_action_catalog"
	game.call("force_controllable_ally_turn_for_testing")
	game.call("set_party_target_for_testing", ally, second_target)
	if not bool(game.call("place_controllable_ally_adjacent_for_testing", second_target)):
		_fail("Could not place Irna beside her selected target for the attack test.")
		return
	if not second_target.is_combat_active():
		_fail("The stable attack fixture became inactive before opening the catalogue.")
		return
	mobile_controls.call("simulate_actions_touch_for_testing")
	for _frame: int in range(3):
		await process_frame
	if not bool(action_catalog.call("is_catalog_open")):
		_fail("The real Actions button could not open Irna's own action catalogue.")
		return
	var entries: Dictionary = action_catalog.call("get_entries_for_testing") as Dictionary
	for required_action: String in ["select_ally_target", "attack", "dash", "disengage", "dodge", "end_turn"]:
		if not _catalog_has_action(entries, required_action):
			_fail("Irna's catalogue is missing action '%s': %s" % [required_action, JSON.stringify(entries)])
			return
	if not _catalog_action_enabled(entries, "attack"):
		_fail("Irna's attack entry is present but disabled beside a valid target: %s" % JSON.stringify(entries))
		return
	action_catalog.call("_emit_action", "attack", "", true)
	for _frame: int in range(4):
		await process_frame
	if turn_system.action_available:
		_fail("Irna attack did not consume Irna's primary action.")
		return
	var party_action: Dictionary = game.call("get_last_party_action_for_testing") as Dictionary
	var attack_result: Dictionary = party_action.get("result", {}) as Dictionary
	if str(party_action.get("action_id", "")) != "attack" or not bool(attack_result.get("success", false)):
		_fail("Irna's catalogue attack was not resolved successfully: %s" % JSON.stringify(party_action))
		return

	_stage = "hero_context_restored"
	game.call("force_player_turn_for_testing")
	await process_frame
	if int(game.call("get_active_controlled_actor_instance_id_for_testing")) != player.get_instance_id():
		_fail("Control did not return to the hero on the hero initiative turn.")
		return
	if int(game.call("get_party_target_instance_id_for_testing", player)) != first_target.get_instance_id():
		_fail("The hero target was not restored after Irna's turn.")
		return
	if int(game.call("get_party_target_instance_id_for_testing", ally)) != second_target.get_instance_id():
		_fail("Irna target was lost after control returned to the hero.")
		return
	if not turn_system.action_available:
		_fail("Irna spending her action also spent the hero action.")
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
		_fail("Planning the hero route changed Irna's position.")
		return

	if turn_system.active:
		game.call("_stop_turn_based_combat", "Party control smoke complete.")
	game.queue_free()
	await process_frame
	_completed = true
	print("Independent hero and Irna initiative, movement, action and target contexts passed.")
	quit(0)


func _catalog_action_enabled(entries: Dictionary, action_id: String) -> bool:
	for category_id: String in ["action", "bonus", "reaction"]:
		var values: Variant = entries.get(category_id, [])
		if not values is Array:
			continue
		for entry_value: Variant in values as Array:
			if entry_value is Dictionary and str((entry_value as Dictionary).get("id", "")) == action_id:
				return bool((entry_value as Dictionary).get("enabled", false))
	return false


func _fail(message: String) -> void:
	var game: Node = root.get_node_or_null("Game")
	var diagnostics: Dictionary = {}
	if is_instance_valid(game):
		if game.has_method("get_catalog_action_handler_methods_for_testing"):
			diagnostics["catalog_handlers"] = game.call("get_catalog_action_handler_methods_for_testing")
		if game.has_method("get_last_party_action_for_testing"):
			diagnostics["last_party_action"] = game.call("get_last_party_action_for_testing")
		var turn_system_value: Variant = game.get("_turn_system")
		if turn_system_value is TurnBasedCombatSystem:
			var turn_system: TurnBasedCombatSystem = turn_system_value as TurnBasedCombatSystem
			diagnostics["action_available"] = turn_system.action_available
			diagnostics["movement_remaining_feet"] = turn_system.movement_remaining_feet
			var current_actor: Node = turn_system.current_actor()
			diagnostics["current_actor_id"] = current_actor.get_instance_id() if is_instance_valid(current_actor) else 0
	push_error("%s Diagnostics: %s" % [message, JSON.stringify(diagnostics)])
	quit(1)
