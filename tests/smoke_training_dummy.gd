extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const STATUS_PATH: String = "res://build/test/training-dummy-status.txt"


func _init() -> void:
	call_deferred("_run")


func _write_status(message: String) -> void:
	var absolute_path: String = ProjectSettings.globalize_path(STATUS_PATH)
	DirAccess.make_dir_recursive_absolute(absolute_path.get_base_dir())
	var file: FileAccess = FileAccess.open(absolute_path, FileAccess.WRITE)
	if file != null:
		file.store_string(message)


func _fail(message: String) -> void:
	_write_status("failure: " + message)
	push_error(message)
	quit(1)


func _run() -> void:
	var game_state: Node = get_root().get_node_or_null("GameState")
	if game_state == null:
		_fail("GameState autoload is missing.")
		return

	var character := PlayerCharacter.new()
	character.character_name = "Боец"
	character.character_class_id = "fighter"
	character.character_class_name = "Воин"
	character.level = 1
	character.abilities["strength"] = 16
	game_state.set("player_character", character)
	game_state.set("player_position", Vector2(320.0, 360.0))
	game_state.set("input_locked", false)

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	if packed == null:
		_fail("Game scene failed to load.")
		return
	var game: Node = packed.instantiate()
	get_root().add_child(game)
	await process_frame
	await process_frame

	var dummy: Node = game.get_node_or_null("TrainingDummy")
	if dummy == null:
		var child_names: Array[String] = []
		for child: Node in game.get_children():
			child_names.append(child.name)
		var script_path: String = str((game.get_script() as Script).resource_path) if game.get_script() is Script else "no script"
		_fail("Training dummy was not created. script=%s children=%s" % [script_path, ",".join(child_names)])
		return
	if int(dummy.call("get_armor_class")) != 10 or int(dummy.call("get_current_health")) != 12:
		_fail("Training dummy has incorrect initial combat stats.")
		return

	var popup: Node = game.get_node_or_null("Interface/AttackResultPopup")
	if popup == null or bool(popup.get("visible")):
		_fail("Attack result popup was not initialized hidden.")
		return

	var result: Variant = dummy.call("attack_for_testing", 10)
	if result == null:
		_fail("Training attack returned no result.")
		return
	var damage: int = int(result.get("damage"))
	if not bool(result.get("hit")) or int(result.get("total")) != 15:
		_fail("Training weapon attack roll is incorrect: hit=%s total=%d." % [str(result.get("hit")), int(result.get("total"))])
		return
	if str(result.get("attack_name")) != "Двуручный меч" or damage < 5 or damage > 15:
		_fail("Fighter equipment or damage is incorrect: attack=%s damage=%d weapon=%s." % [str(result.get("attack_name")), damage, character.equipped_weapon_id])
		return
	if int(dummy.call("get_current_health")) != maxi(0, 12 - damage):
		_fail("Training dummy did not receive weapon damage: hp=%d damage=%d." % [int(dummy.call("get_current_health")), damage])
		return

	game.queue_free()
	await process_frame
	_write_status("success")
	print("Training dummy smoke test passed.")
	quit(0)
