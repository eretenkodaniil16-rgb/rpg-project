extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"

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
	var opponents: Array[Node] = []
	for target: Node in get_nodes_in_group("combat_targets"):
		if target.has_method("is_combat_active") and bool(target.call("is_combat_active")):
			opponents.append(target)
	if player == null or ally == null or opponents.is_empty():
		_fail("Required combat actors are missing.")
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

	_stage = "movement"
	var moved: bool = false
	for step: Vector2i in [Vector2i.LEFT, Vector2i.RIGHT, Vector2i.UP, Vector2i.DOWN]:
		if bool(game.call("move_controllable_ally_for_testing", step)):
			moved = true
			break
	if not moved or turn_system.movement_remaining_feet >= int(ally.call("get_combat_speed_feet")):
		_fail("Irna could not spend movement through the production grid path.")
		return

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

	_stage = "dodge"
	game.call("force_controllable_ally_turn_for_testing")
	game.call("_on_dodge_requested")
	if turn_system.action_available or not bool(ally.call("is_dodging")):
		_fail("Irna Dodge contract failed.")
		return

	_stage = "attack"
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

	_stage = "close_attack_result"
	var attack_popup: Control = game.get("_attack_popup") as Control
	if attack_popup != null:
		attack_popup.hide()
	await process_frame

	_stage = "end_turn"
	if turn_system.active:
		game.call("force_controllable_ally_turn_for_testing")
		game.call("_on_end_turn_requested")
		if turn_system.is_actor_turn(ally):
			_fail("End Turn did not advance away from Irna.")
			return

	if turn_system.active:
		game.call("_stop_turn_based_combat", "Control smoke complete.")
	game.queue_free()
	await process_frame
	_completed = true
	print("Controllable ally movement, actions, targeting and attack smoke passed.")
	quit(0)


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
