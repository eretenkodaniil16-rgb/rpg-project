extends "res://tests/smoke_srd_combat_core.gd"


func _fail(message: String) -> void:
	var diagnostics: Dictionary = {}
	var game: Node = root.get_node_or_null("Game")
	if is_instance_valid(game):
		diagnostics["game_script"] = (game.get_script() as Script).resource_path if game.get_script() is Script else ""
		var player: Node = game.get_node_or_null("Player")
		var target: Node = game.get("_selected_target") as Node
		diagnostics["player_id"] = player.get_instance_id() if is_instance_valid(player) else 0
		diagnostics["target_id"] = target.get_instance_id() if is_instance_valid(target) else 0
		diagnostics["target_valid"] = bool(game.call("_target_is_valid", target)) if game.has_method("_target_is_valid") and is_instance_valid(target) else false
		var turn_value: Variant = game.get("_turn_system")
		if turn_value is TurnBasedCombatSystem:
			var turns: TurnBasedCombatSystem = turn_value as TurnBasedCombatSystem
			var current: Node = turns.current_actor()
			diagnostics["turn_active"] = turns.active
			diagnostics["current_actor_id"] = current.get_instance_id() if is_instance_valid(current) else 0
			diagnostics["player_turn"] = turns.is_actor_turn(player)
		var catalog: ActionCatalogUI = game.get_node_or_null("Interface/ActionCatalogUI") as ActionCatalogUI
		if catalog != null:
			var connections: Array[Dictionary] = []
			for value: Variant in catalog.get_signal_connection_list(&"action_requested"):
				if not value is Dictionary:
					continue
				var callback_value: Variant = (value as Dictionary).get("callable")
				if not callback_value is Callable:
					continue
				var callback: Callable = callback_value as Callable
				var owner: Object = callback.get_object()
				connections.append({
					"method": str(callback.get_method()),
					"owner_class": owner.get_class() if owner != null else "",
					"owner_path": str((owner as Node).get_path()) if owner is Node else ""
				})
			diagnostics["catalog_connections"] = connections
		var dialogue: Control = game.get_node_or_null("Interface/DialogueUI") as Control
		diagnostics["dialogue_visible_before_direct"] = dialogue.visible if dialogue != null else false
		var controller: CombatSocialTerrainController = game.get_node_or_null("CombatSocialTerrainController") as CombatSocialTerrainController
		diagnostics["controller_found"] = controller != null
		if controller != null:
			diagnostics["controller_initialized"] = bool(controller.get("_initialized"))
			diagnostics["external_dispatch"] = bool(controller.get("_external_catalog_dispatch"))
			var controller_game: Node = controller.get("_game") as Node
			diagnostics["controller_game_path"] = str(controller_game.get_path()) if is_instance_valid(controller_game) else ""
			diagnostics["direct_handled"] = controller.handle_catalog_action("combat_dialogue")
			diagnostics["dialogue_visible_after_direct"] = dialogue.visible if dialogue != null else false
	push_error("%s Diagnostics: %s" % [message, JSON.stringify(diagnostics)])
	quit(1)
