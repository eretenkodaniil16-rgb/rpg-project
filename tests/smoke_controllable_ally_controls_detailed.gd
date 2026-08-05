extends "res://tests/smoke_controllable_ally_controls.gd"


func _create_route_with_mobile_joystick(
	game: Node,
	mobile_controls: Node,
	expected_owner: Node
) -> bool:
	var popup: AttackResultPopup = game.get("_attack_popup") as AttackResultPopup
	if popup != null and popup.visible:
		# Reproduce the player's required Continue transaction. The result popup
		# deliberately locks all spatial input until it is acknowledged.
		popup.call("_on_continue_pressed")
		await process_frame
		if GameState.input_locked:
			return false
	return await super._create_route_with_mobile_joystick(
		game,
		mobile_controls,
		expected_owner
	)


func _fail(message: String) -> void:
	var game: Node = root.get_node_or_null("Game")
	var diagnostics: Dictionary = {"stage": _stage}
	if is_instance_valid(game):
		var game_script: Script = game.get_script() as Script
		diagnostics["game_script"] = game_script.resource_path if game_script != null else ""
		diagnostics["has_party_refresh_entry"] = game.has_method("refresh_active_party_action_catalog")
		if game.has_method("get_catalog_action_handler_methods_for_testing"):
			diagnostics["catalog_handlers"] = game.call("get_catalog_action_handler_methods_for_testing")
		if game.has_method("get_last_party_action_for_testing"):
			diagnostics["last_party_action"] = game.call("get_last_party_action_for_testing")
		if game.has_method("get_catalog_context_diagnostics_for_testing"):
			diagnostics["catalog_context"] = game.call("get_catalog_context_diagnostics_for_testing")
		var ally: Node = game.call("get_controllable_ally_for_testing") if game.has_method("get_controllable_ally_for_testing") else null
		if is_instance_valid(ally) and game.has_method("get_party_target_instance_id_for_testing"):
			diagnostics["ally_id"] = ally.get_instance_id()
			diagnostics["ally_target_id"] = game.call("get_party_target_instance_id_for_testing", ally)
		var catalog: Node = game.get_node_or_null("Interface/ActionCatalogUI")
		if catalog != null and catalog.has_method("get_entries_for_testing"):
			diagnostics["catalog_entries"] = catalog.call("get_entries_for_testing")
		var turn_system_value: Variant = game.get("_turn_system")
		if turn_system_value is TurnBasedCombatSystem:
			var turn_system: TurnBasedCombatSystem = turn_system_value as TurnBasedCombatSystem
			diagnostics["action_available"] = turn_system.action_available
			diagnostics["movement_remaining_feet"] = turn_system.movement_remaining_feet
			var current_actor: Node = turn_system.current_actor()
			diagnostics["current_actor_id"] = current_actor.get_instance_id() if is_instance_valid(current_actor) else 0
	push_error("%s Diagnostics: %s" % [message, JSON.stringify(diagnostics)])
	quit(1)
