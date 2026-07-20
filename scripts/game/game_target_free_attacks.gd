extends "res://scripts/game/game_racial_planned.gd"


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
