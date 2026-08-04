extends "res://scripts/game/game_squad_tactical_plans_runtime.gd"

const THROWABLE_PROP_SYSTEM_SCRIPT: Script = preload("res://scripts/systems/throwable_prop_system.gd")
const THROWABLE_WORLD_PROP_SCRIPT: Script = preload("res://scripts/game/throwable_world_prop.gd")

const GUARD_POST_ENCOUNTER_ID: String = "vault_guard_post_01"
const GUARD_POST_ACTOR_IDS: Array[String] = ["caretaker", "service_guard", "training_marksman", "training_mage"]
const GUARD_POST_APPROACH_X: float = 610.0
const GUARD_POST_STEALTH_EXIT_X: float = 1170.0
const PROP_INTERACTION_DISTANCE_FEET: int = 5
const PICKUP_ACTION_PREFIX: String = "pickup_throwable_prop__"
const THROW_HELD_ACTION_ID: String = "throw_held_prop"
const PROP_REGISTRY_FLAG: String = "guard_post_prop_registry_v1"

const INITIAL_PROPS: Array[Dictionary] = [
	{"prop_id": "guard_post_mug_01", "prop_type_id": "ceramic_mug", "position": Vector2(650.0, 330.0)},
	{"prop_id": "guard_post_candlestick_01", "prop_type_id": "iron_candlestick", "position": Vector2(810.0, 515.0)},
	{"prop_id": "guard_post_stool_01", "prop_type_id": "wooden_stool", "position": Vector2(1080.0, 575.0)}
]

var _throwable_props: ThrowablePropSystem = THROWABLE_PROP_SYSTEM_SCRIPT.new() as ThrowablePropSystem
var _throwable_registry: Dictionary = {}
var _prop_nodes: Dictionary = {}
var _guard_post_check_accumulator: float = 0.0
var _guard_post_resolution_in_progress: bool = false


func _ready() -> void:
	super._ready()
	_restore_throwable_props()
	_evaluate_guard_post_state()


func _process(delta: float) -> void:
	super._process(delta)
	_guard_post_check_accumulator += delta
	if _guard_post_check_accumulator < 0.2:
		return
	_guard_post_check_accumulator = 0.0
	_evaluate_guard_post_state()


func return_to_menu() -> void:
	_store_throwable_registry(true)
	super.return_to_menu()


func _build_catalog_entries() -> Dictionary:
	var entries: Dictionary = super._build_catalog_entries()
	var held_record: Dictionary = _throwable_props.get_held_record(_throwable_registry)
	var nearest_prop: ThrowableWorldProp = _nearest_available_prop()
	if _turn_system.active:
		var bonus_entries: Array = entries.get("bonus", []) as Array
		if held_record.is_empty():
			if nearest_prop != null:
				bonus_entries.append(_entry(
					"%s%s" % [PICKUP_ACTION_PREFIX, nearest_prop.get_prop_id()],
					"ПОДНЯТЬ: %s" % nearest_prop.get_prop_label().to_upper(),
					_turn_system.is_player_turn(player) and _turn_system.bonus_action_available,
					"Поднять соседний предмет интерьера. В бою расходует дополнительное действие; в руках можно нести только один предмет.",
					"world"
				))
			else:
				bonus_entries.append(_entry(
					"pickup_throwable_unavailable",
					"НЕТ ПРЕДМЕТА РЯДОМ",
					false,
					"Подойдите вплотную к кружке, подсвечнику или табуретке.",
					"world"
				))
		entries["bonus"] = bonus_entries
	else:
		var exploration_actions: Array = entries.get("action", []) as Array
		if held_record.is_empty() and nearest_prop != null:
			exploration_actions.append(_entry(
				"%s%s" % [PICKUP_ACTION_PREFIX, nearest_prop.get_prop_id()],
				"ПОДНЯТЬ: %s" % nearest_prop.get_prop_label().to_upper(),
				true,
				"Поднять предмет интерьера. Вне боя действие не расходует боевой ресурс.",
				"world"
			))
		entries["action"] = exploration_actions

	if not held_record.is_empty():
		var definition: Dictionary = _throwable_props.get_definition(str(held_record.get("prop_type_id", "")))
		var action_entries: Array = entries.get("action", []) as Array
		var available: bool = not _turn_system.active or (
			_turn_system.is_player_turn(player) and _turn_system.action_available
		)
		action_entries.append(_entry(
			THROW_HELD_ACTION_ID,
			"МЕТНУТЬ: %s" % str(definition.get("label", "предмет")).to_upper(),
			available,
			"Метнуть предмет действием на расстояние до %d футов. При выбранной цели предмет летит к ней; без цели — по направлению взгляда. В месте падения возникает шум радиусом %d футов." % [
				int(definition.get("throw_range_feet", 20)),
				int(definition.get("noise_radius_feet", 45))
			],
			"attack"
		))
		entries["action"] = action_entries
	return entries


