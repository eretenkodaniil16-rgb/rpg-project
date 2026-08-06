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
		_fail("Ally damage smoke timed out at stage: %s" % _stage)


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
	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var ally: Node = game.call("get_controllable_ally_for_testing")
	var available_value: Variant = game.call("_available_targets")
	var attacker: Node = null
	if available_value is Array:
		for value: Variant in available_value as Array:
			if value is Node2D and is_instance_valid(value as Node2D):
				attacker = value as Node
				break
	if player == null or ally == null or attacker == null or not ally is Node2D:
		_fail("Required ally damage actors are missing.")
		return

	_stage = "target_selection"
	(attacker as Node2D).global_position = Vector2(640.0, 360.0)
	(ally as Node2D).global_position = Vector2(672.0, 360.0)
	player.global_position = Vector2(960.0, 360.0)
	if not bool(game.call("enemy_should_attack_ally_for_testing", attacker)):
		_fail("A nearby enemy did not select the closer controllable ally.")
		return

	_stage = "deterministic_enemy_attack"
	var before: int = int(ally.call("get_current_health"))
	var hit: Dictionary = game.call(
		"resolve_npc_attack_against_ally_for_testing",
		attacker,
		20,
		4
	) as Dictionary
	if not bool(hit.get("hit", false)) or str(hit.get("target", "")) != "ally":
		_fail("The NPC attack route did not resolve against Irna: %s" % hit)
		return
	if int(ally.call("get_current_health")) != before - 4:
		_fail("The deterministic enemy attack did not reduce Irna HP by four.")
		return

	_stage = "enter_dying"
	ally.call("set_current_health", 3)
	var downed: Dictionary = game.call(
		"apply_damage_to_controllable_ally_for_testing",
		5,
		false
	) as Dictionary
	var ally_state: CombatantState = ally.call("get_combatant_state") as CombatantState
	if int(ally.call("get_current_health")) != 0 or ally_state == null or ally_state.dead:
		_fail("Non-massive damage did not place Irna in the dying state: %s" % downed)
		return
	if not ally_state.has_condition("unconscious") or not ally_state.has_condition("incapacitated"):
		_fail("Dying Irna is missing unconscious/incapacitated conditions.")
		return

	_stage = "damage_at_zero"
	var critical_zero: Dictionary = game.call(
		"apply_damage_to_controllable_ally_for_testing",
		1,
		true
	) as Dictionary
	if int(critical_zero.get("failures_added", 0)) != 2 or ally_state.death_save_failures != 2:
		_fail("Critical damage at 0 HP did not add two death-save failures.")
		return
	var final_zero: Dictionary = game.call(
		"apply_damage_to_controllable_ally_for_testing",
		1,
		false
	) as Dictionary
	if not bool(final_zero.get("dead", false)) or not ally_state.dead:
		_fail("The third death-save failure did not kill Irna.")
		return

	game.queue_free()
	await process_frame
	_completed = true
	print("Controllable ally enemy targeting, damage, dying and death smoke passed.")
	quit(0)


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель урона союзника"
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
