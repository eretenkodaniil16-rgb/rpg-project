extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const EXPECTED_RUNTIME: String = "res://scripts/game/game_guard_post_two_room_runtime.gd"
const MARKSMAN_SCENE: String = "res://scenes/game/combat_ai_training_marksman.tscn"
const MAGE_SCENE: String = "res://scenes/game/combat_ai_training_mage.tscn"


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
	if packed == null:
		_fail("Game scene could not be loaded.")
		return
	var game: Node = packed.instantiate()
	root.add_child(game)
	for _frame: int in range(18):
		await process_frame
	var game_script: Script = game.get_script() as Script
	if game_script == null or game_script.resource_path != EXPECTED_RUNTIME:
		_fail("Game scene does not use squad tactical plan runtime.")
		return
	game.set_process(false)

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var caretaker: Node2D = game.get_node_or_null("Caretaker") as Node2D
	var guard: Node2D = game.get_node_or_null("StealthTestRoom/ServiceGuard") as Node2D
	var marksman: Node2D = _instantiate_actor(MARKSMAN_SCENE, game, Vector2(620.0, 220.0))
	var mage: Node2D = _instantiate_actor(MAGE_SCENE, game, Vector2(640.0, 500.0))
	if player == null or caretaker == null or guard == null or marksman == null or mage == null:
		_fail("Squad runtime fixtures are incomplete.")
		return
	for participant: Node2D in [guard, marksman, mage]:
		if not participant.has_method("activate_combat_participant") or not bool(participant.call("activate_combat_participant")):
			_fail("Prepared squad member could not be activated: %s" % participant.name)
			return
	player.global_position = Vector2(510.0, 360.0)
	guard.global_position = Vector2(710.0, 360.0)
	caretaker.global_position = Vector2(760.0, 430.0)

	var environment_events: EnvironmentEventSystem = game.call("get_environment_event_system_for_testing") as EnvironmentEventSystem
	if environment_events != null:
		environment_events.clear_combat_memory()
	game.call("_clear_squad_plan_runtime")

	var guard_profile: Dictionary = game._squad_ai.get_profile("service_guard")
	var guard_context: Dictionary = _base_context()
	game.call("_enrich_advanced_context", guard_context, guard, guard, "service_guard", guard_profile, {})
	var plan: Dictionary = game.call("get_squad_plan_for_testing", "vault_watch") as Dictionary
	if str(plan.get("plan_id", "")) != SquadTacticalPlanSystem.PLAN_SUPPRESS_AND_FLANK:
		_fail("Mixed squad did not choose suppress-and-flank: %s" % JSON.stringify(plan))
		return
	var guard_assignment: Dictionary = game.call("get_squad_assignment_for_testing", "service_guard") as Dictionary
	if str(guard_assignment.get("action", "")) != "flank":
		_fail("Melee guard did not receive flank assignment: %s" % JSON.stringify(guard_assignment))
		return
	var guard_decision: Dictionary = game.call("get_squad_plan_decision_for_testing", "service_guard") as Dictionary
	if str(guard_decision.get("squad_plan_id", "")) != SquadTacticalPlanSystem.PLAN_SUPPRESS_AND_FLANK:
		_fail("Squad plan did not override independent guard action: %s" % JSON.stringify(guard_decision))
		return
	var flank_objective: Vector2 = game.call("_objective_for_advanced_intent", guard, guard.global_position, player.global_position, NpcCombatAiSystem.INTENT_REPOSITION) as Vector2
	if flank_objective.distance_to(player.global_position) < 70.0:
		_fail("Flank objective collapsed onto the target instead of a side sector.")
		return

	var marksman_profile: Dictionary = game._squad_ai.get_profile("training_marksman")
	var marksman_context: Dictionary = _base_context()
	game.call("_enrich_advanced_context", marksman_context, marksman, marksman, "training_marksman", marksman_profile, {})
	var marksman_assignment: Dictionary = game.call("get_squad_assignment_for_testing", "training_marksman") as Dictionary
	if str(marksman_assignment.get("action", "")) != "suppress":
		_fail("Marksman did not receive suppression role: %s" % JSON.stringify(marksman_assignment))
		return

	var mage_profile: Dictionary = game._squad_ai.get_profile("training_mage")
	var mage_context: Dictionary = _base_context()
	mage_context["spell_plan_score"] = 170.0
	game.call("_enrich_advanced_context", mage_context, mage, mage, "training_mage", mage_profile, {})
	var mage_assignment: Dictionary = game.call("get_squad_assignment_for_testing", "training_mage") as Dictionary
	if str(mage_assignment.get("action", "")) != "control_target":
		_fail("Mage did not receive control role: %s" % JSON.stringify(mage_assignment))
		return

	var grid: BattleGrid = game.call("_get_battle_grid") as BattleGrid
	if grid == null:
		_fail("Battle grid is missing for reservation test.")
		return
	var shared_objective: Vector2 = player.global_position + Vector2(120.0, 0.0)
	var guard_plan: Dictionary = game.call("_plan_combat_ai_movement", guard, guard, guard_profile, guard.global_position, shared_objective, NpcCombatAiSystem.INTENT_REPOSITION, 30) as Dictionary
	var caretaker_profile: Dictionary = game._squad_ai.get_profile("caretaker")
	var caretaker_plan: Dictionary = game.call("_plan_combat_ai_movement", caretaker, caretaker, caretaker_profile, caretaker.global_position, shared_objective, NpcCombatAiSystem.INTENT_REPOSITION, 30) as Dictionary
	if not guard_plan.is_empty() and not caretaker_plan.is_empty() and guard_plan.get("cell", null) == caretaker_plan.get("cell", null):
		_fail("Two squad members reserved the same destination cell.")
		return

	game.call("record_squad_plan_outcome_for_testing", "service_guard", false)
	game.call("record_squad_plan_outcome_for_testing", "service_guard", false)
	game.call("record_squad_plan_outcome_for_testing", "service_guard", false)
	var failed_context: Dictionary = _base_context()
	game.call("_enrich_advanced_context", failed_context, guard, guard, "service_guard", guard_profile, {})
	var fallback_assignment: Dictionary = game.call("get_squad_assignment_for_testing", "service_guard") as Dictionary
	if str(fallback_assignment.get("action", "")) != "recover_after_failure":
		_fail("Repeated failed flank did not produce fallback behavior: %s" % JSON.stringify(fallback_assignment))
		return

	game.call("_clear_squad_plan_runtime")
	var search_context: Dictionary = _base_context()
	search_context["target_visible"] = false
	search_context["can_attack"] = false
	search_context["has_target_memory"] = true
	search_context["memory_confidence"] = 0.8
	game.call("_enrich_advanced_context", search_context, guard, guard, "service_guard", guard_profile, {})
	var search_plan: Dictionary = game.call("get_squad_plan_for_testing", "vault_watch") as Dictionary
	if str(search_plan.get("plan_id", "")) != SquadTacticalPlanSystem.PLAN_SECTOR_SEARCH:
		_fail("Squad did not divide the last known position into search sectors: %s" % JSON.stringify(search_plan))
		return

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Squad multi-round plans, role assignments, flank objective, cell reservations, failure fallback and sector search passed.")
	quit(0)


func _base_context() -> Dictionary:
	return {
		"distance_feet": 30,
		"actor_health_ratio": 1.0,
		"target_visible": true,
		"has_target_memory": true,
		"memory_confidence": 1.0,
		"can_attack": true,
		"can_move": true,
		"distance_from_guard_anchor_feet": 0,
		"target_distance_from_guard_anchor_feet": 30,
		"ally_count": 4,
		"hostile_count": 1,
		"defeated_ally_count": 0,
		"escape_route_count": 4,
		"new_casualty_seen": false,
		"casualty_count": 0,
		"rally_active": false,
		"can_shove": false,
		"target_prone": false,
		"better_cover_available": true,
		"nearest_ally_distance_feet": 15,
		"no_useful_attack": false,
		"no_safe_retreat": false,
		"spell_plan_score": 150.0
	}


func _instantiate_actor(scene_path: String, parent: Node, position: Vector2) -> Node2D:
	var actor_scene: PackedScene = load(scene_path) as PackedScene
	if actor_scene == null:
		return null
	var actor: Node2D = actor_scene.instantiate() as Node2D
	if actor == null:
		return null
	parent.add_child(actor)
	actor.global_position = position
	return actor


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель планов"
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
