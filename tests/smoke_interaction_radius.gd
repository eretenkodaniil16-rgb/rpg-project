extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const EPSILON: float = 0.1


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState is missing.")
		return
	state.call("new_game")
	state.set("player_character", PlayerCharacter.create_legacy_default())
	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	var game: Node = packed.instantiate() if packed != null else null
	if game == null:
		_fail("Game scene could not be instantiated.")
		return
	root.add_child(game)
	for _frame: int in range(24):
		await process_frame
	game.set_process(false)

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var caretaker: Node2D = game.get_node_or_null("Caretaker") as Node2D
	var room: Node = game.get_node_or_null("StealthTestRoom")
	var grid: BattleGrid = get_first_node_in_group("battle_grid") as BattleGrid
	var guard: Node2D = room.call("get_patrol_observer") as Node2D if room != null else null
	var marksman: Node2D = room.call("get_training_marksman") as Node2D if room != null else null
	var mage: Node2D = room.call("get_training_mage") as Node2D if room != null else null
	var door: StealthDoor = room.call("get_test_door") as StealthDoor if room != null else null
	if player == null or caretaker == null or guard == null or marksman == null or mage == null or door == null or grid == null:
		_fail("Interaction radius fixtures are incomplete.")
		return

	var required_radius: float = grid.get_cell_size()
	_assert_shape_reach("Caretaker", caretaker.get_node_or_null("InteractionArea/CollisionShape2D") as CollisionShape2D, required_radius)
	_assert_shape_reach("Service guard", guard.get_node_or_null("CollisionShape2D") as CollisionShape2D, required_radius)
	_assert_shape_reach("Marksman", marksman.get_node_or_null("CollisionShape2D") as CollisionShape2D, required_radius)
	_assert_shape_reach("Rune tactician", mage.get_node_or_null("CollisionShape2D") as CollisionShape2D, required_radius)
	var door_size: Vector2 = door.get_interaction_trigger_size_for_testing()
	if door_size.x * 0.5 + EPSILON < required_radius or door_size.y * 0.5 + EPSILON < required_radius:
		_fail("Door interaction trigger is smaller than one 5-foot cell radius: %s" % str(door_size))
		return

	# Verify the runtime registry, not only scene metadata. A player standing one
	# cell from the NPC centre must receive that NPC as an available world action.
	player.global_position = caretaker.global_position + Vector2(required_radius * 0.98, 0.0)
	state.set("player_position", player.global_position)
	for _frame: int in range(4):
		await physics_frame
	if not bool(player.call("has_registered_interactable", caretaker)):
		_fail("Caretaker is not registered from one 5-foot cell away.")
		return

	player.global_position = guard.global_position + Vector2(required_radius * 0.98, 0.0)
	state.set("player_position", player.global_position)
	for _frame: int in range(4):
		await physics_frame
	if not bool(player.call("has_registered_interactable", guard)):
		_fail("Service guard is not registered from one 5-foot cell away.")
		return

	print("NPC and door interaction triggers reach at least one 5-foot cell.")
	game.queue_free()
	await process_frame
	quit(0)


func _assert_shape_reach(label: String, collision: CollisionShape2D, required_radius: float) -> void:
	if collision == null or collision.shape == null:
		_fail("%s interaction collision is missing." % label)
		return
	var reach_x: float = 0.0
	var reach_y: float = 0.0
	if collision.shape is CircleShape2D:
		reach_x = (collision.shape as CircleShape2D).radius
		reach_y = reach_x
	elif collision.shape is RectangleShape2D:
		var size: Vector2 = (collision.shape as RectangleShape2D).size
		reach_x = size.x * 0.5
		reach_y = size.y * 0.5
	else:
		_fail("%s uses an unsupported interaction shape." % label)
		return
	if reach_x + EPSILON < required_radius or reach_y + EPSILON < required_radius:
		_fail("%s interaction reach is below one cell: %.1f x %.1f." % [label, reach_x, reach_y])


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
