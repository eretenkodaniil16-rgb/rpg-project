extends "res://scripts/game/game_world_snapshot_npc_runtime.gd"

const EXPLORATION_PATH_LIMIT: int = 512


func _unhandled_input(event: InputEvent) -> void:
	if _try_handle_exploration_pointer(event):
		return
	super._unhandled_input(event)


func plan_exploration_path_to_world_for_testing(world_position: Vector2) -> Array[Vector2]:
	return _build_exploration_world_path(world_position)


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
