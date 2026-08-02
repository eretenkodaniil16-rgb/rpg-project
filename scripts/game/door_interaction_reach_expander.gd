class_name DoorInteractionReachExpander
extends Node

const HORIZONTAL_MARGIN_PIXELS: float = 20.0
const VERTICAL_MARGIN_PIXELS: float = 20.0
const INTERACTION_AREA_WIDTH: float = 120.0
const INTERACTION_AREA_VERTICAL_PADDING: float = 48.0

var _doors: Array[StealthDoor] = []
var _player: Node2D
var _grid: BattleGrid


func _ready() -> void:
	process_priority = 100
	_player = get_tree().get_first_node_in_group("player") as Node2D
	_grid = get_tree().get_first_node_in_group("battle_grid") as BattleGrid
	_apply_trigger_shapes()


func configure(doors: Array[StealthDoor]) -> void:
	_doors.clear()
	for door: StealthDoor in doors:
		if door != null and is_instance_valid(door):
			_doors.append(door)
	if is_inside_tree():
		_apply_trigger_shapes()


func _process(_delta: float) -> void:
	if not is_instance_valid(_player):
		_player = get_tree().get_first_node_in_group("player") as Node2D
	if _grid == null:
		_grid = get_tree().get_first_node_in_group("battle_grid") as BattleGrid
	if not is_instance_valid(_player) or _grid == null:
		return
	for door: StealthDoor in _doors:
		if not is_instance_valid(door):
			continue
		var in_range: bool = _player_is_in_expanded_range(door, _player)
		var current_player: Node = door.get("_player_in_range") as Node
		if in_range:
			door.call("_set_player_in_range", _player)
		elif current_player == _player:
			door.call("_clear_player_in_range", _player)


func is_player_in_expanded_range_for_testing(door: StealthDoor, player: Node2D) -> bool:
	if _grid == null:
		_grid = get_tree().get_first_node_in_group("battle_grid") as BattleGrid
	return _grid != null and _player_is_in_expanded_range(door, player)


func get_configured_trigger_size_for_testing(door: StealthDoor) -> Vector2:
	if door == null:
		return Vector2.ZERO
	var collision: CollisionShape2D = door.get_node_or_null("InteractionArea/CollisionShape2D") as CollisionShape2D
	if collision == null or not collision.shape is RectangleShape2D:
		return Vector2.ZERO
	return (collision.shape as RectangleShape2D).size


func _player_is_in_expanded_range(door: StealthDoor, player: Node2D) -> bool:
	if door == null or player == null or _grid == null:
		return false
	var local_player: Vector2 = door.to_local(player.global_position)
	var half_cell: float = _grid.get_cell_size() * 0.5
	return (
		absf(local_player.x) <= half_cell + HORIZONTAL_MARGIN_PIXELS
		and absf(local_player.y) <= door.door_size.y * 0.5 - half_cell + VERTICAL_MARGIN_PIXELS
	)


func _apply_trigger_shapes() -> void:
	for door: StealthDoor in _doors:
		if not is_instance_valid(door):
			continue
		var collision: CollisionShape2D = door.get_node_or_null("InteractionArea/CollisionShape2D") as CollisionShape2D
		if collision == null or not collision.shape is RectangleShape2D:
			continue
		var shape: RectangleShape2D = collision.shape as RectangleShape2D
		shape.size = Vector2(
			INTERACTION_AREA_WIDTH,
			door.door_size.y + INTERACTION_AREA_VERTICAL_PADDING
		)
