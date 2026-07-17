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
	var ranger := PlayerCharacter.new()
	ranger.character_name = "Стрелок"
	ranger.character_class_id = "ranger"
	ranger.character_class_name = "Следопыт"
	ranger.maximum_health = 12
	ranger.current_health = 12
	ranger.abilities["dexterity"] = 16
	state.set("player_character", ranger)
	state.set("player_position", Vector2(320.0, 360.0))
	state.set("input_locked", false)

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	if packed == null:
		_fail("Game scene failed to load.")
		return
	var game: Node = packed.instantiate()
	root.add_child(game)
	for _frame: int in range(7):
		await process_frame

	var player: Node = game.get_node_or_null("Player")
	var caretaker: Node = game.get_node_or_null("Caretaker")
	var target_label: Label = game.find_child("TargetLabel", true, false) as Label
	var grid: Node = game.get_node_or_null("BattleGrid")
	if player == null or caretaker == null or target_label == null or grid == null:
		_fail("Free-aim scene dependencies are missing.")
		return
	if game.get("_selected_target") != null:
		_fail("The game must start without an automatically selected target.")
		return
	if target_label.visible:
		_fail("Distance and target details must stay hidden before manual selection.")
		return
	var distance_line: Line2D = grid.get_node_or_null("DistanceLine") as Line2D
	if distance_line == null or distance_line.visible:
		_fail("Grid distance line must be hidden before target selection.")
		return
	if player.get_node_or_null("FacingIndicator") == null:
		_fail("Player facing indicator is missing.")
		return

	var arrows_before: int = int(state.call("get_item_count", "arrow"))
	if arrows_before <= 0:
		_fail("Ranger starter arrows are missing.")
		return
	game.call("_request_attack")
	await create_timer(1.1).timeout
	await process_frame
	if int(state.call("get_item_count", "arrow")) != arrows_before - 1:
		_fail("Directional ranged attack did not consume one arrow.")
		return
	if bool(caretaker.call("is_combat_active")) and not bool(caretaker.call("is_hostile")):
		_fail("The first character in the firing direction did not receive the attack.")
		return
	if game.get("_selected_target") != null or target_label.visible or distance_line.visible:
		_fail("Free aim must not silently select the struck character.")
		return

	var popup: Control = game.find_child("AttackResultPopup", true, false) as Control
	if popup != null and popup.visible:
		popup.call("_on_continue_pressed")
		await process_frame
	game.call("_cycle_target")
	await process_frame
	await process_frame
	if game.get("_selected_target") == null:
		_fail("Manual target button did not select a target.")
		return
	if not target_label.visible or "футов" not in target_label.text or not distance_line.visible:
		_fail("Distance must appear only after manual target selection.")
		return

	var targets: Array = game.call("_available_targets") as Array
	for _index: int in range(targets.size()):
		game.call("_cycle_target")
		await process_frame
	if game.get("_selected_target") != null:
		_fail("Target cycling must return to free-aim mode after the final target.")
		return
	if target_label.visible or distance_line.visible:
		_fail("Distance overlay did not hide after returning to free aim.")
		return

	game.queue_free()
	await process_frame
	print("Free-aim combat smoke test passed.")
	quit(0)
