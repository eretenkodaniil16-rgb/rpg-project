extends "res://scripts/game/game_roll_presentation.gd"

const PRESENTING_SRD_RULES: Script = preload("res://scripts/systems/presenting_srd_combat_rules.gd")


func _ready() -> void:
	_srd_rules = PRESENTING_SRD_RULES.new() as SrdCombatRules
	super._ready()
