extends SceneTree

const RUNTIME_PATH: String = "res://scripts/game/game_combat_ai_coordination_v2_runtime.gd"


func _init() -> void:
	var runtime_script: Script = load(RUNTIME_PATH) as Script
	if runtime_script == null or not runtime_script.can_instantiate():
		push_error("Combat AI Coordination v2 runtime failed direct load: %s" % RUNTIME_PATH)
		quit(1)
		return
	print("Combat AI Coordination v2 runtime direct load passed.")
	quit(0)