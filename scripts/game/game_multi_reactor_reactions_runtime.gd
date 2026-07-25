extends "res://scripts/game/game_damage_fall_reactions_runtime.gd"

const REACTION_COORDINATOR_SCRIPT: Script = preload("res://scripts/systems/reaction_coordinator.gd")

var _reaction_coordinator: ReactionCoordinator = REACTION_COORDINATOR_SCRIPT.new() as ReactionCoordinator
var _active_reaction_event: ReactionEvent


func _try_enemy_spell_turn(actor: Node) -> bool:
	if _enemy_spell_cast_in_progress or actor == null or not (actor is Node2D):
		return false
	var spell: Dictionary = _enemy_spell_definition(actor)
	if spell.is_empty() or not _enemy_has_spell_slot(actor, spell):
		return false
	var distance_feet: int = DistanceSystem.distance_feet((actor as Node2D).global_position, player.global_position)
	if distance_feet > _enemy_spell_reach_feet(spell):
		return false
	var cover: Dictionary = _combat_environment.get_cover(
		(actor as Node2D).global_position,
		player.global_position
	) if _combat_environment != null else {"bonus": 0, "total_cover": false}
	if bool(cover.get("total_cover", false)):
		return false

	_enemy_spell_cast_in_progress = true
	var slot_level: int = _enemy_spell_slot_level(actor, spell)
	var attempt := SpellCastAttempt.new(spell, actor, slot_level)
	attempt.caster_constitution_modifier = (
		int(actor.call("get_saving_throw_modifier", "constitution"))
		if actor.has_method("get_saving_throw_modifier")
		else 0
	)
	attempt.caster_state = _state_for(actor)
	attempt.action_kind = "action"
	attempt.original_resource_key = "enemy_spell_slots_%d" % slot_level
	show_combat_message("%s начинает сотворять «%s»." % [attempt.caster_name, attempt.get_spell_name()], false)

	var save_overrides: Array[int] = []
	if actor.has_method("get_counterspell_save_roll_overrides"):
		var overrides_value: Variant = actor.call("get_counterspell_save_roll_overrides")
		if overrides_value is Array:
			for value: Variant in overrides_value as Array:
				save_overrides.append(int(value))
	var event_context: Dictionary = {
		"attempt": attempt,
		"save_roll_overrides": save_overrides,
		"allow_source_reaction": false
	}
	var selection: Dictionary = await _request_coordinated_reaction(
		"ВОЗМОЖНОСТЬ РЕАКЦИИ",
		"%s начинает сотворять «%s». Все подходящие участники проверены единым координатором реакций." % [
			attempt.caster_name,
			attempt.get_spell_name()
		],
		ReactionOpportunitySystem.TRIGGER_SPELL_CAST_STARTED,
		event_context,
		actor,
		player
	)
	if not selection.is_empty():
		var event: ReactionEvent = selection.get("event") as ReactionEvent
		var selection_id: String = str(selection.get("selection_id", ""))
		var reaction_result: Dictionary = _reaction_coordinator.resolve_selection(event, selection_id)
		_consume_coordinated_reaction(reaction_result)
		show_combat_message(
			str(reaction_result.get("message", "Реакция разрешена.")),
			bool(reaction_result.get("countered", false))
		)
		GameState.save_game()
		_update_status()
		if bool(reaction_result.get("countered", false)):
			_enemy_spell_cast_in_progress = false
			_active_reaction_event = null
			return true
		if not bool(reaction_result.get("resolved", false)):
			attempt.mark_proceeds()
	else:
		attempt.mark_proceeds()
	_active_reaction_event = null

	await get_tree().create_timer(0.18).timeout
	if attempt.countered:
		_enemy_spell_cast_in_progress = false
		return true
	if not actor.has_method("consume_combat_spell_slot") or not bool(actor.call("consume_combat_spell_slot", slot_level)):
		show_combat_message("%s не смог завершить сотворение: ячейка недоступна." % attempt.caster_name, false)
		_enemy_spell_cast_in_progress = false
		return true
	attempt.mark_original_resource_expended("enemy_spell_slots_%d" % slot_level)
	await _resolve_enemy_area_spell(actor, spell, slot_level)
	_enemy_spell_cast_in_progress = false
	return true


