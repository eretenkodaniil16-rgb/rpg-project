extends "res://scripts/game/game_party_control_entry_runtime.gd"


func _begin_current_turn() -> void:
	var incoming_actor: Node = _turn_system.current_actor()
	var selected_before_turn: Node = _selected_target
	var context_actor: Node = _party_control_context.active_actor()
	var stored_target: Node = (
		_party_control_context.target_for(incoming_actor)
		if is_instance_valid(incoming_actor)
		else null
	)
	var should_seed_initial_target: bool = (
		_turn_system.active
		and incoming_actor == player
		and not is_instance_valid(context_actor)
		and not _target_is_valid(stored_target)
		and _target_is_valid(selected_before_turn)
	)
	if should_seed_initial_target:
		_party_control_context.set_target(incoming_actor, selected_before_turn)
	super._begin_current_turn()
