extends "res://scripts/ui/mobile_controls.gd"

const EMULATED_MOUSE_SUPPRESSION_MS: int = 420
const ACTION_TOUCH_DRAG_CANCEL_PIXELS: float = 28.0
const ACTION_RELEASE_MARGIN_PIXELS: float = 10.0

var _last_joystick_direction: Vector2 = Vector2.ZERO
var _control_mode_initialized: bool = false
var _last_combat_mode: bool = false
var _action_gui_input_connected: bool = false
var _action_state_initialized: bool = false
var _observed_combat_active: bool = false
var _observed_player_turn_active: bool = false
var _observed_input_locked: bool = false
var _observed_gameplay_transition_active: bool = false
var _action_touch_index: int = -1
var _action_touch_origin: Vector2 = Vector2.ZERO
var _action_touch_epoch: int = -1
var _action_touch_cancelled: bool = false
var _action_mouse_armed: bool = false
var _action_mouse_epoch: int = -1
var _last_touch_event_msec: int = -10000
var _action_input_epoch: int = 0
var _user_toggle_count: int = 0


func _ready() -> void:
	super._ready()
	_install_action_intent_pipeline()
	_synchronize_action_state(false)


func enable_for_testing() -> void:
	super.enable_for_testing()
	_install_action_intent_pipeline()
	_synchronize_action_state(false)


func _input(event: InputEvent) -> void:
	if not visible or not _initialized:
		return
	_track_raw_action_input(event)
	super._input(event)


func _process(delta: float) -> void:
	super._process(delta)
	var combat_active: bool = _is_combat_active()
	if not _control_mode_initialized or combat_active != _last_combat_mode:
		_control_mode_initialized = true
		_last_combat_mode = combat_active
		_apply_player_control_vector(_last_joystick_direction, combat_active)
	_synchronize_action_state(true)
	if is_instance_valid(interact_button):
		interact_button.disabled = _action_menu_blocked_now()


func _set_player_vector(direction: Vector2) -> void:
	var normalized_direction: Vector2 = direction.limit_length(1.0)
	var joystick_started: bool = (
		normalized_direction.length_squared() > 0.0001
		and _last_joystick_direction.length_squared() <= 0.0001
	)
	var joystick_stopped: bool = (
		normalized_direction.length_squared() <= 0.0001
		and _last_joystick_direction.length_squared() > 0.0001
	)
	if joystick_started or joystick_stopped:
		_invalidate_action_input_epoch()
	if joystick_started:
		_close_action_catalog()
	_last_joystick_direction = normalized_direction
	var combat_active: bool = _is_combat_active()
	_control_mode_initialized = true
	_last_combat_mode = combat_active
	_apply_player_control_vector(_last_joystick_direction, combat_active)


func _reset_player_input() -> void:
	if _last_joystick_direction.length_squared() > 0.0001:
		_invalidate_action_input_epoch()
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


func _install_action_intent_pipeline() -> void:
	if not is_instance_valid(interact_button):
		return
	var pressed_callback := Callable(self, "_on_interact_pressed")
	if interact_button.pressed.is_connected(pressed_callback):
		interact_button.pressed.disconnect(pressed_callback)
	interact_button.action_mode = BaseButton.ACTION_MODE_BUTTON_RELEASE
	interact_button.focus_mode = Control.FOCUS_NONE
	interact_button.mouse_filter = Control.MOUSE_FILTER_STOP
	var gui_callback := Callable(self, "_on_action_button_gui_input")
	if not interact_button.gui_input.is_connected(gui_callback):
		interact_button.gui_input.connect(gui_callback)
	_action_gui_input_connected = true


func _track_raw_action_input(event: InputEvent) -> void:
	if event is InputEventScreenTouch:
		_handle_raw_action_touch(event as InputEventScreenTouch)
	elif event is InputEventScreenDrag:
		_handle_raw_action_drag(event as InputEventScreenDrag)


func _handle_raw_action_touch(event: InputEventScreenTouch) -> void:
	_last_touch_event_msec = Time.get_ticks_msec()
	var inside_button: bool = _action_button_rect().has_point(event.position)
	if event.pressed:
		if event.index == _action_touch_index:
			_clear_action_touch_transaction()
		if not inside_button:
			return
		get_viewport().set_input_as_handled()
		if _action_menu_blocked_now():
			return
		_action_touch_index = event.index
		_action_touch_origin = event.position
		_action_touch_epoch = _action_input_epoch
		_action_touch_cancelled = false
		return

	if event.index != _action_touch_index:
		if inside_button:
			# A release that started somewhere else must not fall through to the
			# Actions button or the battlefield input beneath it.
			get_viewport().set_input_as_handled()
		return
	get_viewport().set_input_as_handled()
	var release_inside: bool = _action_button_rect().grow(ACTION_RELEASE_MARGIN_PIXELS).has_point(event.position)
	var should_commit: bool = (
		not _action_touch_cancelled
		and _action_touch_epoch == _action_input_epoch
		and release_inside
		and not _action_menu_blocked_now()
	)
	_clear_action_touch_transaction()
	if should_commit:
		_commit_action_menu_intent()


