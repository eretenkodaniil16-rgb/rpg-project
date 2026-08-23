extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const REQUIRED_GAME_SCRIPT: String = "res://scripts/game/game_ai_stealth_v2_ui_runtime.gd"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	var game: Node = packed.instantiate() if packed != null else null
	if game == null:
		_fail("Game scene could not be instantiated.")
		return
	root.add_child(game)
	for _frame: int in range(20):
		await process_frame
	var script: Script = game.get_script() as Script
	if not _script_chain_contains(script, REQUIRED_GAME_SCRIPT):
		_fail("Game scene is not wired to AI/stealth v2 runtime.")
		return
	for method_name: String in [
		"set_exploration_stealth_total_v2_for_testing",
		"get_exploration_stealth_total_v2_for_testing",
		"resolve_passive_detection_v2_for_testing",
		"get_last_targeting_diagnostics_v2_for_testing"
	]:
		if not game.has_method(method_name):
			_fail("Missing AI/stealth v2 runtime method: %s" % method_name)
			return

	game.call("set_exploration_stealth_total_v2_for_testing", 18)
	game.call("_refresh_alert_indicator")
	if int(game.call("get_exploration_stealth_total_v2_for_testing")) != 18:
		_fail("Runtime did not retain the exploration Stealth total.")
		return
	if str(game.call("get_alert_indicator_text_for_testing")) != "СКРЫТ":
		_fail("AI v2 exposed internal Stealth DC in the global HUD.")
		return
	var safe: Dictionary = game.call(
		"resolve_passive_detection_v2_for_testing",
		18,
		12,
		20,
		true,
		false
	) as Dictionary
	if bool(safe.get("detected", true)):
		_fail("Integrated runtime did not respect Stealth greater than Passive Perception.")
		return
	var close: Dictionary = game.call(
		"resolve_passive_detection_v2_for_testing",
		18,
		12,
		5,
		true,
		false
	) as Dictionary
	if not bool(close.get("detected", false)):
		_fail("Integrated runtime has no close-contact reveal threshold.")
		return
	game.call("set_exploration_stealth_total_v2_for_testing", 0)
	if bool(game.call("is_exploration_hidden_for_testing")):
		_fail("Runtime failed to leave exploration stealth.")
		return
	game.queue_free()
	await process_frame
	print("AI/stealth v2 runtime smoke test passed.")
	quit(0)


func _script_chain_contains(script: Script, required_path: String) -> bool:
	var current: Script = script
	while current != null:
		if current.resource_path == required_path:
			return true
		current = current.get_base_script()
	return false


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