func _request_coordinated_reaction(
	title: String,
	details: String,
	trigger_id: String,
	base_context: Dictionary,
	source: Node = null,
	target: Node = null,
	explicit_candidates: Array[ReactionCandidate] = []
) -> Dictionary:
	if _reaction_choice_prompt == null or _reaction_choice_prompt.is_waiting_for_decision():
		return {}
	_active_reaction_event = _reaction_coordinator.create_event(trigger_id, base_context, source, target)
	var candidates: Array[ReactionCandidate] = explicit_candidates
	if candidates.is_empty():
		candidates = _collect_reaction_candidates(trigger_id, base_context, source, target)
	var options: Array[Dictionary] = _reaction_coordinator.collect_options(_active_reaction_event, candidates)
	_decorate_multi_reactor_options(options)
	var queue: Array[Dictionary] = _reaction_coordinator.build_controller_queue(options)
	for controller_group: Dictionary in queue:
		if not _reaction_coordinator.should_continue(_active_reaction_event):
			break
		var controller_id: String = str(controller_group.get("controller_id", ReactionCandidate.CONTROLLER_AI))
		var group_options: Array[Dictionary] = _dictionary_options(controller_group.get("options", []))
		if group_options.is_empty():
			continue
		var selected_id: String = ""
		if controller_id == ReactionCandidate.CONTROLLER_PLAYER:
			_reaction_resolution_in_progress = true
			selected_id = await _reaction_choice_prompt.request_reaction(title, details, group_options)
			_reaction_resolution_in_progress = false
		else:
			selected_id = _reaction_coordinator.choose_ai_selection(group_options)
		if selected_id.is_empty():
			_reaction_coordinator.mark_controller_skipped(_active_reaction_event, controller_id, group_options)
			continue
		var payload: Dictionary = _reaction_coordinator.get_selection_payload(_active_reaction_event, selected_id)
		if payload.is_empty():
			continue
		return {
			"event": _active_reaction_event,
			"selection_id": selected_id,
			"payload": payload
		}
	_active_reaction_event.finish()
	return {}


func _collect_reaction_candidates(
	trigger_id: String,
	base_context: Dictionary,
	source: Node,
	target: Node
) -> Array[ReactionCandidate]:
	var result: Array[ReactionCandidate] = []
	var seen_actor_ids: Dictionary = {}
	var player_candidate: ReactionCandidate = _make_player_reaction_candidate(trigger_id, base_context, source, target)
	if player_candidate != null:
		result.append(player_candidate)
		if is_instance_valid(player_candidate.actor):
			seen_actor_ids[player_candidate.actor.get_instance_id()] = true

	if _turn_system != null and _turn_system.active:
		for entry_value: Variant in _turn_system.entries:
			if not entry_value is Dictionary:
				continue
			var entry: Dictionary = entry_value as Dictionary
			var actor: Node = entry.get("node") as Node
			if not is_instance_valid(actor) or seen_actor_ids.has(actor.get_instance_id()):
				continue
			var candidate: ReactionCandidate = _candidate_from_actor_hook(actor, trigger_id, base_context, source, target)
			if candidate == null:
				continue
			if candidate.initiative == 0:
				candidate.initiative = int(entry.get("initiative", 0))
			candidate.reaction_available = candidate.reaction_available and _turn_system.has_reaction(actor)
			result.append(candidate)
			seen_actor_ids[actor.get_instance_id()] = true

	for actor: Node in get_tree().get_nodes_in_group("reaction_reactors"):
		if not is_instance_valid(actor) or seen_actor_ids.has(actor.get_instance_id()):
			continue
		var candidate: ReactionCandidate = _candidate_from_actor_hook(actor, trigger_id, base_context, source, target)
		if candidate != null:
			result.append(candidate)
	return result


func _make_player_reaction_candidate(
	trigger_id: String,
	base_context: Dictionary,
	source: Node,
	target: Node
) -> ReactionCandidate:
	if GameState.player_character == null or not is_instance_valid(player):
		return null
	var candidate := ReactionCandidate.new(
		"player:%d" % player.get_instance_id(),
		player,
		GameState.player_character
	)
	candidate.display_name = GameState.player_character.character_name
	if candidate.display_name.is_empty():
		candidate.display_name = "Герой"
	candidate.team_id = ReactionCandidate.TEAM_PARTY
	candidate.controller_id = ReactionCandidate.CONTROLLER_PLAYER
	candidate.initiative = _turn_system.get_initiative(player) if _turn_system != null and _turn_system.active else 0
	candidate.reaction_available = true if _turn_system == null or not _turn_system.active else _turn_system.has_reaction(player)
	candidate.can_react = not _player_combat_state.dead and GameState.player_character.current_health > 0
	candidate.context_overrides = _player_reaction_context_overrides(trigger_id, base_context, source, target)
	return candidate


