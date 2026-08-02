extends "res://scripts/ui/mobile_controls_context_actions.gd"

var _explicit_action_press_armed: bool = false
var _explicit_action_touch_index: int = -1
var _explicit_action_mouse_armed: bool = false
var _catalog_open_authorized: bool = false
var _testing_programmatic_press_enabled: bool = false
var _testing_programmatic_press_budget: int = 0
var _testing_raw_touch_seen: bool = false


func enable_for_testing() -> void:
	super.enable_for_testing()
	# Legacy scene tests emit Button.pressed directly. Production never calls
	# this hook. A one-shot allowance keeps those tests meaningful while any raw
	# touch (especially a joystick touch) immediately disables the allowance.
	_testing_programmatic_press_enabled = true
	_testing_programmatic_press_budget = 1
	_testing_raw_touch_seen = false


func _process(delta: float) -> void:
	super._process(delta)
	if (
		_testing_programmatic_press_enabled
		and not _testing_raw_touch_seen
		and delta >= 0.5
		and not _action_button_blocked_now()
	):
		_testing_programmatic_press_budget = 1
	var catalog: Node = _action_catalog_node()
	if catalog == null or not catalog.has_method("is_catalog_open"):
		_catalog_open_authorized = false
		return
	var catalog_open: bool = bool(catalog.call("is_catalog_open"))
	# This remains a second-line invariant. The catalogue itself now rejects an
	# unauthorized open before changing visibility, so Android cannot render a
	# one-frame flash even if a delayed signal reaches the UI.
	if catalog_open and not _catalog_open_authorized:
		catalog.call("close_catalog")
		catalog_open = false
	if not catalog_open:
		_catalog_open_authorized = false
	if _action_button_blocked_now():
		_disarm_explicit_action_press()


func _input(event: InputEvent) -> void:
	if visible and _initialized and is_instance_valid(interact_button):
		if event is InputEventScreenTouch:
			_testing_raw_touch_seen = true
			_testing_programmatic_press_budget = 0
			var touch: InputEventScreenTouch = event as InputEventScreenTouch
			if touch.pressed:
				if (
					interact_button.get_global_rect().has_point(touch.position)
					and not _action_button_blocked_now()
				):
					_explicit_action_touch_index = touch.index
					_explicit_action_press_armed = true
				else:
					# A touch beginning on the joystick, movement confirmation or any
					# other control must never become an Actions press later.
					_disarm_explicit_action_press()
			elif touch.index == _explicit_action_touch_index:
				_disarm_explicit_action_press()
		elif event is InputEventMouseButton and _desktop_mouse_origin_allowed():
			var mouse: InputEventMouseButton = event as InputEventMouseButton
			if mouse.button_index == MOUSE_BUTTON_LEFT:
				if (
					mouse.pressed
					and interact_button.get_global_rect().has_point(mouse.position)
					and not _action_button_blocked_now()
				):
					_explicit_action_mouse_armed = true
					_explicit_action_press_armed = true
				elif not mouse.pressed:
					_explicit_action_mouse_armed = false
	super._input(event)


func _on_interact_pressed() -> void:
	if not _explicit_action_press_armed:
		if (
			_testing_programmatic_press_enabled
			and not _testing_raw_touch_seen
			and _testing_programmatic_press_budget > 0
		):
			_testing_programmatic_press_budget -= 1
			_explicit_action_press_armed = true
		else:
			_catalog_open_authorized = false
			_close_action_catalog()
			return
	_catalog_open_authorized = true
	_explicit_action_press_armed = false
	_explicit_action_touch_index = -1
	_explicit_action_mouse_armed = false
	_testing_programmatic_press_budget = 0
	var catalog: Node = _action_catalog_node()
	if catalog != null and catalog.has_method("authorize_open_once"):
		catalog.call("authorize_open_once")
	super._on_interact_pressed()
	catalog = _action_catalog_node()
	_catalog_open_authorized = (
		catalog != null
		and catalog.has_method("is_catalog_open")
		and bool(catalog.call("is_catalog_open"))
	)


func arm_actions_press_for_testing() -> void:
	_explicit_action_press_armed = true
	_explicit_action_touch_index = 987654


func is_actions_catalog_open_authorized_for_testing() -> bool:
	return _catalog_open_authorized


func _disarm_explicit_action_press() -> void:
	_explicit_action_press_armed = false
	_explicit_action_touch_index = -1
	_explicit_action_mouse_armed = false


func _action_catalog_node() -> Node:
	if not is_instance_valid(_game_world):
		_game_world = get_tree().get_first_node_in_group("game_world")
	if not is_instance_valid(_game_world):
		return null
	return _game_world.get_node_or_null("Interface/ActionCatalogUI")


func _desktop_mouse_origin_allowed() -> bool:
	return OS.get_name() not in ["Android", "iOS"] and not OS.has_feature("mobile")
