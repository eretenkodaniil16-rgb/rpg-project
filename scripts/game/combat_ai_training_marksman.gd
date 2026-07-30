class_name CombatAiTrainingMarksman
extends "res://scripts/game/stealth_patrol_observer.gd"


func enter_combat_hostile() -> void:
	if not is_combat_participant_active():
		get_tree().call_group("stealth_world", "activate_tactical_training_squad")
	super.enter_combat_hostile()


func perform_combat_turn_attack() -> void:
	if not can_take_combat_turn():
		return
	get_tree().call_group("game_world", "show_combat_message", "%s выпускает стрелу." % combat_name, false)
	super.perform_combat_turn_attack()


func get_context_status_text() -> String:
	return "%s Роль: стрелок тактического дозора." % super.get_context_status_text()
