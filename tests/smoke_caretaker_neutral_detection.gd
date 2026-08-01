extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const FIRST_ROOM_ID: String = "vault_guard_post_01"
const CARETAKER_ID: String = "caretaker"
const COMBAT_STARTED_FLAG: String = "vault_guard_post_room1_combat_started"
const NOTICED_FLAG: String = "vault_guard_post_caretaker_noticed"


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
	state.set("player_position", Vector2(320.0, 360.0))

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	var game: Node = packed.instantiate() if packed != null else null
	if game == null:
		_fail("Game scene could not be instantiated.")
		return
	root.add_child(game)
	for _frame: int in range(12):
		await process_frame
	game.set_process(false)

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var caretaker: Node = game.get_node_or_null("Caretaker")
	var turn_system: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	var message_label: Label = game.get_node_or_null("Interface/CombatMessageLabel") as Label
	if player == null or caretaker == null or turn_system == null or message_label == null:
		_fail("Neutral caretaker test fixtures are incomplete.")
		return

	player.global_position = Vector2(620.0, 360.0)
	state.set("player_position", player.global_position)
	game.call("_evaluate_guard_post_state")
	if str(state.call("get_encounter_status", FIRST_ROOM_ID)) != EncounterSystem.STATUS_ACTIVE:
		_fail("First-room encounter did not activate before visual detection.")
		return

	var record: Dictionary = state.call("get_stealth_alert_record", CARETAKER_ID) as Dictionary
	record["state"] = StealthAlertSystem.STATE_ALERTED
	record["suspicion"] = StealthAlertSystem.SUSPICION_ALERTED
	record["last_known_position"] = [player.global_position.x, player.global_position.y]
	game.call("_begin_combat_from_alert", caretaker, record)
	await process_frame

	if turn_system.active:
		_fail("Caretaker visual detection started turn-based combat.")
		return
	if caretaker.has_method("is_hostile") and bool(caretaker.call("is_hostile")):
		_fail("Caretaker became hostile from line of sight alone.")
		return
	if bool(state.call("get_flag", COMBAT_STARTED_FLAG, false)):
		_fail("Visual detection incorrectly locked the first room to the combat route.")
		return
	if not bool(state.call("get_flag", NOTICED_FLAG, false)):
		_fail("Caretaker first-contact detection was not persisted.")
		return
	if not message_label.text.contains("не нападает"):
		_fail("Neutral detection did not explain that the caretaker remains non-hostile: %s" % message_label.text)
		return

	caretaker.call("enter_combat_hostile")
	game.call("_start_turn_based_combat", caretaker)
	await process_frame
	if not turn_system.active:
		_fail("Explicit caretaker provocation no longer starts combat.")
		return
	if not bool(state.call("get_flag", COMBAT_STARTED_FLAG, false)):
		_fail("Explicit caretaker provocation did not lock the combat route.")
		return
	if caretaker.has_method("is_hostile") and not bool(caretaker.call("is_hostile")):
		_fail("Explicitly provoked caretaker did not remain hostile in combat.")
		return

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Neutral caretaker detection and explicit provocation combat transition passed.")
	quit(0)


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель нейтрального Смотрителя"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.level = 3
	hero.maximum_health = 28
	hero.current_health = 28
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