func _handle_raw_action_drag(event: InputEventScreenDrag) -> void:
	if event.index != _action_touch_index:
		return
	get_viewport().set_input_as_handled()
	if event.position.distance_to(_action_touch_origin) > ACTION_TOUCH_DRAG_CANCEL_PIXELS:
		_action_touch_cancelled = true
	if not _action_button_rect().grow(ACTION_RELEASE_MARGIN_PIXELS).has_point(event.position):
		_action_touch_cancelled = true


func _on_action_button_gui_input(event: InputEvent) -> void:
	if event is InputEventScreenTouch or event is InputEventScreenDrag:
		# Touch is handled globally so its origin is known even when controls are
		# disabled, hidden or replaced during movement and turn transitions.
		interact_button.accept_event()
		return
	if event is InputEventMouseButton:
		_handle_action_mouse(event as InputEventMouseButton)


func _handle_action_mouse(event: InputEventMouseButton) -> void:
	if event.button_index != MOUSE_BUTTON_LEFT:
		return
	var now_msec: int = Time.get_ticks_msec()
	if now_msec - _last_touch_event_msec <= EMULATED_MOUSE_SUPPRESSION_MS:
		# Android may emit a synthetic mouse press/release for the same touch.
		# Both halves are consumed so one physical gesture cannot toggle twice.
		_action_mouse_armed = false
		_action_mouse_epoch = -1
		interact_button.accept_event()
		return
	if event.pressed:
		_action_mouse_armed = not _action_menu_blocked_now()
		_action_mouse_epoch = _action_input_epoch if _action_mouse_armed else -1
		interact_button.accept_event()
		return
	if not _action_mouse_armed:
		return
	var should_commit: bool = (
		_action_mouse_epoch == _action_input_epoch
		and not _action_menu_blocked_now()
	)
	_action_mouse_armed = false
	_action_mouse_epoch = -1
	interact_button.accept_event()
	if should_commit:
		_commit_action_menu_intent()


func _commit_action_menu_intent() -> void:
	_synchronize_action_state(true)
	if _action_menu_blocked_now():
		_close_action_catalog()
		return
	_toggle_action_catalog_from_user()


func _toggle_action_catalog_from_user() -> void:
	if not is_instance_valid(_player):
		_player = get_tree().get_first_node_in_group("player") as CharacterBody2D
	if not is_instance_valid(_game_world):
		_game_world = get_tree().get_first_node_in_group("game_world")
	if not is_instance_valid(_game_world):
		return
	var action_catalog: Node = _action_catalog_node()
	if action_catalog == null:
		if is_instance_valid(_player) and _player.has_method("request_interaction"):
			_player.call("request_interaction")
		return
	if _game_world.has_method("_refresh_action_catalog"):
		_game_world.call("_refresh_action_catalog")
	var opened: bool = false
	if action_catalog.has_method("request_toggle_from_action_button"):
		opened = bool(action_catalog.call("request_toggle_from_action_button"))
	elif action_catalog.has_method("toggle_catalog"):
		action_catalog.call("toggle_catalog")
		opened = action_catalog.has_method("is_catalog_open") and bool(action_catalog.call("is_catalog_open"))
	_user_toggle_count += 1
	if opened and _nearby_interactable_count() > 0:
		if action_catalog.has_method("_select_category"):
			action_catalog.call("_select_category", "action")
		if action_catalog.has_method("_select_action_group"):
			action_catalog.call("_select_action_group", "world")


func _synchronize_action_state(close_on_transition: bool) -> void:
	var combat_active: bool = _is_combat_active()
	var player_turn_active: bool = combat_active and _is_player_combat_turn()
	var input_locked: bool = GameState.input_locked
	var gameplay_transition_active: bool = _gameplay_action_transition_active()
	if _action_state_initialized:
		var combat_changed: bool = combat_active != _observed_combat_active
		var player_turn_changed: bool = player_turn_active != _observed_player_turn_active
		var input_lock_changed: bool = input_locked != _observed_input_locked
		var gameplay_transition_changed: bool = gameplay_transition_active != _observed_gameplay_transition_active
		if combat_changed or player_turn_changed or input_lock_changed or gameplay_transition_changed:
			_invalidate_action_input_epoch()
			if close_on_transition:
				_close_action_catalog()
	_observed_combat_active = combat_active
	_observed_player_turn_active = player_turn_active
	_observed_input_locked = input_locked
	_observed_gameplay_transition_active = gameplay_transition_active
	_action_state_initialized = true


