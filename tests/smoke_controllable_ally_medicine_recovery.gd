extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const MEDICINE_LABEL: String = "МЕДИЦИНА: СТАБИЛИЗИРОВАТЬ"

var _completed: bool = false
var _stage: String = "init"


func _init() -> void:
	call_deferred("_run")
	call_deferred("_watchdog")


func _watchdog() -> void:
	await create_timer(30.0).timeout
	if not _completed:
		_fail("Ally Medicine/recovery test timed out at stage: %s" % _stage)


func _run() -> void:
	_stage = "setup"
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	state.call("new_game")
	state.set("player_character", _make_hero())
	state.set("inventory", {})
	state.call("add_item", "healers_kit", 3, false)

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	var game: Node = packed.instantiate() if packed != null else null
	if game == null:
		_fail("Game scene could not be instantiated.")
		return
	root.add_child(game)
	for _frame: int in range(20):
		await process_frame

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var ally: ControllableAlly = game.call("get_controllable_ally_for_testing") as ControllableAlly
	if player == null or ally == null:
		_fail("Player or Irina fixture is missing.")
		return
	ally.global_position = player.global_position + Vector2(32.0, 0.0)
	ally.enter_dying()

	_stage = "exploration_action"
	var entries: Dictionary = game.call("get_action_catalog_entries_for_testing") as Dictionary
	if not _has_action_label(entries, MEDICINE_LABEL):
		_fail("Exploration action catalogue does not expose the Medicine action.")
		return

	_stage = "failed_check"
	var failed: Dictionary = game.call("attempt_controllable_ally_medicine_for_testing", 1) as Dictionary
	if bool(failed.get("success", true)) or bool(failed.get("medicine_success", true)):
		_fail("Natural 1 unexpectedly stabilized Irina: %s" % failed)
		return
	if ally.get_combatant_state().stable:
		_fail("Failed Medicine check changed Irina to stable.")
		return
	if int(state.call("get_item_count", "healers_kit")) != 2:
		_fail("Failed Medicine check did not consume exactly one kit use.")
		return

	_stage = "successful_check"
	var successful: Dictionary = game.call("attempt_controllable_ally_medicine_for_testing", 20) as Dictionary
	if not bool(successful.get("success", false)) or not bool(successful.get("medicine_success", false)):
		_fail("Natural 20 did not stabilize Irina: %s" % successful)
		return
	if not ally.get_combatant_state().stable or ally.current_health != 0:
		_fail("Successful Medicine check must stabilize without restoring HP.")
		return
	if not ally.get_combatant_state().has_condition("unconscious"):
		_fail("Stable Irina must remain unconscious at 0 HP.")
		return
	if int(state.call("get_item_count", "healers_kit")) != 1:
		_fail("Successful Medicine check did not consume exactly one kit use.")
		return

	_stage = "long_rest_recovery"
	game.call("recover_controllable_ally_after_long_rest_for_testing")
	await process_frame
	if ally.current_health != ally.maximum_health:
		_fail("Long rest did not restore Irina to full HP.")
		return
	if ally.get_combatant_state().stable:
		_fail("Long rest left the stale stabilization flag active.")
		return
	if ally.get_combatant_state().has_condition("unconscious") or ally.get_combatant_state().has_condition("incapacitated"):
		_fail("Long rest did not return living Irina to consciousness.")
		return

	_stage = "dead_not_revived"
	ally.enter_dying()
	ally.mark_dead()
	game.call("recover_controllable_ally_after_long_rest_for_testing")
	await process_frame
	if not ally.get_combatant_state().dead or ally.current_health != 0:
		_fail("Long rest improperly revived dead Irina.")
		return

	game.queue_free()
	await process_frame
	_completed = true
	print("Exploration Medicine action, kit consumption, stabilization and long-rest recovery passed.")
	quit(0)


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Полевой лекарь"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.maximum_health = 16
	hero.current_health = 16
	hero.abilities["wisdom"] = 10
	hero.starter_loadout_granted = true
	return hero


func _has_action_label(entries: Dictionary, expected: String) -> bool:
	for category_id: String in ["action", "bonus", "free", "reaction"]:
		var values: Variant = entries.get(category_id, [])
		if not values is Array:
			continue
		for value: Variant in values as Array:
			if value is Dictionary and str((value as Dictionary).get("label", "")) == expected:
				return true
	return false


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
