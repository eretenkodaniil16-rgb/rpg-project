extends "res://scripts/game/game.gd"

const DIRECTIONAL_TARGETING_SYSTEM: Script = preload("res://scripts/systems/directional_targeting_system.gd")
const FREE_AIM_BOUNDS: Rect2 = Rect2(45.0, 45.0, 1190.0, 630.0)


func _ready() -> void:
	super._ready()
	_set_selected_target(null)
	_update_target_label()


func _select_nearest_target() -> void:
	_set_selected_target(null)


func _cycle_target() -> void:
	if GameState.input_locked or _attack_in_progress or _any_overlay_visible():
		return
	var targets: Array[Node] = _available_targets()
	if targets.is_empty():
		_set_selected_target(null)
		show_combat_message("Нет доступных целей. Атака будет выполнена по направлению взгляда.", false)
		return
	var current_index: int = targets.find(_selected_target)
	if current_index < 0:
		_set_selected_target(targets[0])
		show_combat_message("Цель выбрана. Расстояние показано на поле.", true)
	elif current_index + 1 < targets.size():
		_set_selected_target(targets[current_index + 1])
		show_combat_message("Выбрана следующая цель.", true)
	else:
		_set_selected_target(null)
		show_combat_message("Свободная атака: удар или выстрел будет направлен по ходу движения.", true)


func _update_target_label() -> void:
	if _target_label == null:
		return
	var has_target: bool = _target_is_valid(_selected_target)
	_target_label.visible = has_target and not _any_overlay_visible()
	if _target_button != null:
		_target_button.text = "СЛЕД. ЦЕЛЬ" if has_target else "ЦЕЛЬ"
	if _attack_button != null:
		var weapon: Dictionary = _class_data.get_equipped_weapon(GameState.player_character)
		if has_target:
			_attack_button.text = "АТАКА"
		elif DistanceSystem.is_ranged_weapon(weapon):
			_attack_button.text = "ВЫСТРЕЛ"
		else:
			_attack_button.text = "УДАР"
	if not has_target:
		_target_label.text = ""
		return
	var target_position: Vector2 = (_selected_target as Node2D).global_position
	var cells: int = DistanceSystem.grid_steps(player.global_position, target_position)
	var distance: int = cells * 5
	_target_label.text = "Цель: %s · %d клеток · %d футов · КД %d · здоровье %d" % [
		_target_name(_selected_target),
		cells,
		distance,
		int(_selected_target.call("get_armor_class")),
		int(_selected_target.call("get_current_health"))
	]


func _request_attack() -> void:
	if GameState.input_locked or _any_overlay_visible() or _attack_in_progress:
		return
	if _target_is_valid(_selected_target):
		_face_toward((_selected_target as Node2D).global_position)
		await super._request_attack()
		return
	var weapon: Dictionary = _class_data.get_equipped_weapon(GameState.player_character)
	if DistanceSystem.is_ranged_weapon(weapon):
		await _request_directional_ranged_attack(weapon)
	else:
		await _request_directional_melee_attack(weapon)


func _request_directional_melee_attack(weapon: Dictionary) -> void:
	var reach_feet: int = maxi(int(weapon.get("reach_ft", 5)), 5)
	var direction: Vector2 = _get_player_facing_direction()
	var target: Node = _find_directional_melee_target(weapon)
	if _target_is_valid(target):
		await _perform_directional_attack_on_target(target, weapon, "")
		return
	var endpoint: Vector2 = DirectionalTargetingSystem.endpoint_inside_rect(
		player.global_position,
		direction,
		DirectionalTargetingSystem.feet_to_pixels(reach_feet),
		FREE_AIM_BOUNDS
	)
	_set_combat_busy(true)
	player.play_attack_animation(endpoint)
	await get_tree().create_timer(0.24).timeout
	_set_combat_busy(false)
	show_combat_message("Удар выполнен по направлению взгляда, но никого не задел.", false)
	_sync_exploration_hud_visibility()


