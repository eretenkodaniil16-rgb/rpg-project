extends "res://scripts/game/game_guard_post_stable_combat_start_runtime.gd"

const LOOT_MANAGER_SCRIPT: Script = preload("res://scripts/game/world_loot_container_manager.gd")
const LOOT_PANEL_SCRIPT: Script = preload("res://scripts/ui/loot_container_panel.gd")
const OPEN_CONTAINER_PREFIX: String = "open_loot_container:"
const OPEN_BODY_LOOT_ACTION: String = "open_selected_body_loot"
const WORLD_CONTAINER_DISTANCE_FEET: int = 10

var _loot_container_manager: WorldLootContainerManager = null
var _loot_container_panel: LootContainerPanel = null
var _active_loot_kind: String = ""
var _active_loot_source_id: String = ""
var _active_loot_body: Node = null
var _loot_previous_input_locked: bool = false


func _ready() -> void:
	super._ready()
	_ensure_loot_runtime()


func _any_overlay_visible() -> bool:
	return super._any_overlay_visible() or (
		_loot_container_panel != null
		and _loot_container_panel.is_open()
	)


func _build_catalog_entries() -> Dictionary:
	var entries: Dictionary = super._build_catalog_entries()
	_append_world_container_entries(entries)
	_replace_body_loot_entries(entries)
	return entries


func _on_feedback_catalog_action_requested(action_id: String) -> void:
	if action_id.begins_with(OPEN_CONTAINER_PREFIX):
		request_open_loot_container(action_id.trim_prefix(OPEN_CONTAINER_PREFIX))
		_refresh_action_catalog()
		return
	if action_id == OPEN_BODY_LOOT_ACTION:
		_open_selected_body_loot()
		_refresh_action_catalog()
		return
	super._on_feedback_catalog_action_requested(action_id)


func request_open_loot_container(container_id: String) -> void:
	_ensure_loot_runtime()
	if _loot_container_manager == null or container_id.is_empty():
		return
	var container: WorldLootContainer = _loot_container_manager.get_container_node(container_id)
	if container == null or not _world_container_is_reachable(container):
		show_combat_message("Для открытия контейнера нужно приблизиться.", false)
		return
	if not _loot_interaction_turn_is_valid():
		return
	var result: Dictionary = _loot_container_manager.open_container(container_id, true)
	if not bool(result.get("success", false)):
		show_combat_message(str(result.get("message", "Контейнер не удалось открыть.")), false)
		return
	_open_loot_panel("world", container_id, result.get("record", {}) as Dictionary, null)


func _open_selected_body_loot() -> void:
	if not _is_body_target(_selected_target) or not bool(_selected_target.call("is_dead_body")):
		show_combat_message("Выбранная цель не является доступным мёртвым телом.", false)
		return
	if not _loot_interaction_turn_is_valid():
		return
	var body: Node = _selected_target
	var distance: int = DistanceSystem.distance_feet(player.global_position, (body as Node2D).global_position)
	if distance > 10:
		show_combat_message("Для обыска нужно приблизиться к телу.", false)
		return
	var actor_id: String = str(body.call("get_body_actor_id")) if body.has_method("get_body_actor_id") else str(body.get_instance_id())
	var record: Dictionary = {
		"container_id": "body:%s" % actor_id,
		"container_type": "corpse",
		"label": "Тело: %s" % _target_name(body),
		"is_open": true,
		"is_locked": false,
		"items": body.call("get_remaining_corpse_loot") as Array[Dictionary] if body.has_method("get_remaining_corpse_loot") else []
	}
	_open_loot_panel("body", actor_id, record, body)


func _open_loot_panel(kind: String, source_id: String, record: Dictionary, body: Node) -> void:
	_ensure_loot_runtime()
	if _loot_container_panel == null:
		return
	_close_action_catalog_immediately()
	_active_loot_kind = kind
	_active_loot_source_id = source_id
	_active_loot_body = body
	_loot_previous_input_locked = GameState.input_locked
	GameState.input_locked = true
	_loot_container_panel.open_source(source_id, record, _definitions_for_record(record))
	_loot_container_panel.set_take_all_enabled(not _turn_system.active)


