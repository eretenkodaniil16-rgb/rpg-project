extends "res://scripts/game/game_party_target_memory_runtime.gd"

const STEALTH_PERCEPTION_SCRIPT: Script = preload("res://scripts/systems/exploration_stealth_perception_system.gd")
const TACTICAL_TARGETING_SCRIPT: Script = preload("res://scripts/systems/npc_tactical_targeting_system.gd")

var _stealth_perception: ExplorationStealthPerceptionSystem = STEALTH_PERCEPTION_SCRIPT.new() as ExplorationStealthPerceptionSystem
var _tactical_targeting: NpcTacticalTargetingSystem = TACTICAL_TARGETING_SCRIPT.new() as NpcTacticalTargetingSystem
var _exploration_stealth_total_v2: int = 0
var _perception_tick_accumulator_v2: float = 0.0
var _active_search_cooldown_by_actor_v2: Dictionary = {}
var _active_search_roll_overrides_v2: Array[int] = []
var _target_claim_round_v2: int = -1
var _target_claim_by_actor_v2: Dictionary = {}
var _target_claim_count_v2: Dictionary = {}
var _last_targeting_diagnostics_v2: Dictionary = {}


func _ready() -> void:
	super._ready()
	_restore_exploration_stealth_v2()
	_refresh_alert_indicator()


func _build_catalog_entries() -> Dictionary:
	var entries: Dictionary = super._build_catalog_entries()
	if _turn_system.active:
		return entries
	var values: Variant = entries.get("action", [])
	if not values is Array:
		return entries
	var action_entries: Array = values as Array
	for index: int in range(action_entries.size()):
		var value: Variant = action_entries[index]
		if not value is Dictionary:
			continue
		var entry: Dictionary = (value as Dictionary).duplicate(true)
		if str(entry.get("id", "")) != "exploration_hide":
			continue
		if _exploration_hidden:
			entry["description"] = "Прекратить скрытное перемещение. Текущий результат Скрытности: %d. Атака, громкий шум или обнаружение также прекращают скрытность." % _exploration_stealth_total_v2
		else:
			var spot: Dictionary = _stealth_alerts.get_hiding_spot_at(player.global_position)
			var bonus: int = int(spot.get("concealment_bonus", 0))
			entry["description"] = "Войти в скрытное перемещение вне прямой видимости. После успешной проверки можно тихо двигаться по обычному миру; каждый NPC сопоставляет результат с собственным пассивным Восприятием.%s" % (" Укрытие даёт +%d." % bonus if bonus != 0 else "")
		action_entries[index] = entry
	entries["action"] = action_entries
	return entries


func _toggle_exploration_hide() -> void:
	if _exploration_hidden:
		_break_exploration_hidden("Герой прекратил скрытное перемещение.")
		return
	var visible_observers: Array[Node] = _visible_exploration_observers()
	if not visible_observers.is_empty():
		show_combat_message(_line_of_sight_failure_message(visible_observers), false)
		return

	var hiding_spot: Dictionary = _stealth_alerts.get_hiding_spot_at(player.global_position)
	var concealment_bonus: int = int(hiding_spot.get("concealment_bonus", 0))
	var difficulty: int = _stealth_perception.get_hide_entry_dc()
	var overrides: Array[int] = _exploration_hide_roll_overrides.duplicate()
	_exploration_hide_roll_overrides.clear()
	var check: Dictionary = _srd_rules.resolve_d20_test(
		GameState.player_character.get_skill_modifier("stealth"),
		difficulty,
		false,
		_player_has_untrained_armor_d20_disadvantage("dexterity"),
		overrides,
		GameState.player_character.reroll_natural_one
	)
	var total: int = int(check.get("total", 0)) + concealment_bonus
	if total < difficulty:
		show_combat_message("Скрыться не удалось: Скрытность %d против СЛ %d." % [total, difficulty], false)
		report_world_noise("quiet_step", player.global_position, {"source_type": "failed_hide"})
		return

	_exploration_hidden = true
	_exploration_stealth_total_v2 = total
	GameState.player_character.active_effects["exploration_hidden"] = true
	GameState.player_character.active_effects["exploration_stealth_total"] = total
	var location_label: String = str(hiding_spot.get("label", "вне прямой видимости"))
	show_combat_message("Герой скрыт (%s): результат Скрытности %d. NPC теперь используют собственное пассивное Восприятие и активный поиск." % [location_label, total], true)
	_refresh_action_catalog()
	_refresh_alert_indicator()


