extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"

func _init() -> void:
	call_deferred("_run_test")

func _run_test() -> void:
	var game_state: Node = root.get_node_or_null("GameState")
	assert(game_state != null)

	var character: PlayerCharacter = PlayerCharacter.create_legacy_default()
	character.character_name = "Арден"
	game_state.call("begin_new_game", character)

	var game: Node = (load(GAME_SCENE) as PackedScene).instantiate()
	root.add_child(game)
	await process_frame

	var player: CharacterBody2D = game.get_node("Player") as CharacterBody2D
	var name_label: Label = game.get_node("Player/NameLabel") as Label
	if player.has_method("apply_character_appearance"):
		player.call("apply_character_appearance")
	await process_frame

	assert(name_label.text == "Арден")
	print("Player name smoke test passed.")
	game.queue_free()
	quit(0)
