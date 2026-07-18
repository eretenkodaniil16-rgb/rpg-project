extends SceneTree

const CHARACTER_CREATOR_SCENE: String = "res://scenes/character_creation/character_creator.tscn"


func _init() -> void:
	call_deferred("_run_smoke_test")


func _run_smoke_test() -> void:
	var packed_scene: PackedScene = load(CHARACTER_CREATOR_SCENE) as PackedScene
	assert(packed_scene != null)
	var creator: Node = packed_scene.instantiate()
	assert(creator != null)
	root.add_child(creator)
	await process_frame
	assert(creator.get_child_count() >= 2)
	var races_value: Variant = creator.get("_races")
	assert(races_value is Array)
	assert((races_value as Array).size() == 9)
	creator.call("_show_step", 1)
	await process_frame
	var content: VBoxContainer = creator.get("_content_container") as VBoxContainer
	assert(content != null)
	var race_grid: GridContainer = null
	for child: Node in content.get_children():
		if child is GridContainer:
			race_grid = child as GridContainer
			break
	assert(race_grid != null)
	assert(race_grid.get_child_count() == 9)
	creator.call("_select_race", "tiefling")
	await process_frame
	assert(str(creator.get("_selected_race_id")) == "tiefling")
	assert(str(creator.get("_title_label").text) == "Выбор расы")
	print("Character creator race selection smoke test passed.")
	creator.queue_free()
	quit(0)
