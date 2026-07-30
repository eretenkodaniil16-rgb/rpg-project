class_name StealthDoor
extends StaticBody2D

const WORLD_INTERACTION_ACTION_ID: String = "world_interact"

@export var door_id: String = "west_service_door"
@export var door_label: String = "Дверь служебной комнаты"
@export var door_size: Vector2 = Vector2(36.0, 120.0)

var _door_state: String = "closed"
var _collision: CollisionShape2D
var _visual: Polygon2D
var _state_label: Label
var _interaction_area: Area2D
var _player_in_range: Node = null
var _last_combat_interaction_turn_token: String = ""


func _ready() -> void:
	add_to_group("stealth_doors")
	_build_nodes()
	var state: Node = _get_game_state()
	if state != null and state.has_method("get_stealth_door_state"):
		_door_state = str(state.call("get_stealth_door_state", door_id))
	_apply_state(false)


func interact() -> void:
	if _is_combat_active():
		if not _combat_player_can_interact_now():
			get_tree().call_group("game_world", "show_combat_message", "Открыть или закрыть дверь можно только на своём ходу.", false)
			return
		var turn_token: String = _current_combat_turn_token()
		if turn_token.is_empty() or turn_token == _last_combat_interaction_turn_token:
			get_tree().call_group("game_world", "show_combat_message", "Взаимодействие с объектом на этом ходу уже использовано.", false)
			return
		if not _door_state_allows_interaction():
			_show_blocked_message()
			return
		_last_combat_interaction_turn_token = turn_token
	perform_world_interaction()


func can_perform_world_interaction() -> bool:
	if not _door_state_allows_interaction():
		return false
	if not _is_combat_active():
		return true
	var turn_token: String = _current_combat_turn_token()
	return _combat_player_can_interact_now() and not turn_token.is_empty() and turn_token != _last_combat_interaction_turn_token


func get_combat_interaction_label() -> String:
	if _door_state == "open":
		return "ЗАКРЫТЬ ДВЕРЬ"
	if _door_state == "closed":
		return "ОТКРЫТЬ ДВЕРЬ"
	return "ДВЕРЬ НЕДОСТУПНА"


func get_combat_interaction_description() -> String:
	if _is_combat_active() and not _combat_player_can_interact_now():
		return "Взаимодействовать с дверью можно только на своём ходу."
	if _is_combat_active() and _current_combat_turn_token() == _last_combat_interaction_turn_token:
		return "Взаимодействие с объектом на этом ходу уже использовано."
	match _door_state:
		"open": return "Закрыть соседнюю дверь. Использует одно взаимодействие с объектом на этом ходу."
		"closed": return "Открыть соседнюю дверь. Использует одно взаимодействие с объектом на этом ходу."
		"locked", "blocked": return "%s заперта или заблокирована." % door_label
		"broken": return "%s разрушена и больше не закрывается." % door_label
		_: return "Взаимодействовать с дверью."


func perform_world_interaction() -> void:
	if not _door_state_allows_interaction():
		_show_blocked_message()
		return
	var next_state: String = "open" if _door_state == "closed" else "closed"
	set_door_state(next_state, true)
	get_tree().call_group(
		"game_world",
		"show_combat_message",
		"%s %s." % [door_label, "открыта" if next_state == "open" else "закрыта"],
		true
	)


func set_door_state(value: String, report_noise: bool = false) -> void:
	if value not in ["open", "closed", "locked", "blocked", "broken"]:
		return
	_door_state = value
	var state: Node = _get_game_state()
	if state != null and state.has_method("set_stealth_door_state"):
		state.call("set_stealth_door_state", door_id, _door_state, true)
	_apply_state(report_noise)


func get_door_state() -> String:
	return _door_state


func get_door_id() -> String:
	return door_id


func blocks_line_of_sight() -> bool:
	return _door_state not in ["open", "broken"]


func get_world_rect() -> Rect2:
	return Rect2(global_position - door_size * 0.5, door_size)


func _door_state_allows_interaction() -> bool:
	return _door_state not in ["locked", "blocked", "broken"]


func _show_blocked_message() -> void:
	var message: String = "%s заперта." % door_label
	if _door_state == "broken":
		message = "%s разрушена и больше не закрывается." % door_label
	get_tree().call_group("game_world", "show_combat_message", message, false)


func _is_combat_active() -> bool:
	var game: Node = get_tree().get_first_node_in_group("game_world")
	return game != null and game.has_method("is_turn_based_combat_active") and bool(game.call("is_turn_based_combat_active"))


func _combat_player_can_interact_now() -> bool:
	var game: Node = get_tree().get_first_node_in_group("game_world")
	if game == null:
		return false
	var turn_system_value: Variant = game.get("_turn_system")
	if not turn_system_value is TurnBasedCombatSystem:
		return false
	var turn_system: TurnBasedCombatSystem = turn_system_value as TurnBasedCombatSystem
	return turn_system.active and is_instance_valid(_player_in_range) and turn_system.current_actor() == _player_in_range


