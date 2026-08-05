extends SceneTree

const CORRECT_SUBTITLE: String = "Башня, уходящая вниз"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var packed: PackedScene = load("res://scenes/menus/loading_screen_composite_preview_v01.tscn")
	if packed == null:
		push_error("Failed to load loading screen composite preview scene")
		quit(1)
		return

	var root_node: Control = packed.instantiate()
	root.add_child(root_node)
	await process_frame

	var background: TextureRect = root_node.get_node_or_null("Background") as TextureRect
	var loading_label: Label = root_node.get_node_or_null("LoadingLabel") as Label
	var subtitle: Label = root_node.get_node_or_null("SubtitleCorrection/Subtitle") as Label
	var progress_bar: Node = root_node.get_node_or_null("LoadingProgressBar")
	if background == null or background.texture == null:
		push_error("Composite preview is missing background texture")
		quit(1)
		return
	if loading_label == null or loading_label.text != "Загрузка...":
		push_error("Composite preview loading label mismatch")
		quit(1)
		return
	if subtitle == null or subtitle.text != CORRECT_SUBTITLE:
		push_error("Composite preview subtitle spelling mismatch")
		quit(1)
		return
	if progress_bar == null or not progress_bar.has_method("set_progress"):
		push_error("Composite preview is missing modular loading bar")
		quit(1)
		return

	progress_bar.call("set_progress", 50.0)
	await process_frame
	print("Loading screen composite smoke test passed")
	quit()
