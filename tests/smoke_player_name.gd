extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"

func _init() -> void:
	call_deferred("_run_test")

func _run_test() -> void:
	var character: PlayerCharacter = PlayerCharacter.create_legacy_default()
	character.character_name = "Арден"
	GameState.begin_new_game(character)
	var game: Node = (load(GAME_SCENE) as PackedScene).instantiate()
	root.add_child(game)
	await process_frame
	var name_label: Label = game.get_node("Player/NameLabel") as Label
	assert(name_label.text == "Арден")
	print("Player name smoke test passed.")
	game.queue_free()
	quit(0)
