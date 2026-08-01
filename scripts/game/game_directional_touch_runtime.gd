extends "res://scripts/game/game_world_snapshot_npc_runtime.gd"

const EXPLORATION_PATH_LIMIT: int = 512
const NPC_TRIGGER_SCALE: float = 1.35
const FOG_RENDER_Z_INDEX: int = 45
const WALL_RENDER_Z_INDEX: int = 50
const DOOR_RENDER_Z_INDEX: int = 51


func _ready() -> void:
	super._ready()
	call_deferred("_expand_npc_trigger_zones")
	call_deferred("_configure_occlusion_rendering")


func _unhandled_input(event: InputEvent) -> void:
	if _try_handle_exploration_pointer(event):
		return
	super._unhandled_input(event)


func plan_exploration_path_to_world_for_testing(world_position: Vector2) -> Array[Vector2]:
	return _build_exploration_world_path(world_position)


func get_npc_trigger_extent_for_testing(actor_id: String) -> Vector2:
	for actor: Node in _persistent_world_actors():
		if _persistent_entity_id(actor) != actor_id:
			continue
		var collision: CollisionShape2D = _interaction_collision_for_actor(actor)
		if collision == null or collision.shape == null:
			return Vector2.ZERO
		if collision.shape is CircleShape2D:
			var radius: float = (collision.shape as CircleShape2D).radius
			return Vector2(radius, radius)
		if collision.shape is RectangleShape2D:
			return (collision.shape as RectangleShape2D).size
	return Vector2.ZERO


func get_visibility_render_order_for_testing() -> Dictionary:
	var fog: CanvasItem = get_tree().get_first_node_in_group("player_visibility") as CanvasItem
	var room: Node = get_node_or_null("StealthTestRoom")
	var wall: Polygon2D = room.get_node_or_null("WestPartitionTop/Polygon2D") as Polygon2D if room != null else null
	var door_visual: Polygon2D = null
	var doors: Array[Node] = get_tree().get_nodes_in_group("stealth_doors")
	if not doors.is_empty() and is_instance_valid(doors[0]):
		door_visual = doors[0].get_node_or_null("Visual") as Polygon2D
	return {
		"fog_z": fog.z_index if fog != null else -1,
		"wall_z": wall.z_index if wall != null else -1,
		"door_z": door_visual.z_index if door_visual != null else -1
	}


func _try_handle_exploration_pointer(event: InputEvent) -> bool:
	if _turn_system.active or GameState.input_locked or _attack_in_progress or _enemy_turn_running:
		return false
	if _any_overlay_visible() or (_action_catalog_ui != null and _action_catalog_ui.is_catalog_open()):
		return false
	var screen_position: Vector2 = Vector2.INF
	if event is InputEventScreenTouch:
		var touch: InputEventScreenTouch = event as InputEventScreenTouch
		if touch.pressed:
			screen_position = touch.position
	elif event is InputEventMouseButton:
		var mouse: InputEventMouseButton = event as InputEventMouseButton
		if mouse.pressed and mouse.button_index == MOUSE_BUTTON_LEFT:
			screen_position = mouse.position
	if screen_position == Vector2.INF:
		return false
	var world_position: Vector2 = get_viewport().get_canvas_transform().affine_inverse() * screen_position
	var path: Array[Vector2] = _build_exploration_world_path(world_position)
	if path.is_empty():
		show_combat_message("До выбранной точки нет безопасного пути.", false)
	else:
		if player.has_method("set_exploration_click_path"):
			player.call("set_exploration_click_path", path)
		show_combat_message("Маршрут выбран касанием. Джойстик меняет только направление взгляда.", true)
	get_viewport().set_input_as_handled()
	return true


func _build_exploration_world_path(world_position: Vector2) -> Array[Vector2]:
	var result: Array[Vector2] = []
	var grid: BattleGrid = _get_battle_grid()
	if grid == null or _combat_environment == null or player == null:
		return result
	var start_cell: Vector2i = grid.world_to_cell(player.global_position)
	var requested_cell: Vector2i = grid.world_to_cell(world_position)
	var occupied: Dictionary = _occupied_cells(player)
	var target_cell: Vector2i = _nearest_safe_cell(grid, requested_cell, occupied)
	if not grid.is_cell_valid(start_cell) or not grid.is_cell_valid(target_cell):
		return result
	var cells: Array[Vector2i] = _find_safe_cell_path(grid, start_cell, target_cell, occupied)
	if cells.is_empty() or cells.size() > EXPLORATION_PATH_LIMIT:
		return result
	for cell: Vector2i in cells:
		result.append(grid.cell_to_world_center(cell))
	return result


func _expand_npc_trigger_zones() -> void:
	for actor: Node in _persistent_world_actors():
		var collision: CollisionShape2D = _interaction_collision_for_actor(actor)
		if collision == null or collision.shape == null or bool(collision.get_meta("npc_trigger_expanded", false)):
			continue
		var expanded: Shape2D = collision.shape.duplicate() as Shape2D
		if expanded is CircleShape2D:
			(expanded as CircleShape2D).radius *= NPC_TRIGGER_SCALE
		elif expanded is RectangleShape2D:
			(expanded as RectangleShape2D).size *= NPC_TRIGGER_SCALE
		else:
			continue
		collision.shape = expanded
		collision.set_meta("npc_trigger_expanded", true)


func _interaction_collision_for_actor(actor: Node) -> CollisionShape2D:
	if actor == null or not is_instance_valid(actor):
		return null
	var interaction_area: Area2D = actor.get_node_or_null("InteractionArea") as Area2D
	if interaction_area != null:
		var dedicated: CollisionShape2D = interaction_area.get_node_or_null("CollisionShape2D") as CollisionShape2D
		if dedicated != null:
			return dedicated
	return actor.get_node_or_null("CollisionShape2D") as CollisionShape2D


func _configure_occlusion_rendering() -> void:
	for _frame: int in range(3):
		await get_tree().process_frame
	var fog: CanvasItem = get_tree().get_first_node_in_group("player_visibility") as CanvasItem
	if fog != null:
		fog.z_as_relative = false
		fog.z_index = FOG_RENDER_Z_INDEX
	var room: Node = get_node_or_null("StealthTestRoom")
	if room != null:
		for wall_name: String in [
			"WestPartitionTop",
			"WestPartitionBottom",
			"InnerPartitionTop",
			"InnerPartitionBottom"
		]:
			var wall: Node = room.get_node_or_null(wall_name)
			if wall == null:
				continue
			for child: Node in wall.get_children():
				if child is Polygon2D:
					var wall_visual: Polygon2D = child as Polygon2D
					wall_visual.z_as_relative = false
					wall_visual.z_index = WALL_RENDER_Z_INDEX
	for door: Node in get_tree().get_nodes_in_group("stealth_doors"):
		if not is_instance_valid(door):
			continue
		var visual: Polygon2D = door.get_node_or_null("Visual") as Polygon2D
		if visual != null:
			visual.z_as_relative = false
			visual.z_index = DOOR_RENDER_Z_INDEX
