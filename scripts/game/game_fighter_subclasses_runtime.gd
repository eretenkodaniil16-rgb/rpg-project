extends "res://scripts/game/game_multi_reactor_reactions_runtime.gd"

var _fighter_subclasses: FighterSubclassSystem = FighterSubclassSystem.new()


func _ready() -> void:
	_class_data = ClassDataSubclassSystem.new()
	_ability_system = ClassAbilitySubclassSystem.new()
	_combat_system = CombatSubclassSystem.new()
	super._ready()
	if _fighter_subclasses.ensure_character(GameState.player_character):
		GameState.save_game()
		if _ability_panel != null:
			_ability_panel.bind_character(GameState.player_character)


func _build_catalog_entries() -> Dictionary:
	var entries: Dictionary = super._build_catalog_entries()
	for ability: Dictionary in _fighter_subclasses.get_active_ability_definitions(
		GameState.player_character
	):
		var ability_id: String = str(ability.get("id", ""))
		var entry_id: String = "ability:%s" % ability_id
		var action_kind: String = _ability_action_kind(ability_id, ability)
		var category: String = "bonus" if action_kind == "bonus" else "action"
		var category_entries: Array = entries.get(category, []) as Array
		if _catalog_contains(category_entries, entry_id):
			continue
		var player_turn: bool = (
			_turn_system.active
			and _turn_system.is_player_turn(player)
			and not _enemy_turn_running
		)
		var action_available: bool = (
			_turn_system.bonus_action_available
			if category == "bonus"
			else _turn_system.action_available
		)
		category_entries.append(_entry(
			entry_id,
			str(ability.get("name", "Способность подкласса")),
			player_turn
			and action_available
			and _ability_attempt_is_valid(ability)
			and _srd_rules.can_take_action(_player_combat_state),
			"%s. Ресурс: %s." % [
				str(ability.get("description", "")),
				_class_data.get_resource_text(GameState.player_character, ability)
			],
			"tactic"
		))
		entries[category] = category_entries
	return entries


func _ability_attempt_is_valid(ability: Dictionary) -> bool:
	var ability_id: String = str(ability.get("id", ""))
	if (
		_fighter_subclasses.is_subclass_ability(ability_id)
		and bool(ability.get("combat_only", false))
		and not _turn_system.active
	):
		return false
	return super._ability_attempt_is_valid(ability)


func _on_ability_requested(ability_id: String) -> void:
	var ability: Dictionary = _fighter_subclasses.get_ability_definition(ability_id)
	var resource_key: String = str(ability.get("resource_key", ""))
	var resource_before: int = (
		GameState.player_character.get_resource(resource_key)
		if not resource_key.is_empty()
		else -1
	)
	await super._on_ability_requested(ability_id)
	if ability.is_empty() or resource_key.is_empty():
		return
	var successfully_consumed: bool = (
		GameState.player_character.get_resource(resource_key) < resource_before
	)
	if not successfully_consumed:
		return
	if str(ability.get("effect", "")) == "guardian_stance":
		var temporary_hit_points: int = _fighter_subclasses.guardian_temporary_hit_points(
			GameState.player_character
		)
		_player_combat_state.temporary_hit_points = maxi(
			_player_combat_state.temporary_hit_points,
			temporary_hit_points
		)
		GameState.player_character.active_effects[
			FighterSubclassSystem.GUARDIAN_ROUND_KEY
		] = _turn_system.round_number
		show_combat_message(
			"Опорная стойка: +1 КД и %d временного здоровья до начала следующего хода."
			% temporary_hit_points,
			true
		)
		GameState.save_game()
		_update_status()
		_refresh_action_catalog()


func _begin_current_turn() -> void:
	if (
		_turn_system.active
		and _turn_system.current_actor() == player
		and bool(GameState.player_character.active_effects.get(
			FighterSubclassSystem.GUARDIAN_ACTIVE_KEY,
			false
		))
	):
		var activated_round: int = int(GameState.player_character.active_effects.get(
			FighterSubclassSystem.GUARDIAN_ROUND_KEY,
			0
		))
		if activated_round > 0 and _turn_system.round_number > activated_round:
			_fighter_subclasses.clear_guardian_stance(GameState.player_character)
			GameState.save_game()
	super._begin_current_turn()


func _stop_turn_based_combat(message: String) -> void:
	if _fighter_subclasses.clear_combat_effects(GameState.player_character):
		GameState.save_game()
	super._stop_turn_based_combat(message)


func _on_level_up_completed(result: Dictionary) -> void:
	if _fighter_subclasses.ensure_character(GameState.player_character):
		GameState.save_game()
	super._on_level_up_completed(result)


func _catalog_contains(entries: Array, entry_id: String) -> bool:
	for value: Variant in entries:
		if value is Dictionary and str((value as Dictionary).get("id", "")) == entry_id:
			return true
	return false