func _current_combat_turn_token() -> String:
	var game: Node = get_tree().get_first_node_in_group("game_world")
	if game == null:
		return ""
	var turn_system_value: Variant = game.get("_turn_system")
	if not turn_system_value is TurnBasedCombatSystem:
		return ""
	return (turn_system_value as TurnBasedCombatSystem).current_turn_token()


func _get_game_state() -> Node:
	return get_tree().root.get_node_or_null("GameState") if is_inside_tree() else null


func _build_nodes() -> void:
	_collision = CollisionShape2D.new()
	_collision.name = "CollisionShape2D"
	var shape := RectangleShape2D.new()
	shape.size = door_size
	_collision.shape = shape
	add_child(_collision)

	_visual = Polygon2D.new()
	_visual.name = "Visual"
	_visual.polygon = PackedVector2Array([
		Vector2(-door_size.x * 0.5, -door_size.y * 0.5),
		Vector2(door_size.x * 0.5, -door_size.y * 0.5),
		Vector2(door_size.x * 0.5, door_size.y * 0.5),
		Vector2(-door_size.x * 0.5, door_size.y * 0.5)
	])
	_visual.z_index = 5
	add_child(_visual)

	_state_label = Label.new()
	_state_label.name = "StateLabel"
	_state_label.position = Vector2(-94.0, -86.0)
	_state_label.size = Vector2(188.0, 30.0)
	_state_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_state_label.add_theme_font_size_override("font_size", 13)
	_state_label.z_index = 6
	add_child(_state_label)

	_interaction_area = Area2D.new()
	_interaction_area.name = "InteractionArea"
	var interaction_shape := RectangleShape2D.new()
	interaction_shape.size = door_size + Vector2(48.0, 64.0)
	var interaction_collision := CollisionShape2D.new()
	interaction_collision.shape = interaction_shape
	_interaction_area.add_child(interaction_collision)
	_interaction_area.body_entered.connect(_on_body_entered)
	_interaction_area.body_exited.connect(_on_body_exited)
	add_child(_interaction_area)


func _apply_state(report_noise: bool) -> void:
	var opened: bool = _door_state in ["open", "broken"]
	if _collision != null:
		_collision.set_deferred("disabled", opened)
	if _visual != null:
		_visual.rotation = deg_to_rad(82.0) if _door_state == "open" else 0.0
		_visual.color = Color(0.38, 0.24, 0.14, 0.72) if opened else Color(0.3, 0.17, 0.1, 1.0)
	if _state_label != null:
		var label: String = {
			"open": "ОТКРЫТА",
			"closed": "ЗАКРЫТА",
			"locked": "ЗАПЕРТА",
			"blocked": "ЗАБЛОКИРОВАНА",
			"broken": "СЛОМАНА"
		}.get(_door_state, _door_state.to_upper())
		_state_label.text = "%s · %s" % [door_label, label]
	if report_noise:
		get_tree().call_group("game_world", "report_world_noise", "door", global_position, {"door_id": door_id})
	get_tree().call_group("game_world", "on_stealth_door_state_changed", door_id, _door_state)
	get_tree().call_group("stealth_world", "set_navigation_door_state", door_id, _door_state)


func _on_body_entered(body: Node2D) -> void:
	if not body.is_in_group("player"):
		return
	_player_in_range = body
	if body.has_method("set_interactable"):
		body.call("set_interactable", self)
	_connect_action_catalog()
	get_tree().call_group(
		"game_world",
		"set_interaction_action",
		true,
		"%s %s" % ["закрыть" if _door_state == "open" else "открыть", door_label.to_lower()],
		"ДВЕРЬ"
	)


func _on_body_exited(body: Node2D) -> void:
	if body != _player_in_range:
		return
	_disconnect_action_catalog()
	if body.has_method("clear_interactable"):
		body.call("clear_interactable", self)
	_player_in_range = null
	get_tree().call_group("game_world", "set_interaction_action", false, "", "ДЕЙСТВИЕ")


func _connect_action_catalog() -> void:
	var game: Node = get_tree().get_first_node_in_group("game_world")
	var catalog: Node = game.get_node_or_null("Interface/ActionCatalogUI") if game != null else null
	var callback := Callable(self, "_on_catalog_action_requested")
	if catalog != null and catalog.has_signal("action_requested") and not catalog.is_connected("action_requested", callback):
		catalog.connect("action_requested", callback)


func _disconnect_action_catalog() -> void:
	var game: Node = get_tree().get_first_node_in_group("game_world")
	var catalog: Node = game.get_node_or_null("Interface/ActionCatalogUI") if game != null else null
	var callback := Callable(self, "_on_catalog_action_requested")
	if catalog != null and catalog.has_signal("action_requested") and catalog.is_connected("action_requested", callback):
		catalog.disconnect("action_requested", callback)


func _on_catalog_action_requested(action_id: String) -> void:
	if action_id != WORLD_INTERACTION_ACTION_ID or not is_instance_valid(_player_in_range):
		return
	interact()
