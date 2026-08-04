extends "res://scripts/ui/mobile_controls.gd"

var _last_joystick_direction: Vector2 = Vector2.ZERO
var _control_mode_initialized: bool = false
var _last_combat_mode: bool = false
var _last_player_turn_active: bool = false


func _ready() -> void:
	super._ready()
	_restore_simple_action_button_input()


func enable_for_testing() -> void:
	super.enable_for_testing()
	_restore_simple_action_button_input()


func _process(delta: float) -> void:
	super._process(delta)
	var combat_active: bool = _is_combat_active()
	var player_turn_active: bool = combat_active and _is_player_combat_turn()
	if not _control_mode_initialized or combat_active != _last_combat_mode:
		_control_mode_initialized = true
		_apply_player_control_vector(_last_joystick_direction, combat_active)
	if combat_active != _last_combat_mode or player_turn_active != _last_player_turn_active:
		_close_action_catalog()
	_last_combat_mode = combat_active
	_last_player_turn_active = player_turn_active
	if is_instance_valid(interact_button):
		interact_button.disabled = _action_button_blocked_now()


func _set_player_vector(direction: Vector2) -> void:
	_last_joystick_direction = direction.limit_length(1.0)
	var combat_active: bool = _is_combat_active()
	_control_mode_initialized = true
	_last_combat_mode = combat_active
	_apply_player_control_vector(_last_joystick_direction, combat_active)


func _reset_player_input() -> void:
	_last_joystick_direction = Vector2.ZERO
	if not is_instance_valid(_player):
		return
	if _player.has_method("set_mobile_vector"):
		_player.call("set_mobile_vector", Vector2.ZERO)
	if _player.has_method("clear_mobile_facing_input"):
		_player.call("clear_mobile_facing_input")
	elif _player.has_method("clear_mobile_input"):
		_player.call("clear_mobile_input")


func get_joystick_output_for_testing() -> Vector2:
	if not is_instance_valid(_player):
		return Vector2.ZERO
	if _is_combat_active() and _player.has_method("get_mobile_facing_direction"):
		return _player.call("get_mobile_facing_direction") as Vector2
	if _player.has_method("get_mobile_direction"):
		return _player.call("get_mobile_direction") as Vector2
	return Vector2.ZERO


func get_action_turn_guard_remaining_for_testing() -> float:
	return 0.0


func action_press_started_blocked_for_testing() -> bool:
	return _action_button_blocked_now()


func _apply_player_control_vector(direction: Vector2, combat_active: bool) -> void:
	if not is_instance_valid(_player):
		_player = get_tree().get_first_node_in_group("player") as CharacterBody2D
	if not is_instance_valid(_player):
		return
	if combat_active:
		if _player.has_method("set_mobile_vector"):
			_player.call("set_mobile_vector", Vector2.ZERO)
		if _player.has_method("set_mobile_facing_vector"):
			_player.call("set_mobile_facing_vector", direction)
		return
	if _player.has_method("clear_mobile_facing_input"):
		_player.call("clear_mobile_facing_input")
	if _player.has_method("set_mobile_vector"):
		_player.call("set_mobile_vector", direction)


func _is_combat_active() -> bool:
	if not is_instance_valid(_game_world):
		_game_world = get_tree().get_first_node_in_group("game_world")
	return (
		is_instance_valid(_game_world)
		and _game_world.has_method("is_turn_based_combat_active")
		and bool(_game_world.call("is_turn_based_combat_active"))
	)


func _is_player_combat_turn() -> bool:
	if not is_instance_valid(_game_world):
		_game_world = get_tree().get_first_node_in_group("game_world")
	if not is_instance_valid(_game_world) or not is_instance_valid(_player):
		return false
	var turn_system: TurnBasedCombatSystem = _game_world.get("_turn_system") as TurnBasedCombatSystem
	return (
		turn_system != null
		and turn_system.active
		and turn_system.is_player_turn(_player)
		and not bool(_game_world.get("_enemy_turn_running"))
	)


func _action_button_blocked_now() -> bool:
	if GameState.input_locked:
		return true
	if not _is_combat_active():
		return false
	return not _is_player_combat_turn()


func _restore_simple_action_button_input() -> void:
	if not is_instance_valid(interact_button):
		return
	# Restore the original Godot BaseButton contract. The button emits `pressed`
	# after a normal short tap/release; no separate button_down authorization,
	# touch index, hold duration or post-turn timer is required.
	interact_button.action_mode = BaseButton.ACTION_MODE_BUTTON_RELEASE
	interact_button.focus_mode = Control.FOCUS_NONE
	interact_button.mouse_filter = Control.MOUSE_FILTER_STOP
	var callback := Callable(self, "_on_interact_pressed")
	if not interact_button.pressed.is_connected(callback):
		interact_button.pressed.connect(callback)
	var obsolete_button_down := Callable(self, "_on_action_button_down")
	if interact_button.button_down.is_connected(obsolete_button_down):
		interact_button.button_down.disconnect(obsolete_button_down)


func _on_action_button_down() -> void:
	# Compatibility method for older tests and loaded callables. A press without
	# release deliberately does not toggle the catalogue.
	pass


func _on_interact_pressed() -> void:
	if _action_button_blocked_now():
		_close_action_catalog()
		return
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

	# The catalogue is always available outside combat, even when no trigger is
	# active. Proximity changes only which world actions are listed inside it.
	if _game_world.has_method("_refresh_action_catalog"):
		_game_world.call("_refresh_action_catalog")
	var nearby_count: int = _nearby_interactable_count()
	var opened: bool = false
	if action_catalog.has_method("request_toggle_from_action_button"):
		opened = bool(action_catalog.call("request_toggle_from_action_button"))
	elif action_catalog.has_method("toggle_catalog"):
		action_catalog.call("toggle_catalog")
		opened = action_catalog.has_method("is_catalog_open") and bool(action_catalog.call("is_catalog_open"))
	if opened and nearby_count > 0:
		if action_catalog.has_method("_select_category"):
			action_catalog.call("_select_category", "action")
		if action_catalog.has_method("_select_action_group"):
			action_catalog.call("_select_action_group", "world")


func _nearby_interactable_count() -> int:
	if not is_instance_valid(_player) or not _player.has_method("get_nearby_interactables"):
		return 0
	var value: Variant = _player.call("get_nearby_interactables")
	return (value as Array).size() if value is Array else 0


func _close_action_catalog() -> void:
	if not is_instance_valid(_game_world):
		_game_world = get_tree().get_first_node_in_group("game_world")
	if not is_instance_valid(_game_world):
		return
	var action_catalog: Node = _game_world.get_node_or_null("Interface/ActionCatalogUI")
	if action_catalog != null and action_catalog.has_method("close_catalog"):
		action_catalog.call("close_catalog")
