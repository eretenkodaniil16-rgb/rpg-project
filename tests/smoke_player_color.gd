extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"

func _init() -> void:
	call_deferred("_run_test")

func _run_test() -> void:
	var character: PlayerCharacter = PlayerCharacter.create_legacy_default()
	character.appearance_color_hex = "#9368D8"
	GameState.begin_new_game(character)
	var game: Node = (load(GAME_SCENE) as PackedScene).instantiate()
	root.add_child(game)
	await process_frame
	var body: Polygon2D = game.get_node("Player/Body") as Polygon2D
	assert(body.color.to_html(false).to_upper() == "9368D8")
	print("Player color smoke test passed.")
	game.queue_free()
	quit(0)
