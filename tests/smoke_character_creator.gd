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
	print("Character creator scene smoke test passed.")
	creator.queue_free()
	quit(0)
