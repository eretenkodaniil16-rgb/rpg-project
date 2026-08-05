extends "res://scripts/ui/mobile_controls_explicit_action_catalog.gd"


func _apply_player_control_vector(direction: Vector2, combat_active: bool) -> void:
	if combat_active:
		_resolve_game_world()
		if is_instance_valid(_game_world) and _game_world.has_method("set_mobile_control_vector"):
			_game_world.call("set_mobile_control_vector", direction.limit_length(1.0))
			return
	super._apply_player_control_vector(direction, combat_active)


func _reset_player_input() -> void:
	_resolve_game_world()
	if is_instance_valid(_game_world) and _game_world.has_method("clear_mobile_control_vector"):
		_game_world.call("clear_mobile_control_vector")
	super._reset_player_input()


func _is_player_combat_turn() -> bool:
	_resolve_game_world()
	if is_instance_valid(_game_world) and _game_world.has_method("is_player_combat_turn"):
		return bool(_game_world.call("is_player_combat_turn"))
	return super._is_player_combat_turn()


func get_joystick_output_for_testing() -> Vector2:
	_resolve_game_world()
	if is_instance_valid(_game_world) and _game_world.has_method("get_mobile_control_vector_for_testing"):
		return _game_world.call("get_mobile_control_vector_for_testing") as Vector2
	return super.get_joystick_output_for_testing()


func _resolve_game_world() -> void:
	if not is_instance_valid(_game_world):
		_game_world = get_tree().get_first_node_in_group("game_world")
