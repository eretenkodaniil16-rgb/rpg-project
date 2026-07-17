extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const DIAGNOSTIC_PATH: String = "res://build/test/player-name.log"

func _init() -> void:
	call_deferred("_run_test")

func _run_test() -> void:
	var character: PlayerCharacter = PlayerCharacter.create_legacy_default()
	character.character_name = "Арден"
	GameState.begin_new_game(character)
	var game: Node = (load(GAME_SCENE) as PackedScene).instantiate()
	root.add_child(game)
	await process_frame
	var player: CharacterBody2D = game.get_node("Player") as CharacterBody2D
	var name_label: Label = game.get_node("Player/NameLabel") as Label
	if player.has_method("apply_character_appearance"):
		player.call("apply_character_appearance")
	await process_frame

	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://build/test"))
	var diagnostic: FileAccess = FileAccess.open(DIAGNOSTIC_PATH, FileAccess.WRITE)
	if diagnostic != null:
		diagnostic.store_line("state_name=%s" % GameState.player_character.character_name)
		diagnostic.store_line("label_text=%s" % name_label.text)
		diagnostic.store_line("has_apply_method=%s" % str(player.has_method("apply_character_appearance")))
		var script_value: Script = player.get_script() as Script
		diagnostic.store_line("script_path=%s" % (script_value.resource_path if script_value != null else "none"))

	assert(name_label.text == "Арден")
	print("Player name smoke test passed.")
	game.queue_free()
	quit(0)
