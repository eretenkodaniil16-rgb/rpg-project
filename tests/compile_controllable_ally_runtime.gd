extends SceneTree

const SCRIPT_PATHS: Array[String] = [
	"res://scripts/game/controllable_ally.gd",
	"res://scripts/game/game_controllable_ally_runtime.gd",
	"res://scripts/game/game_guard_post_polish_runtime.gd"
]


func _init() -> void:
	for script_path: String in SCRIPT_PATHS:
		print("Compiling: %s" % script_path)
		var resource: Resource = load(script_path)
		if resource == null:
			push_error("Failed to compile: %s" % script_path)
			quit(1)
			return
	print("Controllable ally scripts compiled in project/autoload context.")
	quit(0)
