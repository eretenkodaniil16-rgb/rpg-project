class_name CombatEscapeSystem
extends RefCounted

const POLICY_FORBIDDEN: String = "forbidden"
const POLICY_HIDDEN_BOUNDARY: String = "hidden_boundary"
const POLICY_PURSUIT_ROUTES: String = "pursuit_routes"
const ROUTE_HIDEOUT: String = "hideout"
const ROUTE_ROOM_TRANSITION: String = "room_transition"
const ROUTE_LEGACY_BOUNDARY: String = "legacy_boundary"
const DEFAULT_DEPTH_CELLS: int = 1
const DEFAULT_PASSIVE_PERCEPTION: int = 10
const DEFAULT_SEARCH_SWEEPS: int = 2


func get_rules(encounter_definition: Dictionary) -> Dictionary:
	var value: Variant = encounter_definition.get("escape", {})
	if not value is Dictionary:
		return {"policy": POLICY_FORBIDDEN}
	var rules: Dictionary = (value as Dictionary).duplicate(true)
	if not rules.has("policy"):
		rules["policy"] = POLICY_FORBIDDEN
	return rules


func is_escape_allowed(encounter_definition: Dictionary) -> bool:
	var policy: String = str(get_rules(encounter_definition).get("policy", POLICY_FORBIDDEN))
	if policy == POLICY_HIDDEN_BOUNDARY:
		return true
	return policy == POLICY_PURSUIT_ROUTES and not get_routes(encounter_definition).is_empty()


func get_routes(encounter_definition: Dictionary) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	var rules: Dictionary = get_rules(encounter_definition)
	if str(rules.get("policy", POLICY_FORBIDDEN)) != POLICY_PURSUIT_ROUTES:
		return result
	var value: Variant = rules.get("routes", [])
	if not value is Array:
		return result
	for item: Variant in value as Array:
		if not item is Dictionary:
			continue
		var route: Dictionary = (item as Dictionary).duplicate(true)
		var route_id: String = str(route.get("id", ""))
		var route_type: String = str(route.get("type", ""))
		if route_id.is_empty() or route_type not in [ROUTE_HIDEOUT, ROUTE_ROOM_TRANSITION]:
			continue
		result.append(route)
	return result


func get_route(encounter_definition: Dictionary, route_id: String) -> Dictionary:
	for route: Dictionary in get_routes(encounter_definition):
		if str(route.get("id", "")) == route_id:
			return route.duplicate(true)
	return {}


func get_route_type(route: Dictionary) -> String:
	return str(route.get("type", ""))


func get_route_label(route: Dictionary) -> String:
	return str(route.get("label", route.get("id", "Путь отхода")))


func route_hide_cells(route: Dictionary) -> Array[Vector2i]:
	var route_type: String = get_route_type(route)
	if route_type == ROUTE_HIDEOUT:
		var objective: Array[Vector2i] = _cell_array(route.get("objective_cells", []))
		return objective if not objective.is_empty() else _cell_array(route.get("hide_cells", []))
	if route_type == ROUTE_ROOM_TRANSITION:
		return _cell_array(route.get("hide_cells", []))
	return []


func route_transition_cells(route: Dictionary) -> Array[Vector2i]:
	return _cell_array(route.get("transition_cells", [])) if get_route_type(route) == ROUTE_ROOM_TRANSITION else []


func route_destination_cells(route: Dictionary) -> Array[Vector2i]:
	return _cell_array(route.get("destination_cells", [])) if get_route_type(route) == ROUTE_ROOM_TRANSITION else []


func overlay_cells(encounter_definition: Dictionary) -> Dictionary:
	var hideout: Array[Vector2i] = []
	var transition: Array[Vector2i] = []
	var destination: Array[Vector2i] = []
	for route: Dictionary in get_routes(encounter_definition):
		if get_route_type(route) == ROUTE_HIDEOUT:
			_append_unique_many(hideout, route_hide_cells(route))
		else:
			_append_unique_many(transition, route_transition_cells(route))
			_append_unique_many(destination, route_hide_cells(route))
	return {
		"hideout": hideout,
		"transition": transition,
		"destination": destination
	}


