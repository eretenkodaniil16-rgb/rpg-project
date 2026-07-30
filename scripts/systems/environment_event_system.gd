class_name EnvironmentEventSystem
extends RefCounted

const EVENT_HAZARD_ADDED: String = "hazard_added"
const EVENT_HAZARD_REMOVED: String = "hazard_removed"
const EVENT_COVER_DESTROYED: String = "cover_destroyed"
const EVENT_COVER_RESTORED: String = "cover_restored"
const EVENT_PASSAGE_OPENED: String = "passage_opened"
const EVENT_DOOR_CLOSED: String = "door_closed"
const EVENT_DOOR_BROKEN: String = "door_broken"
const EVENT_BODY_MOVED: String = "body_moved"
const EVENT_ALLY_BOUND: String = "ally_bound"

const VALID_EVENT_TYPES: Array[String] = [
	EVENT_HAZARD_ADDED,
	EVENT_HAZARD_REMOVED,
	EVENT_COVER_DESTROYED,
	EVENT_COVER_RESTORED,
	EVENT_PASSAGE_OPENED,
	EVENT_DOOR_CLOSED,
	EVENT_DOOR_BROKEN,
	EVENT_BODY_MOVED,
	EVENT_ALLY_BOUND
]

const MAX_EVENTS: int = 32

var _sequence: int = 0
var _events: Array[Dictionary] = []
var _acknowledged: Dictionary = {}


func report_event(
	event_type: String,
	world_position: Vector2,
	payload: Dictionary = {},
	severity: float = 1.0,
	audible_radius_feet: int = 0,
	visible_radius_feet: int = 60,
	round_number: int = 0
) -> Dictionary:
	if event_type not in VALID_EVENT_TYPES:
		return {}
	_sequence += 1
	var event: Dictionary = {
		"event_id": "environment_event_%d" % _sequence,
		"sequence": _sequence,
		"type": event_type,
		"position": world_position,
		"payload": payload.duplicate(true),
		"severity": clampf(severity, 0.0, 3.0),
		"audible_radius_feet": maxi(audible_radius_feet, 0),
		"visible_radius_feet": maxi(visible_radius_feet, 0),
		"round_number": maxi(round_number, 0)
	}
	_events.append(event)
	while _events.size() > MAX_EVENTS:
		var removed: Dictionary = _events.pop_front()
		_forget_event(str(removed.get("event_id", "")))
	return event.duplicate(true)


func latest_perceived_event(
	actor_id: String,
	actor_position: Vector2,
	current_round: int,
	memory_rounds: int,
	can_see_position: Callable,
	perception_feet: int,
	hearing_feet: int
) -> Dictionary:
	if actor_id.is_empty():
		return {}
	var minimum_round: int = maxi(current_round - maxi(memory_rounds, 0), 0)
	for index: int in range(_events.size() - 1, -1, -1):
		var event: Dictionary = _events[index]
		var event_id: String = str(event.get("event_id", ""))
		if event_id.is_empty() or _actor_acknowledged(actor_id, event_id):
			continue
		if int(event.get("round_number", 0)) < minimum_round:
			continue
		var position: Vector2 = event.get("position", Vector2.ZERO) as Vector2
		var distance_feet: int = DistanceSystem.distance_feet(actor_position, position)
		var visible_limit: int = mini(maxi(int(event.get("visible_radius_feet", 0)), 0), maxi(perception_feet, 0))
		var audible_limit: int = mini(maxi(int(event.get("audible_radius_feet", 0)), 0), maxi(hearing_feet, 0))
		var visible: bool = visible_limit > 0 and distance_feet <= visible_limit and (not can_see_position.is_valid() or bool(can_see_position.call(position)))
		var audible: bool = audible_limit > 0 and distance_feet <= audible_limit
		if not visible and not audible:
			continue
		var result: Dictionary = event.duplicate(true)
		result["perceived_visually"] = visible
		result["perceived_audibly"] = audible
		result["distance_feet"] = distance_feet
		return result
	return {}


func acknowledge(actor_id: String, event_id: String) -> void:
	if actor_id.is_empty() or event_id.is_empty():
		return
	var actor_events: Dictionary = _acknowledged.get(actor_id, {}) as Dictionary if _acknowledged.get(actor_id, {}) is Dictionary else {}
	actor_events[event_id] = true
	_acknowledged[actor_id] = actor_events


func clear_combat_memory() -> void:
	_events.clear()
	_acknowledged.clear()


func event_count() -> int:
	return _events.size()


func latest_event_for_testing() -> Dictionary:
	return _events[-1].duplicate(true) if not _events.is_empty() else {}


func _actor_acknowledged(actor_id: String, event_id: String) -> bool:
	var actor_events: Variant = _acknowledged.get(actor_id, {})
	return actor_events is Dictionary and bool((actor_events as Dictionary).get(event_id, false))


func _forget_event(event_id: String) -> void:
	if event_id.is_empty():
		return
	for actor_key: Variant in _acknowledged.keys():
		var actor_events: Variant = _acknowledged.get(actor_key, {})
		if actor_events is Dictionary:
			(actor_events as Dictionary).erase(event_id)
