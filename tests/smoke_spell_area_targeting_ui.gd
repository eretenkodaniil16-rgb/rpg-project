extends SceneTree

var _finished: bool = false


func _init() -> void:
	call_deferred("_run")
	call_deferred("_watchdog")


func _fail(message: String) -> void:
	_finished = true
	push_error(message)
	quit(1)


func _watchdog() -> void:
	await create_timer(35.0).timeout
	if not _finished:
		_fail("Spell area targeting UI smoke test timed out after 35 seconds.")


func _run() -> void:
	var game_state: Node = root.get_node_or_null("GameState")
	if game_state == null:
		_fail("GameState autoload was unavailable.")
		return
	game_state.call("new_game")
	var wizard := PlayerCharacter.new()
	wizard.character_name = "Пиромант"
	wizard.character_class_id = "wizard"
	wizard.character_class_name = "Волшебник"
	wizard.race_name = "Человек"
	wizard.level = 5
	wizard.abilities["intelligence"] = 18
	wizard.base_abilities["intelligence"] = 18
	game_state.set("player_character", wizard)

	var game_scene: PackedScene = load("res://scenes/game/game.tscn") as PackedScene
	if game_scene == null:
		_fail("Game scene could not be loaded.")
		return
	var game: Node = game_scene.instantiate()
	root.add_child(game)
	for _frame: int in range(8):
		await process_frame

	var burning_hands: Dictionary = ClassDataSystem.new().get_ability_definition("burning_hands")
	if burning_hands.is_empty():
		_fail("Burning Hands definition was unavailable in the running game.")
		return
	game.call("_begin_spell_area_targeting", burning_hands)
	for _frame: int in range(3):
		await process_frame

	var confirm_button: Button = game.get("_spell_area_confirm_button") as Button
	var cancel_button: Button = game.get("_spell_area_cancel_button") as Button
	var grid: BattleGrid = get_first_node_in_group("battle_grid") as BattleGrid
	if confirm_button == null or cancel_button == null or grid == null:
		_fail("Spell-area confirmation controls or BattleGrid were not constructed.")
		return
	if not confirm_button.is_visible_in_tree() or not cancel_button.is_visible_in_tree():
		_fail("Spell-area confirmation controls were not visible during targeting.")
		return
	if not grid.is_spell_area_preview_active() or grid.get_spell_area_preview_cells().is_empty():
		_fail("Entering area targeting did not create a visible grid preview.")
		return
	if confirm_button.text.find("ЦЕЛЕЙ") < 0:
		_fail("Area confirmation did not display the current target count.")
		return

	var player: Node2D = get_first_node_in_group("player") as Node2D
	if player == null:
		_fail("Player node was unavailable to update the targeting direction.")
		return
	game.call("_set_spell_area_aim_world", player.global_position + Vector2.RIGHT * DistanceSystem.feet_to_pixels(15))
	await process_frame
	if grid.get_spell_area_preview_cells().is_empty():
		_fail("Changing the aim direction removed the area preview.")
		return

	game_state.set("input_locked", true)
	await process_frame
	game_state.set("input_locked", false)
	if confirm_button.visible or cancel_button.visible or grid.is_spell_area_preview_active():
		_fail("Opening another input-locking interface did not clear area targeting.")
		return

	game.call("_begin_spell_area_targeting", burning_hands)
	await process_frame
	if not grid.is_spell_area_preview_active():
		_fail("Area targeting could not be started again after overlay cleanup.")
		return
	game.call("_advance_combat_turn")
	await process_frame
	if confirm_button.visible or cancel_button.visible or grid.is_spell_area_preview_active():
		_fail("Advancing combat did not clear area targeting state.")
		return

	var point_spell: Dictionary = burning_hands.duplicate(true)
	point_spell["area"] = {"shape": "sphere", "origin": "point", "radius_ft": 5}
	point_spell["range_ft"] = 30
	game.set("_pending_area_spell", point_spell)
	game.set("_spell_area_targeting_active", true)
	game.call("_set_spell_area_aim_world", player.global_position)
	var expected_origin: Vector2i = grid.world_to_cell(player.global_position)
	var actual_origin: Vector2i = game.get("_pending_area_origin_cell")
	if actual_origin != expected_origin:
		_fail("A point-origin area selected in the caster cell was displaced to a neighboring cell.")
		return
	game.call("_cancel_spell_area_targeting")

	game.call("_begin_spell_area_targeting", burning_hands)
	await process_frame
	var slots_before: int = wizard.get_resource("spell_slots_1")
	if slots_before <= 0:
		_fail("Wizard had no level-one slot for double-confirmation regression test.")
		return
	game.call("_confirm_spell_area")
	if not confirm_button.disabled:
		_fail("Area confirmation button was not disabled before the casting animation await.")
		return
	game.call("_confirm_spell_area")
	await create_timer(0.6).timeout
	if wizard.get_resource("spell_slots_1") != slots_before - 1:
		_fail("A rapid double confirmation consumed more than one spell slot.")
		return
	if confirm_button.visible or cancel_button.visible or grid.is_spell_area_preview_active():
		_fail("Completed area casting did not clear controls and preview.")
		return

	game.call("_begin_spell_area_targeting", burning_hands)
	await process_frame
	game.call("_cancel_spell_area_targeting")
	await process_frame
	if confirm_button.visible or cancel_button.visible or grid.is_spell_area_preview_active():
		_fail("Explicit cancellation did not clear controls and preview.")
		return

	_finished = true
	game.queue_free()
	print("Spell area targeting UI, point origin, atomic confirmation, and lifecycle cleanup smoke test passed.")
	quit(0)
