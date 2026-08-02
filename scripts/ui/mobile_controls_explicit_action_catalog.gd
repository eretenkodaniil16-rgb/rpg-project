extends "res://scripts/ui/mobile_controls_context_actions.gd"

const EMULATED_MOUSE_SUPPRESSION_MS: int = 420

var _action_gui_input_connected: bool = false
var _action_state_initialized: bool = false
var _observed_combat_active: bool = false
var _observed_player_turn_active: bool = false
var _last_touch_intent_msec: int = -10000
var _user_toggle_count: int = 0


func _ready() -> void:
	super._ready()
	_install_action_intent_pipeline()
	_synchronize_action_state(false)


func enable_for_testing() -> void:
	super.enable_for_testing()
	_install_action_intent_pipeline()
	_synchronize_action_state(false)


func _process(delta: float) -> void:
	# Neutralize the legacy button-down/turn-guard pipeline before the inherited
	# process runs. Opening is now controlled exclusively by this script's
	# GUI-origin intent transaction.
	var combat_active: bool = _is_combat_active()
	var player_turn_active: bool = combat_active and _is_player_combat_turn()
	_control_mode_initialized = true
	_last_combat_mode = combat_active
	_last_player_turn_active = player_turn_active
	_action_turn_guard_remaining = 0.0
	_action_press_started_blocked = false
	super._process(delta)
	_synchronize_action_state(true)
	if is_instance_valid(interact_button):
		interact_button.disabled = _action_menu_blocked_now()


func _install_action_intent_pipeline() -> void:
	if not is_instance_valid(interact_button):
		return
	var pressed_callback := Callable(self, "_on_interact_pressed")
	if interact_button.pressed.is_connected(pressed_callback):
		interact_button.pressed.disconnect(pressed_callback)
	var down_callback := Callable(self, "_on_action_button_down")
	if interact_button.button_down.is_connected(down_callback):
		interact_button.button_down.disconnect(down_callback)
	interact_button.action_mode = BaseButton.ACTION_MODE_BUTTON_RELEASE
	interact_button.focus_mode = Control.FOCUS_NONE
	interact_button.mouse_filter = Control.MOUSE_FILTER_STOP
	var gui_callback := Callable(self, "_on_action_button_gui_input")
	if not interact_button.gui_input.is_connected(gui_callback):
		interact_button.gui_input.connect(gui_callback)
	_action_gui_input_connected = true


func _on_action_button_gui_input(event: InputEvent) -> void:
	if not _event_is_primary_press(event):
		return
	var now_msec: int = Time.get_ticks_msec()
	if event is InputEventScreenTouch:
		_last_touch_intent_msec = now_msec
	elif event is InputEventMouseButton and now_msec - _last_touch_intent_msec <= EMULATED_MOUSE_SUPPRESSION_MS:
		# Android can emit a synthetic mouse press for the same physical touch.
		# Consuming it prevents the second toggle that previously caused a flash.
		interact_button.accept_event()
		return
	_synchronize_action_state(true)
	if _action_menu_blocked_now():
		_close_action_catalog()
		interact_button.accept_event()
		return
	_toggle_action_catalog_from_user()
	interact_button.accept_event()


func _event_is_primary_press(event: InputEvent) -> bool:
	if event is InputEventScreenTouch:
		return (event as InputEventScreenTouch).pressed
	if event is InputEventMouseButton:
		var mouse_event := event as InputEventMouseButton
		return mouse_event.pressed and mouse_event.button_index == MOUSE_BUTTON_LEFT
	return false


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
	if _action_state_initialized and close_on_transition:
		var combat_changed: bool = combat_active != _observed_combat_active
		var player_turn_ended: bool = _observed_player_turn_active and not player_turn_active
		if combat_changed or player_turn_ended:
			_close_action_catalog()
	_observed_combat_active = combat_active
	_observed_player_turn_active = player_turn_active
	_action_state_initialized = true


func _action_menu_blocked_now() -> bool:
	if GameState.input_locked:
		return true
	if not _is_combat_active():
		return false
	return not _is_player_combat_turn()


func _on_action_button_down() -> void:
	# Legacy signal intentionally ignored. GUI input is the sole source of a
	# user action-menu intent.
	pass


func _on_interact_pressed() -> void:
	# Legacy BaseButton.pressed intentionally ignored. Keeping the method as a
	# no-op prevents stale or synthetic pressed signals from opening or closing
	# the menu if another scene connects them accidentally.
	pass


func simulate_actions_touch_for_testing() -> void:
	_synchronize_action_state(true)
	if not _action_menu_blocked_now():
		_toggle_action_catalog_from_user()


func simulate_emulated_mouse_after_touch_for_testing() -> void:
	_last_touch_intent_msec = Time.get_ticks_msec()
	var mouse_event := InputEventMouseButton.new()
	mouse_event.button_index = MOUSE_BUTTON_LEFT
	mouse_event.pressed = true
	_on_action_button_gui_input(mouse_event)


func get_action_user_toggle_count_for_testing() -> int:
	return _user_toggle_count


func is_action_gui_pipeline_connected_for_testing() -> bool:
	return _action_gui_input_connected


func arm_actions_press_for_testing() -> void:
	# Compatibility no-op: there is no reusable opening latch anymore.
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
