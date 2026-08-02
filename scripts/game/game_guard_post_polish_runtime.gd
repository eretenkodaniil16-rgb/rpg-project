extends "res://scripts/game/game_guard_post_stable_combat_start_runtime.gd"


func _target_is_valid(target: Node) -> bool:
	# Neutral world actors remain valid informational targets before combat even
	# though they are deliberately absent from combat_targets and initiative.
	if not _turn_system.active and is_instance_valid(target) and target.is_in_group("context_action_targets"):
		if not target is Node2D:
			return false
		if target.has_method("is_combat_active") and not bool(target.call("is_combat_active")):
			return false
		return _target_is_visible_to_player(target)
	return super._target_is_valid(target)


func _cycle_target() -> void:
	if _turn_system.active:
		super._cycle_target()
		return
	_cycle_exploration_context_target()


func _on_feedback_target_requested() -> void:
	_close_action_catalog_immediately()
	if not _turn_system.active:
		if GameState.input_locked or _attack_in_progress or _any_overlay_visible():
			return
		_cycle_exploration_context_target()
		return
	super._on_feedback_target_requested()


func _cycle_exploration_context_target() -> void:
	var targets: Array[Node] = []
	for target: Node in _context_targets():
		if _target_is_valid(target):
			targets.append(target)
	if targets.is_empty():
		_set_selected_target(null)
		show_combat_message("В поле зрения нет доступных целей.", false)
		return
	var current_index: int = targets.find(_selected_target)
	if current_index < 0:
		_set_selected_target(targets[0])
		show_combat_message("Цель выбрана. Нажмите ДЕЙСТВИЯ, чтобы осмотреть её.", true)
	elif current_index + 1 < targets.size():
		_set_selected_target(targets[current_index + 1])
		show_combat_message("Выбрана следующая видимая цель.", true)
	else:
		_set_selected_target(null)
		show_combat_message("Цель снята.", true)


func _update_exploration_alerts(delta: float) -> void:
	# Fog, room concealment and the non-blocking Actions catalogue affect only
	# presentation and player input. They must never stop the world simulation.
	# The inherited pursuit layer paused every observer while any overlay was
	# visible, which made the service guard appear to lose its AI off-screen.
	if GameState.input_locked:
		return
	for actor: Node in _exploration_alert_actors():
		_update_exploration_actor(actor, delta)
