extends "res://scripts/game/game_movement_reactions_runtime.gd"

const CORPSE_INTERACTION_DISTANCE_FEET: int = 10
const BODY_DRAG_SPEED_MULTIPLIER: float = 0.58
const LOOT_ACTION_PREFIX: String = "corpse_loot_item__"

var _dragged_body: Node2D


func _process(delta: float) -> void:
	super._process(delta)
	if _turn_system.active and is_instance_valid(_dragged_body):
		_stop_dragged_body(true, "Перетаскивание прекращено с началом боя.")
	elif is_instance_valid(_dragged_body) and (not _dragged_body.has_method("is_body_interactable") or not bool(_dragged_body.call("is_body_interactable"))):
		_dragged_body = null


func return_to_menu() -> void:
	_stop_dragged_body(true, "")
	super.return_to_menu()


func get_body_drag_speed_multiplier() -> float:
	return BODY_DRAG_SPEED_MULTIPLIER if is_instance_valid(_dragged_body) else 1.0


func get_dragged_body_for_testing() -> Node2D:
	return _dragged_body


func _target_is_valid(target: Node) -> bool:
	if _is_body_target(target):
		return true
	return super._target_is_valid(target)


func _context_targets() -> Array[Node]:
	var result: Array[Node] = super._context_targets()
	var seen_ids: Dictionary = {}
	for target: Node in result:
		if is_instance_valid(target):
			seen_ids[target.get_instance_id()] = true
	for body: Node in get_tree().get_nodes_in_group("corpse_targets"):
		if not _is_body_target(body) or seen_ids.has(body.get_instance_id()):
			continue
		result.append(body)
		seen_ids[body.get_instance_id()] = true
	result.sort_custom(func(left: Node, right: Node) -> bool:
		return player.global_position.distance_squared_to((left as Node2D).global_position) < player.global_position.distance_squared_to((right as Node2D).global_position)
	)
	return result


func _build_catalog_entries() -> Dictionary:
	var entries: Dictionary = super._build_catalog_entries()
	if not _is_body_target(_selected_target):
		if not _turn_system.active and is_instance_valid(_dragged_body):
			var actions: Array = entries.get("action", []) as Array
			actions.append(_entry(
				"corpse_release_dragged_body",
				"ОТПУСТИТЬ ТЕЛО",
				true,
				"Прекратить перетаскивание и сохранить текущее положение тела.",
				"world"
			))
			entries["action"] = actions
		return entries

	var body: Node2D = _selected_target as Node2D
	var near_body: bool = DistanceSystem.distance_feet(player.global_position, body.global_position) <= CORPSE_INTERACTION_DISTANCE_FEET
	var dead_body: bool = bool(body.call("is_dead_body")) if body.has_method("is_dead_body") else false
	var loot: Array[Dictionary] = body.call("get_remaining_corpse_loot") as Array[Dictionary] if body.has_method("get_remaining_corpse_loot") else []
	var action_entries: Array[Dictionary] = [
		_entry("inspect_target", "ОСМОТРЕТЬ ТЕЛО", true, "Определить, мёртв ли NPC, и оценить оставшиеся предметы без раскрытия скрытых чисел.", "target")
	]
	if dead_body:
		for loot_entry: Dictionary in loot:
			var item_id: String = str(loot_entry.get("item_id", ""))
			var quantity: int = maxi(int(loot_entry.get("quantity", 0)), 0)
			if item_id.is_empty() or quantity <= 0:
				continue
			var item: Dictionary = GameState.get_item_definition(item_id)
			var item_name: String = str(item.get("name", item_id))
			action_entries.append(_entry(
				"%s%s" % [LOOT_ACTION_PREFIX, item_id],
				"СНЯТЬ: %s ×%d" % [item_name, quantity],
				near_body,
				"Перенести предмет с тела в существующий инвентарь. Требуется находиться не дальше %d футов." % CORPSE_INTERACTION_DISTANCE_FEET,
				"world"
			))
		action_entries.append(_entry(
			"corpse_loot_all",
			"ЗАБРАТЬ ВСЁ",
			near_body and not loot.is_empty(),
			"Забрать все предметы, для которых есть место в инвентаре. Непоместившиеся предметы останутся на теле.",
			"world"
		))
	else:
		action_entries.append(_entry(
			"corpse_loot_all",
			"СНЯТЬ ПРЕДМЕТЫ",
			false,
			"NPC без сознания, но жив. Снимать с него предметы сейчас нельзя.",
			"world"
		))
	var dragging_selected: bool = is_instance_valid(_dragged_body) and _dragged_body == body
	action_entries.append(_entry(
		"corpse_drag_toggle",
		"ОТПУСТИТЬ ТЕЛО" if dragging_selected else "ТАЩИТЬ ТЕЛО",
		near_body and not _turn_system.active,
		"Перетаскивание снижает скорость исследования и недоступно во время пошагового боя.",
		"world"
	))
	action_entries.append(_entry("clear_target", "СНЯТЬ ВЫБОР", true, "Отменить выбор тела.", "target"))
	entries["action"] = action_entries
	return entries


