extends SceneTree

const TARGET_SCRIPT_PATH: String = "res://scripts/game/game_combat_ai_targeting_v3_runtime.gd"


func _init() -> void:
	var source: String = FileAccess.get_file_as_string(TARGET_SCRIPT_PATH)
	if source.is_empty():
		push_error("Targeting v3 source could not be read.")
		quit(1)
		return
	var script := GDScript.new()
	script.source_code = source
	script.take_over_path(TARGET_SCRIPT_PATH)
	var result: Error = script.reload(true)
	if result != OK:
		push_error("Targeting v3 direct compile failed with error code %d." % int(result))
		quit(1)
		return
	print("Combat AI Targeting v3 direct compile passed.")
	quit(0)