func _on_catalog_action_requested(action_id: String) -> void:
	if action_id.begins_with(PICKUP_ACTION_PREFIX):
		_pickup_throwable_prop(action_id.trim_prefix(PICKUP_ACTION_PREFIX))
		_refresh_action_catalog()
		return
	if action_id == THROW_HELD_ACTION_ID:
		await _throw_held_prop()
		_refresh_action_catalog()
		return
	super._on_catalog_action_requested(action_id)


func _encounter_id_for_actor(actor: Node) -> String:
	var actor_id: String = _actor_id(actor)
	if actor_id in GUARD_POST_ACTOR_IDS:
		return GUARD_POST_ENCOUNTER_ID
	return super._encounter_id_for_actor(actor)


func _resolve_active_combat_encounter_if_complete() -> void:
	if _active_combat_encounter_id != GUARD_POST_ENCOUNTER_ID:
		super._resolve_active_combat_encounter_if_complete()
		return
	if not _combat_should_end():
		return
	var actor_states: Dictionary = _guard_post_actor_states()
	var resolution_id: String = _guard_post_resolution_for_states(actor_states)
	if resolution_id.is_empty():
		return
	_resolve_guard_post(resolution_id, {
		"source_type": "combat",
		"source_id": "guard_post_runtime",
		"combat_round": _turn_system.round_number,
		"actor_states": actor_states
	})


func get_guard_post_encounter_id_for_testing() -> String:
	return GUARD_POST_ENCOUNTER_ID


func get_throwable_registry_for_testing() -> Dictionary:
	return _throwable_registry.duplicate(true)


func get_held_throwable_prop_id_for_testing() -> String:
	return str(_throwable_registry.get("held_prop_id", ""))


func get_throwable_prop_node_for_testing(prop_id: String) -> ThrowableWorldProp:
	var value: Variant = _prop_nodes.get(prop_id, null)
	return value as ThrowableWorldProp if value is ThrowableWorldProp and is_instance_valid(value as ThrowableWorldProp) else null


func get_guard_post_actor_states_for_testing() -> Dictionary:
	return _guard_post_actor_states()


func get_guard_post_resolution_for_states_for_testing(actor_states: Dictionary) -> String:
	return _guard_post_resolution_for_states(actor_states)


func resolve_throw_landing_for_testing(origin: Vector2, intended: Vector2) -> Vector2:
	return _resolve_throw_landing(origin, intended)


func _restore_throwable_props() -> void:
	var stored: Variant = GameState.get_flag(PROP_REGISTRY_FLAG, {})
	_throwable_registry = _throwable_props.normalize_registry(stored, INITIAL_PROPS)
	_store_throwable_registry(false)
	var props: Dictionary = _throwable_registry.get("props", {}) as Dictionary
	for initial: Dictionary in INITIAL_PROPS:
		var prop_id: String = str(initial.get("prop_id", ""))
		var record_value: Variant = props.get(prop_id, {})
		if not record_value is Dictionary:
			continue
		var record: Dictionary = record_value as Dictionary
		var prop_type_id: String = str(record.get("prop_type_id", ""))
		var definition: Dictionary = _throwable_props.get_definition(prop_type_id)
		if definition.is_empty():
			continue
		var prop := THROWABLE_WORLD_PROP_SCRIPT.new() as ThrowableWorldProp
		prop.name = prop_id.to_pascal_case()
		prop.configure(prop_id, prop_type_id, definition)
		add_child(prop)
		prop.global_position = _throwable_props.vector_from_value(record.get("position", []))
		prop.set_available(str(record.get("state", "")) == ThrowablePropSystem.STATE_WORLD)
		_prop_nodes[prop_id] = prop


