extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const RUNTIME_PATH: String = "res://scripts/game/game_guard_post_polish_runtime.gd"
const ENCOUNTER_ID: String = "training_construct"
const AUTOSAVE_PATH: String = "user://save_slots/autosave.json"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("Encounter-aware GameState is missing.")
		return
	var save_path: String = ProjectSettings.globalize_path(AUTOSAVE_PATH)
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	state.call("new_game")
	var hero: PlayerCharacter = _make_hero()
	state.set("player_character", hero)

	var scene: PackedScene = load(GAME_SCENE) as PackedScene
	var game: Node = scene.instantiate() if scene != null else null
	if game == null:
		_fail("Game scene could not be loaded.")
		return
	root.add_child(game)
	for _frame: int in range(20):
		await process_frame
	if str(game.get_script().resource_path) != RUNTIME_PATH:
		_fail("Game scene does not use the stable guard-post runtime facade with hide pursuit.")
		return

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var caretaker: Node = game.get_node_or_null("Caretaker")
	var guard: Node = game.call("get_patrol_actor_for_testing", "service_guard") as Node
	var grid: BattleGrid = get_first_node_in_group("battle_grid") as BattleGrid
	if player == null or caretaker == null or guard == null or grid == null:
		_fail("Player, observers or battle grid is missing.")
		return

	(caretaker as Node2D).global_position = Vector2(930.0, 555.0)
	(guard as Node2D).global_position = Vector2(930.0, 470.0)
	player.global_position = grid.cell_to_world_center(Vector2i(11, 8))
	state.set("player_position", player.global_position)
	var begin_result: Dictionary = state.call(
		"begin_encounter",
		ENCOUNTER_ID,
		{"source_type": "hide_pursuit_smoke", "source_id": "successful_hide"},
		false,
		false
	) as Dictionary
	if not bool(begin_result.get("success", false)) and not bool(begin_result.get("duplicate", false)):
		_fail("Training encounter could not begin.")
		return
	game.call("_start_turn_based_combat", caretaker)
	game.set("_active_combat_encounter_id", ENCOUNTER_ID)
	game.call("force_player_turn_for_testing")
	await process_frame
	if not bool(game.call("is_turn_based_combat_active")):
		_fail("Turn-based combat did not start.")
		return

	game.call("set_hide_roll_overrides_for_testing", [20])
	game.call("_on_hide_requested")
	for _frame: int in range(3):
		await process_frame
	if bool(game.call("is_turn_based_combat_active")):
		_fail("Successful Hide did not end initiative immediately.")
		return
	if not bool(game.call("is_exploration_hidden_for_testing")):
		_fail("Successful combat Hide was not transferred to exploration.")
		return
	if str(state.call("get_encounter_status", ENCOUNTER_ID)) != EncounterSystem.STATUS_ACTIVE:
		_fail("Hide incorrectly resolved or abandoned the active encounter.")
		return
	if hero.experience != 0 or int(state.call("get_item_count", "straw_scrap")) != 0:
		_fail("Hide transition granted victory rewards.")
		return

	for actor_id: String in ["caretaker", "service_guard"]:
		var record: Dictionary = state.call("get_stealth_alert_record", actor_id) as Dictionary
		if str(record.get("state", "")) not in [
			StealthAlertSystem.STATE_INVESTIGATING,
			StealthAlertSystem.STATE_SEARCHING
		]:
			_fail("Observer %s did not retain an active post-hide search state." % actor_id)
			return

	var caretaker_before_search: Vector2 = (caretaker as Node2D).global_position
	var guard_before_search: Vector2 = (guard as Node2D).global_position
	game.call("force_exploration_alert_tick_for_testing", 0.5)
	if (caretaker as Node2D).global_position.distance_to(caretaker_before_search) > 0.1:
		_fail("Stationary caretaker abandoned the post during hide pursuit.")
		return
	if (guard as Node2D).global_position.distance_to(guard_before_search) <= 0.1:
		_fail("Patrolling service guard did not move toward the last known position.")
		return

	# Reacquisition starts a fresh initiative without an unconditional advantage.
	game.call("_break_exploration_hidden", "")
	player.global_position = Vector2(700.0, 360.0)
	state.set("player_position", player.global_position)
	(caretaker as Node2D).global_position = Vector2(760.0, 360.0)
	caretaker.call("set_facing_direction", Vector2.LEFT)
	game.call("force_exploration_alert_tick_for_testing", 1.0)
	await process_frame
	if not bool(game.call("is_turn_based_combat_active")):
		_fail("Seeing the hero again did not restart turn-based combat.")
		return

	# Stop the test combat without resolving the encounter and verify persistence.
	game.call("_stop_turn_based_combat", "Тест повторного обнаружения завершён.")
	if not bool(state.call("save_game")):
		_fail("Active pursuit state could not be autosaved outside initiative.")
		return
	state.set("story_flags", {})
	state.set("quest_states", {})
	state.set("inventory", {})
	if not bool(state.call("load_game")):
		_fail("Pursuit autosave could not be loaded.")
		return
	if str(state.call("get_encounter_status", ENCOUNTER_ID)) != EncounterSystem.STATUS_ACTIVE:
		_fail("Active encounter state was not preserved by save/load.")
		return
	if not FileAccess.file_exists(save_path):
		_fail("Autosave disappeared during pursuit persistence test.")
		return

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Successful Hide preserves a stationary watcher, moving patrol pursuit, reacquisition and active encounter persistence.")
	quit(0)


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Тень"
	hero.character_class_id = "rogue"
	hero.character_class_name = "Плут"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.level = 1
	hero.maximum_health = 10
	hero.current_health = 10
	hero.hit_die_size = 8
	hero.hit_dice_maximum = 1
	hero.hit_dice_current = 1
	hero.abilities["dexterity"] = 18
	hero.base_abilities["dexterity"] = 18
	hero.skill_proficiencies.append("stealth")
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
