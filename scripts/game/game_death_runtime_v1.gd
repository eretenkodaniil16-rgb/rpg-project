extends "res://scripts/game/game_ai_stealth_v2_ui_runtime.gd"

const MINIMUM_DEATH_PRESENTATION_SECONDS: float = 0.8

var _death_presentation_started: bool = false
var _death_presentation_started_at_msec: int = -1


func _ready() -> void:
	super._ready()
	call_deferred("_resume_restored_death_presentation")


func _handle_srd_player_death(source: Node) -> void:
	_player_combat_state.dead = true
	_begin_confirmed_death_presentation()
	if _turn_system.active:
		_stop_turn_based_combat("Персонаж погиб.")
	# The SRD base implementation intentionally calls its own parent defeat
	# handler. At the top of the production stack that would bypass the guard-post
	# death/load transition, so route final death through this runtime's public
	# handler instead.
	await handle_player_defeat(source)


func handle_player_defeat(source: Node = null) -> void:
	_begin_confirmed_death_presentation()
	await super.handle_player_defeat(source)


func is_death_presentation_started_for_testing() -> bool:
	return _death_presentation_started


func get_death_presentation_elapsed_seconds_for_testing() -> float:
	if _death_presentation_started_at_msec < 0:
		return 0.0
	return float(Time.get_ticks_msec() - _death_presentation_started_at_msec) / 1000.0


func get_minimum_death_presentation_seconds_for_testing() -> float:
	return MINIMUM_DEATH_PRESENTATION_SECONDS


func _begin_confirmed_death_presentation() -> bool:
	if _death_presentation_started:
		return true
	if (
		_player_combat_state == null
		or not _player_combat_state.dead
		or GameState.player_character == null
		or GameState.player_character.current_health > 0
	):
		return false
	_death_presentation_started = true
	_death_presentation_started_at_msec = Time.get_ticks_msec()
	GameState.input_locked = true
	_cancel_pending_death_reactions()
	if _spell_area_targeting_active:
		_cancel_spell_area_targeting()
	if player != null and player.has_method("start_confirmed_death_animation"):
		player.call("start_confirmed_death_animation")
	return true


func _resume_restored_death_presentation() -> void:
	if GameState.player_character == null or GameState.player_character.current_health > 0:
		return
	var restored_state: Dictionary = PlayerCharacter.normalize_death_visual_state(
		GameState.player_character.death_visual_state
	)
	if restored_state.is_empty():
		return
	# A persisted death visual can only be written after confirmed final death.
	# Treat it as the durable proof that the transient CombatantState must be
	# restored as dead before resuming the normal last-save transition.
	_player_combat_state.dead = true
	if not _begin_confirmed_death_presentation():
		return
	if _turn_system.active:
		_stop_turn_based_combat("Персонаж погиб.")
	await handle_player_defeat(null)


func _cancel_pending_death_reactions() -> void:
	if (
		_reaction_choice_prompt != null
		and _reaction_choice_prompt.is_waiting_for_decision()
	):
		_reaction_choice_prompt.skip_reaction()
	if (
		_spell_reaction_prompt != null
		and _spell_reaction_prompt.is_waiting_for_decision()
	):
		_spell_reaction_prompt.skip_reaction()