func _break_exploration_hidden(message: String = "") -> void:
	var was_hidden: bool = _exploration_hidden
	super._break_exploration_hidden(message)
	if not was_hidden:
		return
	_exploration_stealth_total_v2 = 0
	GameState.player_character.active_effects.erase("exploration_stealth_total")
	_refresh_alert_indicator()


func _update_exploration_step_noise(delta: float) -> void:
	var current_position: Vector2 = player.global_position
	if _last_exploration_player_position == Vector2.INF:
		_last_exploration_player_position = current_position
		return
	var distance: float = current_position.distance_to(_last_exploration_player_position)
	_last_exploration_player_position = current_position
	if distance <= 0.75:
		_step_noise_elapsed = 0.0
		return
	_step_noise_elapsed += maxf(delta, 0.0)
	if _step_noise_elapsed < STEP_NOISE_INTERVAL_SECONDS:
		return
	_step_noise_elapsed = 0.0
	var hiding_spot: Dictionary = _stealth_alerts.get_hiding_spot_at(current_position)
	var noise_type: String = "quiet_step" if _exploration_hidden else "normal_step"
	var overrides: Dictionary = {"source_type": "player_movement"}
	if not hiding_spot.is_empty():
		overrides["intensity"] = roundi(
			float(_stealth_alerts.get_noise_profile(noise_type).get("intensity", 10))
			* float(hiding_spot.get("noise_multiplier", 1.0))
		)
	report_world_noise(noise_type, current_position, overrides)


func _update_exploration_alerts(delta: float) -> void:
	_perception_tick_accumulator_v2 += maxf(delta, 0.0)
	var interval: float = _stealth_perception.get_perception_tick_seconds()
	if _perception_tick_accumulator_v2 < interval:
		return
	var tick_delta: float = _perception_tick_accumulator_v2
	_perception_tick_accumulator_v2 = 0.0
	for actor: Node in _exploration_alert_actors():
		_update_exploration_actor(actor, tick_delta)


func _update_exploration_actor(actor: Node, delta: float) -> void:
	if actor == null or not is_instance_valid(actor) or not (actor is Node2D):
		return
	var actor_id: String = str(actor.call("get_actor_id"))
	var profile: Dictionary = _stealth_alerts.get_profile(actor_id)
	if profile.is_empty():
		return
	var record: Dictionary = _record_for_actor(actor_id)
	var visible: bool = _exploration_actor_can_see_player(actor, profile)
	if not visible and _exploration_hidden:
		visible = _active_search_finds_hidden_player(actor, profile, record, delta)
	var target_hidden: bool = _exploration_hidden
	record = _stealth_alerts.apply_visual_observation(
		record,
		visible,
		target_hidden,
		player.global_position,
		delta,
		profile
	)
	if visible:
		if _exploration_hidden:
			_break_exploration_hidden("%s обнаружил героя." % _target_name(actor))
		if actor.has_method("set_facing_direction"):
			actor.call("set_facing_direction", player.global_position - (actor as Node2D).global_position)
	else:
		record = _advance_actor_investigation(actor, record, profile, delta)
	_alert_records[actor_id] = record
	_apply_record_to_actor(actor, record)
	if str(record.get("state", "")) == StealthAlertSystem.STATE_ALERTED and visible:
		_begin_combat_from_alert(actor, record)


func _exploration_actor_can_see_player(actor: Node, profile: Dictionary) -> bool:
	var observation: Dictionary = _geometric_exploration_observation(actor, profile)
	if not bool(observation.get("geometric_visible", false)):
		return false
	if not _exploration_hidden:
		return true
	var detection: Dictionary = _stealth_perception.resolve_passive_detection(
		_exploration_stealth_total_v2,
		int(profile.get("passive_perception", 10)),
		int(observation.get("distance_feet", 0)),
		true,
		bool(observation.get("fully_concealed", false))
	)
	return bool(detection.get("detected", false))


func _geometric_exploration_observation(actor: Node, profile: Dictionary) -> Dictionary:
	if actor == null or not is_instance_valid(actor) or not (actor is Node2D):
		return {"geometric_visible": false, "distance_feet": 9999, "fully_concealed": false}
	var actor_position: Vector2 = (actor as Node2D).global_position
	var facing: Vector2 = (
		actor.call("get_facing_direction") as Vector2
		if actor.has_method("get_facing_direction")
		else Vector2.LEFT
	)
	var line_of_sight_clear: bool = not _stealth_alerts.door_blocks_line_of_sight(
		GameState,
		actor_position,
		player.global_position
	)
	if line_of_sight_clear and _combat_environment != null:
		line_of_sight_clear = _combat_environment.has_line_of_sight(actor_position, player.global_position)
	var geometric_visible: bool = _stealth_alerts.can_see_target(
		actor_position,
		facing,
		player.global_position,
		profile,
		line_of_sight_clear,
		false
	)
	return {
		"geometric_visible": geometric_visible,
		"distance_feet": DistanceSystem.distance_feet(actor_position, player.global_position),
		"fully_concealed": _exploration_hidden and not _stealth_alerts.get_hiding_spot_at(player.global_position).is_empty()
	}


