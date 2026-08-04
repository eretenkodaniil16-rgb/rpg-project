class_name DroppedInventoryItemManager
extends Node

const DROPPED_ITEM_SCRIPT: Script = preload("res://scripts/game/dropped_inventory_item.gd")
const SNAPSHOT_KEY: String = "dropped_inventory_items"

var _records: Dictionary = {}
var _nodes: Dictionary = {}
var _sequence: int = 0
var _restored: bool = false


func _ready() -> void:
	add_to_group("world_state_serializers")
	add_to_group("dropped_inventory_item_managers")
	call_deferred("restore_from_world_snapshot")


func spawn_dropped_item(
	item_id: String,
	quantity: int,
	world_position: Vector2,
	requested_drop_id: String = ""
) -> DroppedInventoryItem:
	if item_id.is_empty() or quantity <= 0:
		return null
	var state: Node = _game_state()
	if state == null or not state.has_method("get_item_definition"):
		return null
	var definition: Dictionary = state.call("get_item_definition", item_id) as Dictionary
	if definition.is_empty():
		return null
	var drop_id: String = requested_drop_id
	if drop_id.is_empty():
		_sequence += 1
		drop_id = "drop_%s_%d_%d" % [item_id, Time.get_ticks_usec(), _sequence]
	var record: Dictionary = {
		"drop_id": drop_id,
		"item_id": item_id,
		"quantity": maxi(quantity, 1),
		"position": [world_position.x, world_position.y]
	}
	_records[drop_id] = record
	return _create_drop_node(record)


func collect_drop(drop_id: String, save_after: bool = true) -> bool:
	var record_value: Variant = _records.get(drop_id, {})
	if not record_value is Dictionary:
		return false
	var state: Node = _game_state()
	if state == null:
		return false
	var record: Dictionary = record_value as Dictionary
	var item_id: String = str(record.get("item_id", ""))
	var quantity: int = maxi(int(record.get("quantity", 1)), 1)
	var definition: Dictionary = state.call("get_item_definition", item_id) as Dictionary
	if definition.is_empty():
		return false
	var current: int = int(state.call("get_item_count", item_id))
	var maximum: int = int(definition.get("max_stack", 99)) if bool(definition.get("stackable", true)) else 1
	if current + quantity > maxi(maximum, 1):
		get_tree().call_group(
			"game_world",
			"show_combat_message",
			"В инвентаре нет места для предмета: %s." % str(definition.get("name", item_id)),
			false
		)
		return false
	var updated: int = int(state.call("add_item", item_id, quantity, false))
	if updated - current != quantity:
		return false
	_records.erase(drop_id)
	var node_value: Variant = _nodes.get(drop_id, null)
	if node_value is Node and is_instance_valid(node_value as Node):
		(node_value as Node).queue_free()
	_nodes.erase(drop_id)
	if save_after and state.has_method("save_game"):
		state.call("save_game")
	get_tree().call_group(
		"game_world",
		"show_combat_message",
		"Подобрано: %s%s." % [
			str(definition.get("name", item_id)),
			" ×%d" % quantity if quantity > 1 else ""
		],
		true
	)
	return true


func restore_from_world_snapshot() -> void:
	if _restored:
		return
	_restored = true
	_records.clear()
	for value: Variant in _nodes.values():
		if value is Node and is_instance_valid(value as Node):
			(value as Node).queue_free()
	_nodes.clear()
	var state: Node = _game_state()
	if state == null or not state.has_method("get_world_snapshot"):
		return
	var snapshot: Dictionary = state.call("get_world_snapshot") as Dictionary
	var environment_value: Variant = snapshot.get("environment", {})
	if not environment_value is Dictionary:
		return
	var dropped_value: Variant = (environment_value as Dictionary).get(SNAPSHOT_KEY, {})
	if not dropped_value is Dictionary:
		return
	for key_value: Variant in (dropped_value as Dictionary).keys():
		var value: Variant = (dropped_value as Dictionary).get(key_value, {})
		if not value is Dictionary:
			continue
		var record: Dictionary = _normalize_record(str(key_value), value as Dictionary)
		if record.is_empty():
			continue
		var drop_id: String = str(record.get("drop_id", ""))
		_records[drop_id] = record
		_create_drop_node(record)


func prepare_world_state_for_save() -> void:
	_prune_invalid_nodes()


func can_capture_stable_world_state() -> bool:
	return true


func capture_world_state_for_save() -> Dictionary:
	return {
		"environment": {
			SNAPSHOT_KEY: _records.duplicate(true)
		}
	}


func get_drop_records_for_testing() -> Dictionary:
	return _records.duplicate(true)


func get_drop_count_for_testing() -> int:
	return _records.size()


func get_drop_node_for_testing(drop_id: String) -> DroppedInventoryItem:
	var value: Variant = _nodes.get(drop_id, null)
	return value as DroppedInventoryItem if value is DroppedInventoryItem else null


func _create_drop_node(record: Dictionary) -> DroppedInventoryItem:
	var drop_id: String = str(record.get("drop_id", ""))
	if drop_id.is_empty():
		return null
	var existing_value: Variant = _nodes.get(drop_id, null)
	if existing_value is DroppedInventoryItem and is_instance_valid(existing_value as DroppedInventoryItem):
		return existing_value as DroppedInventoryItem
	var state: Node = _game_state()
	if state == null or not state.has_method("get_item_definition"):
		return null
	var item_id: String = str(record.get("item_id", ""))
	var definition: Dictionary = state.call("get_item_definition", item_id) as Dictionary
	if definition.is_empty():
		return null
	var dropped: DroppedInventoryItem = DROPPED_ITEM_SCRIPT.new() as DroppedInventoryItem
	dropped.name = "Dropped_%s" % drop_id
	dropped.configure(
		self,
		drop_id,
		item_id,
		maxi(int(record.get("quantity", 1)), 1),
		definition
	)
	add_child(dropped)
	dropped.global_position = _position_from_record(record)
	_nodes[drop_id] = dropped
	return dropped


func _normalize_record(fallback_drop_id: String, source: Dictionary) -> Dictionary:
	var state: Node = _game_state()
	if state == null or not state.has_method("get_item_definition"):
		return {}
	var item_id: String = str(source.get("item_id", ""))
	var drop_id: String = str(source.get("drop_id", fallback_drop_id))
	var quantity: int = maxi(int(source.get("quantity", 1)), 1)
	var definition: Dictionary = state.call("get_item_definition", item_id) as Dictionary
	if item_id.is_empty() or drop_id.is_empty() or definition.is_empty():
		return {}
	var position: Vector2 = _position_from_record(source)
	return {
		"drop_id": drop_id,
		"item_id": item_id,
		"quantity": quantity,
		"position": [position.x, position.y]
	}


func _position_from_record(record: Dictionary) -> Vector2:
	var value: Variant = record.get("position", [0.0, 0.0])
	if value is Array and (value as Array).size() >= 2:
		return Vector2(float((value as Array)[0]), float((value as Array)[1]))
	if value is Vector2:
		return value as Vector2
	return Vector2.ZERO


func _prune_invalid_nodes() -> void:
	var stale_ids: Array[String] = []
	for key_value: Variant in _nodes.keys():
		var drop_id: String = str(key_value)
		var value: Variant = _nodes.get(drop_id, null)
		if not value is Node or not is_instance_valid(value as Node):
			stale_ids.append(drop_id)
	for drop_id: String in stale_ids:
		_nodes.erase(drop_id)


func _game_state() -> Node:
	return get_node_or_null("/root/GameState")
