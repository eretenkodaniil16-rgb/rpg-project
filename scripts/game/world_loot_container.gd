class_name WorldLootContainer
extends Node2D

const INTERACTION_ZONE_SIZE: Vector2 = Vector2(128.0, 128.0)

var container_id: String = ""
var record: Dictionary = {}
var _manager: Node = null
var _interaction_area: Area2D = null
var _registered_players: Dictionary = {}
var _body: Polygon2D = null
var _lid: Polygon2D = null
var _label: Label = null


func configure(manager: Node, new_record: Dictionary) -> void:
	_manager = manager
	apply_record(new_record)


func apply_record(new_record: Dictionary) -> void:
	record = new_record.duplicate(true)
	container_id = str(record.get("container_id", ""))
	visible = bool(record.get("is_discovered", true))
	if is_inside_tree():
		_rebuild_visuals()
		_refresh_interaction_state()


func _ready() -> void:
	add_to_group("loot_containers")
	_build_interaction_area()
	_rebuild_visuals()
	_refresh_interaction_state()
	call_deferred("_refresh_overlapping_players")


func _process(_delta: float) -> void:
	_refresh_overlapping_players()


func interact() -> void:
	if container_id.is_empty() or bool(record.get("is_locked", false)):
		get_tree().call_group("game_world", "show_combat_message", "Контейнер заперт.", false)
		return
	get_tree().call_group("game_world", "request_open_loot_container", container_id)


func get_container_id() -> String:
	return container_id


func get_container_record() -> Dictionary:
	return record.duplicate(true)


func get_container_label() -> String:
	return str(record.get("label", "Контейнер"))


func get_interaction_label() -> String:
	var verb: String = "ОБЫСКАТЬ" if bool(record.get("is_open", false)) else "ОТКРЫТЬ"
	return "%s: %s" % [verb, get_container_label().to_upper()]


func get_interaction_description() -> String:
	if bool(record.get("is_locked", false)):
		return "Контейнер заперт. Для открытия потребуется подходящий ключ или взлом."
	return "Открыть контейнер и выбрать предметы для подбора."


func is_available_for_interaction() -> bool:
	return visible and not container_id.is_empty()


func get_interaction_zone_size_for_testing() -> Vector2:
	return INTERACTION_ZONE_SIZE


func _build_interaction_area() -> void:
	if _interaction_area != null:
		return
	_interaction_area = Area2D.new()
	_interaction_area.name = "InteractionArea"
	_interaction_area.collision_layer = 0
	_interaction_area.collision_mask = 1
	_interaction_area.monitorable = false
	_interaction_area.monitoring = visible
	var shape := RectangleShape2D.new()
	shape.size = INTERACTION_ZONE_SIZE
	var collision := CollisionShape2D.new()
	collision.name = "CollisionShape2D"
	collision.shape = shape
	_interaction_area.add_child(collision)
	_interaction_area.body_entered.connect(_on_body_entered)
	_interaction_area.body_exited.connect(_on_body_exited)
	add_child(_interaction_area)


func _on_body_entered(body: Node2D) -> void:
	_register_player(body)


func _on_body_exited(body: Node2D) -> void:
	_unregister_player(body)


func _register_player(body: Node) -> void:
	if not is_available_for_interaction() or body == null or not body.is_in_group("player"):
		return
	_registered_players[body.get_instance_id()] = body
	if body.has_method("register_interactable"):
		body.call("register_interactable", self)
	elif body.has_method("set_interactable"):
		body.call("set_interactable", self)


func _unregister_player(body: Node) -> void:
	if body == null:
		return
	_registered_players.erase(body.get_instance_id())
	if body.has_method("unregister_interactable"):
		body.call("unregister_interactable", self)
	elif body.has_method("clear_interactable"):
		body.call("clear_interactable", self)


func _unregister_all_players() -> void:
	var players: Array[Node] = []
	for value: Variant in _registered_players.values():
		if value is Node and is_instance_valid(value as Node):
			players.append(value as Node)
	for player_node: Node in players:
		_unregister_player(player_node)
	_registered_players.clear()


func _refresh_overlapping_players() -> void:
	if not is_available_for_interaction() or _interaction_area == null or not _interaction_area.monitoring:
		return
	var overlapping_ids: Dictionary = {}
	for body: Node2D in _interaction_area.get_overlapping_bodies():
		if not body.is_in_group("player"):
			continue
		overlapping_ids[body.get_instance_id()] = true
		_register_player(body)
	var stale: Array[Node] = []
	for key: Variant in _registered_players.keys():
		if overlapping_ids.has(key):
			continue
		var value: Variant = _registered_players.get(key, null)
		if value is Node and is_instance_valid(value as Node):
			stale.append(value as Node)
	for player_node: Node in stale:
		_unregister_player(player_node)


func _refresh_interaction_state() -> void:
	if _interaction_area != null:
		_interaction_area.set_deferred("monitoring", visible)
	if not visible:
		_unregister_all_players()
	elif is_inside_tree():
		call_deferred("_refresh_overlapping_players")


func _rebuild_visuals() -> void:
	if _body != null:
		_body.queue_free()
	if _lid != null:
		_lid.queue_free()
	if _label != null:
		_label.queue_free()
	var container_type: String = str(record.get("container_type", "container"))
	var opened: bool = bool(record.get("is_open", false))
	var empty: bool = (record.get("items", []) as Array).is_empty() if record.get("items", []) is Array else true
	_body = Polygon2D.new()
	_body.name = "Body"
	if container_type == "bag":
		_body.polygon = PackedVector2Array([
			Vector2(-18.0, 10.0), Vector2(-13.0, -10.0), Vector2(0.0, -16.0),
			Vector2(13.0, -10.0), Vector2(18.0, 10.0), Vector2(0.0, 16.0)
		])
		_body.color = Color(0.38, 0.24, 0.14, 1.0) if not empty else Color(0.25, 0.18, 0.13, 0.8)
	else:
		_body.polygon = PackedVector2Array([
			Vector2(-25.0, -8.0), Vector2(25.0, -8.0), Vector2(25.0, 18.0), Vector2(-25.0, 18.0)
		])
		_body.color = Color(0.42, 0.27, 0.12, 1.0) if not empty else Color(0.28, 0.21, 0.15, 0.82)
	_body.z_index = 4
	add_child(_body)
	if container_type != "bag":
		_lid = Polygon2D.new()
		_lid.name = "Lid"
		_lid.polygon = PackedVector2Array([
			Vector2(-25.0, -8.0), Vector2(25.0, -8.0), Vector2(20.0, -20.0), Vector2(-20.0, -20.0)
		])
		_lid.position = Vector2(0.0, -10.0) if opened else Vector2.ZERO
		_lid.rotation = -0.28 if opened else 0.0
		_lid.color = Color(0.54, 0.34, 0.14, 1.0)
		_lid.z_index = 5
		add_child(_lid)
	_label = Label.new()
	_label.name = "NameLabel"
	_label.position = Vector2(-100.0, -52.0)
	_label.size = Vector2(200.0, 26.0)
	_label.text = get_container_label()
	_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_label.add_theme_font_size_override("font_size", 13)
	_label.add_theme_color_override("font_color", Color(0.94, 0.85, 0.66, 0.96))
	_label.z_index = 6
	add_child(_label)


func _exit_tree() -> void:
	_unregister_all_players()