func _on_loot_item_requested(_source_id: String, item_id: String) -> void:
	if item_id.is_empty() or _loot_container_panel == null or not _loot_container_panel.is_open():
		return
	if _turn_system.active and not _combat_loot_bonus_action_available():
		show_combat_message("В бою подбор требует свободного дополнительного действия.", false)
		return
	var result: Dictionary
	if _active_loot_kind == "world":
		result = _loot_container_manager.take_item(_active_loot_source_id, item_id, 9999, true)
	elif _active_loot_kind == "body" and is_instance_valid(_active_loot_body) and _active_loot_body.has_method("take_corpse_item"):
		result = _active_loot_body.call("take_corpse_item", item_id, 9999) as Dictionary
	else:
		result = {"success": false, "message": "Источник добычи больше недоступен."}
	if not bool(result.get("success", false)):
		show_combat_message(str(result.get("message", "Предмет не удалось подобрать.")), false)
		return
	if _turn_system.active:
		_turn_system.consume_bonus_action()
	var definition: Dictionary = GameState.get_item_definition(item_id)
	show_combat_message("Подобрано: %s ×%d." % [
		str(definition.get("name", "предмет")),
		maxi(int(result.get("quantity", 1)), 1)
	], true)
	_refresh_open_loot_panel()
	_update_status()
	_refresh_turn_interface()
	if _turn_system.active:
		_close_loot_panel()


func _on_loot_take_all_requested(_source_id: String) -> void:
	if _turn_system.active:
		show_combat_message("Во время боя предметы подбираются по одному дополнительным действием.", false)
		return
	var result: Dictionary
	if _active_loot_kind == "world":
		result = _loot_container_manager.take_all(_active_loot_source_id, true)
	elif _active_loot_kind == "body" and is_instance_valid(_active_loot_body) and _active_loot_body.has_method("take_all_corpse_loot"):
		result = _active_loot_body.call("take_all_corpse_loot") as Dictionary
	else:
		result = {"success": false, "transferred": [], "failures": ["Источник добычи больше недоступен."]}
	var transferred: Array = result.get("transferred", []) as Array
	if transferred.is_empty():
		var failures: Array = result.get("failures", []) as Array
		show_combat_message(str(failures[0]) if not failures.is_empty() else "Подходящих предметов нет.", false)
		return
	var total: int = 0
	for value: Variant in transferred:
		if value is Dictionary:
			total += maxi(int((value as Dictionary).get("quantity", 0)), 0)
	show_combat_message("Подобрано предметов: %d." % total, true)
	_refresh_open_loot_panel()
	_update_status()


func _refresh_open_loot_panel() -> void:
	if _loot_container_panel == null or not _loot_container_panel.is_open():
		return
	var record: Dictionary = _active_loot_record()
	_loot_container_panel.refresh_source(record, _definitions_for_record(record))
	_loot_container_panel.set_take_all_enabled(not _turn_system.active)


func _active_loot_record() -> Dictionary:
	if _active_loot_kind == "world" and _loot_container_manager != null:
		return _loot_container_manager.get_record(_active_loot_source_id)
	if _active_loot_kind == "body" and is_instance_valid(_active_loot_body):
		return {
			"container_id": "body:%s" % _active_loot_source_id,
			"container_type": "corpse",
			"label": "Тело: %s" % _target_name(_active_loot_body),
			"is_open": true,
			"is_locked": false,
			"items": _active_loot_body.call("get_remaining_corpse_loot") as Array[Dictionary] if _active_loot_body.has_method("get_remaining_corpse_loot") else []
		}
	return {}


func _on_loot_panel_close_requested() -> void:
	_close_loot_panel(false)


func _close_loot_panel(hide_panel: bool = true) -> void:
	if _loot_container_panel != null and hide_panel and _loot_container_panel.is_open():
		_loot_container_panel.visible = false
	GameState.input_locked = _loot_previous_input_locked
	_active_loot_kind = ""
	_active_loot_source_id = ""
	_active_loot_body = null
	_refresh_action_catalog()


func _append_world_container_entries(entries: Dictionary) -> void:
	_ensure_loot_runtime()
	if _loot_container_manager == null:
		return
	var category_id: String = "bonus" if _turn_system.active else "action"
	var values: Array = entries.get(category_id, []) as Array
	for container: WorldLootContainer in _nearby_world_containers():
		var record: Dictionary = container.get_container_record()
		var enabled: bool = not bool(record.get("is_locked", false))
		if _turn_system.active:
			enabled = enabled and _combat_loot_bonus_action_available()
		values.append(_entry(
			"%s%s" % [OPEN_CONTAINER_PREFIX, container.get_container_id()],
			container.get_interaction_label(),
			enabled,
			container.get_interaction_description() + (
				" В бою один подобранный стек расходует дополнительное действие." if _turn_system.active else ""
			),
			"world"
		))
	entries[category_id] = values


