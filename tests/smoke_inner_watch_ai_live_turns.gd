extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const EXPECTED_RUNTIME: String = "res://scripts/game/game_guard_post_polish_runtime.gd"
const MARKSMAN_ID: String = "training_marksman"
const MAGE_ID: String = "training_mage"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	var save_path: String = ProjectSettings.globalize_path("user://savegame.json")
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	state.call("new_game")
	state.set("player_character", _make_hero())

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	var game: Node = packed.instantiate() if packed != null else null
	if game == null:
		_fail("Guard post scene could not be instantiated.")
		return
	root.add_child(game)
	for _frame: int in range(40):
		await process_frame
	var game_script: Script = game.get_script() as Script
	if game_script == null or game_script.resource_path != EXPECTED_RUNTIME:
		_fail("Guard post scene does not use the polished AI runtime.")
		return

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var room: GuardPostTwoRoomVisibility = game.get_node_or_null("StealthTestRoom") as GuardPostTwoRoomVisibility
	if player == null or room == null:
		_fail("Inner watch AI fixtures are incomplete.")
		return
	var marksman: Node = room.get_training_marksman()
	var mage: Node = room.get_training_mage()
	if marksman == null or mage == null:
		_fail("Marksman or mage is missing from the inner room.")
		return

	player.global_position = Vector2(650.0, 360.0)
	state.set("player_position", player.global_position)
	game.call("_evaluate_guard_post_state")
	game.call("resolve_first_room_for_testing", "guards_defeated")
	var inner_x: float = room.get_inner_partition_global_x()
	player.global_position = Vector2(inner_x + 96.0, 360.0)
	state.set("player_position", player.global_position)
	game.call("_evaluate_guard_post_state")
	for _frame: int in range(8):
		await process_frame

	var turn_system: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	if turn_system == null or not turn_system.active:
		_fail("Violent entry into the inner room did not start combat.")
		return
	for actor: Node in [marksman, mage]:
		if not bool(actor.call("is_combat_participant_active")):
			_fail("%s was not activated as a combat participant." % actor.call("get_actor_id"))
			return
		if not bool(actor.call("is_hostile")) or not bool(actor.call("can_take_combat_turn")):
			_fail("%s entered initiative without an executable hostile AI state." % actor.call("get_actor_id"))
			return
		if not _turn_contains_actor(turn_system, actor):
			_fail("%s is missing from inner-room initiative." % actor.call("get_actor_id"))
			return

	# Let any initially scheduled turn finish before testing recovery from a
	# deliberately unstarted NPC turn.
	await create_timer(1.4).timeout
	await _verify_watchdog_turn(game, turn_system, marksman, MARKSMAN_ID)
	if not turn_system.active:
		_fail("Combat ended before the mage live-turn check.")
		return
	await _verify_watchdog_turn(game, turn_system, mage, MAGE_ID)

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Inner marksman and mage both execute live AI turns and advance initiative.")
	quit(0)


func _verify_watchdog_turn(game: Node, turn_system: TurnBasedCombatSystem, actor: Node, actor_id: String) -> void:
	var started_before: int = int(game.call("get_inner_watch_ai_turn_started_for_testing", actor_id))
	var completed_before: int = int(game.call("get_inner_watch_ai_turn_completed_for_testing", actor_id))
	turn_system.force_current_actor_for_testing(actor)
	game.set("_enemy_turn_running", false)
	var elapsed: float = 0.0
	while elapsed < 7.0:
		await create_timer(0.1).timeout
		elapsed += 0.1
		var completed_now: int = int(game.call("get_inner_watch_ai_turn_completed_for_testing", actor_id))
		if completed_now > completed_before and turn_system.current_actor() != actor:
			break
	var started_after: int = int(game.call("get_inner_watch_ai_turn_started_for_testing", actor_id))
	var completed_after: int = int(game.call("get_inner_watch_ai_turn_completed_for_testing", actor_id))
	if started_after <= started_before:
		_fail("AI watchdog did not start a turn for %s." % actor_id)
		return
	if completed_after <= completed_before:
		_fail("AI turn for %s started but did not complete." % actor_id)
		return
	if turn_system.current_actor() == actor:
		_fail("Initiative remained stalled on %s after its AI turn." % actor_id)


func _turn_contains_actor(turn_system: TurnBasedCombatSystem, actor: Node) -> bool:
	for entry: Dictionary in turn_system.entries:
		if entry.get("node") == actor:
			return true
	return false


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель внутренней охраны"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.level = 8
	hero.maximum_health = 140
	hero.current_health = 140
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
