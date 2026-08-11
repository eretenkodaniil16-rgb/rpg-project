extends SceneTree

const SCENE: PackedScene = preload("res://scenes/menus/loading_screen_visual_v02.tscn")
const EXPECTED_SOURCE_SIZE: Vector2 = Vector2(768.0, 432.0)
const EXPECTED_TILE_COUNT: int = 1


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var instance: Node = SCENE.instantiate()
	root.add_child(instance)
	await process_frame
	await process_frame

	var background: Control = instance.get_node_or_null("Root/ApprovedBackground") as Control
	assert(background != null, "ApprovedBackground is missing")
	assert(background.has_method("has_complete_tiles"), "ApprovedBackground contract is missing")
	assert(bool(background.call("has_complete_tiles")), "Approved loading pixel master is incomplete")
	assert(int(background.call("expected_tile_count")) == EXPECTED_TILE_COUNT, "Unexpected approved texture count")
	assert(Vector2(background.call("source_size")) == EXPECTED_SOURCE_SIZE, "Unexpected approved source size")

	var progress_bar: Control = instance.get_node_or_null("Root/LoadingProgressBar") as Control
	assert(progress_bar != null, "LoadingProgressBar is missing")
	assert(progress_bar.has_method("set_progress"), "Runtime progress contract is missing")
	progress_bar.call("set_progress", 50.0)

	var progress_label: Label = instance.get_node_or_null("Root/ProgressLabel") as Label
	assert(progress_label != null, "ProgressLabel is missing")
	instance.call("set_progress", 50.0)
	assert(progress_label.text == "50%", "Live loading percentage was not updated")

	print("LOADING_SCREEN_APPROVED_COMPOSITE_V03_SMOKE_OK")
	instance.queue_free()
	quit(0)