func _replace_body_loot_entries(entries: Dictionary) -> void:
	if not _is_body_target(_selected_target) or not bool(_selected_target.call("is_dead_body")):
		return
	var category_id: String = "bonus" if _turn_system.active else "action"
	var original: Array = entries.get(category_id, []) as Array
	var filtered: Array = []
	for value: Variant in original:
		if not value is Dictionary:
			continue
		var entry: Dictionary = value as Dictionary
		var action_id: String = str(entry.get("id", ""))
		if action_id.begins_with("corpse_loot_item__") or action_id == "corpse_loot_all":
			continue
		filtered.append(entry)
	var reachable: bool = DistanceSystem.distance_feet(
		player.global_position,
		(_selected_target as Node2D).global_position
	) <= 10
	var enabled: bool = reachable and (not _turn_system.active or _combat_loot_bonus_action_available())
	filtered.append(_entry(
		OPEN_BODY_LOOT_ACTION,
		"ОБЫСКАТЬ: %s" % _target_name(_selected_target).to_upper(),
		enabled,
		"Открыть общую панель добычи тела.%s" % (
			" В бою один подобранный стек расходует дополнительное действие." if _turn_system.active else ""
		),
		"world"
	))
	entries[category_id] = filtered


func _nearby_world_containers() -> Array[WorldLootContainer]:
	var result: Array[WorldLootContainer] = []
	if player == null or not player.has_method("get_nearby_interactables"):
		return result
	var value: Variant = player.call("get_nearby_interactables")
	if not value is Array:
		return result
	for candidate: Variant in value as Array:
		if candidate is WorldLootContainer and is_instance_valid(candidate as WorldLootContainer):
			var container: WorldLootContainer = candidate as WorldLootContainer
			if container.is_available_for_interaction():
				result.append(container)
	return result


func _world_container_is_reachable(container: WorldLootContainer) -> bool:
	return (
		container != null
		and player != null
		and DistanceSystem.distance_feet(player.global_position, container.global_position) <= WORLD_CONTAINER_DISTANCE_FEET
	)


func _loot_interaction_turn_is_valid() -> bool:
	if not _turn_system.active:
		return not GameState.input_locked
	if not _turn_system.is_player_turn(player) or _enemy_turn_running:
		show_combat_message("Обыскивать можно только на своём ходу.", false)
		return false
	return true


func _combat_loot_bonus_action_available() -> bool:
	return (
		_turn_system.active
		and _turn_system.is_player_turn(player)
		and not _enemy_turn_running
		and _turn_system.bonus_action_available
	)


func _definitions_for_record(record: Dictionary) -> Dictionary:
	var definitions: Dictionary = {}
	var items_value: Variant = record.get("items", [])
	if not items_value is Array:
		return definitions
	for value: Variant in items_value as Array:
		if not value is Dictionary:
			continue
		var item_id: String = str((value as Dictionary).get("item_id", ""))
		if item_id.is_empty():
			continue
		definitions[item_id] = GameState.get_item_definition(item_id)
	return definitions


func _ensure_loot_runtime() -> void:
	if _loot_container_manager == null or not is_instance_valid(_loot_container_manager):
		_loot_container_manager = get_node_or_null("WorldLootContainerManager") as WorldLootContainerManager
		if _loot_container_manager == null:
			_loot_container_manager = LOOT_MANAGER_SCRIPT.new() as WorldLootContainerManager
			_loot_container_manager.name = "WorldLootContainerManager"
			add_child(_loot_container_manager)
	if _loot_container_panel == null or not is_instance_valid(_loot_container_panel):
		_loot_container_panel = get_node_or_null("Interface/LootContainerPanel") as LootContainerPanel
		if _loot_container_panel == null:
			_loot_container_panel = LOOT_PANEL_SCRIPT.new() as LootContainerPanel
			_loot_container_panel.name = "LootContainerPanel"
			$Interface.add_child(_loot_container_panel)
		_loot_container_panel.take_item_requested.connect(_on_loot_item_requested)
		_loot_container_panel.take_all_requested.connect(_on_loot_take_all_requested)
		_loot_container_panel.close_requested.connect(_on_loot_panel_close_requested)


func get_loot_container_manager_for_testing() -> WorldLootContainerManager:
	_ensure_loot_runtime()
	return _loot_container_manager


func get_loot_container_panel_for_testing() -> LootContainerPanel:
	_ensure_loot_runtime()
	return _loot_container_panel


func open_loot_container_for_testing(container_id: String) -> void:
	request_open_loot_container(container_id)


func take_active_loot_item_for_testing(item_id: String) -> void:
	_on_loot_item_requested(_active_loot_source_id, item_id)


func take_all_active_loot_for_testing() -> void:
	_on_loot_take_all_requested(_active_loot_source_id)
