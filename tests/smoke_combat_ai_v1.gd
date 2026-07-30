extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const EXPECTED_RUNTIME: String = "res://scripts/game/game_squad_tactical_plans_runtime.gd"


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
	for _frame: int in range(12):
		await process_frame
	var script: Script = game.get_script() as Script
	if script == null or script.resource_path != EXPECTED_RUNTIME:
		_fail("Game scene does not use the corpse-aware Combat AI runtime.")
		return
	game.set_process(false)

	for role_id: String in [NpcCombatAiSystem.ROLE_MELEE, NpcCombatAiSystem.ROLE_RANGED, NpcCombatAiSystem.ROLE_DEFENDER]:
		var role_profile: Dictionary = game.call("get_combat_ai_role_profile_for_testing", role_id) as Dictionary
		if role_profile.is_empty() or str(role_profile.get("role", "")) != role_id:
			_fail("Combat AI role profile is missing: %s" % role_id)
			return

	var caretaker_profile: Dictionary = game.call("get_combat_ai_profile_for_testing", "caretaker") as Dictionary
	var guard_profile: Dictionary = game.call("get_combat_ai_profile_for_testing", "service_guard") as Dictionary
	if str(caretaker_profile.get("role", "")) != NpcCombatAiSystem.ROLE_DEFENDER:
		_fail("Caretaker is not assigned to the defender role.")
		return
	if str(guard_profile.get("role", "")) != NpcCombatAiSystem.ROLE_MELEE:
		_fail("Service guard is not assigned to the melee role.")
		return

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var caretaker: Node2D = game.get_node_or_null("Caretaker") as Node2D
	if player == null or caretaker == null:
		_fail("Player or caretaker is missing from the game scene.")
		return

	var defender_return: Dictionary = game.call("get_ai_intent_for_testing", "caretaker", {
		"distance_feet": 45,
		"actor_health_ratio": 1.0,
		"target_visible": true,
		"can_attack": false,
		"can_move": true,
		"distance_from_guard_anchor_feet": 40,
		"target_distance_from_guard_anchor_feet": 45
	}) as Dictionary
	if str(defender_return.get("intent", "")) != NpcCombatAiSystem.INTENT_GUARD:
		_fail("Defender did not return to its guard position outside the leash.")
		return

	var defender_intercept: Dictionary = game.call("get_ai_intent_for_testing", "caretaker", {
		"distance_feet": 20,
		"actor_health_ratio": 1.0,
		"target_visible": true,
		"can_attack": false,
		"can_move": true,
		"distance_from_guard_anchor_feet": 0,
		"target_distance_from_guard_anchor_feet": 20
	}) as Dictionary
	if str(defender_intercept.get("intent", "")) != NpcCombatAiSystem.INTENT_INTERCEPT:
		_fail("Defender did not intercept a target inside the guard zone.")
		return

	var melee_advance: Dictionary = game.call("get_ai_intent_for_testing", "service_guard", {
		"distance_feet": 25,
		"actor_health_ratio": 1.0,
		"target_visible": true,
		"can_attack": false,
		"can_move": true
	}) as Dictionary
	if str(melee_advance.get("intent", "")) != NpcAiSystem.INTENT_ADVANCE:
		_fail("Melee service guard did not advance toward a distant target.")
		return

	game.call("_ensure_combat_ai_guard_anchor", "caretaker", caretaker.global_position)
	var first_anchor: Vector2 = game.call("get_combat_ai_anchor_for_testing", "caretaker") as Vector2
	caretaker.global_position += Vector2(160.0, 0.0)
	game.call("_ensure_combat_ai_guard_anchor", "caretaker", caretaker.global_position)
	var second_anchor: Vector2 = game.call("get_combat_ai_anchor_for_testing", "caretaker") as Vector2
	if first_anchor != second_anchor:
		_fail("Defender guard anchor changed after displacement.")
		return

	var ranged_profile: Dictionary = game.call("get_combat_ai_role_profile_for_testing", NpcCombatAiSystem.ROLE_RANGED) as Dictionary
	if int(ranged_profile.get("minimum_range_feet", 0)) <= DistanceSystem.MELEE_REACH_FEET or int(ranged_profile.get("preferred_range_feet", 0)) >= int(ranged_profile.get("attack_range_feet", 0)):
		_fail("Ranged role distance band is invalid.")
		return

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Combat AI v1 through corpse runtime, role profiles, guard anchors and deterministic decisions passed.")
	quit(0)


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель AI"
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
