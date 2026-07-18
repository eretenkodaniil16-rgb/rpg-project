extends SceneTree

const CHARACTER_CREATOR_SCENE: String = "res://scenes/character_creation/character_creator.tscn"


func _init() -> void:
	call_deferred("_run_smoke_test")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run_smoke_test() -> void:
	var packed_scene: PackedScene = load(CHARACTER_CREATOR_SCENE) as PackedScene
	if packed_scene == null:
		_fail("Character creator scene failed to load.")
		return
	var creator: Node = packed_scene.instantiate()
	if creator == null:
		_fail("Character creator scene failed to instantiate.")
		return
	root.add_child(creator)
	await process_frame
	var races_value: Variant = creator.get("_races")
	if not races_value is Array or (races_value as Array).size() != 9:
		_fail("Character creator did not load nine races.")
		return
	creator.call("_show_step", 1)
	await process_frame
	var content: VBoxContainer = creator.get("_content_container") as VBoxContainer
	if content == null:
		_fail("Character creator content container is missing.")
		return
	var race_grid: GridContainer = null
	for child: Node in content.get_children():
		if child is GridContainer:
			race_grid = child as GridContainer
			break
	if race_grid == null or race_grid.get_child_count() != 9:
		_fail("Race selection grid does not contain nine cards.")
		return
	creator.call("_select_race", "tiefling")
	await process_frame
	if str(creator.get("_selected_race_id")) != "tiefling":
		_fail("Race selection was not stored.")
		return
	var title_label: Label = creator.get("_title_label") as Label
	if title_label == null or title_label.text != "Выбор расы":
		_fail("Race step title is incorrect.")
		return
	print("Character creator race selection smoke test passed.")
	creator.queue_free()
	await process_frame
	quit(0)
