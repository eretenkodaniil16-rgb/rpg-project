extends "res://scripts/game/game_presented_rolls.gd"


func _ready() -> void:
	super._ready()
	if _ability_panel != null:
		_ability_panel.name = "AbilityPanel"
