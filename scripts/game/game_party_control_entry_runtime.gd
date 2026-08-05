extends "res://scripts/game/game_party_control_runtime.gd"


func refresh_active_party_action_catalog() -> void:
	# Unique public entry point for the party-aware mobile controller. Calling the
	# generic inherited `_refresh_action_catalog` name through Object.call can bind
	# to an older runtime layer in this long inheritance chain. This adapter has no
	# competing implementation and therefore always reaches the party runtime.
	_refresh_action_catalog()
