extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const AUTOSAVE_PATH: String = "user://save_slots/autosave.json"


class DeterministicLethalCombatSystem:
	extends CombatSystem

	func perform_basic_attack(
		character: PlayerCharacter,
		target_armor_class: int,
		weapon: Dictionary = {},
		natural_roll_override: int = -1,
		damage_rolls_override: Array[int] = [],
		attack_context: Dictionary = {}
	) -> AttackResult:
		var result := AttackResult.new()
		result.attacker_name = character.character_name
		result.attack_name = str(weapon.get("name", "Смертельный тестовый удар"))
		result.target_name = str(attack_context.get("target_name", "Смотритель"))
		result.damage_type = "slashing"
		result.target_armor_class = target_armor_class
		result.first_roll = 20
		result.natural_roll = 20
		result.total = 99
		result.hit = true
		result.critical = true
		result.melee_attack = true
		result.range_state = "melee"
		result.damage = 9999
		result.damage_before_mitigation = 9999
		return result


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	var save_path: String = ProjectSettings.globalize_path(AUTOSAVE_PATH)
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

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var caretaker: Node2D = game.get_node_or_null("Caretaker") as Node2D
	var guard: Node = game.get_node_or_null("StealthTestRoom/ServiceGuard")
	var turn_system: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	if player == null or caretaker == null or guard == null or turn_system == null:
		_fail("Opening-attack test fixtures are incomplete.")
		return

	# The attack begins in exploration. The caretaker is guaranteed to die from
	# one hit while the service guard remains a living member of the same authored
	# encounter roster.
	caretaker.set("maximum_health", 1)
	caretaker.set("current_health", 1)
	guard.set("maximum_health", 40)
	guard.set("current_health", 40)
	player.global_position = caretaker.global_position + Vector2(-48.0, 0.0)
	state.set("player_position", player.global_position)
	game.set("_combat_system", DeterministicLethalCombatSystem.new())
	game.call("_set_selected_target", caretaker)
	if bool(game.call("is_turn_based_combat_active")):
		_fail("Initiative was already active before the opening attack.")
		return
	if not bool(game.call("_target_is_valid", caretaker)):
		_fail("Caretaker is not a valid visible opening target in the test fixture.")
		return

	await game.call("_request_attack")
	for _frame: int in range(6):
		await process_frame

	if not bool(caretaker.call("is_dead_body")):
		_fail("Deterministic opening attack did not kill the caretaker.")
		return
	if not turn_system.active:
		_fail("Killing the opening target before initiative prevented combat from starting.")
		return
	var initiative_ids: Array[String] = _initiative_actor_ids(turn_system)
	if "service_guard" not in initiative_ids:
		_fail("Living service guard did not enter initiative after the caretaker died: %s" % JSON.stringify(initiative_ids))
		return
	if not bool(guard.call("is_hostile")):
		_fail("Service guard remained neutral after witnessing the lethal opening attack.")
		return
	if guard.has_method("is_combat_active") and not bool(guard.call("is_combat_active")):
		_fail("Service guard was added to initiative without an active combat state.")
		return

	game.call("_stop_turn_based_combat", "Тест внезапной атаки завершён.")
	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Lethal exploration opener preserves the living allied roster and starts initiative.")
	quit(0)


func _initiative_actor_ids(turn_system: TurnBasedCombatSystem) -> Array[String]:
	var result: Array[String] = []
	for entry: Dictionary in turn_system.entries:
		if bool(entry.get("is_player", false)):
			continue
		var actor: Node = entry.get("node") as Node
		if is_instance_valid(actor) and actor.has_method("get_actor_id"):
			result.append(str(actor.call("get_actor_id")))
	return result


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель внезапной атаки"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.level = 5
	hero.maximum_health = 500
	hero.current_health = 500
	hero.hit_die_size = 10
	hero.hit_dice_maximum = 5
	hero.hit_dice_current = 5
	hero.abilities["strength"] = 20
	hero.base_abilities["strength"] = 20
	hero.equipped_weapon_id = "greatsword"
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
