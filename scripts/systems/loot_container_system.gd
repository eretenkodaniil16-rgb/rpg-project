class_name LootContainerSystem
extends RefCounted

const DATA_PATH: String = "res://data/world/loot_containers.json"

var _profiles: Dictionary = {}


func _init() -> void:
	_load_profiles()


func get_profile(container_id: String) -> Dictionary:
	var value: Variant = _profiles.get(container_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func get_profile_ids() -> Array[String]:
	var result: Array[String] = []
	for key: Variant in _profiles.keys():
		result.append(str(key))
	result.sort()
	return result


func build_initial_registry() -> Dictionary:
	var registry: Dictionary = {}
	for container_id: String in get_profile_ids():
		var profile: Dictionary = get_profile(container_id)
		var position: Vector2 = _position_from_value(profile.get("position", [0.0, 0.0]))
		registry[container_id] = {
			"container_id": container_id,
			"container_type": str(profile.get("container_type", "container")),
			"label": str(profile.get("label", "Контейнер")),
			"position": [position.x, position.y],
			"is_open": false,
			"is_locked": bool(profile.get("locked", false)),
			"lock_id": str(profile.get("lock_id", "")),
			"is_discovered": bool(profile.get("discovered", true)),
			"items": normalize_items(profile.get("items", []))
		}
	return registry


func normalize_registry(source: Variant) -> Dictionary:
	var initial: Dictionary = build_initial_registry()
	if not source is Dictionary:
		return initial
	var stored: Dictionary = source as Dictionary
	for key: Variant in stored.keys():
		var container_id: String = str(key)
		var value: Variant = stored.get(key, {})
		if not value is Dictionary:
			continue
		var fallback: Dictionary = initial.get(container_id, {}) as Dictionary if initial.get(container_id, {}) is Dictionary else {}
		var record: Dictionary = _normalize_record(container_id, value as Dictionary, fallback)
		if not record.is_empty():
			initial[container_id] = record
	return initial


func get_record(registry: Dictionary, container_id: String) -> Dictionary:
	var value: Variant = registry.get(container_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func set_open(registry: Dictionary, container_id: String, value: bool) -> Dictionary:
	var updated: Dictionary = registry.duplicate(true)
	var record: Dictionary = get_record(updated, container_id)
	if record.is_empty():
		return {"success": false, "registry": updated, "message": "Контейнер не найден."}
	if bool(record.get("is_locked", false)):
		return {"success": false, "registry": updated, "message": "Контейнер заперт."}
	record["is_open"] = value
	updated[container_id] = record
	return {"success": true, "registry": updated, "record": record.duplicate(true)}


func take_item(
	state: Node,
	registry: Dictionary,
	container_id: String,
	item_id: String,
	requested_quantity: int = 1
) -> Dictionary:
	var updated: Dictionary = registry.duplicate(true)
	if state == null or container_id.is_empty() or item_id.is_empty() or requested_quantity <= 0:
		return _failure(updated, "Некорректный запрос подбора.")
	if not state.has_method("get_item_definition") or not state.has_method("get_item_count") or not state.has_method("add_item"):
		return _failure(updated, "Инвентарь недоступен.")
	var record: Dictionary = get_record(updated, container_id)
	if record.is_empty():
		return _failure(updated, "Контейнер не найден.")
	if bool(record.get("is_locked", false)):
		return _failure(updated, "Контейнер заперт.")
	if not bool(record.get("is_open", false)):
		return _failure(updated, "Сначала откройте контейнер.")
	var items: Array[Dictionary] = normalize_items(record.get("items", []))
	var entry_index: int = -1
	var available: int = 0
	for index: int in range(items.size()):
		if str(items[index].get("item_id", "")) == item_id:
			entry_index = index
			available = maxi(int(items[index].get("quantity", 0)), 0)
			break
	if entry_index < 0 or available <= 0:
		return _failure(updated, "Этого предмета в контейнере больше нет.")
	var definition: Dictionary = state.call("get_item_definition", item_id) as Dictionary
	if definition.is_empty():
		return _failure(updated, "Предмет не зарегистрирован в каталоге.")
	var current: int = maxi(int(state.call("get_item_count", item_id)), 0)
	var maximum: int = int(definition.get("max_stack", 99)) if bool(definition.get("stackable", true)) else 1
	var capacity: int = maxi(maximum - current, 0)
	var quantity: int = mini(mini(requested_quantity, available), capacity)
	if quantity <= 0:
		return _failure(updated, "В инвентаре нет места для этого предмета.")
	var after_add: int = int(state.call("add_item", item_id, quantity, false))
	var actually_added: int = maxi(after_add - current, 0)
	if actually_added != quantity:
		if actually_added > 0 and state.has_method("remove_item"):
			state.call("remove_item", item_id, actually_added, false)
		return _failure(updated, "Предмет не удалось атомарно перенести в инвентарь.")
	var remaining: int = available - quantity
	if remaining <= 0:
		items.remove_at(entry_index)
	else:
		items[entry_index]["quantity"] = remaining
	record["items"] = items
	record["is_open"] = true
	updated[container_id] = record
	return {
		"success": true,
		"registry": updated,
		"record": record.duplicate(true),
		"item_id": item_id,
		"quantity": quantity,
		"remaining_quantity": remaining,
		"empty": items.is_empty(),
		"message": "Предмет перенесён в инвентарь."
	}


func take_all(state: Node, registry: Dictionary, container_id: String) -> Dictionary:
	var updated: Dictionary = registry.duplicate(true)
	var transferred: Array[Dictionary] = []
	var failures: Array[String] = []
	var record: Dictionary = get_record(updated, container_id)
	if record.is_empty():
		return {"success": false, "registry": updated, "transferred": transferred, "failures": ["Контейнер не найден."]}
	var snapshot: Array[Dictionary] = normalize_items(record.get("items", []))
	for entry: Dictionary in snapshot:
		var item_id: String = str(entry.get("item_id", ""))
		var quantity: int = maxi(int(entry.get("quantity", 0)), 0)
		if item_id.is_empty() or quantity <= 0:
			continue
		var result: Dictionary = take_item(state, updated, container_id, item_id, quantity)
		updated = result.get("registry", updated) as Dictionary
		if bool(result.get("success", false)):
			transferred.append({"item_id": item_id, "quantity": int(result.get("quantity", 0))})
		else:
			failures.append(str(result.get("message", "Не удалось подобрать предмет.")))
	return {
		"success": not transferred.is_empty(),
		"registry": updated,
		"record": get_record(updated, container_id),
		"transferred": transferred,
		"failures": failures
	}


func normalize_items(source: Variant) -> Array[Dictionary]:
	var counts: Dictionary = {}
	if source is Array:
		for value: Variant in source as Array:
			if not value is Dictionary:
				continue
			var item_id: String = str((value as Dictionary).get("item_id", ""))
			var quantity: int = maxi(int((value as Dictionary).get("quantity", 0)), 0)
			if item_id.is_empty() or quantity <= 0:
				continue
			counts[item_id] = int(counts.get(item_id, 0)) + quantity
	var ids: Array[String] = []
	for key: Variant in counts.keys():
		ids.append(str(key))
	ids.sort()
	var result: Array[Dictionary] = []
	for item_id: String in ids:
		result.append({"item_id": item_id, "quantity": int(counts[item_id])})
	return result


func _normalize_record(container_id: String, source: Dictionary, fallback: Dictionary) -> Dictionary:
	if container_id.is_empty():
		return {}
	var position: Vector2 = _position_from_value(source.get("position", fallback.get("position", [0.0, 0.0])))
	return {
		"container_id": container_id,
		"container_type": str(source.get("container_type", fallback.get("container_type", "container"))),
		"label": str(source.get("label", fallback.get("label", "Контейнер"))),
		"position": [position.x, position.y],
		"is_open": bool(source.get("is_open", fallback.get("is_open", false))),
		"is_locked": bool(source.get("is_locked", fallback.get("is_locked", false))),
		"lock_id": str(source.get("lock_id", fallback.get("lock_id", ""))),
		"is_discovered": bool(source.get("is_discovered", fallback.get("is_discovered", true))),
		"items": normalize_items(source.get("items", fallback.get("items", [])))
	}


func _position_from_value(value: Variant) -> Vector2:
	if value is Array and (value as Array).size() >= 2:
		return Vector2(float((value as Array)[0]), float((value as Array)[1]))
	if value is Vector2:
		return value as Vector2
	return Vector2.ZERO


func _failure(registry: Dictionary, message: String) -> Dictionary:
	return {"success": false, "registry": registry, "message": message}


func _load_profiles() -> void:
	_profiles.clear()
	if not FileAccess.file_exists(DATA_PATH):
		return
	var file: FileAccess = FileAccess.open(DATA_PATH, FileAccess.READ)
	if file == null:
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if parsed is Dictionary:
		_profiles = (parsed as Dictionary).duplicate(true)
