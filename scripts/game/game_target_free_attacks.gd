extends "res://scripts/game/game_racial_planned.gd"

const DIRECTIONAL_ABILITY_MIN_CORRIDOR_PIXELS: float = 28.0
const DIRECTIONAL_ABILITY_MAX_CORRIDOR_PIXELS: float = 78.0

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

	# Capture encounter membership before damage is applied. The opening target
	# can die during the attack animation and cease to be a valid target, but its
	# living allies must still roll initiative after witnessing the hostile act.
	var pending_combat_candidates: Array[Node] = []
	if not _turn_system.active and valid_attempt and _target_is_valid(predicted_target):
		pending_combat_candidates = _capture_exploration_combat_candidates(predicted_target)

	if _target_is_valid(selected_before):
		_face_toward((selected_before as Node2D).global_position)
		var ammo_id: String = str(weapon.get("ammunition_id", ""))
		await _perform_srd_weapon_attack(selected_before, weapon, ammo_id)
	elif DistanceSystem.is_ranged_weapon(weapon):
		await _request_directional_ranged_attack(weapon)
	else:
		await _request_directional_melee_attack(weapon)

	if not _turn_system.active and valid_attempt:
		_start_exploration_combat_from_candidates(pending_combat_candidates)
	_after_player_action()


func _on_ability_requested(ability_id: String) -> void:
	var ability: Dictionary = _class_data.get_ability_definition(ability_id)
	var original_target: Node = _selected_target
	var temporary_directional_target: Node = null
	if (
		not ability.is_empty()
		and _ability_supports_directional_target(ability)
		and not _target_is_valid(original_target)
	):
		temporary_directional_target = _predict_directional_ability_target(ability)
		if not _target_is_valid(temporary_directional_target):
			_ability_panel.set_message("В направлении взгляда нет доступной цели для этой способности.", false)
			return
		# Use an internal transient target. It is deliberately not passed through
		# _set_selected_target(), so the player does not have to select or reveal a
		# target marker before firing in the chosen facing direction.
		_selected_target = temporary_directional_target

	var pending_combat_candidates: Array[Node] = []
	var effect: String = str(ability.get("effect", ""))
	if (
		not _turn_system.active
		and effect in ["spell_attack", "auto_hit_spell", "saving_throw_spell"]
		and _target_is_valid(_selected_target)
		and _ability_attempt_is_valid(ability)
	):
		pending_combat_candidates = _capture_exploration_combat_candidates(_selected_target)

	await super._on_ability_requested(ability_id)

	if is_instance_valid(temporary_directional_target) and _selected_target == temporary_directional_target:
		_selected_target = original_target if _target_is_valid(original_target) else null
		_update_target_label()

	if not _turn_system.active and not pending_combat_candidates.is_empty():
		_start_exploration_combat_from_candidates(pending_combat_candidates)

	if ability.is_empty() or not bool(ability.get("concentration", false)):
		return
	var concentration_id: String = _spellcasting_sync.get_concentration_spell_id(GameState.player_character)
	if not concentration_id.is_empty():
		_player_combat_state.set_concentration(concentration_id, player.get_instance_id())


func _capture_exploration_combat_candidates(trigger_target: Node) -> Array[Node]:
	var result: Array[Node] = []
	if is_instance_valid(trigger_target):
		result.append(trigger_target)
	return result


func _start_exploration_combat_from_candidates(candidates: Array[Node]) -> void:
	if _turn_system.active:
		return
	for candidate: Node in candidates:
		if not _candidate_can_anchor_combat(candidate):
			continue
		_start_turn_based_combat(candidate)
		if _turn_system.active:
			return


func _candidate_can_anchor_combat(candidate: Node) -> bool:
	if not is_instance_valid(candidate) or not candidate is Node2D:
		return false
	if candidate.has_method("is_body_interactable") and bool(candidate.call("is_body_interactable")):
		return false
	if candidate.has_method("is_combat_active") and not bool(candidate.call("is_combat_active")):
		return false
	return true


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
		var target: Node = _selected_target if _target_is_valid(_selected_target) else _predict_directional_ability_target(ability)
		if not _target_is_valid(target):
			return false
		var maximum_range: int = int(ability.get("range_ft", 5))
		if DistanceSystem.distance_feet(player.global_position, (target as Node2D).global_position) > maximum_range:
			return false
	return _ability_system.can_pay_ability_cost(GameState.player_character, ability)


func predict_directional_ability_target_for_testing(ability_id: String) -> Node:
	return _predict_directional_ability_target(_class_data.get_ability_definition(ability_id))


func _ability_supports_directional_target(ability: Dictionary) -> bool:
	if str(ability.get("target", "self")) == "self" or _is_area_spell(ability):
		return false
	return str(ability.get("effect", "")) in [
		"spell_attack",
		"auto_hit_spell",
		"saving_throw_spell",
		"hunters_mark"
	]


func _predict_directional_ability_target(ability: Dictionary) -> Node:
	if ability.is_empty() or not _ability_supports_directional_target(ability) or player == null:
		return null
	var facing: Vector2 = Vector2.RIGHT
	if player.has_method("get_facing_direction"):
		var facing_value: Variant = player.call("get_facing_direction")
		if facing_value is Vector2 and (facing_value as Vector2).length_squared() > 0.0001:
			facing = (facing_value as Vector2).normalized()
	var maximum_range_feet: int = maxi(int(ability.get("range_ft", 5)), 5)
	var maximum_range_pixels: float = DistanceSystem.feet_to_pixels(maximum_range_feet)
	var selected: Node = null
	var selected_score: float = INF
	for target: Node in _available_targets():
		if not _target_is_valid(target) or not target is Node2D or _target_has_total_cover(target):
			continue
		var offset: Vector2 = (target as Node2D).global_position - player.global_position
		var distance_pixels: float = offset.length()
		if distance_pixels <= 0.001 or distance_pixels > maximum_range_pixels:
			continue
		var forward_distance: float = offset.dot(facing)
		if forward_distance <= 0.0:
			continue
		var lateral_distance: float = absf(offset.cross(facing))
		var corridor: float = clampf(
			forward_distance * 0.32,
			DIRECTIONAL_ABILITY_MIN_CORRIDOR_PIXELS,
			DIRECTIONAL_ABILITY_MAX_CORRIDOR_PIXELS
		)
		if lateral_distance > corridor:
			continue
		var score: float = forward_distance + lateral_distance * 2.5
		if score < selected_score:
			selected_score = score
			selected = target
	return selected
