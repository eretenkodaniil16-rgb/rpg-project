extends "res://scripts/ui/mobile_controls.gd"


func _on_interact_pressed() -> void:
	if not is_instance_valid(_player):
		_player = get_tree().get_first_node_in_group("player") as CharacterBody2D
	if not is_instance_valid(_game_world):
		_game_world = get_tree().get_first_node_in_group("game_world")
	if not is_instance_valid(_game_world):
		return
	var action_catalog: Node = _game_world.get_node_or_null("Interface/ActionCatalogUI")
	if action_catalog == null:
		if is_instance_valid(_player) and _player.has_method("request_interaction"):
			_player.call("request_interaction")
		return
	if _game_world.has_method("_refresh_action_catalog"):
		_game_world.call("_refresh_action_catalog")
	var nearby_count: int = _nearby_interactable_count()
	if nearby_count > 0:
		if action_catalog.has_method("is_catalog_open") and not bool(action_catalog.call("is_catalog_open")):
			action_catalog.call("toggle_catalog")
		action_catalog.call("_select_category", "action")
		action_catalog.call("_select_action_group", "world")
		return
	if action_catalog.has_method("toggle_catalog"):
		action_catalog.call("toggle_catalog")


func _nearby_interactable_count() -> int:
	if not is_instance_valid(_player) or not _player.has_method("get_nearby_interactables"):
		return 0
	var value: Variant = _player.call("get_nearby_interactables")
	return (value as Array).size() if value is Array else 0
