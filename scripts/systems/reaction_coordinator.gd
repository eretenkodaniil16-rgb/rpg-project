class_name ReactionCoordinator
extends RefCounted

const SELECTION_SEPARATOR: String = "::"

var _opportunities: ReactionOpportunitySystem = ReactionOpportunitySystem.new()
var _event_counter: int = 0
var _selection_records: Dictionary = {}


func create_event(
	trigger_id: String,
	context: Dictionary,
	source: Node = null,
	target: Node = null,
	event_id: String = ""
) -> ReactionEvent:
	_event_counter += 1
	var resolved_id: String = event_id
	if resolved_id.is_empty():
		resolved_id = "reaction_event_%d" % _event_counter
	_selection_records[resolved_id] = {}
	return ReactionEvent.new(resolved_id, trigger_id, context, source, target)


func collect_options(event: ReactionEvent, candidates: Array[ReactionCandidate]) -> Array[Dictionary]:
	if event == null or not event.is_open() or event.stop_processing:
		return []
	var records: Array[Dictionary] = []
	var option_id_counts: Dictionary = {}
	var valid_candidate_count: int = 0
	for candidate: ReactionCandidate in candidates:
		if candidate == null or not candidate.is_valid() or not event.can_offer_to(candidate.reactor_id):
			continue
		valid_candidate_count += 1
		var reaction_context: Dictionary = candidate.build_context(event.context)
		var options: Array[Dictionary] = _opportunities.collect_options(event.trigger_id, reaction_context)
		for option: Dictionary in options:
			var base_option_id: String = str(option.get("id", ""))
			if base_option_id.is_empty():
				continue
			option_id_counts[base_option_id] = int(option_id_counts.get(base_option_id, 0)) + 1
			records.append({
				"candidate": candidate,
				"context": reaction_context,
				"option": option.duplicate(true),
				"base_option_id": base_option_id
			})

	var event_index: Dictionary = {}
	var display_options: Array[Dictionary] = []
	for record: Dictionary in records:
		var candidate: ReactionCandidate = record.get("candidate") as ReactionCandidate
		var option: Dictionary = record.get("option", {}) as Dictionary
		var base_option_id: String = str(record.get("base_option_id", ""))
		var selection_id: String = base_option_id
		if int(option_id_counts.get(base_option_id, 0)) > 1:
			selection_id = "%s%s%s" % [candidate.reactor_id, SELECTION_SEPARATOR, base_option_id]
		option["id"] = selection_id
		option["base_option_id"] = base_option_id
		option["reactor_id"] = candidate.reactor_id
		option["reactor_name"] = candidate.display_name
		option["reactor_team_id"] = candidate.team_id
		option["controller_id"] = candidate.controller_id
		option["reactor_initiative"] = candidate.initiative
		option["show_reactor_name"] = valid_candidate_count > 1
		option["priority"] = int(option.get("priority", 0)) + int(candidate.metadata.get("reaction_priority_bonus", 0))
		display_options.append(option)
		record["selection_id"] = selection_id
		event_index[selection_id] = record
	_selection_records[event.event_id] = event_index
	return _sort_display_options(display_options)


func build_controller_queue(options: Array[Dictionary]) -> Array[Dictionary]:
	var grouped: Dictionary = {}
	for option: Dictionary in options:
		var controller_id: String = str(option.get("controller_id", ReactionCandidate.CONTROLLER_AI))
		if not grouped.has(controller_id):
			grouped[controller_id] = {
				"controller_id": controller_id,
				"options": [],
				"maximum_initiative": -999999,
				"maximum_priority": -999999
			}
		var group: Dictionary = grouped[controller_id] as Dictionary
		var group_options: Array = group.get("options", []) as Array
		group_options.append(option)
		group["options"] = group_options
		group["maximum_initiative"] = maxi(int(group.get("maximum_initiative", -999999)), int(option.get("reactor_initiative", 0)))
		group["maximum_priority"] = maxi(int(group.get("maximum_priority", -999999)), int(option.get("priority", 0)))
		grouped[controller_id] = group

	var queue: Array[Dictionary] = []
	for controller_id: Variant in grouped.keys():
		var group: Dictionary = grouped[controller_id] as Dictionary
		group["options"] = _sort_display_options(_dictionary_array(group.get("options", [])))
		queue.append(group)
	queue.sort_custom(func(left: Dictionary, right: Dictionary) -> bool:
		var left_initiative: int = int(left.get("maximum_initiative", 0))
		var right_initiative: int = int(right.get("maximum_initiative", 0))
		if left_initiative != right_initiative:
			return left_initiative > right_initiative
		var left_priority: int = int(left.get("maximum_priority", 0))
		var right_priority: int = int(right.get("maximum_priority", 0))
		if left_priority != right_priority:
			return left_priority > right_priority
		return str(left.get("controller_id", "")) < str(right.get("controller_id", ""))
	)
	return queue


