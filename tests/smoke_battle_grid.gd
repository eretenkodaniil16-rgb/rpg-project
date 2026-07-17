extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	state.call("new_game")
	var character := PlayerCharacter.new()
	character.character_name = "Картограф"
	character.character_class_id = "ranger"
	character.character_class_name = "Следопыт"
	character.maximum_health = 12
	character.current_health = 12
	character.abilities["dexterity"] = 16
	state.set("player_character", character)
	state.set("player_position", Vector2(320.0, 360.0))
	state.set("input_locked", false)

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	if packed == null:
		_fail("Game scene failed to load.")
		return
	var game: Node = packed.instantiate()
	root.add_child(game)
	for _frame: int in range(5):
		await process_frame

	var grid: Node2D = game.get_node_or_null("BattleGrid") as Node2D
	if grid == null or not grid.is_in_group("battle_grid"):
		_fail("Battle grid was not attached to the game world.")
		return
	if not grid.visible or absf(float(grid.call("get_cell_size")) - 64.0) > 0.01:
		_fail("Battle grid must start visible with 64-pixel cells.")
		return

	var caretaker: Node = game.get_node_or_null("Caretaker")
	var dummy: Node = game.get_node_or_null("TrainingDummy")
	if caretaker == null or dummy == null:
		_fail("Combat targets are missing from the room.")
		return
	if int((caretaker as CanvasItem).z_index) < 10 or int((dummy as CanvasItem).z_index) < 10:
		_fail("Combatants must render above the grid.")
		return

	game.call("_set_selected_target", caretaker)
	await process_frame
	await process_frame
	var distance_line: Line2D = grid.get_node_or_null("DistanceLine") as Line2D
	var distance_label: Label = grid.get_node_or_null("DistanceLabel") as Label
	if distance_line == null or distance_label == null or not distance_line.visible or not distance_label.visible:
		_fail("Selected target measurement overlay is missing.")
		return
	if "50 футов" not in distance_label.text or "10 клеток" not in distance_label.text:
		_fail("Grid measurement label does not match the combat distance: %s" % distance_label.text)
		return

	var sheet: Control = game.get_node_or_null("Interface/CharacterSheet") as Control
	if sheet == null:
		_fail("Character sheet is missing.")
		return
	sheet.call("open_sheet", character)
	await process_frame
	var toggle: Button = sheet.find_child("GridToggleButton", true, false) as Button
	if toggle == null:
		_fail("Grid toggle is missing from the character sheet.")
		return
	toggle.emit_signal("pressed")
	await process_frame
	if grid.visible:
		_fail("Grid toggle did not hide the grid.")
		return
	toggle.emit_signal("pressed")
	await process_frame
	if not grid.visible:
		_fail("Grid toggle did not restore the grid.")
		return
	sheet.call("close_sheet")

	game.queue_free()
	await process_frame
	print("Battle grid smoke test passed.")
	quit(0)
