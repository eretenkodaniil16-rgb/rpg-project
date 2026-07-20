extends "res://scripts/game/game_presented_rolls.gd"


func _ready() -> void:
	super._ready()
	if _attack_popup != null:
		_attack_popup.remove_from_group("combat_ui")
	_add_exploration_hud_node(_d20_overlay)
	_add_exploration_hud_node(_combat_feed)
