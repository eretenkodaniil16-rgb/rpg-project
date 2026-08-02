extends "res://scripts/ui/mobile_controls_context_actions.gd"

var _explicit_action_press_armed: bool = false
var _explicit_action_touch_index: int = -1
var _explicit_action_mouse_armed: bool = false
var _catalog_open_authorized: bool = false


func _process(delta: float) -> void:
	super._process(delta)
	var catalog: Node = _action_catalog_node()
	if catalog == null or not catalog.has_method("is_catalog_open"):
		_catalog_open_authorized = false
		return
	var catalog_open: bool = bool(catalog.call("is_catalog_open"))
	# The catalogue is a manual UI. No turn transition, movement completion,
	# delayed Button signal or gameplay mechanic may open it without a fresh
	# press that began inside the Actions button.
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
		_catalog_open_authorized = false
		_close_action_catalog()
		return
	_catalog_open_authorized = true
	_explicit_action_press_armed = false
	_explicit_action_touch_index = -1
	_explicit_action_mouse_armed = false
	super._on_interact_pressed()
	var catalog: Node = _action_catalog_node()
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
