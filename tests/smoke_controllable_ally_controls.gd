extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const EXPECTED_MOBILE_SCRIPT: String = "res://scripts/ui/mobile_controls_party_routing.gd"

var _completed: bool = false
var _stage: String = "init"


func _init() -> void:
	call_deferred("_run")
	call_deferred("_watchdog")


func _watchdog() -> void:
	await create_timer(25.0).timeout
	if not _completed:
		_fail("Ally control smoke timed out at stage: %s" % _stage)


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
	for _frame: int in range(18):
		await process_frame

	_stage = "locate_actors"
	var player: Node = game.get_node_or_null("Player")
	var ally: Node = game.call("get_controllable_ally_for_testing")
	var mobile_controls: Node = game.get_node_or_null("Interface/MobileControls")
	var action_catalog: Node = game.get_node_or_null("Interface/ActionCatalogUI")
	var available_value: Variant = game.call("_available_targets")
	var opponents: Array[Node] = []
	if available_value is Array:
		for value: Variant in available_value as Array:
			if value is Node and is_instance_valid(value as Node):
				opponents.append(value as Node)
	if player == null or ally == null or mobile_controls == null or action_catalog == null or opponents.is_empty():
		_fail("Required combat actors or mobile UI nodes are missing.")
		return
	var mobile_script: Script = mobile_controls.get_script() as Script
	if mobile_script == null or mobile_script.resource_path != EXPECTED_MOBILE_SCRIPT:
		_fail("Game scene does not use the party-aware mobile controls runtime.")
		return
	var opponent: Node = opponents[0]
	var turn_system: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	turn_system.set_pending_player_controlled_actors([ally])
	turn_system.start_combat(
		player,
		[opponent],
		0,
		{
			player.get_instance_id(): 10,
			ally.get_instance_id(): 18,
			opponent.get_instance_id(): 5
		}
	)
	game.call("_begin_current_turn")
	if not turn_system.is_actor_turn(ally):
		_fail("Irna did not receive the first deterministic turn.")
		return
	mobile_controls.call("enable_for_testing")

	_stage = "mobile_movement"
	var moved: bool = false
	for direction: Vector2 in [Vector2.LEFT, Vector2.RIGHT, Vector2.UP, Vector2.DOWN]:
		var position_before: Vector2 = (ally as Node2D).global_position
		mobile_controls.call("move_joystick_for_testing", direction)
		for _frame: int in range(3):
			await process_frame
		mobile_controls.call("move_joystick_for_testing", Vector2.ZERO)
		await process_frame
		if not (ally as Node2D).global_position.is_equal_approx(position_before):
			moved = true
			break
	if not moved or turn_system.movement_remaining_feet >= int(ally.call("get_combat_speed_feet")):
		_fail("Real mobile joystick input did not move Irna or spend movement.")
		return

	_stage = "mobile_action_catalog"
	game.call("force_controllable_ally_turn_for_testing")
	mobile_controls.call("simulate_actions_touch_for_testing")
	for _frame: int in range(3):
		await process_frame
	if not bool(action_catalog.call("is_catalog_open")):
		_fail("The real mobile Actions button could not keep Irna's catalogue open.")
		return
	var entries: Dictionary = action_catalog.call("get_entries_for_testing") as Dictionary
	if not _catalog_has_action(entries, "attack") or not _catalog_has_action(entries, "dodge") or not _catalog_has_action(entries, "end_turn"):
		_fail("Irna's mobile catalogue is missing required actions: %s" % JSON.stringify(entries))
		return
	action_catalog.emit_signal("action_requested", "dodge")
	await process_frame
	if turn_system.action_available or not bool(ally.call("is_dodging")):
		_fail("Irna Dodge did not execute through the real action catalogue signal.")
		return
	action_catalog.call("close_catalog")

	_stage = "dash"
	game.call("force_controllable_ally_turn_for_testing")
	var base_speed: int = int(ally.call("get_combat_speed_feet"))
	game.call("_on_dash_requested")
	if turn_system.action_available or turn_system.movement_remaining_feet != base_speed * 2:
		_fail("Irna Dash did not consume action and double movement.")
		return

	_stage = "disengage"
	game.call("force_controllable_ally_turn_for_testing")
	game.call("_on_disengage_requested")
	if turn_system.action_available or not turn_system.disengaged:
		_fail("Irna Disengage contract failed.")
		return

	_stage = "end_turn_catalog"
	game.call("force_controllable_ally_turn_for_testing")
	action_catalog.emit_signal("action_requested", "end_turn")
	await process_frame
	if turn_system.active and turn_system.is_actor_turn(ally):
		_fail("Action catalogue End Turn did not advance away from Irna.")
		return

	_stage = "attack"
	if not turn_system.active:
		turn_system.set_pending_player_controlled_actors([ally])
		turn_system.start_combat(
			player,
			[opponent],
			0,
			{
				player.get_instance_id(): 10,
				ally.get_instance_id(): 18,
				opponent.get_instance_id(): 5
			}
		)
	game.call("force_controllable_ally_turn_for_testing")
	if not bool(game.call("place_controllable_ally_adjacent_for_testing", opponent)):
		_fail("Could not place Irna in a legal adjacent test cell.")
		return
	var attack: Dictionary = await game.call(
		"perform_controllable_ally_attack_for_testing",
		opponent,
		20
	) as Dictionary
	if not bool(attack.get("success", false)) or not bool(attack.get("hit", false)):
		_fail("Irna production attack did not resolve as a hit: %s" % attack)
		return
	if turn_system.action_available:
		_fail("Irna attack did not consume the primary action.")
		return

	var attack_popup: Control = game.get("_attack_popup") as Control
	if attack_popup != null:
		attack_popup.hide()
	if turn_system.active:
		game.call("_stop_turn_based_combat", "Control smoke complete.")
	game.queue_free()
	await process_frame
	_completed = true
	print("Controllable ally mobile joystick, action catalogue, turn actions and attack smoke passed.")
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
	hero.character_name = "Испытатель управления"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.maximum_health = 14
	hero.current_health = 14
	hero.starter_loadout_granted = true
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
