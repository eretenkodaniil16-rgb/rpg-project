extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const FIRST_ROOM_ID: String = "vault_guard_post_01"
const SECOND_ROOM_ID: String = "vault_inner_watch_01"
const AUTHORIZATION_BROKEN_FLAG: String = "vault_guard_post_peaceful_authorization_broken"
const BETRAYAL_RESOLVED_FLAG: String = "vault_inner_watch_betrayal_resolved"

var _has_failed: bool = false


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
	for _frame: int in range(45):
		await process_frame

	var room: GuardPostTwoRoomVisibility = game.get_node_or_null("StealthTestRoom") as GuardPostTwoRoomVisibility
	var player: CharacterBody2D = game.get_node_or_null("Player") as CharacterBody2D
	var caretaker: Node = game.get_node_or_null("Caretaker")
	if room == null or player == null or caretaker == null:
		_fail("Guard-post integrity fixtures are incomplete.")
		return
	var guard: Node = room.get_patrol_observer()
	var marksman: Node = room.get_training_marksman()
	var mage: Node = room.get_training_mage()
	var west_door: StealthDoor = room.get_test_door()
	var inner_gate: StealthDoor = room.get_inner_gate()
	if guard == null or marksman == null or mage == null or west_door == null or inner_gate == null:
		_fail("Guard-post actors or doors are missing.")
		return

	await _verify_outer_boundary(room, player, state)
	if _has_failed:
		return
	_verify_expanded_door_reach(west_door, player, state)
	if _has_failed:
		return
	await _verify_peaceful_betrayal(game, room, player, caretaker, guard, marksman, mage, state)
	if _has_failed:
		return

	print("Outer perimeter collision, expanded door reach and peaceful-betrayal inner AI passed.")
	game.queue_free()
	await process_frame
	quit(0)


func _verify_outer_boundary(
	room: GuardPostTwoRoomVisibility,
	player: CharacterBody2D,
	state: Node
) -> void:
	var bodies: Array[StaticBody2D] = room.get_outer_boundary_bodies_for_testing()
	if bodies.size() != 4:
		_fail("The visible outer perimeter does not have four physical wall bodies.")
		return
	for body: StaticBody2D in bodies:
		var collision: CollisionShape2D = _find_collision_shape(body)
		if collision == null or collision.shape == null or collision.disabled:
			_fail("Outer wall %s has no active collision shape." % body.name)
			return

	player.global_position = Vector2(640.0, 625.0)
	state.set("player_position", player.global_position)
	player.call("set_mobile_vector", Vector2.DOWN)
	for _frame: int in range(30):
		await physics_frame
	player.call("set_mobile_vector", Vector2.ZERO)
	if player.global_position.y > 651.5:
		_fail("Player crossed the lower perimeter wall: y=%.2f." % player.global_position.y)
		return


func _verify_expanded_door_reach(
	door: StealthDoor,
	player: CharacterBody2D,
	state: Node
) -> void:
	var trigger_size: Vector2 = door.get_interaction_trigger_size_for_testing()
	if trigger_size.x < 119.0 or trigger_size.y < door.door_size.y + 47.0:
		_fail("Door interaction Area2D was not enlarged: %s." % trigger_size)
		return
	player.global_position = door.global_position + Vector2(50.0, 50.0)
	state.set("player_position", player.global_position)
	if not door.is_player_adjacent_for_testing():
		_fail("Expanded door reach still rejects a nearby diagonal mobile position.")
		return
	if door.get_door_state() == "closed" and not door.can_perform_world_interaction():
		_fail("Door action remains unavailable inside the enlarged trigger.")
		return


