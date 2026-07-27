extends "res://scripts/game/game_presented_rolls.gd"

var _spellcasting_runtime: SpellcastingSystem = SpellcastingSystem.new()
var _world_time_runtime: WorldTimeSystem = WorldTimeSystem.new()


func _ready() -> void:
	var spell_state_changed: bool = _spellcasting_runtime.ensure_character(GameState.player_character, false)
	_spellcasting_runtime.cleanup_expired_effects(GameState.player_character, _world_time_runtime.get_minutes(GameState))
	if spell_state_changed:
		GameState.save_game()
	super._ready()
	var concentration_source_id: int = player.get_instance_id() if player != null else 0
	_spellcasting_runtime.sync_concentration_to_combat_state(
		GameState.player_character,
		_player_combat_state,
		concentration_source_id
	)
	if _attack_popup != null:
		_attack_popup.remove_from_group("combat_ui")
	_add_exploration_hud_node(_d20_overlay)
	_add_exploration_hud_node(_combat_feed)
