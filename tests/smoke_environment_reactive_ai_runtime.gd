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
		_fail("Game scene does not use environment-reactive runtime.")
		return
	game.set_process(false)

	var caretaker: Node2D = game.get_node_or_null("Caretaker") as Node2D
	var guard: Node2D = game.get_node_or_null("StealthTestRoom/ServiceGuard") as Node2D
	var room: Node = game.get_node_or_null("StealthTestRoom")
	var door: Node2D = room.call("get_test_door") as Node2D if room != null and room.has_method("get_test_door") else null
	var environment: CombatEnvironment = game.get_tree().get_first_node_in_group("combat_environment") as CombatEnvironment
	if caretaker == null or guard == null or door == null or environment == null:
		_fail("Environment runtime fixtures are incomplete.")
		return

	caretaker.global_position = door.global_position + Vector2(48.0, 0.0)
	door.call("set_door_state", "open", true)
	await process_frame
	var event_system: EnvironmentEventSystem = game.call("get_environment_event_system_for_testing") as EnvironmentEventSystem
	var latest: Dictionary = event_system.latest_event_for_testing()
	if str(latest.get("type", "")) != EnvironmentEventSystem.EVENT_PASSAGE_OPENED:
		_fail("Opening the door did not publish a passage event: %s" % JSON.stringify(latest))
		return
	var caretaker_profile: Dictionary = game._environment_ai.get_profile("caretaker")
	var caretaker_context: Dictionary = _base_context()
	game.call("_enrich_advanced_context", caretaker_context, caretaker, caretaker, "caretaker", caretaker_profile, {})
	var caretaker_decision: Dictionary = game.call("get_environment_decision_for_testing", "caretaker") as Dictionary
	if str(caretaker_decision.get("environment_action", "")) != EnvironmentReactiveNpcAiSystem.ACTION_SECURE_PASSAGE:
		_fail("Defender did not choose to secure the opened passage: %s" % JSON.stringify(caretaker_decision))
		return
	await game.call("_execute_combat_ai_path", caretaker, [], NpcCombatAiSystem.INTENT_INTERCEPT)
	if str(door.call("get_door_state")) != "closed":
		_fail("Defender did not close the reachable opened door.")
		return

	guard.global_position = door.global_position + Vector2(64.0, 0.0)
	door.call("set_door_state", "open", true)
	await process_frame
	var guard_profile: Dictionary = game._environment_ai.get_profile("service_guard")
	var guard_context: Dictionary = _base_context()
	game.call("_enrich_advanced_context", guard_context, guard, guard, "service_guard", guard_profile, {})
	var guard_decision: Dictionary = game.call("get_environment_decision_for_testing", "service_guard") as Dictionary
	var local_exploit: bool = str(guard_decision.get("environment_action", "")) == EnvironmentReactiveNpcAiSystem.ACTION_EXPLOIT_OPENING
	var coordinated_support: bool = (
		str(guard_decision.get("squad_plan_id", "")) == SquadTacticalPlanSystem.PLAN_HOLD_CHOKEPOINT
		and str(guard_decision.get("squad_plan_action", "")) == "support_choke"
	)
	if not local_exploit and not coordinated_support:
		_fail("Melee guard neither exploited nor supported the opened passage: %s" % JSON.stringify(guard_decision))
		return

	var marksman: Node2D = _instantiate_actor(MARKSMAN_SCENE, game, Vector2(590.0, 230.0))
	if marksman == null:
		_fail("Training marksman could not be instantiated.")
		return
	if not environment.destroy_cover_object("low_barricade"):
		_fail("Low barricade could not be destroyed.")
		return
	await process_frame
	var marksman_profile: Dictionary = game._environment_ai.get_profile("training_marksman")
	var marksman_context: Dictionary = _base_context()
	game.call("_enrich_advanced_context", marksman_context, marksman, marksman, "training_marksman", marksman_profile, {})
	var marksman_decision: Dictionary = game.call("get_environment_decision_for_testing", "training_marksman") as Dictionary
	if str(marksman_decision.get("environment_action", "")) != EnvironmentReactiveNpcAiSystem.ACTION_RECOVER_COVER:
		_fail("Marksman did not seek new cover after destruction: %s" % JSON.stringify(marksman_decision))
		return

	var mage: Node2D = _instantiate_actor(MAGE_SCENE, game, Vector2(400.0, 400.0))
	if mage == null:
		_fail("Training mage could not be instantiated.")
		return
	if not environment.add_hazard("runtime_fire", Rect2(mage.global_position - Vector2(48.0, 48.0), Vector2(96.0, 96.0)), "fire", 1.8, false, 35):
		_fail("Runtime fire hazard could not be created.")
		return
	await process_frame
	var mage_profile: Dictionary = game._environment_ai.get_profile("training_mage")
	var mage_context: Dictionary = _base_context()
	mage_context["spell_plan_score"] = 150.0
	game.call("_enrich_advanced_context", mage_context, mage, mage, "training_mage", mage_profile, {})
	var mage_decision: Dictionary = game.call("get_environment_decision_for_testing", "training_mage") as Dictionary
	if str(mage_decision.get("environment_action", "")) != EnvironmentReactiveNpcAiSystem.ACTION_AVOID_HAZARD:
		_fail("Mage did not abandon a hazardous casting position: %s" % JSON.stringify(mage_decision))
		return
	var grid: BattleGrid = game.call("_get_battle_grid") as BattleGrid
	if grid != null:
		var hazard_cell: Vector2i = grid.world_to_cell(mage.global_position)
		if bool(game.call("_combat_ai_cell_is_available", grid, hazard_cell, {})):
			_fail("AI pathfinding still accepts a hazardous cell.")
			return

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Door, breach, destroyed cover, hazard avoidance and role-specific environment reactions passed.")
	quit(0)


func _base_context() -> Dictionary:
	return {
		"distance_feet": 25,
		"actor_health_ratio": 1.0,
		"target_visible": true,
		"has_target_memory": true,
		"memory_confidence": 1.0,
		"can_attack": true,
		"can_move": true,
		"distance_from_guard_anchor_feet": 0,
		"target_distance_from_guard_anchor_feet": 25,
		"ally_count": 2,
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
		"no_safe_retreat": false
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
	hero.character_name = "Испытатель окружения"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.level = 5
	hero.maximum_health = 42
	hero.current_health = 42
	hero.hit_die_size = 10
	hero.hit_dice_maximum = 5
	hero.hit_dice_current = 5
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