func _action_menu_blocked_now() -> bool:
	if GameState.input_locked:
		return true
	if _last_joystick_direction.length_squared() > 0.0001:
		return true
	if _gameplay_action_transition_active():
		return true
	if not _is_combat_active():
		return false
	return not _is_player_combat_turn()


func _gameplay_action_transition_active() -> bool:
	if not is_instance_valid(_game_world):
		_game_world = get_tree().get_first_node_in_group("game_world")
	if not is_instance_valid(_game_world):
		return false
	return (
		bool(_game_world.get("_movement_execution_running"))
		or bool(_game_world.get("_route_drawing"))
		or bool(_game_world.get("_jump_in_progress"))
		or bool(_game_world.get("_attack_in_progress"))
	)


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


func _nearby_interactable_count() -> int:
	if not is_instance_valid(_player) or not _player.has_method("get_nearby_interactables"):
		return 0
	var value: Variant = _player.call("get_nearby_interactables")
	return (value as Array).size() if value is Array else 0


func _action_button_rect() -> Rect2:
	return interact_button.get_global_rect() if is_instance_valid(interact_button) else Rect2()


func _invalidate_action_input_epoch() -> void:
	_action_input_epoch += 1
	_clear_action_touch_transaction()
	_action_mouse_armed = false
	_action_mouse_epoch = -1


func _clear_action_touch_transaction() -> void:
	_action_touch_index = -1
	_action_touch_origin = Vector2.ZERO
	_action_touch_epoch = -1
	_action_touch_cancelled = false


func _close_action_catalog() -> void:
	var catalog: Node = _action_catalog_node()
	if catalog != null and catalog.has_method("close_catalog"):
		catalog.call("close_catalog")


func _on_interact_pressed() -> void:
	# The base scene keeps this callback for compatibility, but production input
	# is handled only by the raw press/release transaction above.
	pass


func simulate_actions_touch_for_testing() -> void:
	var touch_index: int = 9000 + _user_toggle_count
	var center: Vector2 = _action_button_rect().get_center()
	var press := InputEventScreenTouch.new()
	press.index = touch_index
	press.position = center
	press.pressed = true
	_handle_raw_action_touch(press)
	var release := InputEventScreenTouch.new()
	release.index = touch_index
	release.position = center
	release.pressed = false
	_handle_raw_action_touch(release)


func simulate_actions_press_for_testing(touch_index: int = 9100) -> void:
	var press := InputEventScreenTouch.new()
	press.index = touch_index
	press.position = _action_button_rect().get_center()
	press.pressed = true
	_handle_raw_action_touch(press)


func simulate_actions_release_for_testing(touch_index: int = 9100) -> void:
	var release := InputEventScreenTouch.new()
	release.index = touch_index
	release.position = _action_button_rect().get_center()
	release.pressed = false
	_handle_raw_action_touch(release)


func simulate_emulated_mouse_after_touch_for_testing() -> void:
	_last_touch_event_msec = Time.get_ticks_msec()
	var press := InputEventMouseButton.new()
	press.button_index = MOUSE_BUTTON_LEFT
	press.pressed = true
	_handle_action_mouse(press)
	var release := InputEventMouseButton.new()
	release.button_index = MOUSE_BUTTON_LEFT
	release.pressed = false
	_handle_action_mouse(release)


func get_action_user_toggle_count_for_testing() -> int:
	return _user_toggle_count


func get_action_input_epoch_for_testing() -> int:
	return _action_input_epoch


func is_action_gui_pipeline_connected_for_testing() -> bool:
	return _action_gui_input_connected


func get_action_turn_guard_remaining_for_testing() -> float:
	return 0.0


func action_press_started_blocked_for_testing() -> bool:
	return _action_touch_index < 0 and _action_menu_blocked_now()


func arm_actions_press_for_testing() -> void:
	# Compatibility no-op: the controller has no reusable opening latch.
	pass


func is_actions_catalog_open_authorized_for_testing() -> bool:
	var catalog: Node = _action_catalog_node()
	return catalog != null and catalog.has_method("is_catalog_open") and bool(catalog.call("is_catalog_open"))


func _action_catalog_node() -> Node:
	if not is_instance_valid(_game_world):
		_game_world = get_tree().get_first_node_in_group("game_world")
	if not is_instance_valid(_game_world):
		return null
	return _game_world.get_node_or_null("Interface/ActionCatalogUI")
