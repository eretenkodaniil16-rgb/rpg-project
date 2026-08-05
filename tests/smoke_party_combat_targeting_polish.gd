extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const FORBIDDEN_ACTION_NAME_FRAGMENT: String = "ИРИН"

var _completed: bool = false
var _stage: String = "init"


func _init() -> void:
	call_deferred("_run")
	call_deferred("_watchdog")


func _watchdog() -> void:
	await create_timer(35.0).timeout
	if not _completed:
		_fail("Party combat targeting polish timed out at stage: %s" % _stage)


func _run() -> void:
	_stage = "setup"
	var game_state: Node = root.get_node_or_null("GameState")
	if game_state == null:
		_fail("GameState is missing.")
		return
	game_state.call("new_game")
	game_state.set("player_character", _make_hero())

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	var game: Node = packed.instantiate() if packed != null else null
	if game == null:
		_fail("Game scene could not be instantiated.")
		return
	root.add_child(game)
	for _frame: int in range(24):
		await process_frame

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var ally: Node = game.call("get_controllable_ally_for_testing")
	var mobile_controls: Node = game.get_node_or_null("Interface/MobileControls")
	var action_catalog: Node = game.get_node_or_null("Interface/ActionCatalogUI")
	var target_button: Button = game.get("_target_button") as Button
	var attacker: Node = _find_party_aware_enemy(game)
	if player == null or ally == null or not ally is Node2D or mobile_controls == null or action_catalog == null or target_button == null or attacker == null:
		_fail("Required party targeting fixtures are incomplete.")
		return
	mobile_controls.call("enable_for_testing")

	_stage = "start_irina_turn"
	game.call(
		"start_party_combat_for_testing",
		[attacker] as Array[Node],
		{
			ally.get_instance_id(): 20,
			player.get_instance_id(): 10,
			attacker.get_instance_id(): 1
		}
	)
	await process_frame
	var turn_system: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	if turn_system == null or not turn_system.is_actor_turn(ally):
		_fail("Irina did not receive the deterministic first turn.")
		return

	_stage = "target_button_with_feedback"
	game.call("set_party_target_for_testing", ally, null)
	game.call("show_combat_message", "Проверка выбора цели поверх сообщения.", true)
	game.call("_update_combat_controls")
	if target_button.disabled:
		_fail("The target button is disabled during Irina's valid combat turn.")
		return
	target_button.emit_signal("pressed")
	await process_frame
	if int(game.call("get_party_target_instance_id_for_testing", ally)) == 0:
		_fail("Irina could not select a target while combat feedback was visible.")
		return

	_stage = "generic_action_labels"
	game.call("set_party_target_for_testing", ally, attacker)
	if not bool(game.call("place_controllable_ally_adjacent_for_testing", attacker)):
		_fail("Could not place Irina beside the hostile fixture.")
		return
	mobile_controls.call("simulate_actions_touch_for_testing")
	for _frame: int in range(3):
		await process_frame
	var entries: Dictionary = action_catalog.call("get_entries_for_testing") as Dictionary
	for expected_label: String in [
		"АТАКА КОРОТКИМ МЕЧОМ",
		"РЫВОК",
		"ОТХОД",
		"УКЛОНЕНИЕ",
		"ЗАВЕРШИТЬ ХОД"
	]:
		if not _catalog_has_label(entries, expected_label):
			_fail("Irina's catalogue is missing generic label '%s': %s" % [expected_label, JSON.stringify(entries)])
			return
	for label: String in _catalog_labels(entries):
		if FORBIDDEN_ACTION_NAME_FRAGMENT in label.to_upper():
			_fail("Irina's name remains inside an action label: %s" % label)
			return

	_stage = "catalog_attack"
	action_catalog.call("_emit_action", "attack", "", true)
	for _frame: int in range(5):
		await process_frame
	if turn_system.action_available:
		_fail("The catalogue attack did not consume Irina's action.")
		return

	_stage = "enemy_target_selection"
	game.call("force_player_turn_for_testing")
	await process_frame
	var grid: BattleGrid = game.call("_get_battle_grid") as BattleGrid
	if grid == null:
		_fail("Battle grid is missing for enemy target selection.")
		return
	var attacker_node: Node2D = attacker as Node2D
	attacker_node.global_position = grid.cell_to_world_center(Vector2i(7, 5))
	(ally as Node2D).global_position = grid.cell_to_world_center(Vector2i(10, 5))
	player.global_position = grid.cell_to_world_center(Vector2i(16, 5))
	var selected_target: Node = game.call("select_enemy_party_target_for_testing", attacker)
	if selected_target != ally:
		_fail("The enemy did not select visible Irina standing ahead of the hero.")
		return
	var combat_ai: NpcCombatAiSystem = game.get("_combat_ai") as NpcCombatAiSystem
	var profile: Dictionary = combat_ai.get_profile(str(attacker.call("get_actor_id"))) if combat_ai != null else {}
	var plan: Dictionary = game.call(
		"_plan_enemy_movement_to_party_target",
		attacker_node,
		attacker,
		ally,
		int(attacker.call("get_combat_speed_feet")),
		maxi(int(profile.get("attack_range_feet", 5)), 5),
		maxi(int(profile.get("minimum_range_feet", 0)), 0),
		maxi(int(profile.get("preferred_range_feet", 5)), 5)
	) as Dictionary
	var path: Array = plan.get("path", []) as Array
	if path.is_empty():
		_fail("The enemy could not build a movement plan toward selected Irina.")
		return

	_stage = "enemy_attack_route"
	attacker_node.global_position = grid.cell_to_world_center(Vector2i(9, 5))
	(ally as Node2D).global_position = grid.cell_to_world_center(Vector2i(10, 5))
	player.global_position = grid.cell_to_world_center(Vector2i(16, 5))
	selected_target = game.call("select_enemy_party_target_for_testing", attacker)
	if selected_target != ally:
		_fail("The enemy lost Irina as its selected attack target.")
		return
	var hero_character: PlayerCharacter = game_state.get("player_character") as PlayerCharacter
	if hero_character == null:
		_fail("The hero character model is missing during enemy attack routing.")
		return
	var ally_health_before: int = int(ally.call("get_current_health"))
	var hero_health_before: int = hero_character.current_health
	var attack_result: Dictionary = await game.call(
		"resolve_npc_attack",
		attacker,
		100,
		2,
		3,
		"slashing"
	) as Dictionary
	if str(attack_result.get("target", "")) != "ally" or not bool(attack_result.get("hit", false)):
		_fail("The selected enemy attack was not routed to Irina: %s" % JSON.stringify(attack_result))
		return
	if int(ally.call("get_current_health")) >= ally_health_before:
		_fail("The enemy attack did not damage selected Irina.")
		return
	if hero_character.current_health != hero_health_before:
		_fail("The attack selected for Irina also damaged the hero.")
		return

	if turn_system.active:
		game.call("_stop_turn_based_combat", "Party combat targeting polish complete.")
	game.queue_free()
	await process_frame
	_completed = true
	print("Irina target button, generic action labels and enemy party targeting passed.")
	quit(0)


func _find_party_aware_enemy(game: Node) -> Node:
	var available_value: Variant = game.call("_available_targets")
	if not available_value is Array:
		return null
	for value: Variant in available_value as Array:
		if value is Node and bool(game.call("_enemy_supports_party_targeting", value as Node)):
			return value as Node
	return null


func _catalog_has_label(entries: Dictionary, expected_label: String) -> bool:
	return expected_label in _catalog_labels(entries)


func _catalog_labels(entries: Dictionary) -> Array[String]:
	var labels: Array[String] = []
	for category_value: Variant in entries.values():
		if not category_value is Array:
			continue
		for entry_value: Variant in category_value as Array:
			if entry_value is Dictionary:
				labels.append(str((entry_value as Dictionary).get("label", "")))
	return labels


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель партийных целей"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.maximum_health = 20
	hero.current_health = 20
	hero.starter_loadout_granted = true
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
