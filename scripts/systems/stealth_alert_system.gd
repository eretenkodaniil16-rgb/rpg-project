class_name StealthAlertSystem
extends RefCounted

const DATA_PATH: String = "res://data/world/stealth_alerts.json"
const REGISTRY_FLAG: String = "stealth_alert_registry_v1"
const SCHEMA_VERSION: int = 1

const STATE_CALM: String = "calm"
const STATE_SUSPICIOUS: String = "suspicious"
const STATE_INVESTIGATING: String = "investigating"
const STATE_SEARCHING: String = "searching"
const STATE_ALERTED: String = "alerted"
const STATE_COMBAT: String = "combat"

const SUSPICION_SUSPICIOUS: float = 30.0
const SUSPICION_INVESTIGATING: float = 70.0
const SUSPICION_ALERTED: float = 100.0

var _profiles: Dictionary = {}
var _rooms: Dictionary = {}
var _doors: Dictionary = {}
var _hiding_spots: Dictionary = {}
var _noise_profiles: Dictionary = {}


func _init() -> void:
	_load_data()


func ensure_state(state: Node) -> bool:
	if state == null or not state.has_method("get_flag") or not state.has_method("set_flag"):
		return false
	var current_value: Variant = state.call("get_flag", REGISTRY_FLAG, {})
	var registry: Dictionary = current_value as Dictionary if current_value is Dictionary else {}
	var changed: bool = false
	if int(registry.get("schema_version", 0)) != SCHEMA_VERSION:
		registry["schema_version"] = SCHEMA_VERSION
		changed = true
	if not registry.get("actors", {}) is Dictionary:
		registry["actors"] = {}
		changed = true
	if not registry.get("doors", {}) is Dictionary:
		registry["doors"] = {}
		changed = true
	if not registry.get("noise_events", []) is Array:
		registry["noise_events"] = []
		changed = true
	var door_states: Dictionary = registry.get("doors", {}) as Dictionary
	for door_id_value: Variant in _doors.keys():
		var door_id: String = str(door_id_value)
		if door_states.has(door_id):
			continue
		door_states[door_id] = str((_doors[door_id] as Dictionary).get("initial_state", "closed"))
		changed = true
	registry["doors"] = door_states
	if changed or not current_value is Dictionary:
		state.call("set_flag", REGISTRY_FLAG, registry.duplicate(true))
	return changed


