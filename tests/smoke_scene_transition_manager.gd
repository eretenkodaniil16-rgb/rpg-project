extends SceneTree

const VISUAL_SCENE_PATH: String = "res://scenes/menus/loading_screen_visual_v02.tscn"
const MANAGER_SCRIPT_PATH: String = "res://scripts/systems/scene_transition_manager.gd"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var visual_resource: Resource = load(VISUAL_SCENE_PATH)
	assert(visual_resource is PackedScene)
	var visual: CanvasLayer = (visual_resource as PackedScene).instantiate() as CanvasLayer
	assert(visual != null)
	root.add_child(visual)
	await process_frame
	assert(visual.has_method("set_progress"))
	assert(visual.has_method("has_runtime_progress_bar"))
	assert(bool(visual.call("has_runtime_progress_bar")))
	assert(visual.has_method("has_approved_background"))
	assert(bool(visual.call("has_approved_background")))
	var approved_background: Control = visual.get_node("Root/ApprovedBackground") as Control
	assert(approved_background != null)
	assert(approved_background.visible)
	assert(approved_background.has_method("source_size"))
	assert(approved_background.call("source_size") == Vector2(1672.0, 941.0))
	assert(approved_background.has_method("texture_path"))
	assert(
		String(approved_background.call("texture_path"))
		== "res://assets/branding/loading_screen/approved/loading_screen_visual_v02/background/loading_screen_tower_blue_v02.png"
	)
	visual.call("set_progress", 50.0)
	var progress_label: Label = visual.get_node("Root/ProgressLabel") as Label
	var subtitle: Label = visual.get_node("Root/SubtitlePanel/Subtitle") as Label
	assert(progress_label.text == "50%")
	assert(subtitle.text == "Башня, уходящая вниз")
	visual.queue_free()
	await process_frame

	var manager_script: Script = load(MANAGER_SCRIPT_PATH) as Script
	assert(manager_script != null)
	var manager: Node = manager_script.new() as Node
	root.add_child(manager)
	await process_frame
	assert(manager.has_method("request_scene"))
	assert(manager.has_method("is_busy"))
	var accepted: bool = bool(manager.call("request_scene", "res://missing/scene_for_transition_test.tscn"))
	assert(not accepted)
	assert(not bool(manager.call("is_busy")))
	manager.queue_free()
	await process_frame

	print("Scene transition manager smoke test passed.")
	quit(0)