func escape_cells(grid: BattleGrid, encounter_definition: Dictionary) -> Array[Vector2i]:
	var result: Array[Vector2i] = []
	if grid == null:
		return result
	var rules: Dictionary = get_rules(encounter_definition)
	var policy: String = str(rules.get("policy", POLICY_FORBIDDEN))
	if policy == POLICY_PURSUIT_ROUTES:
		var overlay: Dictionary = overlay_cells(encounter_definition)
		for key: String in ["hideout", "transition", "destination"]:
			_append_unique_many(result, overlay.get(key, []) as Array[Vector2i])
		return result
	if policy != POLICY_HIDDEN_BOUNDARY:
		return result
	var field: Rect2 = grid.get_field_rect()
	var size: float = maxf(grid.get_cell_size(), 1.0)
	var columns: int = maxi(floori(field.size.x / size), 1)
	var rows: int = maxi(floori(field.size.y / size), 1)
	var depth: int = clampi(int(rules.get("depth_cells", DEFAULT_DEPTH_CELLS)), 1, mini(columns, rows))
	var edges: Array[String] = _string_array(rules.get("edges", ["west"]))
	for edge: String in edges:
		match edge:
			"west":
				for x: int in range(depth):
					for y: int in range(rows):
						_append_unique(result, Vector2i(x, y))
			"east":
				for x_offset: int in range(depth):
					for y: int in range(rows):
						_append_unique(result, Vector2i(columns - 1 - x_offset, y))
			"north":
				for y: int in range(depth):
					for x: int in range(columns):
						_append_unique(result, Vector2i(x, y))
			"south":
				for y_offset: int in range(depth):
					for x: int in range(columns):
						_append_unique(result, Vector2i(x, rows - 1 - y_offset))
	return result


func is_escape_cell(grid: BattleGrid, encounter_definition: Dictionary, cell: Vector2i) -> bool:
	return cell in escape_cells(grid, encounter_definition)


func find_hide_route(encounter_definition: Dictionary, cell: Vector2i) -> Dictionary:
	for route: Dictionary in get_routes(encounter_definition):
		if cell in route_hide_cells(route):
			return route.duplicate(true)
	return {}


func find_destination_route(encounter_definition: Dictionary, cell: Vector2i) -> Dictionary:
	for route: Dictionary in get_routes(encounter_definition):
		if get_route_type(route) == ROUTE_ROOM_TRANSITION and cell in route_destination_cells(route):
			return route.duplicate(true)
	return {}


func find_room_transition_route(encounter_definition: Dictionary, path: Array[Vector2i]) -> Dictionary:
	if path.size() < 2:
		return {}
	var final_cell: Vector2i = path[path.size() - 1]
	for route: Dictionary in get_routes(encounter_definition):
		if get_route_type(route) != ROUTE_ROOM_TRANSITION:
			continue
		if final_cell not in route_destination_cells(route):
			continue
		var crossed_transition: bool = false
		for cell: Vector2i in path:
			if cell in route_transition_cells(route):
				crossed_transition = true
				break
		if crossed_transition:
			return route.duplicate(true)
	return {}


func route_requires_rehide(route: Dictionary) -> bool:
	return get_route_type(route) == ROUTE_ROOM_TRANSITION and bool(route.get("requires_rehide", true))


func get_concealment_bonus(route: Dictionary) -> int:
	return maxi(int(route.get("concealment_bonus", 0)), 0)


func get_trace_dc_bonus(route: Dictionary) -> int:
	return maxi(int(route.get("trace_dc_bonus", 0)), 0)


func get_required_search_sweeps(route: Dictionary, encounter_definition: Dictionary = {}) -> int:
	var rules: Dictionary = get_rules(encounter_definition)
	var fallback: int = maxi(int(rules.get("default_required_search_sweeps", DEFAULT_SEARCH_SWEEPS)), 1)
	return maxi(int(route.get("required_search_sweeps", fallback)), 1)


func get_tracking_dc(stealth_total: int, route: Dictionary) -> int:
	return maxi(stealth_total + get_trace_dc_bonus(route), 1)


func get_search_dc(stealth_total: int, route: Dictionary) -> int:
	return maxi(stealth_total + get_concealment_bonus(route), 1)