func _player_reaction_context_overrides(
	trigger_id: String,
	_base_context: Dictionary,
	source: Node,
	_target: Node
) -> Dictionary:
	var result: Dictionary = {"casting_context": _build_spellcasting_context()}
	if trigger_id == ReactionOpportunitySystem.TRIGGER_SPELL_CAST_STARTED and is_instance_valid(source) and source is Node2D:
		result["distance_feet"] = DistanceSystem.distance_feet(player.global_position, (source as Node2D).global_position)
		result["can_see_caster"] = true if _combat_environment == null else _combat_environment.has_line_of_sight(
			player.global_position,
			(source as Node2D).global_position
		)
	return result


func _candidate_from_actor_hook(
	actor: Node,
	trigger_id: String,
	base_context: Dictionary,
	source: Node,
	target: Node
) -> ReactionCandidate:
	if actor == source and not bool(base_context.get("allow_source_reaction", false)):
		return null
	if not actor.has_method("get_reaction_candidate_descriptor"):
		return null
	var descriptor_value: Variant = actor.call(
		"get_reaction_candidate_descriptor",
		trigger_id,
		base_context.duplicate(true),
		source,
		target
	)
	if not descriptor_value is Dictionary:
		return null
	var descriptor: Dictionary = descriptor_value as Dictionary
	if descriptor.is_empty():
		return null
	descriptor["actor"] = actor
	if str(descriptor.get("reactor_id", "")).is_empty():
		descriptor["reactor_id"] = "actor:%d" % actor.get_instance_id()
	if not descriptor.has("reaction_available"):
		descriptor["reaction_available"] = true
	return ReactionCandidate.from_descriptor(descriptor)


func _decorate_multi_reactor_options(options: Array[Dictionary]) -> void:
	var reactor_ids: Dictionary = {}
	for option: Dictionary in options:
		reactor_ids[str(option.get("reactor_id", ""))] = true
	if reactor_ids.size() <= 1:
		return
	for option: Dictionary in options:
		var reactor_name: String = str(option.get("reactor_name", "Участник"))
		var original_label: String = str(option.get("label", option.get("name", "Реакция")))
		option["label"] = "%s · %s" % [reactor_name.to_upper(), original_label]
		option["description"] = "Реагирует: %s. %s" % [reactor_name, str(option.get("description", ""))]


func _consume_coordinated_reaction(result: Dictionary) -> void:
	if not bool(result.get("consume_reaction", false)) or _turn_system == null or not _turn_system.active:
		return
	var reactor_actor: Node = result.get("reactor_actor") as Node
	if is_instance_valid(reactor_actor):
		_turn_system.consume_reaction(reactor_actor)


func _dictionary_options(value: Variant) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	if value is Array:
		for option: Variant in value as Array:
			if option is Dictionary:
				result.append(option as Dictionary)
	return result


func collect_reaction_options_for_testing(
	trigger_id: String,
	base_context: Dictionary,
	candidate_descriptors: Array[Dictionary]
) -> Dictionary:
	var candidates: Array[ReactionCandidate] = []
	for descriptor: Dictionary in candidate_descriptors:
		candidates.append(ReactionCandidate.from_descriptor(descriptor))
	var event: ReactionEvent = _reaction_coordinator.create_event(trigger_id, base_context, null, null, "testing_event")
	var options: Array[Dictionary] = _reaction_coordinator.collect_options(event, candidates)
	_decorate_multi_reactor_options(options)
	return {
		"event": event,
		"options": options,
		"queue": _reaction_coordinator.build_controller_queue(options)
	}


func get_reaction_coordinator_for_testing() -> ReactionCoordinator:
	return _reaction_coordinator


func get_active_reaction_event_for_testing() -> ReactionEvent:
	return _active_reaction_event
