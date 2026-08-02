extends "res://scripts/ui/mobile_controls_context_actions.gd"

var _explicit_action_press_armed: bool = false
var _catalog_open_authorized: bool = false


func enable_for_testing() -> void:
	super.enable_for_testing()
	_explicit_action_press_armed = false
	_catalog_open_authorized = false


func _process(delta: float) -> void:
	super._process(delta)
	var catalog: Node = _action_catalog_node()
	if catalog == null or not catalog.has_method("is_catalog_open"):
		_catalog_open_authorized = false
		return
	if not bool(catalog.call("is_catalog_open")):
		_catalog_open_authorized = false
	if _action_button_blocked_now():
		_explicit_action_press_armed = false


func _on_action_button_down() -> void:
	super._on_action_button_down()
	_explicit_action_press_armed = not _action_press_started_blocked and not _action_button_blocked_now()
	if not _explicit_action_press_armed:
		_catalog_open_authorized = false


func _on_interact_pressed() -> void:
	if not _explicit_action_press_armed:
		_catalog_open_authorized = false
		_close_action_catalog()
		return
	# Consume the GUI-origin latch in the same call stack as the pressed signal.
	# No frame, turn transition or gameplay signal can retain it for later use.
	_explicit_action_press_armed = false
	super._on_interact_pressed()
	var catalog: Node = _action_catalog_node()
	_catalog_open_authorized = (
		catalog != null
		and catalog.has_method("is_catalog_open")
		and bool(catalog.call("is_catalog_open"))
	)


func arm_actions_press_for_testing() -> void:
	_explicit_action_press_armed = true


func is_actions_catalog_open_authorized_for_testing() -> bool:
	return _catalog_open_authorized


func _action_catalog_node() -> Node:
	if not is_instance_valid(_game_world):
		_game_world = get_tree().get_first_node_in_group("game_world")
	if not is_instance_valid(_game_world):
		return null
	return _game_world.get_node_or_null("Interface/ActionCatalogUI")