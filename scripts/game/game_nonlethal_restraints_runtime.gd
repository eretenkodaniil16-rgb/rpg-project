extends "res://scripts/game/game_advanced_combat_ai_runtime.gd"

const BIND_ACTION_PREFIX: String = "bind_unconscious__"
const NONLETHAL_TOGGLE_ACTION: String = "toggle_nonlethal_attack"
const RELEASE_RESTRAINT_ACTION: String = "release_body_restraint"

var _nonlethal_mode_enabled: bool = false


func return_to_menu() -> void:
	_nonlethal_mode_enabled = false
	super.return_to_menu()


func is_nonlethal_mode_enabled_for_testing() -> bool:
	return _nonlethal_mode_enabled


func _build_catalog_entries() -> Dictionary:
	var entries: Dictionary = super._build_catalog_entries()
	var actions: Array = entries.get("action", []) as Array
	if not _is_body_target(_selected_target):
		actions.append(_entry(
			NONLETHAL_TOGGLE_ACTION,
			"НЕСМЕРТЕЛЬНЫЙ УДАР: %s" % ("ВКЛ" if _nonlethal_mode_enabled else "ВЫКЛ"),
			true,
			"Свободно переключает намерение. Срабатывает только когда атака ближнего боя должна снизить живую цель до 0 HP; тогда цель остаётся с 1 HP без сознания. Дальние атаки и заклинания не получают этот эффект.",
			"tactic"
		))
		entries["action"] = actions
		return entries

	var body: Node = _selected_target
	if not body.has_method("is_unconscious_body") or not bool(body.call("is_unconscious_body")):
		entries["action"] = actions
		return entries
	var near_body: bool = DistanceSystem.distance_feet(player.global_position, (body as Node2D).global_position) <= CORPSE_INTERACTION_DISTANCE_FEET
	var action_available: bool = not _turn_system.active or (
		_turn_system.is_player_turn(player) and _turn_system.action_available
	)
	if body.has_method("is_bound_body") and bool(body.call("is_bound_body")):
		var binding: Dictionary = body.call("get_binding_context") as Dictionary if body.has_method("get_binding_context") else {}
		actions.append(_entry(
			RELEASE_RESTRAINT_ACTION,
			"ОСВОБОДИТЬ ОТ ПУТ",
			near_body and action_available,
			"Освободить цель от %s. В бою расходует действие; вне боя выполняется сразу." % str(binding.get("label", "пут")),
			"world"
		))
	else:
		var sources: Array[Dictionary] = body.call("get_available_restraint_sources") as Array[Dictionary] if body.has_method("get_available_restraint_sources") else []
		if sources.is_empty():
			actions.append(_entry(
				"bind_unconscious_unavailable",
				"СВЯЗАТЬ",
				false,
				"Нужна свободная верёвка, кандалы или другой зарегистрированный источник пут. Один источник нельзя использовать для нескольких пленников одновременно.",
				"world"
			))
		else:
			for source: Dictionary in sources:
				var item_id: String = str(source.get("item_id", ""))
				if item_id.is_empty():
					continue
				actions.append(_entry(
					"%s%s" % [BIND_ACTION_PREFIX, item_id],
					"СВЯЗАТЬ: %s" % str(source.get("label", item_id)),
					near_body and action_available,
					"Зафиксировать бессознательную живую цель. Сл освобождения: %d. В бою расходует действие; источник пут резервируется до освобождения." % int(source.get("escape_dc", 10)),
					"world"
				))
	entries["action"] = actions
	return entries


func _on_catalog_action_requested(action_id: String) -> void:
	if action_id == NONLETHAL_TOGGLE_ACTION:
		_nonlethal_mode_enabled = not _nonlethal_mode_enabled
		show_combat_message(
			"Несмертельный удар включён: следующий добивающий удар ближнего боя оставит цель без сознания." if _nonlethal_mode_enabled else "Несмертельный удар выключен: снижение врага до 0 HP будет смертельным.",
			true
		)
	elif action_id.begins_with(BIND_ACTION_PREFIX):
		_bind_selected_unconscious_body(action_id.trim_prefix(BIND_ACTION_PREFIX))
	elif action_id == RELEASE_RESTRAINT_ACTION:
		_release_selected_body_restraint()
	else:
		super._on_catalog_action_requested(action_id)
	_refresh_action_catalog()


