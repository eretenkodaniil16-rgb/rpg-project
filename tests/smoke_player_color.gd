extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"

func _init() -> void:
	call_deferred("_run_test")

func _run_test() -> void:
	var game_state: Node = root.get_node_or_null("GameState")
	if game_state == null:
		push_error("GameState is missing.")
		quit(1)
		return

	var character: PlayerCharacter = PlayerCharacter.create_legacy_default()
	RaceDataSystem.new().apply_race(character, "tiefling")
	game_state.call("begin_new_game", character)

	var game: Node = (load(GAME_SCENE) as PackedScene).instantiate()
	root.add_child(game)
	await process_frame
	var body: Polygon2D = game.get_node("Player/Body") as Polygon2D
	if body.color.to_html(false).to_upper() != "9368D8":
		push_error("Player color does not match the selected Tiefling race.")
		quit(1)
		return
	print("Race-defined player color smoke test passed.")
	game.queue_free()
	quit(0)