func get_selection_payload(event: ReactionEvent, selection_id: String) -> Dictionary:
	if event == null or selection_id.is_empty():
		return {}
	var event_index: Dictionary = _selection_records.get(event.event_id, {}) as Dictionary
	if not event_index.has(selection_id):
		return {}
	var record: Dictionary = event_index[selection_id] as Dictionary
	var candidate: ReactionCandidate = record.get("candidate") as ReactionCandidate
	if candidate == null or not candidate.is_valid() or not event.can_offer_to(candidate.reactor_id):
		return {}
	return {
		"selection_id": selection_id,
		"option_id": str(record.get("base_option_id", "")),
		"candidate": candidate,
		"reactor_id": candidate.reactor_id,
		"reactor_actor": candidate.actor,
		"reactor_character": candidate.character,
		"controller_id": candidate.controller_id,
		"context": (record.get("context", {}) as Dictionary).duplicate(true),
		"option": (record.get("option", {}) as Dictionary).duplicate(true)
	}


func resolve_selection(event: ReactionEvent, selection_id: String) -> Dictionary:
	var payload: Dictionary = get_selection_payload(event, selection_id)
	if payload.is_empty():
		return _failed("Выбранная реакция больше недоступна.")
	var reactor_id: String = str(payload.get("reactor_id", ""))
	var option_id: String = str(payload.get("option_id", ""))
	if not event.begin_resolution(reactor_id, option_id):
		return _failed("Событие реакции уже завершено или этот участник уже ответил.")
	var context: Dictionary = payload.get("context", {}) as Dictionary
	var result: Dictionary
	match event.trigger_id:
		ReactionOpportunitySystem.TRIGGER_SPELL_CAST_STARTED:
			result = _opportunities.resolve_spell_cast_option(option_id, context)
		ReactionOpportunitySystem.TRIGGER_ATTACK_ROLL_HIT, ReactionOpportunitySystem.TRIGGER_MAGIC_MISSILE_TARGETED, ReactionOpportunitySystem.TRIGGER_ELEMENTAL_DAMAGE_TAKEN:
			result = _opportunities.resolve_defensive_option(option_id, context)
		ReactionOpportunitySystem.TRIGGER_CREATURE_DAMAGE_RECEIVED, ReactionOpportunitySystem.TRIGGER_FALL_DAMAGE_PENDING:
			result = _opportunities.resolve_damage_fall_option(option_id, context)
		ReactionOpportunitySystem.TRIGGER_ENEMY_LEAVES_REACH, ReactionOpportunitySystem.TRIGGER_READIED_ACTION:
			result = {
				"available": true,
				"resolved": true,
				"consume_reaction": true,
				"runtime_action": option_id,
				"message": "Реакция выбрана и ожидает выполнения игрового действия."
			}
		_:
			result = _failed("Для этого триггера не зарегистрирован обработчик реакции.")
	result["selection_id"] = selection_id
	result["option_id"] = option_id
	result["reactor_id"] = reactor_id
	result["reactor_actor"] = payload.get("reactor_actor")
	result["controller_id"] = payload.get("controller_id")
	event.complete_resolution(reactor_id, option_id, result)
	return result


func mark_controller_skipped(event: ReactionEvent, controller_id: String, options: Array[Dictionary]) -> void:
	if event == null:
		return
	var marked: Dictionary = {}
	for option: Dictionary in options:
		if str(option.get("controller_id", "")) != controller_id:
			continue
		var reactor_id: String = str(option.get("reactor_id", ""))
		if reactor_id.is_empty() or marked.has(reactor_id):
			continue
		marked[reactor_id] = true
		event.mark_skipped(reactor_id, controller_id)


func choose_ai_selection(options: Array[Dictionary]) -> String:
	var sorted: Array[Dictionary] = _sort_display_options(options)
	for option: Dictionary in sorted:
		if bool(option.get("ai_decline", false)):
			continue
		return str(option.get("id", ""))
	return ""


func should_continue(event: ReactionEvent) -> bool:
	return event != null and event.is_open() and not event.stop_processing


func _sort_display_options(options: Array[Dictionary]) -> Array[Dictionary]:
	var result: Array[Dictionary] = options.duplicate(true)
	result.sort_custom(func(left: Dictionary, right: Dictionary) -> bool:
		var left_priority: int = int(left.get("priority", 0))
		var right_priority: int = int(right.get("priority", 0))
		if left_priority != right_priority:
			return left_priority > right_priority
		var left_initiative: int = int(left.get("reactor_initiative", 0))
		var right_initiative: int = int(right.get("reactor_initiative", 0))
		if left_initiative != right_initiative:
			return left_initiative > right_initiative
		return str(left.get("id", "")) < str(right.get("id", ""))
	)
	return result


func _dictionary_array(value: Variant) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	if value is Array:
		for item: Variant in value as Array:
			if item is Dictionary:
				result.append(item as Dictionary)
	return result


func _failed(message: String) -> Dictionary:
	return {
		"available": false,
		"resolved": false,
		"consume_reaction": false,
		"message": message
	}