func _verify_peaceful_betrayal(
	game: Node,
	room: GuardPostTwoRoomVisibility,
	player: CharacterBody2D,
	caretaker: Node,
	guard: Node,
	marksman: Node,
	mage: Node,
	state: Node
) -> void:
	player.global_position = Vector2(620.0, 360.0)
	state.set("player_position", player.global_position)
	game.call("_evaluate_guard_post_state")
	state.call("set_flag", "caretaker_convinced", true)
	for _frame: int in range(5):
		await process_frame
	var first_state: Dictionary = state.call("get_encounter_state", FIRST_ROOM_ID) as Dictionary
	if str(first_state.get("resolution_id", "")) != "peaceful_passage":
		_fail("Peaceful authorization setup failed.")
		return

	player.global_position = Vector2(room.get_inner_partition_global_x() + 96.0, 360.0)
	state.set("player_position", player.global_position)
	game.call("_evaluate_guard_post_state")
	for _frame: int in range(3):
		await process_frame
	var second_state: Dictionary = state.call("get_encounter_state", SECOND_ROOM_ID) as Dictionary
	if str(second_state.get("resolution_id", "")) != "authorized_passage":
		_fail("The inner room was not resolved as authorized before betrayal.")
		return

	player.global_position = Vector2(700.0, 360.0)
	state.set("player_position", player.global_position)
	game.call("_start_turn_based_combat", caretaker)
	await process_frame
	var turn_system: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	if not turn_system.active:
		_fail("Attacking the previously peaceful caretaker did not start combat.")
		return
	turn_system.stop_combat()
	game.set("_active_combat_encounter_id", "")
	_mark_actor_dead(caretaker)
	_mark_actor_dead(guard)
	game.call("_evaluate_guard_post_state")
	await process_frame
	if not bool(state.call("get_flag", AUTHORIZATION_BROKEN_FLAG, false)):
		_fail("Killing the authorized outer guard did not revoke peaceful passage.")
		return
	if not bool(game.call("is_peaceful_authorization_broken_for_testing")):
		_fail("Leaf runtime did not observe the persisted authorization revocation.")
		return

	player.global_position = Vector2(room.get_inner_partition_global_x() + 112.0, 360.0)
	state.set("player_position", player.global_position)
	game.call("_evaluate_guard_post_state")
	for _frame: int in range(6):
		await process_frame
	if not turn_system.active:
		_fail("Returning to the inner room after betrayal did not start consequence combat.")
		return
	var expected_runtime_id: String = str(game.call("get_inner_watch_betrayal_runtime_id_for_testing"))
	if str(game.call("get_active_combat_encounter_id_for_testing")) != expected_runtime_id:
		_fail("Betrayal combat did not use its no-double-reward runtime ID.")
		return
	for actor: Node in [marksman, mage]:
		if not bool(actor.call("is_combat_participant_active")):
			_fail("%s was not reactivated after peaceful betrayal." % actor.name)
			return
		if not actor.is_in_group("combat_targets") or not actor.is_in_group("stealth_alert_actors"):
			_fail("%s is missing target or alert groups after reactivation." % actor.name)
			return
		if not _turn_contains_actor(turn_system, actor):
			_fail("%s is missing from betrayal initiative." % actor.name)
			return
		if not bool(game.call("_target_is_valid", actor)):
			_fail("%s is active but cannot be selected as a visible combat target." % actor.name)
			return

	var visible_targets: Array[Node] = game.call("get_visible_targets_for_testing") as Array[Node]
	for actor: Node in [marksman, mage]:
		if not visible_targets.has(actor):
			_fail("%s is absent from the real visible target cycle." % actor.name)
			return

	var catalog: ActionCatalogUI = game.get_node_or_null("Interface/ActionCatalogUI") as ActionCatalogUI
	var target_button: Button = game.get_node_or_null("Interface/TargetButton") as Button
	var mobile_controls: Control = game.get_node_or_null("Interface/MobileControls") as Control
	if catalog == null or target_button == null or mobile_controls == null:
		_fail("Action catalog, Target button or mobile controls are missing from the betrayal test.")
		return
	mobile_controls.call("enable_for_testing")
	game.call("force_player_turn_for_testing")
	mobile_controls.call("_process", 0.0)
	mobile_controls.call("simulate_actions_touch_for_testing")
	if not catalog.panel.visible:
		_fail("Could not open the catalog through the real Actions button before target selection.")
		return
	var selected_actor_ids: Dictionary = {}
	for _press: int in range(8):
		target_button.emit_signal("pressed")
		if catalog.panel.visible:
			_fail("Target selection did not close the stale Actions panel.")
			return
		var selected: Node = game.get("_selected_target") as Node
		if is_instance_valid(selected) and selected.has_method("get_actor_id"):
			selected_actor_ids[str(selected.call("get_actor_id"))] = true
	if not bool(selected_actor_ids.get("training_marksman", false)):
		_fail("Repeated real Target-button presses never selected the marksman.")
		return
	if not bool(selected_actor_ids.get("training_mage", false)):
		_fail("Repeated real Target-button presses never selected the rune tactician.")
		return

	second_state = state.call("get_encounter_state", SECOND_ROOM_ID) as Dictionary
	if str(second_state.get("resolution_id", "")) != "authorized_passage":
		_fail("Betrayal incorrectly rewrote the already completed authorization encounter.")
		return

	_mark_actor_dead(marksman)
	_mark_actor_dead(mage)
	game.call("_resolve_active_combat_encounter_if_complete")
	await process_frame
	if turn_system.active:
		_fail("Betrayal combat did not stop after both inner defenders were defeated.")
		return
	if not bool(state.call("get_flag", BETRAYAL_RESOLVED_FLAG, false)):
		_fail("Betrayal consequence completion was not persisted.")
		return


func _find_collision_shape(body: StaticBody2D) -> CollisionShape2D:
	for child: Node in body.get_children():
		if child is CollisionShape2D:
			return child as CollisionShape2D
	return null


func _mark_actor_dead(actor: Node) -> void:
	actor.set("current_health", 0)
	actor.set("defeated", true)
	actor.set("hostile", false)
	if actor.has_method("_activate_body_from_defeat"):
		actor.call("_activate_body_from_defeat", CorpseInteractionSystem.BODY_DEAD)
	elif actor.has_method("_apply_body_groups"):
		actor.set("_body_state", CorpseInteractionSystem.BODY_DEAD)
		actor.call("_apply_body_groups")


func _turn_contains_actor(turn_system: TurnBasedCombatSystem, actor: Node) -> bool:
	for entry: Dictionary in turn_system.entries:
		if entry.get("node") == actor:
			return true
	return false


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.create_legacy_default()
	hero.character_name = "Проверяющий зависимости"
	hero.level = 5
	hero.maximum_health = 100
	hero.current_health = 100
	return hero


func _fail(message: String) -> void:
	if _has_failed:
		return
	_has_failed = true
	push_error(message)
	quit(1)
