class_name ContextStealthCombatNpc
extends "res://scripts/game/npc_stealth.gd"


func interact() -> void:
	if is_body_interactable() or defeated or hostile:
		super.interact()
		return
	var dialogue_data: Dictionary = _load_dialogue()
	if dialogue_data.is_empty():
		get_tree().call_group("game_world", "show_combat_message", "%s сейчас нечего сказать." % combat_name, false)
		return
	var quest_event: String = str(dialogue_data.get("quest_event", ""))
	var state: Node = _get_game_state()
	if not quest_event.is_empty() and state != null and state.has_method("report_quest_event"):
		state.call("report_quest_event", quest_event)
	# The NPC itself is the dialogue target. No selected combat target is required.
	get_tree().call_group("dialogue_ui", "start_dialogue", dialogue_data, self)
	get_tree().call_group("game_world", "set_interaction_hint", false)


func can_perform_world_interaction() -> bool:
	if not is_instance_valid(player_in_range):
		return false
	# A defeated body is still a world object. Hostility blocks conversation, but
	# death/unconsciousness must not block inspection, loot or restraint actions.
	return is_body_interactable() or (not defeated and not hostile)


func get_interaction_label() -> String:
	if defeated:
		return "ОСМОТРЕТЬ: %s" % combat_name.to_upper()
	if hostile:
		return "%s НЕ ЖЕЛАЕТ ГОВОРИТЬ" % combat_name.to_upper()
	return "ПОГОВОРИТЬ: %s" % combat_name.to_upper()


func get_interaction_description() -> String:
	if defeated:
		return "Осмотреть состояние персонажа %s." % combat_name
	if hostile:
		return "%s настроен враждебно; мирный разговор недоступен." % combat_name
	return "Начать разговор с персонажем %s из его триггерной зоны. Выбирать боевую цель не требуется." % combat_name