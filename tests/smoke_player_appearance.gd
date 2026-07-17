extends SceneTree

const PLAYER_SCRIPT: Script = preload("res://scripts/game/player.gd")


func _init() -> void:
	call_deferred("_run_test")


func _run_test() -> void:
	var character: PlayerCharacter = PlayerCharacter.new()
	character.character_name = "Арден"
	character.character_class_id = "fighter"
	character.character_class_name = "Воин"
	character.appearance_color_hex = "#9368D8"
	GameState.begin_new_game(character)

	var player: CharacterBody2D = CharacterBody2D.new()
	player.name = "Player"
	var body: Polygon2D = Polygon2D.new()
	body.name = "Body"
	player.add_child(body)
	var name_label: Label = Label.new()
	name_label.name = "NameLabel"
	player.add_child(name_label)
	player.set_script(PLAYER_SCRIPT)
	root.add_child(player)
	await process_frame

	assert(name_label.text == "Арден")
	assert(body.color.is_equal_approx(Color.from_string("#9368D8", Color.WHITE)))
	print("Player appearance smoke test passed.")
	player.queue_free()
	quit(0)