func _pickup_throwable_prop(prop_id: String) -> void:
	var prop: ThrowableWorldProp = get_throwable_prop_node_for_testing(prop_id)
	if prop == null or not prop.is_available_for_pickup():
		show_combat_message("Предмет уже недоступен.", false)
		return
	if DistanceSystem.distance_feet(player.global_position, prop.global_position) > PROP_INTERACTION_DISTANCE_FEET:
		show_combat_message("Чтобы поднять предмет, нужно стоять рядом с ним.", false)
		return
	if _turn_system.active:
		if not _turn_system.is_player_turn(player):
			show_combat_message("Поднять предмет можно только на своём ходу.", false)
			return
		if not _turn_system.consume_bonus_action():
			show_combat_message("Дополнительное действие на этом ходу уже использовано.", false)
			return
	var result: Dictionary = _throwable_props.pickup(_throwable_registry, prop_id)
	if not bool(result.get("success", false)):
		show_combat_message(str(result.get("message", "Не удалось поднять предмет.")), false)
		return
	_throwable_registry = result.get("registry", {}) as Dictionary
	prop.set_available(false)
	_store_throwable_registry(true)
	show_combat_message("Поднято: %s. Предмет можно метнуть действием." % prop.get_prop_label(), true)
	_update_status()


func _throw_held_prop() -> void:
	var held_record: Dictionary = _throwable_props.get_held_record(_throwable_registry)
	if held_record.is_empty():
		show_combat_message("В руках нет метаемого предмета.", false)
		return
	var definition: Dictionary = _throwable_props.get_definition(str(held_record.get("prop_type_id", "")))
	var prop_id: String = str(held_record.get("prop_id", ""))
	var prop: ThrowableWorldProp = get_throwable_prop_node_for_testing(prop_id)
	if prop == null:
		show_combat_message("Переносимый предмет не найден в сцене.", false)
		return
	if _turn_system.active:
		if not _turn_system.is_player_turn(player):
			show_combat_message("Метать предмет можно только на своём ходу.", false)
			return
		if not _turn_system.consume_action():
			show_combat_message("Действие на этом ходу уже использовано.", false)
			return
	var range_feet: int = maxi(int(definition.get("throw_range_feet", 20)), 5)
	var intended: Vector2 = _throw_intended_position(range_feet)
	var landing: Vector2 = _resolve_throw_landing(player.global_position, intended)
	var result: Dictionary = _throwable_props.throw_held(_throwable_registry, landing)
	if not bool(result.get("success", false)):
		show_combat_message(str(result.get("message", "Бросок не удался.")), false)
		return

	# Commit gameplay state before cosmetic flight. An interrupted tween must not leave hands occupied.
	_throwable_registry = result.get("registry", {}) as Dictionary
	_store_throwable_registry(true)
	_set_combat_busy(true)
	await prop.play_throw(player.global_position, landing)

	var noise_radius: int = maxi(int(definition.get("noise_radius_feet", 45)), 5)
	var noise_intensity: int = maxi(int(definition.get("noise_intensity", 40)), 1)
	GameState.report_stealth_noise("thrown_object", landing, {
		"radius_feet": noise_radius,
		"intensity": noise_intensity,
		"source_prop_id": prop_id,
		"source_label": str(definition.get("label", "предмет"))
	}, true, true)
	if bool(result.get("broken", false)):
		prop.mark_broken()
		_prop_nodes.erase(prop_id)
	else:
		prop.global_position = landing
		prop.set_available(true)
	_set_combat_busy(false)
	show_combat_message("%s приземляется и создаёт шум радиусом %d футов." % [str(definition.get("label", "Предмет")).capitalize(), noise_radius], true)
	_update_status()
	_after_player_action()


