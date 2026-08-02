extends "res://scripts/ui/mobile_controls.gd"

const COMBAT_ACTION_TURN_GUARD_SECONDS: float = 0.28

var _last_joystick_direction: Vector2 = Vector2.ZERO
var _control_mode_initialized: bool = false
var _last_combat_mode: bool = false
var _last_player_turn_active: bool = false
var _action_turn_guard_remaining: float = 0.0
var _action_press_started_blocked: bool = false


func _ready() -> void:
	super._ready()
	_install_action_press_origin_guard()


func _process(delta: float) -> void:
	super._process(delta)
	var combat_active: bool = _is_combat_active()
	var player_turn_active: bool = combat_active and _is_player_combat_turn()
	if not _control_mode_initialized or combat_active != _last_combat_mode:
		_control_mode_initialized = true
		_last_combat_mode = combat_active
		_apply_player_control_vector(_last_joystick_direction, combat_active)
	if combat_active and player_turn_active != _last_player_turn_active:
		_close_action_catalog()
		_action_turn_guard_remaining = COMBAT_ACTION_TURN_GUARD_SECONDS if player_turn_active else 0.0
		if is_instance_valid(interact_button):
			interact_button.set_pressed_no_signal(false)
	elif not combat_active:
		_action_turn_guard_remaining = 0.0
	_last_player_turn_active = player_turn_active
	_action_turn_guard_remaining = maxf(_action_turn_guard_remaining - maxf(delta, 0.0), 0.0)
	if is_instance_valid(interact_button):
		interact_button.disabled = _action_button_blocked_now()


func _input(event: InputEvent) -> void:
	if visible and _initialized and event is InputEventScreenTouch and is_instance_valid(interact_button):
		var touch: InputEventScreenTouch = event as InputEventScreenTouch
		if touch.pressed and interact_button.get_global_rect().has_point(touch.position):
			_action_press_started_blocked = _action_button_blocked_now()
			if _action_press_started_blocked:
				interact_button.set_pressed_no_signal(false)
				_close_action_catalog()
				get_viewport().set_input_as_handled()
				return
	super._input(event)


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
	return _action_turn_guard_remaining


func action_press_started_blocked_for_testing() -> bool:
	return _action_press_started_blocked


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
	var combat_active: bool = _is_combat_active()
	return (
		GameState.input_locked
		or (
			combat_active
			and (
				not _last_player_turn_active
				or not _is_player_combat_turn()
				or _action_turn_guard_remaining > 0.0
			)
		)
	)


func _install_action_press_origin_guard() -> void:
	if not is_instance_valid(interact_button):
		return
	# Trigger on the physical press, not on release. A finger that went down while
	# the button was disabled can therefore never open the catalog when it is
	# lifted after the turn changes.
	interact_button.action_mode = BaseButton.ACTION_MODE_BUTTON_PRESS
	var callback := Callable(self, "_on_action_button_down")
	if not interact_button.button_down.is_connected(callback):
		interact_button.button_down.connect(callback)


func _on_action_button_down() -> void:
	_action_press_started_blocked = _action_button_blocked_now()
	if _action_press_started_blocked:
		interact_button.set_pressed_no_signal(false)
		_close_action_catalog()


func _on_interact_pressed() -> void:
	var press_started_blocked: bool = _action_press_started_blocked
	_action_press_started_blocked = false
	if press_started_blocked:
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
	if _is_combat_active() and (
		not _is_player_combat_turn()
		or _action_turn_guard_remaining > 0.0
	):
		_close_action_catalog()
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


func _close_action_catalog() -> void:
	if not is_instance_valid(_game_world):
		_game_world = get_tree().get_first_node_in_group("game_world")
	if not is_instance_valid(_game_world):
		return
	var action_catalog: Node = _game_world.get_node_or_null("Interface/ActionCatalogUI")
	if action_catalog != null and action_catalog.has_method("close_catalog"):
		action_catalog.call("close_catalog")
