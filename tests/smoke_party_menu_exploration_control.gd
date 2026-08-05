extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const PLAYER_MEMBER_ID: String = "player_character"
const IRINA_MEMBER_ID: String = "companion_irna_guard_01"

var _completed: bool = false
var _stage: String = "init"


class PartyMenuTarget:
	extends Node2D

	var current_health: int = 50
	var _combat_state: CombatantState = CombatantState.new()

	func _ready() -> void:
		add_to_group("combat_targets")

	func get_combat_name() -> String:
		return "Цель меню отряда"

	func get_current_health() -> int:
		return current_health

	func get_armor_class() -> int:
		return 10

	func get_initiative_modifier() -> int:
		return 0

	func get_combat_speed_feet() -> int:
		return 0

	func get_combatant_state() -> CombatantState:
		return _combat_state

	func is_combat_active() -> bool:
		return current_health > 0

	func can_take_combat_turn() -> bool:
		return current_health > 0

	func is_hostile() -> bool:
		return true

	func enter_combat_hostile() -> void:
		pass

	func set_turn_active(_value: bool) -> void:
		pass

	func set_combat_targeted(_value: bool) -> void:
		pass

	func set_combat_overlay_visible(_value: bool) -> void:
		pass

	func set_turn_based_mode(_value: bool) -> void:
		pass

	func perform_combat_turn_attack() -> void:
		pass

	func perform_opportunity_attack() -> void:
		pass

	func receive_player_attack(result: AttackResult, _show_interface: bool = true) -> void:
		if result.hit:
			current_health = maxi(1, current_health - maxi(result.damage, 0))
		result.target_health_after = current_health
		result.target_max_health = 50


func _init() -> void:
	call_deferred("_run")
	call_deferred("_watchdog")


func _watchdog() -> void:
	await create_timer(30.0).timeout
	if not _completed:
		_fail("Party menu smoke timed out at stage: %s" % _stage)


