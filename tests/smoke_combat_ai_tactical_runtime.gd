extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const MARKSMAN_SCENE: String = "res://scenes/game/combat_ai_training_marksman.tscn"


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	state.call("new_game")
	state.set("player_character", _make_hero())

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	if packed == null:
		_fail("Game scene could not be loaded.")
		return
	var game: Node = packed.instantiate()
	root.add_child(game)
	for _frame: int in range(12):
		await process_frame
	game.set_process(false)

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var caretaker: Node2D = game.get_node_or_null("Caretaker") as Node2D
	var room: StealthTestRoom = get_first_node_in_group("stealth_world") as StealthTestRoom
	var guard: Node2D = room.get_patrol_observer() as Node2D if room != null else null
	if player == null or caretaker == null or guard == null:
		_fail("Combat AI runtime actors are missing.")
		return

	game.call("record_combat_ai_sighting_for_testing", "service_guard", player.global_position)
	var shared_memory: Dictionary = game.call("get_combat_ai_memory_for_testing", "caretaker") as Dictionary
	if shared_memory.is_empty() or not shared_memory.get("position", null) is Vector2:
		_fail("Defender did not receive the squad's last-known target position.")
		return
	if (shared_memory.get("position") as Vector2).distance_to(player.global_position) > 0.1:
		_fail("Squad memory stored an incorrect target position.")
		return

	var combat_state: CombatantState = game.get("_player_combat_state") as CombatantState
	if combat_state == null:
		_fail("Player combat state is missing.")
		return
	combat_state.hidden = true
	if bool(game.call("_combat_ai_can_see_player_from", caretaker.global_position)):
		_fail("Combat AI sees the exact position of a hidden player.")
		return
	combat_state.hidden = false

	var plan: Dictionary = game.call(
		"plan_combat_ai_movement_for_testing",
		guard,
		"service_guard",
		player.global_position,
		NpcAiSystem.INTENT_ADVANCE,
		30
	) as Dictionary
	var path: Array = plan.get("path", []) as Array
	if path.is_empty() or path.size() > 6:
		_fail("Tactical planner did not build a bounded movement path.")
		return
	if float(plan.get("score", NpcCombatAiSystem.BLOCKED_SCORE)) <= NpcCombatAiSystem.BLOCKED_SCORE:
		_fail("Tactical planner failed to score reachable cells.")
		return

	var marksman_packed: PackedScene = load(MARKSMAN_SCENE) as PackedScene
	if marksman_packed == null:
		_fail("Training marksman scene could not be loaded.")
		return
	var marksman: Node = marksman_packed.instantiate()
	game.add_child(marksman)
	await process_frame
	if not marksman.has_method("get_actor_id") or str(marksman.call("get_actor_id")) != "training_marksman":
		_fail("Training marksman does not expose its stable actor ID.")
		return
	if not marksman.has_method("activate_combat_participant") or not bool(marksman.call("activate_combat_participant")):
		_fail("Training marksman could not become a combat participant.")
		return
	var marksman_profile: Dictionary = game.call("get_combat_ai_profile_for_testing", "training_marksman") as Dictionary
	if str(marksman_profile.get("role", "")) != NpcCombatAiSystem.ROLE_RANGED:
		_fail("Training marksman is not connected to the ranged AI profile.")
		return

	game.queue_free()
	await process_frame
	print("Combat AI squad memory, hidden-target fairness, path planning and marksman runtime smoke test passed.")
	quit(0)


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Тактическая цель"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.level = 1
	hero.maximum_health = 14
	hero.current_health = 14
	hero.hit_die_size = 10
	hero.hit_dice_maximum = 1
	hero.hit_dice_current = 1
	return hero
