extends SceneTree

const RUNTIME_PATH: String = "res://scripts/game/game_combat_ai_coordination_v1_runtime.gd"


func _init() -> void:
	var runtime_script: Script = load(RUNTIME_PATH) as Script
	if runtime_script == null:
		push_error("Combat AI Coordination v1 runtime failed direct load: %s" % RUNTIME_PATH)
		quit(1)
		return
	print("Combat AI Coordination v1 runtime direct load passed.")
	quit(0)