func _perform_srd_weapon_attack(target: Node, weapon: Dictionary, ammo_id: String) -> void:
	if not _target_is_valid(target):
		return
	var target_position: Vector2 = (target as Node2D).global_position
	var distance: int = DistanceSystem.distance_feet(player.global_position, target_position)
	var context: Dictionary = _build_srd_attack_context(target, distance)
	context["no_ammunition"] = not ammo_id.is_empty() and not GameState.has_item(ammo_id)
	var result: AttackResult = _combat_system.perform_basic_attack(
		GameState.player_character,
		int(target.call("get_armor_class")),
		weapon,
		-1,
		[],
		context
	)
	result.melee_attack = result.range_state == "melee"
	if result.out_of_range or result.no_ammunition or (result.automatic_miss and not result.note.is_empty()):
		_attack_popup.show_result(result)
		_sync_exploration_hud_visibility()
		return
	_set_combat_busy(true)
	if not ammo_id.is_empty():
		GameState.remove_item(ammo_id, 1, false)
	if result.hit:
		_apply_mitigation_to_result(result, _state_for(target))
		_prepare_nonlethal_knockout(result, target)
	if DistanceSystem.is_ranged_weapon(weapon):
		await _play_weapon_projectile(weapon, target_position, result.hit)
	else:
		player.play_attack_animation(target_position)
	if _target_is_valid(target):
		target.call("receive_player_attack", result, true)
		if int(target.call("get_current_health")) <= 0 or result.nonlethal_knockout:
			_release_grapples_for(target)
	if result.nonlethal_knockout:
		_nonlethal_mode_enabled = false
		show_combat_message("Цель выведена из боя несмертельным ударом и остаётся жива без сознания.", true)
	GameState.save_game()
	_update_status()
	_set_combat_busy(false)
	_sync_exploration_hud_visibility()


func _prepare_nonlethal_knockout(result: AttackResult, target: Node) -> void:
	if not _nonlethal_mode_enabled or result == null or not result.hit or not result.melee_attack:
		return
	if target == null or not target.has_method("get_current_health"):
		return
	var health_before: int = maxi(int(target.call("get_current_health")), 0)
	if health_before <= 0 or result.damage < health_before:
		return
	result.nonlethal_knockout = true
	result.target_health_after = 1
	result.note = "%s %s" % [result.note, "Несмертельный исход: цель остаётся с 1 HP без сознания."]
	result.note = result.note.strip_edges()


func _bind_selected_unconscious_body(item_id: String) -> void:
	if not _selected_body_is_reachable() or not _selected_target.has_method("bind_unconscious_body"):
		show_combat_message("Чтобы связать цель, нужно находиться рядом с ней.", false)
		return
	if not _consume_restraint_action_if_needed():
		return
	var result: Dictionary = _selected_target.call("bind_unconscious_body", item_id) as Dictionary
	show_combat_message(str(result.get("message", "Связывание не удалось.")), bool(result.get("success", false)))
	if bool(result.get("success", false)):
		_update_status()


func _release_selected_body_restraint() -> void:
	if not _selected_body_is_reachable() or not _selected_target.has_method("release_body_restraint"):
		show_combat_message("Чтобы освободить цель, нужно находиться рядом с ней.", false)
		return
	if not _consume_restraint_action_if_needed():
		return
	var result: Dictionary = _selected_target.call("release_body_restraint") as Dictionary
	show_combat_message(str(result.get("message", "Освобождение не удалось.")), bool(result.get("success", false)))
	if bool(result.get("success", false)):
		_update_status()


func _consume_restraint_action_if_needed() -> bool:
	if not _turn_system.active:
		return true
	if not _turn_system.is_player_turn(player):
		show_combat_message("Связывать или освобождать можно только на своём ходу.", false)
		return false
	if not _turn_system.consume_action():
		show_combat_message("Действие на этом ходу уже использовано.", false)
		return false
	return true