func _throw_intended_position(range_feet: int) -> Vector2:
	if _target_is_valid(_selected_target) and _selected_target is Node2D:
		var target_position: Vector2 = (_selected_target as Node2D).global_position
		var direction_to_target: Vector2 = target_position - player.global_position
		var maximum_pixels: float = DistanceSystem.feet_to_pixels(range_feet)
		if direction_to_target.length() > maximum_pixels:
			return player.global_position + direction_to_target.normalized() * maximum_pixels
		return target_position
	var facing := Vector2.RIGHT
	if player.has_method("get_facing_direction"):
		var facing_value: Variant = player.call("get_facing_direction")
		if facing_value is Vector2 and (facing_value as Vector2).length_squared() > 0.0001:
			facing = (facing_value as Vector2).normalized()
	else:
		var last_direction: Variant = player.get("last_direction")
		if last_direction is Vector2 and (last_direction as Vector2).length_squared() > 0.0001:
			facing = (last_direction as Vector2).normalized()
	return player.global_position + facing * DistanceSystem.feet_to_pixels(range_feet)


func _resolve_throw_landing(origin: Vector2, intended: Vector2) -> Vector2:
	var grid: BattleGrid = _get_battle_grid()
	if grid == null:
		return intended
	var current: Vector2i = grid.world_to_cell(origin)
	var target: Vector2i = grid.world_to_cell(intended)
	if not grid.is_cell_valid(current):
		return origin
	if not grid.is_cell_valid(target):
		var field: Rect2 = grid.get_field_rect()
		var cell_size: float = grid.get_cell_size()
		var columns: int = maxi(floori(field.size.x / cell_size), 1)
		var rows: int = maxi(floori(field.size.y / cell_size), 1)
		target = Vector2i(
			clampi(target.x, 0, columns - 1),
			clampi(target.y, 0, rows - 1)
		)
	for _step: int in range(64):
		if current == target:
			break
		var remaining: Vector2i = target - current
		var next: Vector2i = current
		if absi(remaining.x) >= absi(remaining.y) and remaining.x != 0:
			next.x += signi(remaining.x)
		elif remaining.y != 0:
			next.y += signi(remaining.y)
		if not grid.is_cell_valid(next):
			break
		if _combat_environment != null and _combat_environment.is_transition_blocked(grid, current, next):
			break
		current = next
	return grid.cell_to_world_center(current)


func _nearest_available_prop() -> ThrowableWorldProp:
	var nearest: ThrowableWorldProp = null
	var nearest_distance: int = 999999
	for value: Variant in _prop_nodes.values():
		if not value is ThrowableWorldProp or not is_instance_valid(value as ThrowableWorldProp):
			continue
		var prop: ThrowableWorldProp = value as ThrowableWorldProp
		if not prop.is_available_for_pickup():
			continue
		var distance: int = DistanceSystem.distance_feet(player.global_position, prop.global_position)
		if distance <= PROP_INTERACTION_DISTANCE_FEET and distance < nearest_distance:
			nearest = prop
			nearest_distance = distance
	return nearest


func _store_throwable_registry(save_after: bool) -> void:
	GameState.set_flag(PROP_REGISTRY_FLAG, _throwable_registry.duplicate(true))
	if save_after:
		GameState.save_game()


func _evaluate_guard_post_state() -> void:
	if _guard_post_resolution_in_progress or not GameState.has_method("get_encounter_status"):
		return
	var status: String = str(GameState.get_encounter_status(GUARD_POST_ENCOUNTER_ID))
	if status in [EncounterSystem.STATUS_RESOLVED, EncounterSystem.STATUS_REWARDED]:
		return
	if status == EncounterSystem.STATUS_AVAILABLE and player.global_position.x >= GUARD_POST_APPROACH_X:
		GameState.begin_encounter(GUARD_POST_ENCOUNTER_ID, {
			"source_type": "exploration",
			"source_id": "guard_post_approach"
		}, true, true)
		status = str(GameState.get_encounter_status(GUARD_POST_ENCOUNTER_ID))
	if status != EncounterSystem.STATUS_ACTIVE:
		return
	if not _turn_system.active and bool(GameState.get_flag("caretaker_convinced", false)):
		_resolve_guard_post("peaceful_passage", {"source_type": "dialogue", "source_id": "caretaker_convinced"})
		return
	if not _turn_system.active and player.global_position.x >= GUARD_POST_STEALTH_EXIT_X and _guard_post_all_observers_calm():
		_resolve_guard_post("stealth_bypass", {"source_type": "stealth", "source_id": "east_exit"})
		return
	var actor_states: Dictionary = _guard_post_actor_states()
	var resolution_id: String = _guard_post_resolution_for_states(actor_states)
	if not resolution_id.is_empty():
		_resolve_guard_post(resolution_id, {
			"source_type": "combat",
			"combat_round": _turn_system.round_number,
			"actor_states": actor_states
		})


