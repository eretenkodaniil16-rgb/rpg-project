extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"


func _init() -> void:
	call_deferred("_run_test")


func _run_test() -> void:
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
	var body: Polygon2D = player.get_node("Body") as Polygon2D
	var name_label: Label = player.get_node("NameLabel") as Label
	assert(name_label.text == "Арден")
	assert(body.color.is_equal_approx(Color.from_string("#9368D8", Color.WHITE)))
	print("Player appearance smoke test passed.")
	game.queue_free()
	quit(0)
