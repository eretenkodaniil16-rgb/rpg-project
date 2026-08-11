extends SceneTree

const DEMO_SCENE: String = "res://scenes/game/environment/cold_ancient_stone_demo_v01.tscn"
const GAME_SCENE: String = "res://scenes/game/game.tscn"
const OUTPUT_ROOT: String = "res://build/environment-integration-v01"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var output_absolute: String = ProjectSettings.globalize_path(OUTPUT_ROOT)
	var make_error: Error = DirAccess.make_dir_recursive_absolute(output_absolute)
	if make_error != OK:
		_fail("Cannot create review output directory: %s" % error_string(make_error))
		return

	var demo: Node = _instantiate(DEMO_SCENE)
	if demo == null:
		_fail("Cannot instantiate environment demo scene.")
		return
	root.add_child(demo)
	for _frame: int in range(6):
		await process_frame
	if not await _capture("%s/cold_ancient_stone_demo_v01.png" % OUTPUT_ROOT):
		return
	demo.queue_free()
	await process_frame

	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	state.call("discard_autosave")
	state.call("new_game")
	state.set("player_character", _make_hero())
	state.set("player_position", Vector2(650.0, 360.0))
	var game: Node = _instantiate(GAME_SCENE)
	if game == null:
		_fail("Cannot instantiate game scene.")
		return
	root.add_child(game)
	for _frame: int in range(55):
		await process_frame
	var room := game.get_node_or_null("StealthTestRoom") as GuardPostEnvironmentIntegration
	if room == null or not room.is_environment_visual_ready_for_testing():
		_fail("Game scene fell back instead of installing approved environment art.")
		return
	if not await _capture("%s/guard_post_environment_v01.png" % OUTPUT_ROOT):
		return
	game.queue_free()
	await process_frame
	state.call("discard_autosave")
	print("Environment review captures written to %s" % OUTPUT_ROOT)
	quit(0)


func _capture(path: String) -> bool:
	RenderingServer.force_draw(false)
	await process_frame
	var image: Image = root.get_texture().get_image()
	if image == null or image.is_empty():
		_fail("Viewport capture is empty: %s" % path)
		return false
	var save_error: Error = image.save_png(ProjectSettings.globalize_path(path))
	if save_error != OK:
		_fail("Cannot save review capture %s: %s" % [path, error_string(save_error)])
		return false
	return true


func _instantiate(path: String) -> Node:
	var packed := ResourceLoader.load(path, "PackedScene") as PackedScene
	return packed.instantiate() if packed != null else null


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель окружения"
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
