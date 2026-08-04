extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const POSITION_EPSILON: float = 0.2


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	state.call("new_game")
	state.set("player_character", _make_hero())

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	var game: Node = packed.instantiate() if packed != null else null
	if game == null:
		_fail("Game scene could not be instantiated.")
		return
	root.add_child(game)
	for _frame: int in range(20):
		await process_frame
	game.set_process(false)

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var caretaker: Node = game.get_node_or_null("Caretaker")
	var room: GuardPostTwoRoomVisibility = game.get_node_or_null("StealthTestRoom") as GuardPostTwoRoomVisibility
	var guard: Node = room.get_patrol_observer() if room != null else null
	var west_door: StealthDoor = room.get_test_door() if room != null else null
	var stealth: StealthAlertSystem = game.get("_stealth_alerts") as StealthAlertSystem
	if player == null or caretaker == null or guard == null or west_door == null or stealth == null:
		_fail("Exploration NPC behavior fixtures are incomplete.")
		return

	var caretaker_profile: Dictionary = stealth.get_profile("caretaker")
	var guard_profile: Dictionary = stealth.get_profile("service_guard")
	if str(caretaker_profile.get("movement_mode", "")) != "stationary":
		_fail("Caretaker profile is not explicitly stationary.")
		return
	if str(guard_profile.get("movement_mode", "")) != "patrol":
		_fail("Service guard profile is not explicitly patrol-driven.")
		return

	# Simulation 1: the authored stationary NPC may turn and investigate, but it
	# must never walk away from its post when sight is lost.
	caretaker.global_position = Vector2(500.0, 360.0)
	player.global_position = Vector2(700.0, 360.0)
	caretaker.call("set_facing_direction", Vector2.RIGHT)
	_set_record(state, "caretaker", StealthAlertSystem.STATE_INVESTIGATING, 82.0, player.global_position)
	game.call("_restore_exploration_alerts")
	var caretaker_start: Vector2 = caretaker.global_position
	game.call("force_exploration_alert_tick_for_testing", 0.75)
	player.global_position = Vector2(100.0, 110.0)
	west_door.set_door_state("closed", false)
	game.call("force_exploration_alert_tick_for_testing", 1.0)
	if caretaker.global_position.distance_to(caretaker_start) > POSITION_EPSILON:
		_fail("Stationary caretaker moved after visual loss: start=%s current=%s" % [caretaker_start, caretaker.global_position])
		return

	# Simulation 2: a calm patrol keeps moving even while the hero is visible. A
	# short loss of sight remains suspicious and does not become a chase.
	west_door.set_door_state("open", false)
	(guard as Node2D).global_position = Vector2(760.0, 180.0)
	player.global_position = Vector2(620.0, 180.0)
	guard.call("set_facing_direction", Vector2.LEFT)
	_set_record(state, "service_guard", StealthAlertSystem.STATE_CALM, 0.0, Vector2.ZERO)
	game.call("_restore_exploration_alerts")
	game.call("force_patrol_tick_for_testing", guard, 0.7)
	var visible_patrol_start: Vector2 = (guard as Node2D).global_position
	for _tick: int in range(5):
		game.call("force_exploration_alert_tick_for_testing", 0.25)
	if (guard as Node2D).global_position.distance_to(visible_patrol_start) <= 0.5:
		_fail("Visible calm guard froze instead of continuing patrol.")
		return
	var briefly_seen_position: Vector2 = player.global_position
	_set_record(state, "service_guard", StealthAlertSystem.STATE_SUSPICIOUS, 45.0, briefly_seen_position)
	game.call("_restore_exploration_alerts")
	west_door.set_door_state("closed", false)
	player.global_position = Vector2(100.0, 110.0)
	game.call("force_exploration_alert_tick_for_testing", 0.5)
	var brief_loss: Dictionary = game.call("get_exploration_alert_record_for_testing", guard) as Dictionary
	if str(brief_loss.get("state", "")) != StealthAlertSystem.STATE_SUSPICIOUS:
		_fail("Brief visual loss incorrectly became an investigation: %s" % brief_loss)
		return

	# Simulation 3: a confirmed investigator follows one fixed sensory memory via
	# obstacle-aware navigation. Repeated footsteps cannot drag the destination
	# forward every frame while the NPC is still travelling to the first sound.
	var fixed_target := Vector2(620.0, 180.0)
	(guard as Node2D).global_position = Vector2(760.0, 180.0)
	_set_record(state, "service_guard", StealthAlertSystem.STATE_INVESTIGATING, 82.0, fixed_target)
	game.call("_restore_exploration_alerts")
	var first_noise := Vector2(720.0, 245.0)
	game.call("report_world_noise", "normal_step", first_noise, {"source_type": "npc_behavior_test"})
	await process_frame
	var after_first_noise: Dictionary = game.call("get_exploration_alert_record_for_testing", guard) as Dictionary
	var stored_target: Vector2 = stealth.vector_from_value(after_first_noise.get("last_known_position", []))
	if stored_target.distance_to(fixed_target) > POSITION_EPSILON:
		_fail("Footstep retargeted an investigator before it reached the fixed memory: expected=%s actual=%s" % [fixed_target, stored_target])
		return
	var distance_before: float = (guard as Node2D).global_position.distance_to(fixed_target)
	game.call("force_exploration_alert_tick_for_testing", 0.5)
	var distance_after: float = (guard as Node2D).global_position.distance_to(fixed_target)
	var moving_record: Dictionary = game.call("get_exploration_alert_record_for_testing", guard) as Dictionary
	if distance_after >= distance_before - POSITION_EPSILON:
		_fail("Investigating guard did not advance toward the fixed last-known position through navigation.")
		return
	if not bool(moving_record.get("navigation_used", false)):
		_fail("Investigation movement bypassed the shared obstacle-aware navigator.")
		return
	var second_noise := Vector2(735.0, 115.0)
	game.call("report_world_noise", "normal_step", second_noise, {"source_type": "npc_behavior_test_repeat"})
	await process_frame
	var after_second_noise: Dictionary = game.call("get_exploration_alert_record_for_testing", guard) as Dictionary
	stored_target = stealth.vector_from_value(after_second_noise.get("last_known_position", []))
	if stored_target.distance_to(fixed_target) > POSITION_EPSILON:
		_fail("Repeated footsteps produced continuous hidden-position tracking: expected=%s actual=%s" % [fixed_target, stored_target])
		return

	print("Stationary post, visible patrol, brief sight loss, fixed sensory memory and obstacle-aware investigation simulations passed.")
	game.queue_free()
	await process_frame
	quit(0)


func _set_record(
	state: Node,
	actor_id: String,
	state_name: String,
	suspicion: float,
	last_known_position: Vector2
) -> void:
	var record: Dictionary = state.call("get_stealth_alert_record", actor_id) as Dictionary
	record["state"] = state_name
	record["suspicion"] = suspicion
	record["last_known_position"] = [last_known_position.x, last_known_position.y]
	record["search_seconds_remaining"] = 10.0
	record["alert_cooldown_seconds"] = 20.0
	record["step_retarget_cooldown_seconds"] = 0.0
	state.call("set_stealth_alert_record", actor_id, record, false, false)


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.create_legacy_default()
	hero.character_name = "Observer"
	hero.abilities["dexterity"] = 18
	hero.base_abilities["dexterity"] = 18
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
