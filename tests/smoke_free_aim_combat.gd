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

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var caretaker: Node2D = game.get_node_or_null("Caretaker") as Node2D
	var target_label: Label = game.find_child("TargetLabel", true, false) as Label
	var combat_message: Label = game.find_child("CombatMessageLabel", true, false) as Label
	var grid: Node = game.get_node_or_null("BattleGrid")
	if player == null or caretaker == null or target_label == null or combat_message == null or grid == null:
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

	var character: PlayerCharacter = state.get("player_character") as PlayerCharacter
	var original_weapon: String = character.equipped_weapon_id
	var original_caretaker_position: Vector2 = caretaker.global_position
	var melee_weapon: Dictionary = state.call("get_item_definition", "shortsword") as Dictionary
	caretaker.global_position = player.global_position + Vector2(64.0, 0.0)
	player.call("set_facing_direction", Vector2.RIGHT)
	var predicted_melee: Node = game.call("_find_directional_melee_target", melee_weapon) as Node
	if predicted_melee != caretaker:
		_fail("Target-free melee direction did not detect a nearby character.")
		return
	if not bool(game.call("_weapon_attempt_is_valid", melee_weapon, null, predicted_melee)):
		_fail("Target-free melee attack was rejected by turn-action validation.")
		return
	if not bool(game.call("_weapon_attempt_is_valid", melee_weapon, null, null)):
		_fail("An empty melee swing must still be a valid attack attempt.")
		return

	caretaker.global_position = original_caretaker_position
	character.equipped_weapon_id = "shortsword"
	player.call("set_facing_direction", Vector2.LEFT)
	game.call("_request_attack")
	await create_timer(0.45).timeout
	if game.get("_selected_target") != null:
		_fail("Target-free melee swing silently selected a target.")
		return
	if "никого не задел" not in combat_message.text:
		_fail("Target-free melee swing did not complete into empty space.")
		return

	character.equipped_weapon_id = original_weapon if not original_weapon.is_empty() else "longbow"
	player.call("set_facing_direction", Vector2.RIGHT)
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
	if not target_label.visible or "футов" not in target_label.text or "здоровье" not in target_label.text or "HP" in target_label.text or not distance_line.visible:
		_fail("Russian distance and health text must appear only after manual target selection.")
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
	print("Target-free melee and ranged combat smoke test passed.")
	quit(0)
