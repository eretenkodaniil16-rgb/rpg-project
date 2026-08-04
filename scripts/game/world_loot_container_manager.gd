class_name WorldLootContainerManager
extends Node

signal container_changed(container_id: String, record: Dictionary)

const CONTAINER_SCRIPT: Script = preload("res://scripts/game/world_loot_container.gd")
const SNAPSHOT_KEY: String = "loot_containers"

var _system: LootContainerSystem = LootContainerSystem.new()
var _registry: Dictionary = {}
var _nodes: Dictionary = {}
var _restored: bool = false


func _ready() -> void:
	add_to_group("world_state_serializers")
	add_to_group("loot_container_managers")
	call_deferred("restore_from_world_snapshot")


func restore_from_world_snapshot(force: bool = false) -> void:
	if _restored and not force:
		return
	_restored = true
	_clear_nodes()
	var state: Node = _game_state()
	var stored: Variant = {}
	if state != null and state.has_method("get_world_snapshot"):
		var snapshot: Dictionary = state.call("get_world_snapshot") as Dictionary
		var environment_value: Variant = snapshot.get("environment", {})
		if environment_value is Dictionary:
			stored = (environment_value as Dictionary).get(SNAPSHOT_KEY, {})
	_registry = _system.normalize_registry(stored)
	for container_id: String in _system.get_profile_ids():
		var record: Dictionary = _system.get_record(_registry, container_id)
		if record.is_empty() or not bool(record.get("is_discovered", true)):
			continue
		_create_node(record)
	_sync_snapshot_cache()


func get_record(container_id: String) -> Dictionary:
	return _system.get_record(_registry, container_id)


func get_registry_for_testing() -> Dictionary:
	return _registry.duplicate(true)


func get_container_node(container_id: String) -> WorldLootContainer:
	var value: Variant = _nodes.get(container_id, null)
	return value as WorldLootContainer if value is WorldLootContainer and is_instance_valid(value as WorldLootContainer) else null


func open_container(container_id: String, save_after: bool = true) -> Dictionary:
	var result: Dictionary = _system.set_open(_registry, container_id, true)
	if not bool(result.get("success", false)):
		return result
	_registry = (result.get("registry", _registry) as Dictionary).duplicate(true)
	_apply_record_to_node(container_id)
	_sync_snapshot_cache()
	if save_after:
		_save_state()
	var record: Dictionary = get_record(container_id)
	container_changed.emit(container_id, record)
	return {"success": true, "record": record}


func take_item(container_id: String, item_id: String, quantity: int = 1, save_after: bool = true) -> Dictionary:
	var result: Dictionary = _system.take_item(_game_state(), _registry, container_id, item_id, quantity)
	if not bool(result.get("success", false)):
		return result
	_registry = (result.get("registry", _registry) as Dictionary).duplicate(true)
	_apply_record_to_node(container_id)
	_sync_snapshot_cache()
	if save_after:
		_save_state()
	var record: Dictionary = get_record(container_id)
	container_changed.emit(container_id, record)
	result["record"] = record
	return result


func take_all(container_id: String, save_after: bool = true) -> Dictionary:
	var result: Dictionary = _system.take_all(_game_state(), _registry, container_id)
	if not bool(result.get("success", false)) and (result.get("transferred", []) as Array).is_empty():
		return result
	_registry = (result.get("registry", _registry) as Dictionary).duplicate(true)
	_apply_record_to_node(container_id)
	_sync_snapshot_cache()
	if save_after:
		_save_state()
	var record: Dictionary = get_record(container_id)
	container_changed.emit(container_id, record)
	result["record"] = record
	return result


func prepare_world_state_for_save() -> void:
	_prune_invalid_nodes()


func can_capture_stable_world_state() -> bool:
	return true


func capture_world_state_for_save() -> Dictionary:
	return {"environment": {SNAPSHOT_KEY: _registry.duplicate(true)}}


func reload_from_snapshot_for_testing() -> void:
	restore_from_world_snapshot(true)


func _create_node(record: Dictionary) -> WorldLootContainer:
	var container_id: String = str(record.get("container_id", ""))
	if container_id.is_empty():
		return null
	var existing: WorldLootContainer = get_container_node(container_id)
	if existing != null:
		existing.apply_record(record)
		return existing
	var node: WorldLootContainer = CONTAINER_SCRIPT.new() as WorldLootContainer
	node.name = "LootContainer_%s" % container_id
	node.configure(self, record)
	add_child(node)
	node.global_position = _position_from_record(record)
	_nodes[container_id] = node
	return node


func _apply_record_to_node(container_id: String) -> void:
	var node: WorldLootContainer = get_container_node(container_id)
	var record: Dictionary = get_record(container_id)
	if node == null and not record.is_empty() and bool(record.get("is_discovered", true)):
		node = _create_node(record)
	if node != null:
		node.apply_record(record)
		node.global_position = _position_from_record(record)


func _position_from_record(record: Dictionary) -> Vector2:
	var value: Variant = record.get("position", [0.0, 0.0])
	if value is Array and (value as Array).size() >= 2:
		return Vector2(float((value as Array)[0]), float((value as Array)[1]))
	return value as Vector2 if value is Vector2 else Vector2.ZERO


func _sync_snapshot_cache() -> void:
	var state: Node = _game_state()
	if state == null or not state.has_method("get_world_snapshot") or not state.has_method("set_world_snapshot"):
		return
	var snapshot: Dictionary = state.call("get_world_snapshot") as Dictionary
	var environment_value: Variant = snapshot.get("environment", {})
	var environment: Dictionary = (environment_value as Dictionary).duplicate(true) if environment_value is Dictionary else {}
	environment[SNAPSHOT_KEY] = _registry.duplicate(true)
	snapshot["environment"] = environment
	state.call("set_world_snapshot", snapshot)


func _save_state() -> void:
	var state: Node = _game_state()
	if state != null and state.has_method("save_game"):
		state.call("save_game")


func _prune_invalid_nodes() -> void:
	var stale: Array[String] = []
	for key: Variant in _nodes.keys():
		var value: Variant = _nodes.get(key, null)
		if not value is Node or not is_instance_valid(value as Node):
			stale.append(str(key))
	for container_id: String in stale:
		_nodes.erase(container_id)


func _clear_nodes() -> void:
	for value: Variant in _nodes.values():
		if value is Node and is_instance_valid(value as Node):
			(value as Node).queue_free()
	_nodes.clear()


func _game_state() -> Node:
	return get_node_or_null("/root/GameState")
