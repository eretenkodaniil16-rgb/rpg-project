class_name CorpseInteractionSystem
extends RefCounted

const DATA_PATH: String = "res://data/world/corpse_loot_profiles.json"
const RESTRAINT_DATA_PATH: String = "res://data/rules/restraint_sources.json"
const REGISTRY_KEY: String = "corpse_registry_v1"

const BODY_ALIVE: String = "alive"
const BODY_UNCONSCIOUS: String = "unconscious"
const BODY_DEAD: String = "dead"
const VALID_DEFEAT_OUTCOMES: Array[String] = [BODY_UNCONSCIOUS, BODY_DEAD]

var _profiles: Dictionary = {}
var _restraint_sources: Dictionary = {}


func _init() -> void:
	_load_profiles()
	_load_restraint_sources()


func get_profile(actor_id: String) -> Dictionary:
	var value: Variant = _profiles.get(actor_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func has_profile(actor_id: String) -> bool:
	return not get_profile(actor_id).is_empty()


func get_record(state: Node, actor_id: String) -> Dictionary:
	if state == null or actor_id.is_empty():
		return {}
	var registry: Dictionary = _registry(state)
	var value: Variant = registry.get(actor_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func mark_defeated(
	state: Node,
	actor_id: String,
	world_position: Vector2,
	defeat_outcome_override: String = ""
) -> Dictionary:
	var profile: Dictionary = get_profile(actor_id)
	if state == null or profile.is_empty():
		return {}
	var outcome: String = defeat_outcome_override
	if outcome not in VALID_DEFEAT_OUTCOMES:
		outcome = str(profile.get("defeat_outcome", BODY_DEAD))
	if outcome not in VALID_DEFEAT_OUTCOMES:
		outcome = BODY_DEAD
	var registry: Dictionary = _registry(state)
	var existing: Dictionary = registry.get(actor_id, {}) as Dictionary if registry.get(actor_id, {}) is Dictionary else {}
	var record: Dictionary = existing.duplicate(true)
	if record.is_empty():
		record = {
			"corpse_id": str(profile.get("corpse_id", "body_%s" % actor_id)),
			"actor_id": actor_id,
			"body_state": outcome,
			"remaining_loot": _normalized_loot(profile.get("loot", [])),
			"drag_weight": str(profile.get("drag_weight", "medium")),
			"position": [world_position.x, world_position.y],
			"bound": false,
			"binding_item_id": "",
			"binding_label": "",
			"binding_kind": "",
			"restraint_escape_dc": 0,
			"nonlethal_knockout": outcome == BODY_UNCONSCIOUS
		}
	else:
		record["body_state"] = outcome
		record["position"] = [world_position.x, world_position.y]
		record["nonlethal_knockout"] = outcome == BODY_UNCONSCIOUS
		_ensure_binding_fields(record)
	registry[actor_id] = record
	_store_registry(state, registry, true)
	return record.duplicate(true)


func clear_record(state: Node, actor_id: String, save_after: bool = true) -> void:
	if state == null or actor_id.is_empty():
		return
	var registry: Dictionary = _registry(state)
	if not registry.erase(actor_id):
		return
	_store_registry(state, registry, save_after)


func update_body_position(state: Node, actor_id: String, world_position: Vector2, save_after: bool = true) -> bool:
	var registry: Dictionary = _registry(state)
	var value: Variant = registry.get(actor_id, {})
	if not value is Dictionary:
		return false
	var record: Dictionary = (value as Dictionary).duplicate(true)
	record["position"] = [world_position.x, world_position.y]
	registry[actor_id] = record
	_store_registry(state, registry, save_after)
	return true


func get_body_position(record: Dictionary, fallback: Vector2 = Vector2.ZERO) -> Vector2:
	var value: Variant = record.get("position", [])
	if value is Array and (value as Array).size() >= 2:
		return Vector2(float((value as Array)[0]), float((value as Array)[1]))
	return fallback


func is_bound(state: Node, actor_id: String) -> bool:
	return bool(get_record(state, actor_id).get("bound", false))


func get_binding_context(state: Node, actor_id: String) -> Dictionary:
	var record: Dictionary = get_record(state, actor_id)
	if record.is_empty() or not bool(record.get("bound", false)):
		return {}
	return {
		"bound": true,
		"item_id": str(record.get("binding_item_id", "")),
		"label": str(record.get("binding_label", "путы")),
		"kind": str(record.get("binding_kind", "restraint")),
		"escape_dc": maxi(int(record.get("restraint_escape_dc", 0)), 0)
	}


func get_available_restraint_sources(state: Node, actor_id: String) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	var record: Dictionary = get_record(state, actor_id)
	if state == null or str(record.get("body_state", BODY_ALIVE)) != BODY_UNCONSCIOUS or bool(record.get("bound", false)):
		return result
	if not state.has_method("get_item_count"):
		return result
	var registry: Dictionary = _registry(state)
	var source_ids: Array[String] = []
	for source_key: Variant in _restraint_sources.keys():
		source_ids.append(str(source_key))
	source_ids.sort()
	for item_id: String in source_ids:
		var source_value: Variant = _restraint_sources.get(item_id, {})
		if not source_value is Dictionary:
			continue
		var source: Dictionary = source_value as Dictionary
		var capacity_per_item: int = maxi(int(source.get("capacity", 1)), 1)
		var owned_count: int = maxi(int(state.call("get_item_count", item_id)), 0)
		var total_capacity: int = owned_count * capacity_per_item
		var reserved: int = _reserved_restraint_uses(registry, item_id, actor_id)
		var available: int = maxi(total_capacity - reserved, 0)
		if available <= 0:
			continue
		result.append({
			"item_id": item_id,
			"label": str(source.get("label", item_id)),
			"kind": str(source.get("kind", "restraint")),
			"escape_dc": maxi(int(source.get("escape_dc", 10)), 1),
			"available_uses": available
		})
	return result


func bind_unconscious(state: Node, actor_id: String, item_id: String) -> Dictionary:
	if state == null or actor_id.is_empty() or item_id.is_empty():
		return {"success": false, "message": "Некорректный запрос связывания."}
	var registry: Dictionary = _registry(state)
	var value: Variant = registry.get(actor_id, {})
	if not value is Dictionary:
		return {"success": false, "message": "Бессознательная цель не зарегистрирована."}
	var record: Dictionary = (value as Dictionary).duplicate(true)
	if str(record.get("body_state", BODY_ALIVE)) != BODY_UNCONSCIOUS:
		return {"success": false, "message": "Связать можно только живую цель без сознания."}
	if bool(record.get("bound", false)):
		return {"success": false, "message": "Цель уже связана."}
	var selected: Dictionary = {}
	for source: Dictionary in get_available_restraint_sources(state, actor_id):
		if str(source.get("item_id", "")) == item_id:
			selected = source
			break
	if selected.is_empty():
		return {"success": false, "message": "Свободных пут этого типа нет."}
	record["bound"] = true
	record["binding_item_id"] = item_id
	record["binding_label"] = str(selected.get("label", item_id))
	record["binding_kind"] = str(selected.get("kind", "restraint"))
	record["restraint_escape_dc"] = maxi(int(selected.get("escape_dc", 10)), 1)
	registry[actor_id] = record
	_store_registry(state, registry, true)
	return {
		"success": true,
		"item_id": item_id,
		"label": str(record.get("binding_label", item_id)),
		"escape_dc": int(record.get("restraint_escape_dc", 10)),
		"message": "Бессознательная цель связана."
	}


func release_restraint(state: Node, actor_id: String) -> Dictionary:
	if state == null or actor_id.is_empty():
		return {"success": false, "message": "Некорректный запрос освобождения."}
	var registry: Dictionary = _registry(state)
	var value: Variant = registry.get(actor_id, {})
	if not value is Dictionary:
		return {"success": false, "message": "Цель не зарегистрирована."}
	var record: Dictionary = (value as Dictionary).duplicate(true)
	if not bool(record.get("bound", false)):
		return {"success": false, "message": "Цель не связана."}
	var label: String = str(record.get("binding_label", "путы"))
	record["bound"] = false
	record["binding_item_id"] = ""
	record["binding_label"] = ""
	record["binding_kind"] = ""
	record["restraint_escape_dc"] = 0
	registry[actor_id] = record
	_store_registry(state, registry, true)
	return {"success": true, "label": label, "message": "Путы освобождены и снова доступны."}


func get_remaining_loot(state: Node, actor_id: String) -> Array[Dictionary]:
	var record: Dictionary = get_record(state, actor_id)
	return _normalized_loot(record.get("remaining_loot", []))


func take_item(state: Node, actor_id: String, item_id: String, requested_quantity: int = 1) -> Dictionary:
	if state == null or actor_id.is_empty() or item_id.is_empty() or requested_quantity <= 0:
		return {"success": false, "message": "Некорректный запрос добычи."}
	if not state.has_method("get_item_definition") or not state.has_method("get_item_count") or not state.has_method("add_item"):
		return {"success": false, "message": "Инвентарь недоступен."}
	var registry: Dictionary = _registry(state)
	var value: Variant = registry.get(actor_id, {})
	if not value is Dictionary:
		return {"success": false, "message": "У тела нет сохранённой добычи."}
	var record: Dictionary = (value as Dictionary).duplicate(true)
	if str(record.get("body_state", BODY_ALIVE)) != BODY_DEAD:
		return {"success": false, "message": "Снимать предметы можно только с мёртвого тела."}
	var loot: Array[Dictionary] = _normalized_loot(record.get("remaining_loot", []))
	var entry_index: int = -1
	var available_quantity: int = 0
	for index: int in range(loot.size()):
		if str(loot[index].get("item_id", "")) == item_id:
			entry_index = index
			available_quantity = int(loot[index].get("quantity", 0))
			break
	if entry_index < 0 or available_quantity <= 0:
		return {"success": false, "message": "Этого предмета на теле больше нет."}
	var definition: Dictionary = state.call("get_item_definition", item_id) as Dictionary
	if definition.is_empty():
		return {"success": false, "message": "Предмет не зарегистрирован в каталоге."}
	var current_count: int = int(state.call("get_item_count", item_id))
	var maximum: int = int(definition.get("max_stack", 99)) if bool(definition.get("stackable", true)) else 1
	var capacity: int = maxi(maximum - current_count, 0)
	var transfer_quantity: int = mini(mini(requested_quantity, available_quantity), capacity)
	if transfer_quantity <= 0:
		return {"success": false, "message": "В инвентаре уже нет места для этого предмета."}
	var updated_count: int = int(state.call("add_item", item_id, transfer_quantity, false))
	if updated_count <= current_count:
		return {"success": false, "message": "Предмет не удалось добавить в инвентарь."}
	var remaining_quantity: int = available_quantity - transfer_quantity
	if remaining_quantity <= 0:
		loot.remove_at(entry_index)
	else:
		loot[entry_index]["quantity"] = remaining_quantity
	record["remaining_loot"] = loot
	registry[actor_id] = record
	_store_registry(state, registry, true)
	return {
		"success": true,
		"item_id": item_id,
		"quantity": transfer_quantity,
		"remaining_quantity": remaining_quantity,
		"message": "Предмет перенесён в инвентарь."
	}


func take_all(state: Node, actor_id: String) -> Dictionary:
	var transferred: Array[Dictionary] = []
	var failures: Array[String] = []
	var snapshot: Array[Dictionary] = get_remaining_loot(state, actor_id)
	for entry: Dictionary in snapshot:
		var item_id: String = str(entry.get("item_id", ""))
		var quantity: int = maxi(int(entry.get("quantity", 0)), 0)
		if item_id.is_empty() or quantity <= 0:
			continue
		var result: Dictionary = take_item(state, actor_id, item_id, quantity)
		if bool(result.get("success", false)):
			transferred.append({"item_id": item_id, "quantity": int(result.get("quantity", 0))})
		else:
			failures.append(str(result.get("message", "Не удалось забрать %s." % item_id)))
	return {
		"success": not transferred.is_empty(),
		"transferred": transferred,
		"failures": failures
	}


func _registry(state: Node) -> Dictionary:
	if state == null:
		return {}
	var flags_value: Variant = state.get("story_flags")
	var flags: Dictionary = flags_value as Dictionary if flags_value is Dictionary else {}
	var registry_value: Variant = flags.get(REGISTRY_KEY, {})
	return (registry_value as Dictionary).duplicate(true) if registry_value is Dictionary else {}


func _store_registry(state: Node, registry: Dictionary, save_after: bool) -> void:
	var flags_value: Variant = state.get("story_flags")
	var flags: Dictionary = flags_value as Dictionary if flags_value is Dictionary else {}
	flags[REGISTRY_KEY] = registry.duplicate(true)
	state.set("story_flags", flags)
	if save_after and state.has_method("save_game"):
		state.call("save_game")


func _reserved_restraint_uses(registry: Dictionary, item_id: String, excluded_actor_id: String = "") -> int:
	var reserved: int = 0
	for actor_key: Variant in registry.keys():
		var actor_id: String = str(actor_key)
		if actor_id == excluded_actor_id:
			continue
		var value: Variant = registry.get(actor_key, {})
		if not value is Dictionary:
			continue
		var record: Dictionary = value as Dictionary
		if bool(record.get("bound", false)) and str(record.get("binding_item_id", "")) == item_id:
			reserved += 1
	return reserved


func _ensure_binding_fields(record: Dictionary) -> void:
	if not record.has("bound"):
		record["bound"] = false
	if not record.has("binding_item_id"):
		record["binding_item_id"] = ""
	if not record.has("binding_label"):
		record["binding_label"] = ""
	if not record.has("binding_kind"):
		record["binding_kind"] = ""
	if not record.has("restraint_escape_dc"):
		record["restraint_escape_dc"] = 0


func _normalized_loot(value: Variant) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	if not value is Array:
		return result
	for entry_value: Variant in value:
		if not entry_value is Dictionary:
			continue
		var entry: Dictionary = entry_value as Dictionary
		var item_id: String = str(entry.get("item_id", ""))
		var quantity: int = maxi(int(entry.get("quantity", 0)), 0)
		if item_id.is_empty() or quantity <= 0:
			continue
		result.append({"item_id": item_id, "quantity": quantity})
	return result


func _load_profiles() -> void:
	_profiles = _load_dictionary_section(DATA_PATH, "profiles")


func _load_restraint_sources() -> void:
	_restraint_sources = _load_dictionary_section(RESTRAINT_DATA_PATH, "sources")


func _load_dictionary_section(path: String, section: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var file: FileAccess = FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {}
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		return {}
	var data: Dictionary = parsed as Dictionary
	var value: Variant = data.get(section, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}