func _guard_post_resolution_for_states(actor_states: Dictionary) -> String:
	if actor_states.size() != GUARD_POST_ACTOR_IDS.size():
		return ""
	var dead_count: int = 0
	var unconscious_count: int = 0
	for actor_id: String in GUARD_POST_ACTOR_IDS:
		var actor_state: String = str(actor_states.get(actor_id, "missing"))
		if actor_state not in ["dead", "unconscious"]:
			return ""
		dead_count += 1 if actor_state == "dead" else 0
		unconscious_count += 1 if actor_state == "unconscious" else 0
	if unconscious_count == GUARD_POST_ACTOR_IDS.size():
		return "guards_subdued"
	if dead_count == GUARD_POST_ACTOR_IDS.size():
		return "guards_defeated"
	return "mixed_neutralization"


func _resolve_guard_post(resolution_id: String, context: Dictionary) -> void:
	if _guard_post_resolution_in_progress:
		return
	_guard_post_resolution_in_progress = true
	var result: Dictionary = GameState.resolve_encounter(GUARD_POST_ENCOUNTER_ID, resolution_id, context, true, true)
	if bool(result.get("success", false)):
		show_combat_message(str(result.get("message", "Караульный пост пройден.")), true)
		if _active_combat_encounter_id == GUARD_POST_ENCOUNTER_ID:
			_active_combat_encounter_id = ""
	_guard_post_resolution_in_progress = false


func _guard_post_actor_states() -> Dictionary:
	var result: Dictionary = {}
	for actor_id: String in GUARD_POST_ACTOR_IDS:
		result[actor_id] = _guard_post_actor_state(actor_id)
	return result


func _guard_post_actor_state(actor_id: String) -> String:
	for node: Node in _guard_post_candidate_nodes():
		if not is_instance_valid(node):
			continue
		var node_actor_id: String = _actor_id(node)
		if node_actor_id.is_empty() and node.has_method("get_body_actor_id"):
			node_actor_id = str(node.call("get_body_actor_id"))
		if node_actor_id != actor_id:
			continue
		if node.has_method("is_dead_body") and bool(node.call("is_dead_body")):
			return "dead"
		if node.has_method("is_unconscious_body") and bool(node.call("is_unconscious_body")):
			return "unconscious"
		if node.has_method("get_current_health") and int(node.call("get_current_health")) <= 0:
			return "dead"
		return "active"
	return "missing"


func _guard_post_candidate_nodes() -> Array[Node]:
	var result: Array[Node] = []
	var caretaker: Node = get_node_or_null("Caretaker")
	if caretaker != null:
		result.append(caretaker)
	var room: Node = get_node_or_null("StealthTestRoom")
	if room != null:
		for method_name: String in ["get_patrol_observer", "get_training_marksman", "get_training_mage"]:
			if room.has_method(method_name):
				var value: Variant = room.call(method_name)
				if value is Node:
					result.append(value as Node)
	for body: Node in get_tree().get_nodes_in_group("visible_bodies"):
		if body not in result:
			result.append(body)
	return result


func _guard_post_all_observers_calm() -> bool:
	for actor_id: String in GUARD_POST_ACTOR_IDS:
		var record: Dictionary = GameState.get_stealth_alert_record(actor_id)
		if str(record.get("state", StealthAlertSystem.STATE_CALM)) != StealthAlertSystem.STATE_CALM:
			return false
	return true


func _actor_id(actor: Node) -> String:
	if actor == null or not is_instance_valid(actor):
		return ""
	if actor.has_method("get_actor_id"):
		return str(actor.call("get_actor_id"))
	if actor.has_method("get_body_actor_id"):
		return str(actor.call("get_body_actor_id"))
	return ""