func blocks_cross_room_line_of_sight(
	grid: BattleGrid,
	encounter_definition: Dictionary,
	observer_position: Vector2,
	target_position: Vector2
) -> bool:
	if grid == null:
		return false
	var observer_cell: Vector2i = grid.world_to_cell(observer_position)
	var target_cell: Vector2i = grid.world_to_cell(target_position)
	for route: Dictionary in get_routes(encounter_definition):
		if get_route_type(route) != ROUTE_ROOM_TRANSITION or not bool(route.get("blocks_cross_room_los", false)):
			continue
		var destination: Array[Vector2i] = route_destination_cells(route)
		var observer_inside: bool = observer_cell in destination
		var target_inside: bool = target_cell in destination
		if observer_inside != target_inside:
			return true
	return false


func get_safe_anchor(encounter_definition: Dictionary, fallback: Vector2, route: Dictionary = {}) -> Vector2:
	var value: Variant = route.get("safe_anchor", []) if not route.is_empty() else []
	if not (value is Array and (value as Array).size() >= 2):
		value = get_rules(encounter_definition).get("safe_anchor", [])
	if value is Array and (value as Array).size() >= 2:
		return Vector2(float((value as Array)[0]), float((value as Array)[1]))
	return fallback


func get_reason_id(encounter_definition: Dictionary, route: Dictionary = {}) -> String:
	if not route.is_empty() and not str(route.get("reason_id", "")).is_empty():
		return str(route.get("reason_id", ""))
	return str(get_rules(encounter_definition).get("reason_id", "player_escaped_hidden"))


func get_alert_flag(encounter_definition: Dictionary) -> String:
	return str(get_rules(encounter_definition).get("alert_flag", ""))


func should_restore_participants(encounter_definition: Dictionary) -> bool:
	return bool(get_rules(encounter_definition).get("restore_participants", true))


func observer_passive_perception(observer: Node) -> int:
	if observer == null or not is_instance_valid(observer):
		return DEFAULT_PASSIVE_PERCEPTION
	if observer.has_method("get_passive_perception"):
		return maxi(int(observer.call("get_passive_perception")), 1)
	var property_value: Variant = observer.get("passive_perception")
	if property_value != null:
		return maxi(int(property_value), 1)
	if observer.has_method("get_saving_throw_modifier"):
		return maxi(10 + int(observer.call("get_saving_throw_modifier", "wisdom")), 1)
	return DEFAULT_PASSIVE_PERCEPTION


func highest_passive_perception(observers: Array[Node]) -> int:
	var result: int = DEFAULT_PASSIVE_PERCEPTION
	for observer: Node in observers:
		result = maxi(result, observer_passive_perception(observer))
	return result


func stealth_succeeds(stealth_total: int, observers: Array[Node]) -> bool:
	for observer: Node in observers:
		if stealth_total < observer_passive_perception(observer):
			return false
	return true


func perception_modifier(observer: Node) -> int:
	return observer_passive_perception(observer) - 10


func tracking_modifier(observer: Node) -> int:
	if observer == null or not is_instance_valid(observer):
		return 0
	if observer.has_method("get_tracking_modifier"):
		return int(observer.call("get_tracking_modifier"))
	var property_value: Variant = observer.get("tracking_modifier")
	if property_value != null:
		return int(property_value)
	return perception_modifier(observer)


static func _append_unique(values: Array[Vector2i], value: Vector2i) -> void:
	if value not in values:
		values.append(value)


static func _append_unique_many(values: Array[Vector2i], additions: Array[Vector2i]) -> void:
	for value: Vector2i in additions:
		_append_unique(values, value)


static func _cell_array(value: Variant) -> Array[Vector2i]:
	var result: Array[Vector2i] = []
	if not value is Array:
		return result
	for item: Variant in value as Array:
		if item is Vector2i:
			_append_unique(result, item as Vector2i)
		elif item is Array and (item as Array).size() >= 2:
			_append_unique(result, Vector2i(int((item as Array)[0]), int((item as Array)[1])))
	return result


static func _string_array(value: Variant) -> Array[String]:
	var result: Array[String] = []
	if value is Array:
		for item: Variant in value as Array:
			var text: String = str(item)
			if not text.is_empty() and text not in result:
				result.append(text)
	return result
