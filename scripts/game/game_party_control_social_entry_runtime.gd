extends "res://scripts/game/game_party_control_entry_runtime.gd"


func _ready() -> void:
	super._ready()
	# The inherited party runtime defers its catalog rebinding. Restore the
	# specialized social-only handler afterwards so combat dialogue remains
	# available to the hero without sharing Irina's combat command path.
	call_deferred("_restore_combat_social_catalog_dispatch")


func _restore_combat_social_catalog_dispatch() -> void:
	if _action_catalog_ui == null:
		return
	var controller: CombatSocialTerrainController = get_node_or_null("CombatSocialTerrainController") as CombatSocialTerrainController
	if controller == null:
		return
	var callback := Callable(controller, "_on_action_requested")
	if not _action_catalog_ui.action_requested.is_connected(callback):
		_action_catalog_ui.action_requested.connect(callback)