func _active_search_finds_hidden_player(
	actor: Node,
	profile: Dictionary,
	record: Dictionary,
	delta: float
) -> bool:
	if not _exploration_hidden or _exploration_stealth_total_v2 <= 0:
		return false
	var state_id: String = str(record.get("state", StealthAlertSystem.STATE_CALM))
	if not _stealth_perception.is_active_search_state(state_id):
		return false
	var actor_id: String = str(actor.call("get_actor_id"))
	var cooldown: float = maxf(float(_active_search_cooldown_by_actor_v2.get(actor_id, 0.0)) - maxf(delta, 0.0), 0.0)
	_active_search_cooldown_by_actor_v2[actor_id] = cooldown
	if cooldown > 0.0:
		return false
	var observation: Dictionary = _geometric_exploration_observation(actor, profile)
	if not bool(observation.get("geometric_visible", false)):
		return false
	if int(observation.get("distance_feet", 9999)) > _stealth_perception.get_active_search_max_distance_feet():
		return false
	_active_search_cooldown_by_actor_v2[actor_id] = _stealth_perception.get_active_search_interval_seconds()
	var natural: int
	if not _active_search_roll_overrides_v2.is_empty():
		natural = clampi(_active_search_roll_overrides_v2.pop_front(), 1, 20)
	else:
		natural = int(_srd_rules.roll_d20(0).get("natural", 1))
	var search: Dictionary = _stealth_perception.resolve_active_search(
		_exploration_stealth_total_v2,
		int(profile.get("perception_modifier", 0)),
		natural
	)
	if bool(search.get("success", false)):
		show_combat_message("%s проводит активный поиск и замечает героя: Восприятие %d против Скрытности %d." % [
			_target_name(actor),
			int(search.get("total", 0)),
			_exploration_stealth_total_v2
		], false)
		return true
	return false


func _refresh_alert_indicator() -> void:
	super._refresh_alert_indicator()
	if _alert_indicator != null and _exploration_hidden and _exploration_stealth_total_v2 > 0:
		_alert_indicator.text += " · СКРЫТНОСТЬ %d" % _exploration_stealth_total_v2


func _restore_exploration_stealth_v2() -> void:
	if GameState.player_character == null:
		return
	var hidden_value: Variant = GameState.player_character.active_effects.get("exploration_hidden", false)
	var stored_total: int = int(GameState.player_character.active_effects.get("exploration_stealth_total", 0))
	if bool(hidden_value):
		_exploration_hidden = true
		_exploration_stealth_total_v2 = stored_total if stored_total > 0 else _stealth_perception.get_hide_entry_dc()
		GameState.player_character.active_effects["exploration_stealth_total"] = _exploration_stealth_total_v2
	else:
		_exploration_hidden = false
		_exploration_stealth_total_v2 = 0


