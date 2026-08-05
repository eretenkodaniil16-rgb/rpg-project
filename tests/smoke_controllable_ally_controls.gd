extends "res://tests/smoke_party_combat_control_context.gd"


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
