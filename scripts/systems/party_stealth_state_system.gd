class_name PartyStealthStateSystem
extends RefCounted

var _target_states: Dictionary = {}
var _observer_memories: Dictionary = {}
var _squad_memories: Dictionary = {}
var _sequence: int = 0


func has_target_state(actor_id: String) -> bool:
	return not actor_id.is_empty() and _target_states.has(actor_id)


func set_target_state(actor_id: String, hidden: bool, stealth_total: int = 0) -> Dictionary:
	if actor_id.is_empty():
		return {}
	var stored: Dictionary = {
		"actor_id": actor_id,
		"hidden": hidden,
		"stealth_total": maxi(stealth_total, 0) if hidden else 0
	}
	_target_states[actor_id] = stored
	return stored.duplicate(true)


func get_target_state(actor_id: String) -> Dictionary:
	var value: Variant = _target_states.get(actor_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func is_hidden(actor_id: String) -> bool:
	return bool(get_target_state(actor_id).get("hidden", false))


func get_stealth_total(actor_id: String) -> int:
	return maxi(int(get_target_state(actor_id).get("stealth_total", 0)), 0)


func record_sighting(
	observer_actor_id: String,
	squad_id: String,
	target_actor_id: String,
	position: Vector2,
	confidence: float = 1.0,
	source: String = "visual",
	share_with_squad: bool = true
) -> Dictionary:
	if observer_actor_id.is_empty() or target_actor_id.is_empty():
		return {}
	_sequence += 1
	var memory: Dictionary = {
		"observer_actor_id": observer_actor_id,
		"target_actor_id": target_actor_id,
		"position": position,
		"confidence": clampf(confidence, 0.0, 1.0),
		"source": source,
		"sequence": _sequence
	}
	var observer_targets: Dictionary = _observer_memories.get(observer_actor_id, {}) as Dictionary if _observer_memories.get(observer_actor_id, {}) is Dictionary else {}
	observer_targets[target_actor_id] = memory.duplicate(true)
	_observer_memories[observer_actor_id] = observer_targets
	if share_with_squad and not squad_id.is_empty():
		var squad_targets: Dictionary = _squad_memories.get(squad_id, {}) as Dictionary if _squad_memories.get(squad_id, {}) is Dictionary else {}
		var shared: Dictionary = memory.duplicate(true)
		shared["shared_by_actor_id"] = observer_actor_id
		squad_targets[target_actor_id] = shared
		_squad_memories[squad_id] = squad_targets
	return memory.duplicate(true)


func get_observer_memory(observer_actor_id: String, target_actor_id: String) -> Dictionary:
	var targets: Variant = _observer_memories.get(observer_actor_id, {})
	if not targets is Dictionary:
		return {}
	var value: Variant = (targets as Dictionary).get(target_actor_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func get_squad_memory(squad_id: String, target_actor_id: String) -> Dictionary:
	var targets: Variant = _squad_memories.get(squad_id, {})
	if not targets is Dictionary:
		return {}
	var value: Variant = (targets as Dictionary).get(target_actor_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func get_latest_observer_memory(observer_actor_id: String) -> Dictionary:
	var targets: Variant = _observer_memories.get(observer_actor_id, {})
	if not targets is Dictionary:
		return {}
	var latest: Dictionary = {}
	for value: Variant in (targets as Dictionary).values():
		if not value is Dictionary:
			continue
		var candidate: Dictionary = value as Dictionary
		if latest.is_empty() or int(candidate.get("sequence", 0)) > int(latest.get("sequence", 0)):
			latest = candidate
	return latest.duplicate(true)


func get_known_target_ids_for_observer(observer_actor_id: String) -> Array[String]:
	var result: Array[String] = []
	var targets: Variant = _observer_memories.get(observer_actor_id, {})
	if targets is Dictionary:
		for key: Variant in (targets as Dictionary).keys():
			result.append(str(key))
	result.sort()
	return result


func clear_target_memory(target_actor_id: String) -> void:
	if target_actor_id.is_empty():
		return
	for observer_id: Variant in _observer_memories.keys():
		var observer_targets: Variant = _observer_memories.get(observer_id, {})
		if observer_targets is Dictionary:
			(observer_targets as Dictionary).erase(target_actor_id)
	for squad_id: Variant in _squad_memories.keys():
		var squad_targets: Variant = _squad_memories.get(squad_id, {})
		if squad_targets is Dictionary:
			(squad_targets as Dictionary).erase(target_actor_id)


func serialize_persistent_state() -> Dictionary:
	var result: Dictionary = {
		"schema_version": 1,
		"targets": _target_states.duplicate(true),
		"observer_memories": {},
		"squad_memories": {},
		"sequence": _sequence
	}
	result["observer_memories"] = _serialize_memory_map(_observer_memories)
	result["squad_memories"] = _serialize_memory_map(_squad_memories)
	return result


func restore_persistent_state(value: Variant) -> void:
	clear()
	if not value is Dictionary:
		return
	var data: Dictionary = value as Dictionary
	var targets_value: Variant = data.get("targets", {})
	if targets_value is Dictionary:
		for actor_id_value: Variant in (targets_value as Dictionary).keys():
			var actor_id: String = str(actor_id_value)
			var state_value: Variant = (targets_value as Dictionary).get(actor_id_value, {})
			if state_value is Dictionary:
				set_target_state(
					actor_id,
					bool((state_value as Dictionary).get("hidden", false)),
					int((state_value as Dictionary).get("stealth_total", 0))
				)
	_observer_memories = _restore_memory_map(data.get("observer_memories", {}))
	_squad_memories = _restore_memory_map(data.get("squad_memories", {}))
	_sequence = maxi(int(data.get("sequence", _highest_memory_sequence())), _highest_memory_sequence())


func clear() -> void:
	_target_states.clear()
	_observer_memories.clear()
	_squad_memories.clear()
	_sequence = 0


func _serialize_memory_map(source: Dictionary) -> Dictionary:
	var result: Dictionary = {}
	for owner_id_value: Variant in source.keys():
		var targets_value: Variant = source.get(owner_id_value, {})
		if not targets_value is Dictionary:
			continue
		var stored_targets: Dictionary = {}
		for target_id_value: Variant in (targets_value as Dictionary).keys():
			var memory_value: Variant = (targets_value as Dictionary).get(target_id_value, {})
			if not memory_value is Dictionary:
				continue
			var memory: Dictionary = (memory_value as Dictionary).duplicate(true)
			var position: Vector2 = memory.get("position", Vector2.ZERO) as Vector2
			memory["position"] = [position.x, position.y]
			stored_targets[str(target_id_value)] = memory
		result[str(owner_id_value)] = stored_targets
	return result


func _restore_memory_map(value: Variant) -> Dictionary:
	var result: Dictionary = {}
	if not value is Dictionary:
		return result
	for owner_id_value: Variant in (value as Dictionary).keys():
		var targets_value: Variant = (value as Dictionary).get(owner_id_value, {})
		if not targets_value is Dictionary:
			continue
		var restored_targets: Dictionary = {}
		for target_id_value: Variant in (targets_value as Dictionary).keys():
			var memory_value: Variant = (targets_value as Dictionary).get(target_id_value, {})
			if not memory_value is Dictionary:
				continue
			var memory: Dictionary = (memory_value as Dictionary).duplicate(true)
			var position_value: Variant = memory.get("position", [])
			if position_value is Array and (position_value as Array).size() >= 2:
				memory["position"] = Vector2(float((position_value as Array)[0]), float((position_value as Array)[1]))
			else:
				memory["position"] = Vector2.ZERO
			restored_targets[str(target_id_value)] = memory
		result[str(owner_id_value)] = restored_targets
	return result


func _highest_memory_sequence() -> int:
	var highest: int = 0
	for memory_map: Dictionary in [_observer_memories, _squad_memories]:
		for targets_value: Variant in memory_map.values():
			if not targets_value is Dictionary:
				continue
			for memory_value: Variant in (targets_value as Dictionary).values():
				if memory_value is Dictionary:
					highest = maxi(highest, int((memory_value as Dictionary).get("sequence", 0)))
	return highest
