class_name StealthPatrolObserver
extends "res://scripts/game/npc_stealth.gd"

@export var display_name: String = "Служебный дозорный"

var _combat_participant_active: bool = false


func _ready() -> void:
	combat_name = display_name
	super._ready()
	add_to_group("stealth_alert_actors")
	add_to_group("context_action_targets")
	remove_from_group("combat_targets")
	_combat_participant_active = false
	var agent: NavigationAgent2D = get_node_or_null("NpcNavigationAgent") as NavigationAgent2D
	if agent != null:
		agent.path_desired_distance = 8.0
		agent.target_desired_distance = 10.0
		agent.avoidance_enabled = false


func activate_combat_participant() -> bool:
	if defeated:
		return false
	if not is_in_group("combat_targets"):
		add_to_group("combat_targets")
	_combat_participant_active = true
	enter_combat_hostile()
	return true


func is_combat_participant_active() -> bool:
	return _combat_participant_active


func reset_combat_state(full_restore: bool = true) -> void:
	super.reset_combat_state(full_restore)
	remove_from_group("combat_targets")
	_combat_participant_active = false
	add_to_group("context_action_targets")


func get_context_status_text() -> String:
	return "%s Роль: патрульный дозора." % super.get_context_status_text()
