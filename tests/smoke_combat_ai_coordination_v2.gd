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
		&"build_coordination_context_v2_for_testing",
		&"choose_coordination_intent_v2_for_testing",
		&"get_coordination_plan_v2_for_testing",
		&"get_coordination_assignment_v1_for_testing",
		&"clear_coordination_runtime_v2_for_testing"
	]:
		if not game.has_method(method_name):
			_fail("Game runtime is missing Coordination v2 capability: %s" % method_name)
			return

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var caretaker: Node2D = game.get_node_or_null("Caretaker") as Node2D
	var guard: Node2D = game.get_node_or_null("StealthTestRoom/ServiceGuard") as Node2D
	var marksman: Node2D = _instantiate_actor(MARKSMAN_SCENE, game, Vector2(690.0, 250.0))
	var mage: Node2D = _instantiate_actor(MAGE_SCENE, game, Vector2(690.0, 500.0))
	if player == null or caretaker == null or guard == null or marksman == null or mage == null:
		_fail("Coordination v2 fixtures are incomplete.")
		return
	for participant: Node2D in [guard, marksman, mage]:
		if participant.has_method("activate_combat_participant") and not bool(participant.call("activate_combat_participant")):
			_fail("Prepared squad member could not be activated: %s" % participant.name)
			return

	player.global_position = Vector2(500.0, 360.0)
	guard.global_position = Vector2(700.0, 360.0)
	caretaker.global_position = Vector2(740.0, 430.0)
	marksman.global_position = Vector2(680.0, 230.0)
	mage.global_position = Vector2(680.0, 510.0)
	game.call("clear_coordination_runtime_v2_for_testing")

	var baseline_overrides: Dictionary = {
		"target_visible": true,
		"has_target_memory": true,
		"memory_confidence": 1.0,
		"escape_route_count": 5,
		"better_cover_available": true,
		"spell_plan_score": 190.0
	}
	game.call("build_coordination_context_v2_for_testing", guard, player, baseline_overrides)
	var baseline: Dictionary = game.call("get_coordination_plan_v2_for_testing", SQUAD_ID) as Dictionary
	_assert_plan(baseline, SquadTacticalPlanSystem.PLAN_SUPPRESS_AND_FLANK, "Baseline mixed-squad coordination")

	# Production context must detect an actually wounded squad member, not only a
	# synthetic testing flag.
	var marksman_max_health: int = maxi(int(marksman.get("maximum_health")), 1)
	marksman.set("current_health", maxi(int(round(float(marksman_max_health) * 0.20)), 1))
	game.call("build_coordination_context_v2_for_testing", guard, player, baseline_overrides)
	var protect: Dictionary = game.call("get_coordination_plan_v2_for_testing", SQUAD_ID) as Dictionary
	_assert_plan(protect, SquadTacticalPlanSystem.PLAN_PROTECT_WOUNDED_ALLY, "Critical ally protection")
	if str(protect.get("focus_actor_id", "")) != "training_marksman":
		_fail("Protection plan did not focus the actual wounded marksman: %s" % JSON.stringify(protect))
		return
	if not protect.get("focus_position", null) is Vector2 or (protect.get("focus_position") as Vector2).distance_to(marksman.global_position) > 1.0:
		_fail("Protection plan did not track wounded ally position: %s" % JSON.stringify(protect))
		return

	game.call("build_coordination_context_v2_for_testing", caretaker, player, baseline_overrides)
	var caretaker_assignment: Dictionary = game.call("get_coordination_assignment_v1_for_testing", "caretaker") as Dictionary
	if str(caretaker_assignment.get("action", "")) != "protect_wounded":
		_fail("Defender did not receive wounded-screen assignment: %s" % JSON.stringify(caretaker_assignment))
		return
	var wounded_objective: Vector2 = game.call(
		"_objective_for_advanced_intent",
		caretaker,
		caretaker.global_position,
		player.global_position,
		NpcCombatAiSystem.INTENT_GUARD
	) as Vector2
	if wounded_objective.distance_to(marksman.global_position) > 190.0 or wounded_objective.distance_to(marksman.global_position) < 20.0:
		_fail("Wounded-screen objective is not a distinct support sector: %s" % wounded_objective)
		return

	marksman.set("current_health", marksman_max_health)
	game.call("build_coordination_context_v2_for_testing", guard, player, baseline_overrides)
	var recovered: Dictionary = game.call("get_coordination_plan_v2_for_testing", SQUAD_ID) as Dictionary
	_assert_plan(recovered, SquadTacticalPlanSystem.PLAN_SUPPRESS_AND_FLANK, "Recovery from wounded protection")

	var casualty_overrides: Dictionary = baseline_overrides.duplicate(true)
	casualty_overrides["recent_casualty"] = true
	casualty_overrides["casualty_count"] = 1
	casualty_overrides["latest_casualty_actor_id"] = "training_marksman"
	casualty_overrides["latest_casualty_position"] = marksman.global_position
	game.call("build_coordination_context_v2_for_testing", guard, player, casualty_overrides)
	var casualty_plan: Dictionary = game.call("get_coordination_plan_v2_for_testing", SQUAD_ID) as Dictionary
	_assert_plan(casualty_plan, SquadTacticalPlanSystem.PLAN_CASUALTY_REGROUP, "Immediate casualty regroup")
	if str(casualty_plan.get("switch_reason", "")) != "priority_interrupt":
		_fail("Casualty regroup did not interrupt offensive plan: %s" % JSON.stringify(casualty_plan))
		return

	game.call("build_coordination_context_v2_for_testing", mage, player, casualty_overrides)
	var mage_assignment: Dictionary = game.call("get_coordination_assignment_v1_for_testing", "training_mage") as Dictionary
	if str(mage_assignment.get("action", "")) != "rally_after_casualty" or str(mage_assignment.get("intent", "")) != AdvancedNpcCombatAiSystem.INTENT_RALLY:
		_fail("Caster did not receive squad rally assignment after casualty: %s" % JSON.stringify(mage_assignment))
		return

	var collapse_overrides: Dictionary = baseline_overrides.duplicate(true)
	collapse_overrides["casualty_count"] = 2
	game.call("build_coordination_context_v2_for_testing", guard, player, collapse_overrides)
	var withdrawal: Dictionary = game.call("get_coordination_plan_v2_for_testing", SQUAD_ID) as Dictionary
	_assert_plan(withdrawal, SquadTacticalPlanSystem.PLAN_ORDERLY_WITHDRAWAL, "Casualty-driven orderly withdrawal")

	game.call("clear_coordination_runtime_v2_for_testing")
	game.call("build_coordination_context_v2_for_testing", guard, player, baseline_overrides)
	var lost_overrides: Dictionary = baseline_overrides.duplicate(true)
	lost_overrides["target_visible"] = false
	lost_overrides["has_target_memory"] = true
	lost_overrides["memory_confidence"] = 0.8
	game.call("build_coordination_context_v2_for_testing", guard, player, lost_overrides)
	var search: Dictionary = game.call("get_coordination_plan_v2_for_testing", SQUAD_ID) as Dictionary
	_assert_plan(search, SquadTacticalPlanSystem.PLAN_SECTOR_SEARCH, "Contact-loss sector search")
	game.call("build_coordination_context_v2_for_testing", guard, player, baseline_overrides)
	var reacquired: Dictionary = game.call("get_coordination_plan_v2_for_testing", SQUAD_ID) as Dictionary
	_assert_plan(reacquired, SquadTacticalPlanSystem.PLAN_SUPPRESS_AND_FLANK, "Target reacquisition")

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Combat AI Coordination v2 dynamic replanning, wounded protection, casualty response and search/reacquire passed.")
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


func _assert_plan(plan: Dictionary, expected_id: String, label: String) -> void:
	if str(plan.get("plan_id", "")) != expected_id:
		_fail("%s selected wrong plan: %s" % [label, JSON.stringify(plan)])


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель координации v2"
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