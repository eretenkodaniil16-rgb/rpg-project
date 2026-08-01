extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	_cleanup_saves(state)
	state.call("new_game")
	state.set("player_character", _make_hero())

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	var game: Node = packed.instantiate() if packed != null else null
	if game == null:
		_fail("Game scene could not be instantiated.")
		return
	root.add_child(game)
	for _frame: int in range(45):
		await process_frame

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var caretaker: Node = game.get_node_or_null("Caretaker")
	var room: GuardPostTwoRoomVisibility = game.get_node_or_null("StealthTestRoom") as GuardPostTwoRoomVisibility
	var fog: RoomFogOverlay = room.get_room_fog_for_testing() if room != null else null
	var inner_gate: StealthDoor = room.get_inner_gate() if room != null else null
	var pause_menu: GamePauseSaveMenu = game.call("get_pause_save_menu_for_testing") as GamePauseSaveMenu
	if player == null or caretaker == null or room == null or fog == null or inner_gate == null or pause_menu == null:
		_fail("Visibility or save-menu runtime fixtures are incomplete.")
		return

	game.call("return_to_menu")
	await process_frame
	if not pause_menu.is_menu_open() or not bool(state.get("input_locked")):
		_fail("Menu button did not open the in-game pause/save panel.")
		return
	if not pause_menu.is_save_available_for_testing() or not pause_menu.is_main_menu_available_for_testing():
		_fail("Exploration menu incorrectly disabled stable save actions.")
		return
	pause_menu.close_menu()
	await process_frame
	if pause_menu.is_menu_open() or bool(state.get("input_locked")):
		_fail("Closing the pause menu did not restore gameplay input.")
		return

	var partition_x: float = room.get_inner_partition_global_x()
	var observer_position := Vector2(partition_x - 96.0, 360.0)
	var concealed_position := Vector2(partition_x + 96.0, 360.0)
	player.global_position = observer_position
	state.set("player_position", observer_position)
	inner_gate.set_door_state("closed", false)
	for _frame: int in range(5):
		await process_frame
	fog.force_refresh_for_testing()
	if fog.is_world_position_visible(concealed_position):
		_fail("Closed inner gate did not block the hero's field of view.")
		return
	inner_gate.set_door_state("open", false)
	for _frame: int in range(5):
		await process_frame
	fog.force_refresh_for_testing()
	if not fog.is_world_position_visible(concealed_position):
		_fail("Opening the inner gate did not reveal the cells behind it.")
		return
	if fog.is_world_position_visible(observer_position + Vector2(fog.get_vision_radius_for_testing() + 96.0, 0.0)):
		_fail("Visibility exceeded the configured hero vision radius.")
		return

	state.get("player_character").current_health = 29
	state.set("player_position", observer_position)
	if not bool(state.call("save_manual_slot", 3)):
		_fail("Manual save slot could not be created from the in-game state.")
		return
	state.get("player_character").current_health = 4
	state.set("player_position", concealed_position)
	if not bool(state.call("save_game")):
		_fail("Autosave could not be updated after the manual checkpoint.")
		return
	if not bool(state.call("load_last_manual_save")):
		_fail("Last manual save could not be loaded for death rollback.")
		return
	var restored_character: PlayerCharacter = state.get("player_character") as PlayerCharacter
	if restored_character.current_health != 29 or (state.get("player_position") as Vector2) != observer_position:
		_fail("Death rollback contract restored autosave data instead of the manual checkpoint.")
		return

	game.call("_start_turn_based_combat", caretaker)
	game.call("force_player_turn_for_testing")
	await process_frame
	game.call("return_to_menu")
	await process_frame
	if not pause_menu.is_menu_open():
		_fail("Pause menu was not available during active combat.")
		return
	if pause_menu.is_save_available_for_testing() or pause_menu.is_main_menu_available_for_testing():
		_fail("Pause menu allowed an incomplete checkpoint or menu exit during active initiative.")
		return
	if "боя" not in pause_menu.get_save_status_for_testing():
		_fail("Combat save restriction did not explain why the checkpoint is unavailable.")
		return
	pause_menu.close_menu()
	var turn_system: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	if turn_system != null:
		turn_system.stop_combat()
	if player.has_method("set_turn_based_mode"):
		player.call("set_turn_based_mode", false)
	await process_frame

	restored_character.current_health = 0
	if bool(state.call("save_game")):
		_fail("Autosave accepted an invalid zero-HP death state.")
		return

	game.queue_free()
	await process_frame
	_cleanup_saves(state)
	print("Obstacle-aware visibility, stable pause saves, combat restriction and manual death rollback passed.")
	quit(0)


func _cleanup_saves(state: Node) -> void:
	for slot_id: int in range(1, SaveSlotSystem.MANUAL_SLOT_COUNT + 1):
		state.call("delete_manual_save_slot", slot_id)
	state.call("discard_autosave")


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель видимости"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.level = 5
	hero.maximum_health = 42
	hero.current_health = 42
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