func _on_catalog_action_requested(action_id: String) -> void:
	if action_id.begins_with(LOOT_ACTION_PREFIX):
		_take_selected_body_item(action_id.trim_prefix(LOOT_ACTION_PREFIX))
	elif action_id == "corpse_loot_all":
		_take_all_from_selected_body()
	elif action_id == "corpse_drag_toggle":
		_toggle_selected_body_drag()
	elif action_id == "corpse_release_dragged_body":
		_stop_dragged_body(true, "Тело отпущено.")
	else:
		super._on_catalog_action_requested(action_id)
	_refresh_action_catalog()


func _take_selected_body_item(item_id: String) -> void:
	if not _selected_body_is_reachable() or not _selected_target.has_method("take_corpse_item"):
		show_combat_message("Для снятия предмета нужно приблизиться к телу.", false)
		return
	var result: Dictionary = _selected_target.call("take_corpse_item", item_id, 9999) as Dictionary
	if not bool(result.get("success", false)):
		show_combat_message(str(result.get("message", "Предмет не удалось снять.")), false)
		return
	var item: Dictionary = GameState.get_item_definition(item_id)
	show_combat_message("Получено: %s ×%d." % [str(item.get("name", item_id)), int(result.get("quantity", 0))], true)
	_update_status()


func _take_all_from_selected_body() -> void:
	if not _selected_body_is_reachable() or not _selected_target.has_method("take_all_corpse_loot"):
		show_combat_message("Для обыска нужно приблизиться к телу.", false)
		return
	var result: Dictionary = _selected_target.call("take_all_corpse_loot") as Dictionary
	var transferred: Array = result.get("transferred", []) as Array
	if transferred.is_empty():
		var failures: Array = result.get("failures", []) as Array
		show_combat_message(str(failures[0]) if not failures.is_empty() else "На теле нет доступной добычи.", false)
		return
	var total: int = 0
	for entry_value: Variant in transferred:
		if entry_value is Dictionary:
			total += maxi(int((entry_value as Dictionary).get("quantity", 0)), 0)
	show_combat_message("Обыск завершён. Перенесено предметов: %d." % total, true)
	_update_status()


func _toggle_selected_body_drag() -> void:
	if not _selected_body_is_reachable() or _turn_system.active:
		show_combat_message("Тело можно начать тащить только рядом и вне боя.", false)
		return
	var body: Node2D = _selected_target as Node2D
	if is_instance_valid(_dragged_body) and _dragged_body == body:
		_stop_dragged_body(true, "Тело отпущено.")
		return
	_stop_dragged_body(true, "")
	if not body.has_method("begin_body_drag") or not bool(body.call("begin_body_drag", player)):
		show_combat_message("Это тело нельзя переместить.", false)
		return
	_dragged_body = body
	show_combat_message("Вы тащите тело. Скорость передвижения снижена.", true)


func _stop_dragged_body(save_position: bool, message: String) -> void:
	if is_instance_valid(_dragged_body) and _dragged_body.has_method("stop_body_drag"):
		_dragged_body.call("stop_body_drag", save_position)
	_dragged_body = null
	if not message.is_empty():
		show_combat_message(message, true)


func _selected_body_is_reachable() -> bool:
	return _is_body_target(_selected_target) and DistanceSystem.distance_feet(player.global_position, (_selected_target as Node2D).global_position) <= CORPSE_INTERACTION_DISTANCE_FEET


func _is_body_target(target: Node) -> bool:
	return is_instance_valid(target) and target is Node2D and target.has_method("is_body_interactable") and bool(target.call("is_body_interactable"))