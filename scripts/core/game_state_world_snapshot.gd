extends "res://scripts/core/game_state_inventory_transactions.gd"

signal world_snapshot_changed

const WORLD_SAVE_VERSION: int = 7
const WORLD_SNAPSHOT_REVISION: int = 1

var world_snapshot: Dictionary = {}


func new_game() -> void:
	super.new_game()
	world_snapshot = _empty_world_snapshot()
	world_snapshot_changed.emit()


func save_game() -> bool:
	if not _world_snapshot_is_stable():
		return false
	_capture_world_snapshot_from_scene()
	return super.save_game()


func save_manual_slot(slot_id: int) -> bool:
	if not _world_snapshot_is_stable():
		return false
	_capture_world_snapshot_from_scene()
	return super.save_manual_slot(slot_id)


func get_world_snapshot() -> Dictionary:
	return world_snapshot.duplicate(true)


func set_world_snapshot(snapshot: Dictionary) -> void:
	world_snapshot = _normalize_world_snapshot(snapshot)
	world_snapshot_changed.emit()


func get_world_entity_state(entity_id: String) -> Dictionary:
	if entity_id.is_empty():
		return {}
	var entities_value: Variant = world_snapshot.get("entities", {})
	if not entities_value is Dictionary:
		return {}
	var state_value: Variant = (entities_value as Dictionary).get(entity_id, {})
	return (state_value as Dictionary).duplicate(true) if state_value is Dictionary else {}


func _build_save_data(kind: String, slot_id: int) -> Dictionary:
	# A save payload must be an immutable point-in-time snapshot. The inherited
	# serializer exposes live Dictionary references for inventory, quests and
	# story flags; detach them before the next gameplay mutation can change an
	# already prepared autosave or manual-slot payload.
	var save_data: Dictionary = super._build_save_data(kind, slot_id).duplicate(true)
	save_data["version"] = WORLD_SAVE_VERSION
	save_data["world_snapshot"] = _normalize_world_snapshot(world_snapshot)
	return save_data


func _apply_save_data(original_data: Dictionary) -> bool:
	var incoming_version: int = int(original_data.get("version", 0))
	var base_data: Dictionary = original_data.duplicate(true)
	var loaded_snapshot: Dictionary = _empty_world_snapshot()
	if incoming_version == WORLD_SAVE_VERSION:
		var snapshot_value: Variant = base_data.get("world_snapshot", {})
		loaded_snapshot = _normalize_world_snapshot(snapshot_value as Dictionary if snapshot_value is Dictionary else {})
		base_data.erase("world_snapshot")
		# The inherited serializer owns versions 1-6. Version 7 only wraps that
		# payload with a stable world snapshot, so the old migration chain remains
		# authoritative for character, quest, inventory and story data.
		base_data["version"] = 6
	elif incoming_version > WORLD_SAVE_VERSION:
		push_error("Неподдерживаемая версия сохранения мира: %d" % incoming_version)
		return false
	if not super._apply_save_data(base_data):
		return false
	world_snapshot = loaded_snapshot
	world_snapshot_changed.emit()
	return true


func _world_snapshot_is_stable() -> bool:
	if not is_inside_tree():
		return true
	for serializer: Node in get_tree().get_nodes_in_group("world_state_serializers"):
		if not is_instance_valid(serializer):
			continue
		if serializer.has_method("can_capture_stable_world_state") and not bool(serializer.call("can_capture_stable_world_state")):
			return false
	return true


func _capture_world_snapshot_from_scene() -> void:
	if not is_inside_tree():
		return
	var serializers: Array[Node] = get_tree().get_nodes_in_group("world_state_serializers")
	if serializers.is_empty():
		# Loading and migration can save before the gameplay scene exists. Keep the
		# loaded snapshot instead of replacing it with an empty dictionary.
		return
	# Preparation is a separate deterministic phase. Runtime systems can flush
	# their current in-memory records before any serializer reads them.
	for serializer: Node in serializers:
		if is_instance_valid(serializer) and serializer.has_method("prepare_world_state_for_save"):
			serializer.call("prepare_world_state_for_save")
	var merged: Dictionary = _empty_world_snapshot()
	var captured_any: bool = false
	for serializer: Node in serializers:
		if not is_instance_valid(serializer) or not serializer.has_method("capture_world_state_for_save"):
			continue
		var value: Variant = serializer.call("capture_world_state_for_save")
		if not value is Dictionary:
			continue
		_merge_world_snapshot(merged, value as Dictionary)
		captured_any = true
	if captured_any:
		world_snapshot = _normalize_world_snapshot(merged)
		world_snapshot_changed.emit()


func _merge_world_snapshot(target: Dictionary, source: Dictionary) -> void:
	for scalar_key: String in ["location_id", "player_facing", "captured_at_unix"]:
		if source.has(scalar_key):
			target[scalar_key] = source[scalar_key]
	for dictionary_key: String in ["entities", "doors", "environment"]:
		var source_value: Variant = source.get(dictionary_key, {})
		if not source_value is Dictionary:
			continue
		var target_value: Variant = target.get(dictionary_key, {})
		var target_dictionary: Dictionary = target_value as Dictionary if target_value is Dictionary else {}
		for key: Variant in (source_value as Dictionary).keys():
			target_dictionary[key] = (source_value as Dictionary)[key]
		target[dictionary_key] = target_dictionary


func _normalize_world_snapshot(snapshot: Dictionary) -> Dictionary:
	var normalized: Dictionary = _empty_world_snapshot()
	normalized["revision"] = maxi(int(snapshot.get("revision", WORLD_SNAPSHOT_REVISION)), 1)
	normalized["location_id"] = str(snapshot.get("location_id", "guard_post"))
	normalized["captured_at_unix"] = int(snapshot.get("captured_at_unix", 0))
	var facing_value: Variant = snapshot.get("player_facing", [1.0, 0.0])
	normalized["player_facing"] = _normalize_vector_value(facing_value, Vector2.RIGHT)
	for dictionary_key: String in ["entities", "doors", "environment"]:
		var value: Variant = snapshot.get(dictionary_key, {})
		normalized[dictionary_key] = (value as Dictionary).duplicate(true) if value is Dictionary else {}
	return normalized


func _normalize_vector_value(value: Variant, fallback: Vector2) -> Array[float]:
	if value is Array and (value as Array).size() >= 2:
		return [float((value as Array)[0]), float((value as Array)[1])]
	if value is Vector2:
		return [(value as Vector2).x, (value as Vector2).y]
	return [fallback.x, fallback.y]


func _empty_world_snapshot() -> Dictionary:
	return {
		"revision": WORLD_SNAPSHOT_REVISION,
		"location_id": "guard_post",
		"captured_at_unix": 0,
		"player_facing": [1.0, 0.0],
		"entities": {},
		"doors": {},
		"environment": {}
	}
