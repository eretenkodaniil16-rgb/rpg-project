extends "res://scripts/ui/mobile_controls_context_actions.gd"

var _user_toggle_count: int = 0


func _on_interact_pressed() -> void:
	var was_open: bool = _is_catalog_open()
	super._on_interact_pressed()
	var is_open: bool = _is_catalog_open()
	if was_open != is_open:
		_user_toggle_count += 1


func arm_actions_press_for_testing() -> void:
	# Compatibility no-op. The production button no longer requires arming.
	pass


func is_actions_catalog_open_authorized_for_testing() -> bool:
	return _is_catalog_open()


func get_action_user_toggle_count_for_testing() -> int:
	return _user_toggle_count


func get_action_input_epoch_for_testing() -> int:
	return _user_toggle_count


func get_catalog_visibility_correction_count_for_testing() -> int:
	# There is no external visibility owner anymore. The catalogue itself owns
	# open/close state and generic mobile toggle calls remain rejected there.
	return 0


func is_action_gui_pipeline_connected_for_testing() -> bool:
	if not is_instance_valid(interact_button):
		return false
	return (
		interact_button.action_mode == BaseButton.ACTION_MODE_BUTTON_RELEASE
		and interact_button.pressed.is_connected(Callable(self, "_on_interact_pressed"))
	)


func simulate_actions_touch_for_testing() -> void:
	if is_instance_valid(interact_button):
		interact_button.emit_signal("pressed")


func simulate_actions_press_for_testing(_touch_index: int = 9100) -> void:
	# ACTION_MODE_BUTTON_RELEASE: beginning a touch alone does not activate.
	pass


func simulate_actions_release_for_testing(_touch_index: int = 9100) -> void:
	if is_instance_valid(interact_button):
		interact_button.emit_signal("pressed")


func simulate_unowned_action_release_for_testing(_touch_index: int = 9200) -> void:
	# A release not routed by BaseButton cannot emit this button's `pressed`.
	pass


func simulate_emulated_mouse_after_touch_for_testing() -> void:
	# Godot BaseButton owns touch/mouse de-duplication.
	pass


func _is_catalog_open() -> bool:
	var catalog: Node = _action_catalog_node()
	return (
		catalog != null
		and catalog.has_method("is_catalog_open")
		and bool(catalog.call("is_catalog_open"))
	)


func _action_catalog_node() -> Node:
	if not is_instance_valid(_game_world):
		_game_world = get_tree().get_first_node_in_group("game_world")
	if not is_instance_valid(_game_world):
		return null
	return _game_world.get_node_or_null("Interface/ActionCatalogUI")