func _select_enemy_party_target(actor: Node) -> Node:
	if not actor is Node2D:
		return player
	_reset_target_claims_if_needed_v2()
	var actor_id: int = actor.get_instance_id()
	var actor_key: String = str(actor.call("get_actor_id")) if actor.has_method("get_actor_id") else ""
	var profile: Dictionary = _combat_ai.get_profile(actor_key) if _combat_ai != null and not actor_key.is_empty() else {}
	var role_id: String = str(profile.get("role", NpcCombatAiSystem.ROLE_MELEE))
	var attack_range: int = maxi(int(profile.get("attack_range_feet", DistanceSystem.MELEE_REACH_FEET)), DistanceSystem.MELEE_REACH_FEET)
	var minimum_range: int = maxi(int(profile.get("minimum_range_feet", 0)), 0)
	var preferred_range: int = clampi(int(profile.get("preferred_range_feet", attack_range)), minimum_range, attack_range)
	var previous_target_id: int = int(_enemy_party_target_by_actor_id.get(actor_id, 0))
	var candidates: Array[Dictionary] = []
	for target: Node in [player, _controllable_ally]:
		if not _enemy_party_target_is_available(target):
			continue
		if not _enemy_can_see_party_target_from((actor as Node2D).global_position, target):
			continue
		var distance: int = DistanceSystem.distance_feet((actor as Node2D).global_position, (target as Node2D).global_position)
		var target_id: int = target.get_instance_id()
		var claim_count: int = _claim_count_for_target_v2(target_id, actor_id)
		candidates.append({
			"target": target,
			"target_id": target_id,
			"available": true,
			"visible": true,
			"distance_feet": distance,
			"attack_ready": distance <= attack_range and distance >= minimum_range,
			"preferred_range_feet": preferred_range,
			"health_ratio": _party_target_health_ratio_v2(target),
			"previous_target": target_id == previous_target_id,
			"claim_count": claim_count,
			"immediate_melee_threat": distance <= DistanceSystem.MELEE_REACH_FEET,
			"full_tactics_supported": target == player,
			"role": role_id
		})
	if candidates.is_empty():
		_release_actor_target_claim_v2(actor_id)
		_enemy_party_target_by_actor_id.erase(actor_id)
		return player
	var selection: Dictionary = _tactical_targeting.choose_target(candidates, previous_target_id)
	var selected: Node = selection.get("target") as Node
	if not is_instance_valid(selected):
		selected = candidates[0].get("target") as Node
	_assign_actor_target_claim_v2(actor_id, selected.get_instance_id())
	_enemy_party_target_by_actor_id[actor_id] = selected.get_instance_id()
	_enemy_attack_range_by_actor_id[actor_id] = attack_range
	_last_targeting_diagnostics_v2 = {
		"actor_id": actor_key,
		"selected_target_id": selected.get_instance_id(),
		"selected_target_name": _target_name(selected),
		"selected_score": float(selection.get("utility_score", 0.0)),
		"candidate_count": candidates.size(),
		"round": _turn_system.round_number
	}
	return selected


func _plan_enemy_movement_to_party_target(
	actor_node: Node2D,
	actor: Node,
	target: Node,
	movement_feet: int,
	attack_range_feet: int,
	minimum_range_feet: int,
	preferred_range_feet: int
) -> Dictionary:
	if not target is Node2D:
		return {"path": [], "score": NpcCombatAiSystem.BLOCKED_SCORE}
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return {"path": [], "score": NpcCombatAiSystem.BLOCKED_SCORE}
	var actor_key: String = str(actor.call("get_actor_id")) if actor.has_method("get_actor_id") else ""
	var profile: Dictionary = _combat_ai.get_profile(actor_key) if _combat_ai != null and not actor_key.is_empty() else {}
	var role_id: String = str(profile.get("role", NpcCombatAiSystem.ROLE_MELEE))
	var health_ratio: float = _actor_health_ratio_v2(actor)
	var retreat_threshold: float = clampf(float(profile.get("retreat_health_ratio", 0.18)), 0.0, 1.0)
	var retreating: bool = health_ratio <= retreat_threshold
	var cover_preference: float = clampf(float(profile.get("cover_preference", 0.0)), 0.0, 2.0)
	var spacing_feet: int = maxi(int(profile.get("spacing_feet", 5)), 0)
	var target_position: Vector2 = (target as Node2D).global_position
	var selected: Dictionary = {}
	var selected_score: float = NpcCombatAiSystem.BLOCKED_SCORE
	for candidate: Dictionary in _build_combat_ai_reachable_candidates(actor_node, movement_feet):
		var cell: Vector2i = candidate.get("cell", grid.world_to_cell(actor_node.global_position)) as Vector2i
		var position: Vector2 = grid.cell_to_world_center(cell)
		var visible: bool = _enemy_can_see_party_target_from(position, target)
		var distance: int = DistanceSystem.distance_feet(position, target_position)
		var attack_ready: bool = visible and distance <= attack_range_feet and distance >= minimum_range_feet
		var cover: Dictionary = _combat_environment.get_cover(target_position, position) if _combat_environment != null else {"bonus": 0, "total_cover": false}
		var mobility: int = _combat_ai_mobility_from(actor_node, position)
		var ally_distance: int = _nearest_combat_ai_ally_distance(actor, position)
		var score: float
		if retreating:
			score = float(distance) * 4.2 + float(int(cover.get("bonus", 0))) * 18.0 + float(mobility) * 3.0
			if bool(cover.get("total_cover", false)):
				score += 55.0
		else:
			score = 0.0
			if attack_ready:
				score += 10000.0
			if visible:
				score += 130.0
			score -= float(absi(distance - preferred_range_feet)) * (6.5 if role_id in [NpcCombatAiSystem.ROLE_RANGED, AdvancedNpcCombatAiSystem.ROLE_CASTER] else 4.0)
			if role_id in [NpcCombatAiSystem.ROLE_RANGED, AdvancedNpcCombatAiSystem.ROLE_CASTER]:
				score += float(int(cover.get("bonus", 0))) * 15.0 * maxf(cover_preference, 0.35)
				if distance < minimum_range_feet:
					score -= float(minimum_range_feet - distance) * 12.0
			else:
				score -= float(distance) * 0.35
			score += float(mobility) * 2.2
			if ally_distance < spacing_feet:
				score -= float(spacing_feet - ally_distance) * 3.0
		score -= float(int(candidate.get("cost_feet", 0))) * 0.12
		candidate["score"] = score
		candidate["world_position"] = position
		candidate["target_visible"] = visible
		candidate["attack_ready"] = attack_ready
		candidate["retreating"] = retreating
		if _combat_ai_candidate_is_better(candidate, score, selected, selected_score):
			selected = candidate.duplicate(true)
			selected_score = score
	if selected.is_empty():
		return {"path": [], "score": NpcCombatAiSystem.BLOCKED_SCORE}
	selected["score"] = selected_score
	return selected


