extends "res://scripts/game/game_racial_planned.gd"

var _spellcasting_sync: SpellcastingSystem = SpellcastingSystem.new()


func _request_attack() -> void:
	if GameState.input_locked or _any_overlay_visible() or _attack_in_progress or _enemy_turn_running:
		return
	if _turn_system.active and not _turn_system.is_player_turn(player):
		show_combat_message("Атаковать можно только на своём ходу.", false)
		return
	if not _srd_rules.can_take_action(_player_combat_state):
		show_combat_message("Текущее состояние не позволяет совершать действия.", false)
		return

	var weapon: Dictionary = _class_data.get_equipped_weapon(GameState.player_character)
	var selected_before: Node = _selected_target
	var predicted_target: Node = selected_before if _target_is_valid(selected_before) else _predict_directional_target(weapon)
	if _target_is_valid(selected_before) and _target_has_total_cover(selected_before):
		show_combat_message("Цель находится за полным укрытием.", false)
		return
	var valid_attempt: bool = _weapon_attempt_is_valid(weapon, selected_before, predicted_target)
	if _turn_system.active and valid_attempt and not _turn_system.consume_action():
		show_combat_message("Действие на этом ходу уже использовано.", false)
		return

	if _target_is_valid(selected_before):
		_face_toward((selected_before as Node2D).global_position)
		var ammo_id: String = str(weapon.get("ammunition_id", ""))
		await _perform_srd_weapon_attack(selected_before, weapon, ammo_id)
	elif DistanceSystem.is_ranged_weapon(weapon):
		await _request_directional_ranged_attack(weapon)
	else:
		await _request_directional_melee_attack(weapon)

	if not _turn_system.active and valid_attempt and _target_is_valid(predicted_target):
		_start_turn_based_combat(predicted_target)
	_after_player_action()


func _on_ability_requested(ability_id: String) -> void:
	await super._on_ability_requested(ability_id)
	var ability: Dictionary = _class_data.get_ability_definition(ability_id)
	if ability.is_empty() or not bool(ability.get("concentration", false)):
		return
	var concentration_id: String = _spellcasting_sync.get_concentration_spell_id(GameState.player_character)
	if not concentration_id.is_empty():
		_player_combat_state.set_concentration(concentration_id, player.get_instance_id())


func apply_damage_to_player(amount: int, damage_type: String, critical_hit: bool = false, source: Node = null) -> Dictionary:
	var result: Dictionary = super.apply_damage_to_player(amount, damage_type, critical_hit, source)
	if _player_combat_state.concentrating_on.is_empty():
		_spellcasting_sync.end_concentration(GameState.player_character)
	return result


func _build_srd_attack_context(target: Node, distance: int) -> Dictionary:
	var context: Dictionary = super._build_srd_attack_context(target, distance)
	context["turn_based"] = _turn_system.active
	if is_instance_valid(target) and target.has_method("get_current_health") and target.has_method("get_maximum_health"):
		context["target_wounded"] = int(target.call("get_current_health")) < int(target.call("get_maximum_health"))
	else:
		context["target_wounded"] = false
	return context


func _ability_attempt_is_valid(ability: Dictionary) -> bool:
	var target_type: String = str(ability.get("target", "self"))
	if target_type != "self":
		if not _target_is_valid(_selected_target):
			return false
		var maximum_range: int = int(ability.get("range_ft", 5))
		if DistanceSystem.distance_feet(player.global_position, (_selected_target as Node2D).global_position) > maximum_range:
			return false
	return _ability_system.can_pay_ability_cost(GameState.player_character, ability)
