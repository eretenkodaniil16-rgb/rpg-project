extends "res://scripts/ui/mobile_controls_context_actions.gd"

var _explicit_action_press_armed: bool = false
var _catalog_open_authorized: bool = false
var _catalog_expected_open: bool = false
var _catalog_visibility_guard_connected: bool = false
var _catalog_visibility_correction: bool = false
var _catalog_visibility_correction_count: int = 0
var _gameplay_transition_was_active: bool = false
var _user_toggle_count: int = 0


func _ready() -> void:
	super._ready()
	_reset_action_catalog_state()
	_install_catalog_visibility_guard()


func enable_for_testing() -> void:
	super.enable_for_testing()
	_reset_action_catalog_state()
	_install_catalog_visibility_guard()


func _process(delta: float) -> void:
	super._process(delta)
	_install_catalog_visibility_guard()
	var gameplay_transition_active: bool = _gameplay_action_transition_active()
	if gameplay_transition_active and not _gameplay_transition_was_active:
		_explicit_action_press_armed = false
		_close_action_catalog()
	_gameplay_transition_was_active = gameplay_transition_active

	var catalog: Node = _action_catalog_node()
	if catalog == null or not catalog.has_method("is_catalog_open"):
		_catalog_expected_open = false
		_catalog_open_authorized = false
		return
	var actual_open: bool = bool(catalog.call("is_catalog_open"))
	if actual_open and not _catalog_expected_open:
		_close_unexpected_catalog_visibility()
	elif not actual_open:
		_catalog_expected_open = false
		_catalog_open_authorized = false
	if _action_button_blocked_now():
		_explicit_action_press_armed = false


func _action_button_blocked_now() -> bool:
	# A real button_down is already an authoritative GUI-origin event. The old
	# 0.28 s turn-transition timer existed only to suppress delayed pressed
	# signals, which are now rejected by the explicit arm below. Keeping that
	# timer in the disabled state made legitimate quick taps feel unresponsive.
	if GameState.input_locked or _gameplay_action_transition_active():
		return true
	if not _is_combat_active():
		return false
	return not _is_player_combat_turn()


func _on_action_button_down() -> void:
	if not _action_button_blocked_now():
		_action_turn_guard_remaining = 0.0
	super._on_action_button_down()
	_explicit_action_press_armed = (
		not _action_press_started_blocked
		and not _action_button_blocked_now()
	)
	if not _explicit_action_press_armed:
		_catalog_open_authorized = false


func _on_interact_pressed() -> void:
	var catalog: Node = _action_catalog_node()
	var was_open: bool = (
		catalog != null
		and catalog.has_method("is_catalog_open")
		and bool(catalog.call("is_catalog_open"))
	)
	if not _explicit_action_press_armed:
		_catalog_expected_open = false
		_catalog_open_authorized = false
		_close_action_catalog()
		return

	# The normal BaseButton button_down -> pressed path is intentionally kept.
	# It reacts to a regular tap immediately and stores no touch index that can
	# remain stuck when a finger leaves the button before release.
	_explicit_action_press_armed = false
	_catalog_expected_open = not was_open
	_catalog_open_authorized = _catalog_expected_open
	super._on_interact_pressed()
	_user_toggle_count += 1

	catalog = _action_catalog_node()
	var actual_open: bool = (
		catalog != null
		and catalog.has_method("is_catalog_open")
		and bool(catalog.call("is_catalog_open"))
	)
	_catalog_expected_open = actual_open
	_catalog_open_authorized = actual_open


func _close_action_catalog() -> void:
	_catalog_expected_open = false
	_catalog_open_authorized = false
	super._close_action_catalog()


func _reset_action_catalog_state() -> void:
	_explicit_action_press_armed = false
	_catalog_open_authorized = false
	_catalog_expected_open = false
	_gameplay_transition_was_active = _gameplay_action_transition_active()


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


func _install_catalog_visibility_guard() -> void:
	if _catalog_visibility_guard_connected:
		return
	var panel: CanvasItem = _action_catalog_panel()
	if panel == null:
		return
	var callback := Callable(self, "_on_catalog_panel_visibility_changed")
	if not panel.visibility_changed.is_connected(callback):
		panel.visibility_changed.connect(callback)
	_catalog_visibility_guard_connected = true


func _on_catalog_panel_visibility_changed() -> void:
	if _catalog_visibility_correction:
		return
	var panel: CanvasItem = _action_catalog_panel()
	if panel == null:
		return
	if panel.visible and not _catalog_expected_open:
		_close_unexpected_catalog_visibility()
	elif not panel.visible:
		_catalog_expected_open = false
		_catalog_open_authorized = false


func _close_unexpected_catalog_visibility() -> void:
	if _catalog_visibility_correction:
		return
	_catalog_visibility_correction = true
	_catalog_visibility_correction_count += 1
	var catalog: Node = _action_catalog_node()
	if catalog != null and catalog.has_method("close_catalog"):
		catalog.call("close_catalog")
	_catalog_visibility_correction = false
	_catalog_expected_open = false
	_catalog_open_authorized = false


func _action_catalog_panel() -> CanvasItem:
	var catalog: Node = _action_catalog_node()
	if catalog == null:
		return null
	var panel_value: Variant = catalog.get("panel")
	return panel_value as CanvasItem if panel_value is CanvasItem else null


func arm_actions_press_for_testing() -> void:
	_explicit_action_press_armed = true


func is_actions_catalog_open_authorized_for_testing() -> bool:
	return _catalog_open_authorized


func get_action_user_toggle_count_for_testing() -> int:
	return _user_toggle_count


func get_action_input_epoch_for_testing() -> int:
	return _user_toggle_count


func get_catalog_visibility_correction_count_for_testing() -> int:
	return _catalog_visibility_correction_count


func is_action_gui_pipeline_connected_for_testing() -> bool:
	if not is_instance_valid(interact_button):
		return false
	return (
		interact_button.button_down.is_connected(Callable(self, "_on_action_button_down"))
		and interact_button.pressed.is_connected(Callable(self, "_on_interact_pressed"))
	)


func simulate_actions_touch_for_testing() -> void:
	if not is_instance_valid(interact_button):
		return
	interact_button.emit_signal("button_down")
	interact_button.emit_signal("pressed")


func simulate_actions_press_for_testing(_touch_index: int = 9100) -> void:
	if is_instance_valid(interact_button):
		interact_button.emit_signal("button_down")


func simulate_actions_release_for_testing(_touch_index: int = 9100) -> void:
	if is_instance_valid(interact_button):
		interact_button.emit_signal("pressed")


func simulate_unowned_action_release_for_testing(_touch_index: int = 9200) -> void:
	# A release not routed through BaseButton has no relationship to Actions.
	pass


func simulate_emulated_mouse_after_touch_for_testing() -> void:
	# BaseButton owns touch/mouse de-duplication again; no parallel raw pipeline
	# exists that could toggle the catalogue a second time.
	pass


func _action_catalog_node() -> Node:
	if not is_instance_valid(_game_world):
		_game_world = get_tree().get_first_node_in_group("game_world")
	if not is_instance_valid(_game_world):
		return null
	return _game_world.get_node_or_null("Interface/ActionCatalogUI")
