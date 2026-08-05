extends "res://scripts/game/game_guard_post_polish_runtime.gd"

const LEGACY_CATALOG_METHODS: Array[StringName] = [
	&"_on_catalog_action_requested",
	&"_on_feedback_catalog_action_requested"
]


func _ready() -> void:
	super._ready()
	call_deferred("_bind_party_action_catalog")


func _bind_party_action_catalog() -> void:
	if _action_catalog_ui == null:
		return
	var signal_name: StringName = &"action_requested"
	for connection_value: Variant in _action_catalog_ui.get_signal_connection_list(signal_name):
		if not connection_value is Dictionary:
			continue
		var callable_value: Variant = (connection_value as Dictionary).get("callable")
		if not callable_value is Callable:
			continue
		var existing: Callable = callable_value as Callable
		if existing.get_object() == self and existing.get_method() in LEGACY_CATALOG_METHODS:
			_action_catalog_ui.disconnect(signal_name, existing)
	var party_handler := Callable(self, "_on_party_catalog_action_requested")
	if not _action_catalog_ui.is_connected(signal_name, party_handler):
		_action_catalog_ui.connect(signal_name, party_handler)


func _on_party_catalog_action_requested(action_id: String) -> void:
	# Invoke the most-derived party handler explicitly. The inherited feedback
	# runtime connected its own method name while the lower-level game script was
	# active, which could bypass the later ally-specific override.
	_on_feedback_catalog_action_requested(action_id)


func get_catalog_action_handler_methods_for_testing() -> Array[String]:
	var result: Array[String] = []
	if _action_catalog_ui == null:
		return result
	for connection_value: Variant in _action_catalog_ui.get_signal_connection_list(&"action_requested"):
		if not connection_value is Dictionary:
			continue
		var callable_value: Variant = (connection_value as Dictionary).get("callable")
		if callable_value is Callable:
			var callable: Callable = callable_value as Callable
			if callable.get_object() == self:
				result.append(str(callable.get_method()))
	return result
