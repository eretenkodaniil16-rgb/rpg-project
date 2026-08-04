class_name DroppedInventoryItem
extends Node2D

const INTERACTION_ZONE_SIZE: Vector2 = Vector2(128.0, 128.0)

var drop_id: String = ""
var item_id: String = ""
var quantity: int = 1
var definition: Dictionary = {}

var _manager: Node = null
var _interaction_area: Area2D = null
var _registered_players: Dictionary = {}
var _body: Polygon2D = null
var _label: Label = null


func configure(
	manager: Node,
	new_drop_id: String,
	new_item_id: String,
	new_quantity: int,
	new_definition: Dictionary
) -> void:
	_manager = manager
	drop_id = new_drop_id
	item_id = new_item_id
	quantity = maxi(new_quantity, 1)
	definition = new_definition.duplicate(true)
	if is_inside_tree():
		_rebuild_visuals()


func _ready() -> void:
	add_to_group("dropped_inventory_items")
	_build_interaction_area()
	_rebuild_visuals()
	call_deferred("_refresh_overlapping_players")


func _process(_delta: float) -> void:
	_refresh_overlapping_players()


func interact() -> void:
	var game: Node = get_tree().get_first_node_in_group("game_world")
	if (
		game != null
		and game.has_method("is_turn_based_combat_active")
		and bool(game.call("is_turn_based_combat_active"))
	):
		get_tree().call_group(
			"game_world",
			"show_combat_message",
			"В бою подберите предмет через ДЕЙСТВИЯ: это расходует дополнительное действие.",
			false
		)
		return
	collect()


func collect() -> bool:
	if not is_available_for_pickup():
		return false
	if _manager == null or not is_instance_valid(_manager) or not _manager.has_method("collect_drop"):
		return false
	return bool(_manager.call("collect_drop", drop_id, true))


func mark_collected() -> void:
	quantity = 0
	visible = false
	set_process(false)
	if _interaction_area != null:
		_interaction_area.monitoring = false
	_unregister_all_players()


func is_available_for_pickup() -> bool:
	return not drop_id.is_empty() and quantity > 0 and visible


func get_drop_id() -> String:
	return drop_id


func get_item_id() -> String:
	return item_id


func get_quantity() -> int:
	return quantity


func get_item_label() -> String:
	var base_label: String = str(definition.get("name", item_id))
	return "%s ×%d" % [base_label, quantity] if quantity > 1 else base_label


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
	_interaction_area.monitoring = true
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
	if not is_available_for_pickup() or body == null or not body.is_in_group("player"):
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
	if not is_available_for_pickup() or _interaction_area == null or not _interaction_area.monitoring:
		return
	var overlapping_ids: Dictionary = {}
	for body: Node2D in _interaction_area.get_overlapping_bodies():
		if not body.is_in_group("player"):
			continue
		overlapping_ids[body.get_instance_id()] = true
		_register_player(body)
	var stale_players: Array[Node] = []
	for key: Variant in _registered_players.keys():
		if overlapping_ids.has(key):
			continue
		var value: Variant = _registered_players.get(key, null)
		if value is Node and is_instance_valid(value as Node):
			stale_players.append(value as Node)
	for player_node: Node in stale_players:
		_unregister_player(player_node)


func _rebuild_visuals() -> void:
	if _body != null:
		_body.queue_free()
	if _label != null:
		_label.queue_free()
	_body = Polygon2D.new()
	_body.name = "Body"
	_body.polygon = PackedVector2Array([
		Vector2(0.0, -10.0),
		Vector2(18.0, 0.0),
		Vector2(0.0, 10.0),
		Vector2(-18.0, 0.0)
	])
	_body.color = Color(0.74, 0.69, 0.58, 1.0)
	_body.z_index = 4
	add_child(_body)
	_label = Label.new()
	_label.name = "NameLabel"
	_label.position = Vector2(-90.0, -40.0)
	_label.size = Vector2(180.0, 24.0)
	_label.text = get_item_label()
	_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_label.add_theme_font_size_override("font_size", 12)
	_label.add_theme_color_override("font_color", Color(0.94, 0.88, 0.72, 0.96))
	_label.z_index = 5
	add_child(_label)


func _exit_tree() -> void:
	_unregister_all_players()
