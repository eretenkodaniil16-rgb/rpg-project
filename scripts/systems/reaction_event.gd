class_name ReactionEvent
extends RefCounted

enum Status {
	OPEN,
	RESOLVING,
	RESOLVED,
	CANCELLED,
	INVALIDATED
}

var event_id: String = ""
var trigger_id: String = ""
var source: Node
var target: Node
var context: Dictionary = {}
var status: Status = Status.OPEN
var stop_processing: bool = false
var invalid_reason: String = ""
var history: Array[Dictionary] = []
var processed_reactor_ids: Dictionary = {}


func _init(
	new_event_id: String = "",
	new_trigger_id: String = "",
	new_context: Dictionary = {},
	new_source: Node = null,
	new_target: Node = null
) -> void:
	event_id = new_event_id
	trigger_id = new_trigger_id
	context = new_context.duplicate(true)
	source = new_source
	target = new_target


func is_open() -> bool:
	return status == Status.OPEN or status == Status.RESOLVING


func can_offer_to(reactor_id: String) -> bool:
	return is_open() and not stop_processing and not processed_reactor_ids.has(reactor_id)


func begin_resolution(reactor_id: String, option_id: String) -> bool:
	if not can_offer_to(reactor_id):
		return false
	status = Status.RESOLVING
	history.append({
		"reactor_id": reactor_id,
		"option_id": option_id,
		"state": "selected"
	})
	return true


func complete_resolution(reactor_id: String, option_id: String, result: Dictionary) -> void:
	processed_reactor_ids[reactor_id] = true
	var stop_chain: bool = (
		bool(result.get("stop_reaction_chain", false))
		or bool(result.get("event_invalidated", false))
		or bool(result.get("countered", false))
		or bool(result.get("blocks_magic_missile", false))
		or bool(result.get("prevents_triggering_hit", false))
	)
	stop_processing = stop_processing or stop_chain
	history.append({
		"reactor_id": reactor_id,
		"option_id": option_id,
		"state": "resolved" if bool(result.get("resolved", false)) else "failed",
		"result": result.duplicate(true),
		"stop_chain": stop_chain
	})
	status = Status.RESOLVED if stop_processing else Status.OPEN


func record_runtime_outcome(
	reactor_id: String,
	option_id: String,
	outcome: Dictionary
) -> void:
	var stop_chain: bool = (
		bool(outcome.get("stop_reaction_chain", false))
		or bool(outcome.get("event_invalidated", false))
		or bool(outcome.get("target_invalid", false))
	)
	history.append({
		"reactor_id": reactor_id,
		"option_id": option_id,
		"state": "runtime_completed",
		"outcome": outcome.duplicate(true),
		"stop_chain": stop_chain
	})
	if stop_chain:
		stop_processing = true
		status = Status.RESOLVED


func mark_skipped(reactor_id: String, controller_id: String = "") -> void:
	processed_reactor_ids[reactor_id] = true
	history.append({
		"reactor_id": reactor_id,
		"controller_id": controller_id,
		"state": "skipped"
	})
	if status == Status.RESOLVING:
		status = Status.OPEN


func cancel(reason: String = "") -> void:
	status = Status.CANCELLED
	stop_processing = true
	invalid_reason = reason


func invalidate(reason: String) -> void:
	status = Status.INVALIDATED
	stop_processing = true
	invalid_reason = reason


func finish() -> void:
	if status in [Status.OPEN, Status.RESOLVING]:
		status = Status.RESOLVED
