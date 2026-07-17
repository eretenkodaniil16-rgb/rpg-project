extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"


func _init() -> void:
	call_deferred("_run_smoke_test")


func _run_smoke_test() -> void:
	var character: PlayerCharacter = PlayerCharacter.new()
	character.character_name = "Арден"
	character.character_class_id = "fighter"
	character.character_class_name = "Воин"
	character.appearance_color_hex = "#9368D8"
	character.maximum_health = 10
	character.current_health = 10
	GameState.begin_new_game(character)

	var packed_scene: PackedScene = load(GAME_SCENE) as PackedScene
	assert(packed_scene != null)
	var game: Node = packed_scene.instantiate()
	assert(game != null)
	root.add_child(game)
	await process_frame

	var player: CharacterBody2D = game.get_node("Player") as CharacterBody2D
	assert(player != null)
	var name_label: Label = player.get_node("NameLabel") as Label
	var body: Polygon2D = player.get_node("Body") as Polygon2D
	assert(name_label.text == "Арден")
	assert(body.color.is_equal_approx(Color.from_string("#9368D8", Color.WHITE)))

	var start_x: float = player.global_position.x
	player.call("set_mobile_vector", Vector2.RIGHT)
	await physics_frame
	await physics_frame
	player.call("clear_mobile_input")
	assert(player.global_position.x > start_x)

	print("Player runtime smoke test passed.")
	game.queue_free()
	quit(0)
