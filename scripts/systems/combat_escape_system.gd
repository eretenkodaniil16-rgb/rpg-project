class_name CombatEscapeSystem
extends RefCounted

const POLICY_FORBIDDEN: String = "forbidden"
const POLICY_HIDDEN_BOUNDARY: String = "hidden_boundary"
const DEFAULT_DEPTH_CELLS: int = 1
const DEFAULT_PASSIVE_PERCEPTION: int = 10


func get_rules(encounter_definition: Dictionary) -> Dictionary:
	var value: Variant = encounter_definition.get("escape", {})
	if not value is Dictionary:
		return {"policy": POLICY_FORBIDDEN}
	var rules: Dictionary = (value as Dictionary).duplicate(true)
	if not rules.has("policy"):
		rules["policy"] = POLICY_FORBIDDEN
	return rules


func is_escape_allowed(encounter_definition: Dictionary) -> bool:
	return str(get_rules(encounter_definition).get("policy", POLICY_FORBIDDEN)) == POLICY_HIDDEN_BOUNDARY


func escape_cells(grid: BattleGrid, encounter_definition: Dictionary) -> Array[Vector2i]:
	var result: Array[Vector2i] = []
	if grid == null:
		return result
	var rules: Dictionary = get_rules(encounter_definition)
	if str(rules.get("policy", POLICY_FORBIDDEN)) != POLICY_HIDDEN_BOUNDARY:
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


func get_safe_anchor(encounter_definition: Dictionary, fallback: Vector2) -> Vector2:
	var rules: Dictionary = get_rules(encounter_definition)
	var value: Variant = rules.get("safe_anchor", [])
	if value is Array and (value as Array).size() >= 2:
		return Vector2(float((value as Array)[0]), float((value as Array)[1]))
	return fallback


func get_reason_id(encounter_definition: Dictionary) -> String:
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


static func _append_unique(values: Array[Vector2i], value: Vector2i) -> void:
	if value not in values:
		values.append(value)


static func _string_array(value: Variant) -> Array[String]:
	var result: Array[String] = []
	if value is Array:
		for item: Variant in value as Array:
			var text: String = str(item)
			if not text.is_empty() and text not in result:
				result.append(text)
	return result
