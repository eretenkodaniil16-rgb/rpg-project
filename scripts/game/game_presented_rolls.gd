extends "res://scripts/game/game_roll_presentation.gd"

const PRESENTING_SRD_RULES: Script = preload("res://scripts/systems/presenting_srd_combat_rules.gd")

func _ready() -> void:
	_srd_rules = PRESENTING_SRD_RULES.new() as SrdCombatRules
	super._ready()
	if _ability_panel != null:
		_ability_panel.name = "AbilityPanel"

func _process(delta: float) -> void:
	super._process(delta)
	var hub: CharacterHub = _character_sheet as CharacterHub
	if hub != null and hub.visible and not GameState.input_locked:
		hub.close_sheet()
