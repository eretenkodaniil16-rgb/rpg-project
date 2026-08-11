extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const MARKSMAN_SCENE: String = "res://scenes/game/combat_ai_training_marksman.tscn"
const MAGE_SCENE: String = "res://scenes/game/combat_ai_training_mage.tscn"
const SQUAD_ID: String = "vault_watch"


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
		_fail("Game scene could not be instantiated.")
		return
	root.add_child(game)
	for _frame: int in range(20):
		await process_frame
	game.set_process(false)

	for method_name: StringName in [
		&"build_coordination_context_v1_for_testing",
		&"choose_coordination_intent_v1_for_testing",
		&"get_coordination_plan_v1_for_testing",
		&"get_coordination_assignment_v1_for_testing",
		&"get_coordination_objective_v1_for_testing",
		&"get_coordination_reserved_cells_v1_for_testing",
		&"clear_coordination_runtime_v1_for_testing"
	]:
		if not game.has_method(method_name):
			_fail("Game runtime is missing coordination capability: %s" % method_name)
			return

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var caretaker: Node2D = game.get_node_or_null("Caretaker") as Node2D
	var guard: Node2D = game.get_node_or_null("StealthTestRoom/ServiceGuard") as Node2D
	var marksman: Node2D = _instantiate_actor(MARKSMAN_SCENE, game, Vector2(690.0, 250.0))
	var mage: Node2D = _instantiate_actor(MAGE_SCENE, game, Vector2(690.0, 500.0))
	if player == null or caretaker == null or guard == null or marksman == null or mage == null:
		_fail("Coordination fixtures are incomplete.")
		return
	for participant: Node2D in [guard, marksman, mage]:
		if participant.has_method("activate_combat_participant") and not bool(participant.call("activate_combat_participant")):
			_fail("Prepared squad member could not be activated: %s" % participant.name)
			return

	# Keep all roles in one unobstructed tactical pocket. The squad context is
	# collected by stable squad_id, not by hard-coded scene node names.
	player.global_position = Vector2(500.0, 360.0)
	guard.global_position = Vector2(700.0, 360.0)
	caretaker.global_position = Vector2(740.0, 430.0)
	marksman.global_position = Vector2(680.0, 230.0)
	mage.global_position = Vector2(680.0, 510.0)
	game.call("clear_coordination_runtime_v1_for_testing")

	var actors: Dictionary = {
		"service_guard": guard,
		"caretaker": caretaker,
		"training_marksman": marksman,
		"training_mage": mage
	}
	var expected: Dictionary = {
		"service_guard": {"action": "flank", "intent": NpcCombatAiSystem.INTENT_REPOSITION, "objective": "target_flank"},
		"caretaker": {"action": "pin_target", "intent": NpcCombatAiSystem.INTENT_INTERCEPT, "objective": "target_front"},
		"training_marksman": {"action": "suppress", "intent": AdvancedNpcCombatAiSystem.INTENT_TAKE_COVER, "objective": "target_rear"},
		"training_mage": {"action": "control_target", "intent": AdvancedNpcCombatAiSystem.INTENT_CAST_SPELL, "objective": "target_rear"}
	}

	for actor_id: String in actors.keys():
		var actor: Node = actors[actor_id] as Node
		var context: Dictionary = game.call(
			"build_coordination_context_v1_for_testing",
			actor,
			player,
			{
				"target_visible": true,
				"has_target_memory": true,
				"escape_route_count": 5,
				"better_cover_available": true,
				"spell_plan_score": 190.0
			}
		) as Dictionary
		if context.is_empty():
			_fail("Coordination context is empty for %s." % actor_id)
			return

	var plan: Dictionary = game.call("get_coordination_plan_v1_for_testing", SQUAD_ID) as Dictionary
	if str(plan.get("plan_id", "")) != SquadTacticalPlanSystem.PLAN_SUPPRESS_AND_FLANK:
		_fail("Mixed vault_watch squad did not choose suppress-and-flank: %s" % JSON.stringify(plan))
		return

	var distinct_actions: Dictionary = {}
	for actor_id: String in actors.keys():
		var assignment: Dictionary = game.call("get_coordination_assignment_v1_for_testing", actor_id) as Dictionary
		var expected_assignment: Dictionary = expected[actor_id] as Dictionary
		for field: String in ["action", "intent", "objective"]:
			if str(assignment.get(field, "")) != str(expected_assignment.get(field, "")):
				_fail("%s received wrong %s: %s" % [actor_id, field, JSON.stringify(assignment)])
				return
		distinct_actions[str(assignment.get("action", ""))] = true
	if distinct_actions.size() < 4:
		_fail("Role-specific coordination collapsed into identical assignments.")
		return

	var guard_assignment: Dictionary = game.call("get_coordination_assignment_v1_for_testing", "service_guard") as Dictionary
	var guard_objective: Vector2 = game.call(
		"_objective_for_advanced_intent",
		guard,
		guard.global_position,
		player.global_position,
		str(guard_assignment.get("intent", NpcCombatAiSystem.INTENT_REPOSITION))
	) as Vector2
	var caretaker_assignment: Dictionary = game.call("get_coordination_assignment_v1_for_testing", "caretaker") as Dictionary
	var caretaker_objective: Vector2 = game.call(
		"_objective_for_advanced_intent",
		caretaker,
		caretaker.global_position,
		player.global_position,
		str(caretaker_assignment.get("intent", NpcCombatAiSystem.INTENT_INTERCEPT))
	) as Vector2
	if guard_objective.distance_to(player.global_position) < 60.0:
		_fail("Flanker objective collapsed onto selected party target.")
		return
	if caretaker_objective.distance_to(guard_objective) < 24.0:
		_fail("Defender and flanker received effectively the same tactical sector.")
		return

	# The squad-aware AI must be able to override independent utility with the
	# assignment generated by the shared plan.
	var guard_decision: Dictionary = game.call(
		"choose_coordination_intent_v1_for_testing",
		guard,
		player,
		{
			"target_visible": true,
			"has_target_memory": true,
			"escape_route_count": 5,
			"better_cover_available": true
		}
	) as Dictionary
	if str(guard_decision.get("squad_plan_id", "")) != SquadTacticalPlanSystem.PLAN_SUPPRESS_AND_FLANK:
		_fail("Shared plan did not reach the squad-aware utility decision: %s" % JSON.stringify(guard_decision))
		return

	var guard_profile: Dictionary = game.call("get_combat_ai_profile_for_testing", "service_guard") as Dictionary
	var caretaker_profile: Dictionary = game.call("get_combat_ai_profile_for_testing", "caretaker") as Dictionary
	var guard_move: Dictionary = game.call(
		"_plan_advanced_party_movement_v1",
		guard,
		guard,
		player,
		guard_profile,
		guard.global_position,
		guard_objective,
		str(guard_assignment.get("intent", NpcCombatAiSystem.INTENT_REPOSITION)),
		30
	) as Dictionary
	var caretaker_move: Dictionary = game.call(
		"_plan_advanced_party_movement_v1",
		caretaker,
		caretaker,
		player,
		caretaker_profile,
		caretaker.global_position,
		caretaker_objective,
		str(caretaker_assignment.get("intent", NpcCombatAiSystem.INTENT_INTERCEPT)),
		30
	) as Dictionary
	var reservations: Dictionary = game.call("get_coordination_reserved_cells_v1_for_testing", SQUAD_ID) as Dictionary
	if not guard_move.is_empty() and not caretaker_move.is_empty():
		if guard_move.get("cell", null) == caretaker_move.get("cell", null):
			_fail("Two coordinated actors selected the same reserved destination cell.")
			return
		if reservations.size() < 2:
			_fail("Movement planner did not retain per-actor squad reservations: %s" % JSON.stringify(reservations))
			return

	game.call("clear_coordination_runtime_v1_for_testing")
	if not (game.call("get_coordination_plan_v1_for_testing", SQUAD_ID) as Dictionary).is_empty():
		_fail("Coordination plan survived explicit runtime cleanup.")
		return
	if not (game.call("get_coordination_reserved_cells_v1_for_testing", SQUAD_ID) as Dictionary).is_empty():
		_fail("Coordination cell reservations survived explicit runtime cleanup.")
		return

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Combat AI Coordination v1 shared plan, role assignments, tactical sectors and cell reservations passed.")
	quit(0)


func _instantiate_actor(scene_path: String, parent: Node, position: Vector2) -> Node2D:
	var packed: PackedScene = load(scene_path) as PackedScene
	if packed == null:
		return null
	var actor: Node2D = packed.instantiate() as Node2D
	if actor == null:
		return null
	parent.add_child(actor)
	actor.global_position = position
	return actor


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель координации"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.level = 5
	hero.maximum_health = 46
	hero.current_health = 46
	hero.hit_die_size = 10
	hero.hit_dice_maximum = 5
	hero.hit_dice_current = 5
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