func _find_directional_melee_target(weapon: Dictionary) -> Node:
	var reach_feet: int = maxi(int(weapon.get("reach_ft", 5)), 5)
	var eligible_targets: Array[Node] = []
	for candidate: Node in _available_targets():
		if DistanceSystem.distance_feet(player.global_position, (candidate as Node2D).global_position) <= reach_feet:
			eligible_targets.append(candidate)
	return DirectionalTargetingSystem.find_first_target(
		player.global_position,
		_get_player_facing_direction(),
		eligible_targets,
		DirectionalTargetingSystem.feet_to_pixels(reach_feet) * 1.5
	)


func _request_directional_ranged_attack(weapon: Dictionary) -> void:
	var normal_range_feet: int = int(weapon.get("range_normal_ft", 0))
	var long_range_feet: int = int(weapon.get("range_long_ft", normal_range_feet))
	if normal_range_feet <= 0 or long_range_feet <= 0:
		show_combat_message("У оружия не задана дальность свободной атаки.", false)
		return
	var ammo_id: String = str(weapon.get("ammunition_id", ""))
	if not ammo_id.is_empty() and not GameState.has_item(ammo_id):
		show_combat_message("Нет подходящих боеприпасов.", false)
		return
	var direction: Vector2 = _get_player_facing_direction()
	var eligible_targets: Array[Node] = []
	for candidate: Node in _available_targets():
		if DistanceSystem.distance_feet(player.global_position, (candidate as Node2D).global_position) <= long_range_feet:
			eligible_targets.append(candidate)
	var maximum_pixels: float = DirectionalTargetingSystem.feet_to_pixels(long_range_feet)
	var target: Node = DirectionalTargetingSystem.find_first_target(
		player.global_position,
		direction,
		eligible_targets,
		maximum_pixels
	)
	if _target_is_valid(target):
		await _perform_directional_attack_on_target(target, weapon, ammo_id)
		return
	var endpoint: Vector2 = DirectionalTargetingSystem.endpoint_inside_rect(
		player.global_position,
		direction,
		DirectionalTargetingSystem.feet_to_pixels(normal_range_feet),
		FREE_AIM_BOUNDS
	)
	_set_combat_busy(true)
	if not ammo_id.is_empty():
		GameState.remove_item(ammo_id, 1, false)
	await _play_weapon_projectile(weapon, endpoint, true)
	_set_combat_busy(false)
	GameState.save_game()
	_update_status()
	show_combat_message("Снаряд выпущен по направлению взгляда, но никого не задел.", false)
	_sync_exploration_hud_visibility()


func _perform_directional_attack_on_target(target: Node, weapon: Dictionary, ammo_id: String) -> void:
	var target_position: Vector2 = (target as Node2D).global_position
	var distance: int = DistanceSystem.distance_feet(player.global_position, target_position)
	var context: Dictionary = {
		"target_name": _target_name(target),
		"distance_feet": distance,
		"disadvantage": _has_hostile_within_five_feet(),
		"no_ammunition": not ammo_id.is_empty() and not GameState.has_item(ammo_id)
	}
	var result: AttackResult = _combat_system.perform_basic_attack(
		GameState.player_character,
		int(target.call("get_armor_class")),
		weapon,
		-1,
		[],
		context
	)
	if result.out_of_range or result.no_ammunition:
		_attack_popup.show_result(result)
		_sync_exploration_hud_visibility()
		return
	_set_combat_busy(true)
	if not ammo_id.is_empty():
		GameState.remove_item(ammo_id, 1, false)
	if DistanceSystem.is_ranged_weapon(weapon):
		await _play_weapon_projectile(weapon, target_position, result.hit)
	else:
		player.play_attack_animation(target_position)
		await get_tree().create_timer(0.24).timeout
	if _target_is_valid(target):
		target.call("receive_player_attack", result, true)
	GameState.save_game()
	_update_status()
	_set_combat_busy(false)
	_sync_exploration_hud_visibility()


func _get_player_facing_direction() -> Vector2:
	if player.has_method("get_facing_direction"):
		var direction: Variant = player.call("get_facing_direction")
		if direction is Vector2:
			return DirectionalTargetingSystem.normalized_direction(direction as Vector2)
	return Vector2.RIGHT


func _face_toward(target_position: Vector2) -> void:
	if player.has_method("set_facing_direction"):
		player.call("set_facing_direction", target_position - player.global_position)