func _party_target_health_ratio_v2(target: Node) -> float:
	if target == player:
		var character: PlayerCharacter = GameState.player_character as PlayerCharacter
		return float(character.current_health) / float(maxi(character.maximum_health, 1)) if character != null else 0.0
	if target == _controllable_ally:
		return float(_ally_current_health()) / float(maxi(_ally_maximum_health(), 1))
	return 1.0


func _actor_health_ratio_v2(actor: Node) -> float:
	var current: int = int(actor.call("get_current_health")) if actor != null and actor.has_method("get_current_health") else 1
	var maximum: int = int(actor.call("get_maximum_health")) if actor != null and actor.has_method("get_maximum_health") else maxi(current, 1)
	return float(current) / float(maxi(maximum, 1))


func _reset_target_claims_if_needed_v2() -> void:
	if _target_claim_round_v2 == _turn_system.round_number:
		return
	_target_claim_round_v2 = _turn_system.round_number
	_target_claim_by_actor_v2.clear()
	_target_claim_count_v2.clear()


func _claim_count_for_target_v2(target_id: int, querying_actor_id: int) -> int:
	var count: int = maxi(int(_target_claim_count_v2.get(target_id, 0)), 0)
	if int(_target_claim_by_actor_v2.get(querying_actor_id, 0)) == target_id:
		count = maxi(count - 1, 0)
	return count


func _release_actor_target_claim_v2(actor_id: int) -> void:
	var previous_target_id: int = int(_target_claim_by_actor_v2.get(actor_id, 0))
	if previous_target_id != 0:
		var previous_count: int = maxi(int(_target_claim_count_v2.get(previous_target_id, 0)) - 1, 0)
		if previous_count <= 0:
			_target_claim_count_v2.erase(previous_target_id)
		else:
			_target_claim_count_v2[previous_target_id] = previous_count
	_target_claim_by_actor_v2.erase(actor_id)


func _assign_actor_target_claim_v2(actor_id: int, target_id: int) -> void:
	_release_actor_target_claim_v2(actor_id)
	_target_claim_by_actor_v2[actor_id] = target_id
	_target_claim_count_v2[target_id] = maxi(int(_target_claim_count_v2.get(target_id, 0)), 0) + 1


func set_exploration_stealth_total_v2_for_testing(total: int) -> void:
	_exploration_hidden = total > 0
	_exploration_stealth_total_v2 = maxi(total, 0)
	if _exploration_hidden:
		GameState.player_character.active_effects["exploration_hidden"] = true
		GameState.player_character.active_effects["exploration_stealth_total"] = _exploration_stealth_total_v2
	else:
		GameState.player_character.active_effects.erase("exploration_hidden")
		GameState.player_character.active_effects.erase("exploration_stealth_total")


func get_exploration_stealth_total_v2_for_testing() -> int:
	return _exploration_stealth_total_v2


func set_active_search_roll_overrides_v2_for_testing(values: Array) -> void:
	_active_search_roll_overrides_v2.clear()
	for value: Variant in values:
		_active_search_roll_overrides_v2.append(int(value))


func resolve_passive_detection_v2_for_testing(
	stealth_total: int,
	passive_perception: int,
	distance_feet: int,
	geometric_visible: bool,
	fully_concealed: bool = false
) -> Dictionary:
	return _stealth_perception.resolve_passive_detection(
		stealth_total,
		passive_perception,
		distance_feet,
		geometric_visible,
		fully_concealed
	)


func get_last_targeting_diagnostics_v2_for_testing() -> Dictionary:
	return _last_targeting_diagnostics_v2.duplicate(true)
