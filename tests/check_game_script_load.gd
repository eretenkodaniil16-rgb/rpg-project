extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var script: Script = load("res://scripts/game/game.gd") as Script
	if script == null:
		push_error("scripts/game/game.gd failed to load.")
		quit(1)
		return
	print("Game script load check passed: %s" % script.resource_path)
	quit(0)