func _run() -> void:
	_stage = "setup"
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState is missing.")
		return
	state.call("new_game")
	state.set("player_character", _make_hero())

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	var game: Node = packed.instantiate() if packed != null else null
	if game == null:
		_fail("Game scene could not be instantiated.")
		return
	root.add_child(game)
	for _frame: int in range(24):
		await process_frame

	var player: Node = game.get_node_or_null("Player")
	var ally: Node = game.call("get_controllable_ally_for_testing")
	var party_menu: Node = game.get_node_or_null("Interface/PartyMenuUI")
	var mobile_controls: Node = game.get_node_or_null("Interface/MobileControls")
	var action_catalog: Node = game.get_node_or_null("Interface/ActionCatalogUI")
	var target_button: Button = game.get("_target_button") as Button
	if player == null or ally == null or party_menu == null or mobile_controls == null or action_catalog == null or target_button == null:
		_fail("Party menu fixtures are incomplete.")
		return
	mobile_controls.call("enable_for_testing")

	_stage = "default_follow"
	var default_snapshot: Dictionary = game.call("get_party_menu_snapshot_for_testing") as Dictionary
	if str(default_snapshot.get("active_member_id", "")) != PLAYER_MEMBER_ID:
		_fail("The hero is not selected by default in the party menu.")
		return
	if not bool(player.call("is_party_input_enabled")):
		_fail("The hero input is disabled before manual ally takeover.")
		return
	if bool(ally.call("is_manual_control_enabled")) or not bool(ally.call("is_following_player")):
		_fail("Irina does not begin in automatic follow mode.")
		return

	_stage = "manual_irina_control"
	var player_position_before: Vector2 = (player as Node2D).global_position
	var ally_position_before: Vector2 = (ally as Node2D).global_position
	party_menu.call("request_member_for_testing", IRINA_MEMBER_ID)
	await process_frame
	if game.call("get_exploration_controlled_actor_for_testing") != ally:
		_fail("Selecting Irina did not make her the exploration input owner.")
		return
	if bool(player.call("is_party_input_enabled")):
		_fail("The hero kept exploration input after Irina was selected.")
		return
	if not bool(ally.call("is_manual_control_enabled")):
		_fail("Irina did not enter manual exploration mode.")
		return
	mobile_controls.call("move_joystick_for_testing", Vector2.RIGHT)
	for _frame: int in range(10):
		await physics_frame
	mobile_controls.call("move_joystick_for_testing", Vector2.ZERO)
	await physics_frame
	if (ally as Node2D).global_position.is_equal_approx(ally_position_before):
		_fail("The mobile joystick did not move manually selected Irina.")
		return
	if not (player as Node2D).global_position.is_equal_approx(player_position_before):
		_fail("Moving Irina also moved the hero.")
		return

	_stage = "resume_follow"
	party_menu.call("request_member_for_testing", PLAYER_MEMBER_ID)
	await process_frame
	if game.call("get_exploration_controlled_actor_for_testing") != player:
		_fail("The party menu did not return exploration control to the hero.")
		return
	if not bool(player.call("is_party_input_enabled")) or bool(ally.call("is_manual_control_enabled")):
		_fail("Returning to the hero did not release Irina from manual control.")
		return
	(player as Node2D).global_position = Vector2(760.0, 360.0)
	(ally as Node2D).global_position = Vector2(500.0, 360.0)
	var follow_position_before: Vector2 = (ally as Node2D).global_position
	for _frame: int in range(20):
		await physics_frame
	if (ally as Node2D).global_position.x <= follow_position_before.x:
		_fail("Irina did not resume automatic following after the hero was reselected.")
		return

	_stage = "initiative_lock"
	var target := PartyMenuTarget.new()
	target.name = "PartyMenuTarget"
	target.global_position = Vector2(950.0, 360.0)
	game.add_child(target)
	await process_frame
	var opponents: Array[Node] = [target]
	game.call(
		"start_party_combat_for_testing",
		opponents,
		{
			ally.get_instance_id(): 20,
			player.get_instance_id(): 10,
			target.get_instance_id(): 1
		}
	)
	await process_frame
	var turn_system: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	if turn_system == null or not turn_system.is_actor_turn(ally):
		_fail("Irina did not receive the deterministic initiative turn.")
		return
	var combat_snapshot: Dictionary = game.call("get_party_menu_snapshot_for_testing") as Dictionary
	if str(combat_snapshot.get("active_member_id", "")) != IRINA_MEMBER_ID:
		_fail("The party menu does not track Irina's initiative turn.")
		return
	party_menu.call("request_member_for_testing", PLAYER_MEMBER_ID)
	await process_frame
	if not turn_system.is_actor_turn(ally):
		_fail("The party menu allowed the player to bypass initiative order.")
		return

	_stage = "full_targeting"
	if not bool(game.call("place_controllable_ally_adjacent_for_testing", target)):
		_fail("Could not place Irina beside the test target.")
		return
	target_button.emit_signal("pressed")
	await process_frame
	if int(game.call("get_party_target_instance_id_for_testing", ally)) != target.get_instance_id():
		_fail("The standard target button did not assign Irina's own target.")
		return
	mobile_controls.call("simulate_actions_touch_for_testing")
	for _frame: int in range(3):
		await process_frame
	var entries: Dictionary = action_catalog.call("get_entries_for_testing") as Dictionary
	if _catalog_has_action(entries, "select_ally_target"):
		_fail("Irina still exposes NPC-style target switching inside the action catalogue.")
		return
	for required_action: String in ["attack", "confirm_move", "dash", "disengage", "dodge", "end_turn"]:
		if not _catalog_has_action(entries, required_action):
			_fail("Irina's playable catalogue is missing '%s'." % required_action)
			return

	if turn_system.active:
		game.call("_stop_turn_based_combat", "Party menu smoke complete.")
	game.queue_free()
	await process_frame
	_completed = true
	print("Party menu selection, manual Irina exploration, follow resume, initiative lock and full target button passed.")
	quit(0)


func _catalog_has_action(entries: Dictionary, action_id: String) -> bool:
	for category_value: Variant in entries.values():
		if not category_value is Array:
			continue
		for entry_value: Variant in category_value as Array:
			if entry_value is Dictionary and str((entry_value as Dictionary).get("id", "")) == action_id:
				return true
	return false


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель меню отряда"
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