func get_profile(actor_id: String) -> Dictionary:
	var value: Variant = _profiles.get(actor_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func has_profile(actor_id: String) -> bool:
	return not get_profile(actor_id).is_empty()


func get_actor_record(state: Node, actor_id: String) -> Dictionary:
	var registry: Dictionary = _registry(state)
	var actors: Dictionary = registry.get("actors", {}) as Dictionary
	var value: Variant = actors.get(actor_id, {})
	return _normalize_actor_record(value as Dictionary if value is Dictionary else {}, actor_id)


func store_actor_record(state: Node, actor_id: String, record: Dictionary) -> Dictionary:
	var registry: Dictionary = _registry(state)
	var actors: Dictionary = registry.get("actors", {}) as Dictionary
	var normalized: Dictionary = _normalize_actor_record(record, actor_id)
	actors[actor_id] = normalized.duplicate(true)
	registry["actors"] = actors
	_store_registry(state, registry)
	return normalized


func clear_actor_record(state: Node, actor_id: String) -> void:
	var registry: Dictionary = _registry(state)
	var actors: Dictionary = registry.get("actors", {}) as Dictionary
	actors.erase(actor_id)
	registry["actors"] = actors
	_store_registry(state, registry)


func get_all_actor_records(state: Node) -> Dictionary:
	return (_registry(state).get("actors", {}) as Dictionary).duplicate(true)


func get_door_state(state: Node, door_id: String) -> String:
	var registry: Dictionary = _registry(state)
	var door_states: Dictionary = registry.get("doors", {}) as Dictionary
	if door_states.has(door_id):
		return str(door_states[door_id])
	return str(get_door_definition(door_id).get("initial_state", "closed"))


func set_door_state(state: Node, door_id: String, door_state: String) -> bool:
	if get_door_definition(door_id).is_empty() or door_state not in ["open", "closed", "locked", "blocked", "broken"]:
		return false
	var registry: Dictionary = _registry(state)
	var door_states: Dictionary = registry.get("doors", {}) as Dictionary
	door_states[door_id] = door_state
	registry["doors"] = door_states
	_store_registry(state, registry)
	return true


func append_noise_event(state: Node, event: Dictionary, maximum_events: int = 16) -> Dictionary:
	var registry: Dictionary = _registry(state)
	var events: Array = registry.get("noise_events", []) as Array
	var normalized: Dictionary = event.duplicate(true)
	normalized["sequence"] = int(registry.get("noise_sequence", 0)) + 1
	registry["noise_sequence"] = normalized["sequence"]
	events.append(normalized)
	while events.size() > maxi(maximum_events, 1):
		events.pop_front()
	registry["noise_events"] = events
	_store_registry(state, registry)
	return normalized


func get_noise_events(state: Node, after_sequence: int = 0) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	var registry: Dictionary = _registry(state)
	for value: Variant in registry.get("noise_events", []) as Array:
		if value is Dictionary and int((value as Dictionary).get("sequence", 0)) > after_sequence:
			result.append((value as Dictionary).duplicate(true))
	return result


func get_room_definition(room_id: String) -> Dictionary:
	var value: Variant = _rooms.get(room_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func get_door_definition(door_id: String) -> Dictionary:
	var value: Variant = _doors.get(door_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func get_hiding_spot_definition(spot_id: String) -> Dictionary:
	var value: Variant = _hiding_spots.get(spot_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func get_room_id_at(world_position: Vector2) -> String:
	for room_id_value: Variant in _rooms.keys():
		var room_id: String = str(room_id_value)
		var room: Dictionary = _rooms[room_id] as Dictionary
		if _rect_from(room.get("rect", [])).has_point(world_position):
			return room_id
	return ""


func get_hiding_spot_at(world_position: Vector2) -> Dictionary:
	for spot_id_value: Variant in _hiding_spots.keys():
		var spot: Dictionary = _hiding_spots[spot_id_value] as Dictionary
		if _rect_from(spot.get("rect", [])).has_point(world_position):
			return spot.duplicate(true)
	return {}


func get_noise_profile(noise_type: String) -> Dictionary:
	var value: Variant = _noise_profiles.get(noise_type, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func can_see_target(
	observer_position: Vector2,
	observer_facing: Vector2,
	target_position: Vector2,
	profile: Dictionary,
	line_of_sight_clear: bool,
	fully_concealed: bool = false
) -> bool:
	if not line_of_sight_clear:
		return false
	var distance_feet: int = DistanceSystem.distance_feet(observer_position, target_position)
	var maximum_distance: int = maxi(int(profile.get("view_distance_feet", 45)), 5)
	if distance_feet > maximum_distance:
		return false
	var direction: Vector2 = target_position - observer_position
	if direction.length_squared() <= 0.0001:
		return true
	if fully_concealed and distance_feet > DistanceSystem.MELEE_REACH_FEET:
		return false
	var facing: Vector2 = observer_facing.normalized() if observer_facing.length_squared() > 0.0001 else Vector2.LEFT
	var normalized_direction: Vector2 = direction.normalized()
	var half_angle_radians: float = deg_to_rad(float(profile.get("view_angle_degrees", 100.0)) * 0.5)
	var inside_primary_cone: bool = facing.dot(normalized_direction) >= cos(half_angle_radians)
	if inside_primary_cone:
		return true
	return distance_feet <= maxi(int(profile.get("peripheral_distance_feet", 10)), 0)


func door_blocks_line_of_sight(state: Node, start: Vector2, finish: Vector2) -> bool:
	for door_id_value: Variant in _doors.keys():
		var door_id: String = str(door_id_value)
		var definition: Dictionary = _doors[door_id] as Dictionary
		if not bool(definition.get("blocks_line_of_sight_when_closed", true)):
			continue
		if get_door_state(state, door_id) in ["open", "broken"]:
			continue
		if _segment_crosses_rect(start, finish, _rect_from(definition.get("rect", []))):
			return true
	return false


func noise_multiplier_between_rooms(state: Node, source_room_id: String, listener_room_id: String) -> float:
	if source_room_id.is_empty() or listener_room_id.is_empty() or source_room_id == listener_room_id:
		return 1.0
	for door_id_value: Variant in _doors.keys():
		var door_id: String = str(door_id_value)
		var definition: Dictionary = _doors[door_id] as Dictionary
		var rooms_value: Variant = definition.get("rooms", [])
		if not rooms_value is Array:
			continue
		var rooms: Array = rooms_value as Array
		if source_room_id not in rooms or listener_room_id not in rooms:
			continue
		var open_state: bool = get_door_state(state, door_id) in ["open", "broken"]
		return clampf(
			float(definition.get("open_noise_multiplier", 0.9)) if open_state else float(definition.get("closed_noise_multiplier", 0.4)),
			0.0,
			1.0
		)
	return 0.35


func actor_hears_noise(
	state: Node,
	actor_position: Vector2,
	actor_room_id: String,
	noise_event: Dictionary,
	profile: Dictionary
) -> bool:
	var source_position: Vector2 = vector_from_value(noise_event.get("position", []))
	var source_room_id: String = str(noise_event.get("room_id", ""))
	var multiplier: float = noise_multiplier_between_rooms(state, source_room_id, actor_room_id)
	var hearing_radius: float = float(noise_event.get("radius_feet", 0)) * multiplier
	var profile_multiplier: float = maxf(float(profile.get("hearing_multiplier", 1.0)), 0.0)
	hearing_radius *= profile_multiplier
	return float(DistanceSystem.distance_feet(actor_position, source_position)) <= hearing_radius


func apply_visual_observation(
	record: Dictionary,
	visible: bool,
	target_hidden: bool,
	target_position: Vector2,
	delta: float,
	profile: Dictionary
) -> Dictionary:
	var result: Dictionary = _normalize_actor_record(record, str(record.get("actor_id", "")))
	var suspicion: float = float(result.get("suspicion", 0.0))
	if visible:
		var visible_rate: float = float(profile.get("suspicion_visible_per_second", 45.0))
		var hidden_rate: float = float(profile.get("suspicion_hidden_per_second", 12.0))
		suspicion += maxf(hidden_rate if target_hidden else visible_rate, 0.0) * maxf(delta, 0.0)
		result["last_known_position"] = vector_to_value(target_position)
		result["search_seconds_remaining"] = float(profile.get("search_duration_seconds", 10.0))
	else:
		var current_state: String = str(result.get("state", STATE_CALM))
		if current_state in [STATE_CALM, STATE_SUSPICIOUS]:
			suspicion -= maxf(float(profile.get("suspicion_decay_per_second", 8.0)), 0.0) * maxf(delta, 0.0)
	result["suspicion"] = clampf(suspicion, 0.0, SUSPICION_ALERTED)
	result["state"] = state_for_suspicion(float(result["suspicion"]), str(result.get("state", STATE_CALM)), visible)
	return result


func apply_noise(record: Dictionary, noise_event: Dictionary, profile: Dictionary) -> Dictionary:
	var result: Dictionary = _normalize_actor_record(record, str(record.get("actor_id", "")))
	var intensity: float = maxf(float(noise_event.get("intensity", 0.0)), 0.0)
	var multiplier: float = maxf(float(profile.get("noise_suspicion_multiplier", 0.7)), 0.0)
	result["suspicion"] = clampf(float(result.get("suspicion", 0.0)) + intensity * multiplier, 0.0, SUSPICION_ALERTED)
	result["last_known_position"] = noise_event.get("position", [0.0, 0.0])
	result["last_noise_type"] = str(noise_event.get("noise_type", "unknown"))
	result["search_seconds_remaining"] = float(profile.get("search_duration_seconds", 10.0))
	if float(result["suspicion"]) >= SUSPICION_ALERTED:
		result["state"] = STATE_ALERTED
	else:
		result["state"] = STATE_INVESTIGATING
	return result


func advance_search(record: Dictionary, delta: float, reached_last_known: bool, profile: Dictionary) -> Dictionary:
	var result: Dictionary = _normalize_actor_record(record, str(record.get("actor_id", "")))
	var current_state: String = str(result.get("state", STATE_CALM))
	if current_state not in [STATE_INVESTIGATING, STATE_SEARCHING, STATE_ALERTED]:
		return result
	if not reached_last_known:
		result["state"] = STATE_INVESTIGATING if current_state != STATE_ALERTED else STATE_ALERTED
		return result
	if current_state != STATE_ALERTED:
		result["state"] = STATE_SEARCHING
	var remaining: float = maxf(float(result.get("search_seconds_remaining", profile.get("search_duration_seconds", 10.0))) - maxf(delta, 0.0), 0.0)
	result["search_seconds_remaining"] = remaining
	if remaining > 0.0:
		return result
	var cooldown: float = maxf(float(result.get("alert_cooldown_seconds", profile.get("alert_cooldown_seconds", 20.0))) - maxf(delta, 0.0), 0.0)
	result["alert_cooldown_seconds"] = cooldown
	result["suspicion"] = clampf(float(result.get("suspicion", 0.0)) - float(profile.get("suspicion_decay_per_second", 8.0)) * maxf(delta, 0.0), 0.0, SUSPICION_ALERTED)
	if cooldown <= 0.0 and float(result["suspicion"]) < SUSPICION_SUSPICIOUS:
		result["state"] = STATE_CALM
	else:
		result["state"] = STATE_SUSPICIOUS
	return result


func state_for_suspicion(suspicion: float, current_state: String = STATE_CALM, visible: bool = false) -> String:
	if current_state == STATE_COMBAT:
		return STATE_COMBAT
	if suspicion >= SUSPICION_ALERTED:
		return STATE_ALERTED
	if suspicion >= SUSPICION_INVESTIGATING:
		return STATE_INVESTIGATING if not visible else STATE_SUSPICIOUS
	if suspicion >= SUSPICION_SUSPICIOUS:
		return STATE_SUSPICIOUS
	return STATE_CALM


func vector_to_value(value: Vector2) -> Array[float]:
	return [value.x, value.y]


func vector_from_value(value: Variant) -> Vector2:
	if value is Vector2:
		return value as Vector2
	if value is Array and (value as Array).size() >= 2:
		return Vector2(float((value as Array)[0]), float((value as Array)[1]))
	return Vector2.ZERO


func rect_from_value(value: Variant) -> Rect2:
	return _rect_from(value)


func _normalize_actor_record(record: Dictionary, actor_id: String) -> Dictionary:
	var result: Dictionary = record.duplicate(true)
	result["actor_id"] = actor_id
	result["state"] = str(result.get("state", STATE_CALM))
	result["suspicion"] = clampf(float(result.get("suspicion", 0.0)), 0.0, SUSPICION_ALERTED)
	if not result.get("last_known_position", []) is Array:
		result["last_known_position"] = [0.0, 0.0]
	result["search_seconds_remaining"] = maxf(float(result.get("search_seconds_remaining", 0.0)), 0.0)
	result["alert_cooldown_seconds"] = maxf(float(result.get("alert_cooldown_seconds", 0.0)), 0.0)
	return result


func _registry(state: Node) -> Dictionary:
	ensure_state(state)
	var value: Variant = state.call("get_flag", REGISTRY_FLAG, {}) if state != null and state.has_method("get_flag") else {}
	var registry: Dictionary = value as Dictionary if value is Dictionary else {}
	if not registry.get("actors", {}) is Dictionary:
		registry["actors"] = {}
	if not registry.get("doors", {}) is Dictionary:
		registry["doors"] = {}
	if not registry.get("noise_events", []) is Array:
		registry["noise_events"] = []
	return registry.duplicate(true)


func _store_registry(state: Node, registry: Dictionary) -> void:
	if state != null and state.has_method("set_flag"):
		state.call("set_flag", REGISTRY_FLAG, registry.duplicate(true))


func _rect_from(value: Variant) -> Rect2:
	if value is Rect2:
		return value as Rect2
	if value is Array and (value as Array).size() >= 4:
		return Rect2(
			float((value as Array)[0]),
			float((value as Array)[1]),
			float((value as Array)[2]),
			float((value as Array)[3])
		)
	return Rect2()


func _segment_crosses_rect(start: Vector2, finish: Vector2, rect: Rect2) -> bool:
	if rect.size == Vector2.ZERO:
		return false
	var distance: float = start.distance_to(finish)
	var samples: int = maxi(ceili(distance / 6.0), 1)
	for index: int in range(1, samples):
		if rect.has_point(start.lerp(finish, float(index) / float(samples))):
			return true
	return false


func _load_data() -> void:
	_profiles.clear()
	_rooms.clear()
	_doors.clear()
	_hiding_spots.clear()
	_noise_profiles.clear()
	if not FileAccess.file_exists(DATA_PATH):
		return
	var file: FileAccess = FileAccess.open(DATA_PATH, FileAccess.READ)
	if file == null:
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		return
	var data: Dictionary = parsed as Dictionary
	_profiles = (data.get("profiles", {}) as Dictionary).duplicate(true) if data.get("profiles", {}) is Dictionary else {}
	_rooms = (data.get("rooms", {}) as Dictionary).duplicate(true) if data.get("rooms", {}) is Dictionary else {}
	_doors = (data.get("doors", {}) as Dictionary).duplicate(true) if data.get("doors", {}) is Dictionary else {}
	_hiding_spots = (data.get("hiding_spots", {}) as Dictionary).duplicate(true) if data.get("hiding_spots", {}) is Dictionary else {}
	_noise_profiles = (data.get("noise_profiles", {}) as Dictionary).duplicate(true) if data.get("noise_profiles", {}) is Dictionary else {}
