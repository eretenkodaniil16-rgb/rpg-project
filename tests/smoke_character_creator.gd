extends SceneTree

const CHARACTER_CREATOR_SCENE: String = "res://scenes/character_creation/character_creator.tscn"


func _init() -> void:
	call_deferred("_run_smoke_test")


func _run_smoke_test() -> void:
	var packed_scene: PackedScene = load(CHARACTER_CREATOR_SCENE) as PackedScene
	if packed_scene == null:
		push_error("Character creator scene failed to load.")
		quit(1)
		return
	var creator: Node = packed_scene.instantiate()
	if creator == null:
		push_error("Character creator scene failed to instantiate.")
		quit(1)
		return
	root.add_child(creator)
	await process_frame
	print("Character creator scene smoke test passed.")
	creator.queue_free()
	quit(0)
