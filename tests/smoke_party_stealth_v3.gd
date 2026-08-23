extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const HERO_ID: String = "player_character"
const IRINA_ID: String = "companion_irna_guard_01"
const THIRD_ID: String = "companion_test_stealth_03"

class DummyPartyTarget:
	extends Node2D
	var actor_id: String = THIRD_ID
	var current_health: int = 10
	var combat_state: CombatantState = CombatantState.new()

	func get_actor_id() -> String:
		return actor_id

	func get_combat_name() -> String:
		return "Третий разведчик"

	func get_current_health() -> int:
		return current_health

	func get_maximum_health() -> int:
		return 10

	func get_saving_throw_modifier(ability_id: String) -> int:
		return 3 if ability_id == "dexterity" else 0

	func get_combatant_state() -> CombatantState:
		return combat_state


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
	var game: Node = packed.instantiate() if packed != null else null
	if game == null:
		_fail("Game scene could not be instantiated.")
		return
	root.add_child(game)
	for _frame: int in range(20):
		await process_frame
	game.set_process(false)

	for method_name: StringName in [
		&"get_party_stealth_actor_ids_v3_for_testing",
		&"set_party_stealth_total_v3_for_testing",
		&"get_party_stealth_snapshot_v3_for_testing",
		&"resolve_party_passive_detection_v3_for_testing",
		&"force_party_target_detection_v3_for_testing",
		&"get_party_sighting_memory_v3_for_testing",
		&"get_squad_sighting_memory_v3_for_testing",
		&"report_party_noise_v3_for_testing",
		&"get_persisted_party_stealth_state_v3_for_testing",
		&"is_party_follow_position_exposed_v3_for_testing",
		&"is_player_combat_hidden_v3_for_testing"
	]:
		if not game.has_method(method_name):
			_fail("Final game runtime is missing Party Stealth v3 capability: %s" % method_name)
			return

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var irina: Node = game.call("get_controllable_ally_for_testing") as Node
	var caretaker: Node2D = game.get_node_or_null("Caretaker") as Node2D
	if player == null or irina == null or caretaker == null:
		_fail("Party Stealth v3 fixtures are incomplete.")
		return
	var third := DummyPartyTarget.new()
	third.name = "PartyStealthThirdCompanion"
	game.add_child(third)
	third.add_to_group("controllable_allies")
	third.add_to_group("friendly_combatants")
	third.global_position = player.global_position + Vector2(48.0, 72.0)

	var ids: Array[String] = game.call("get_party_stealth_actor_ids_v3_for_testing") as Array[String]
	for expected_id: String in [HERO_ID, IRINA_ID, THIRD_ID]:
		if not ids.has(expected_id):
			_fail("Party stealth registry missed actor_id %s: %s" % [expected_id, JSON.stringify(ids)])
			return

	game.call("set_party_stealth_total_v3_for_testing", player, 24)
	game.call("set_party_stealth_total_v3_for_testing", irina, 0)
	game.call("set_party_stealth_total_v3_for_testing", third, 12)
	var hero_state: Dictionary = game.call("get_party_stealth_snapshot_v3_for_testing", player) as Dictionary
	var irina_state: Dictionary = game.call("get_party_stealth_snapshot_v3_for_testing", irina) as Dictionary
	var third_state: Dictionary = game.call("get_party_stealth_snapshot_v3_for_testing", third) as Dictionary
	if not bool(hero_state.get("hidden", false)) or int(hero_state.get("stealth_total", 0)) != 24:
		_fail("Hero stealth state was not stored independently.")
		return
	if bool(irina_state.get("hidden", true)) or int(irina_state.get("stealth_total", -1)) != 0:
		_fail("Visible Irina inherited the hero's hidden state.")
		return
	if int(third_state.get("stealth_total", 0)) != 12:
		_fail("Third companion did not receive an independent stealth total.")
		return

	# The live scene gets a few initialization frames before the smoke freezes it.
	# Clear any incidental hero sighting from those frames so this case measures
	# only whether an Irina sighting leaks to an unrelated hidden target.
	var party_stealth_state: PartyStealthStateSystem = game.get("_party_stealth_state_v3") as PartyStealthStateSystem
	if party_stealth_state == null:
		_fail("Party Stealth v3 state system is missing from the final runtime.")
		return
	party_stealth_state.clear_target_memory(HERO_ID)
	game.call("_persist_party_stealth_state_v3")

	var detected: Dictionary = game.call("force_party_target_detection_v3_for_testing", caretaker, irina) as Dictionary
	if str(detected.get("target_actor_id", "")) != IRINA_ID:
		_fail("Forced sighting did not identify Irina.")
		return
	hero_state = game.call("get_party_stealth_snapshot_v3_for_testing", player) as Dictionary
	if not bool(hero_state.get("hidden", false)):
		_fail("Detecting Irina incorrectly revealed the hidden hero.")
		return
	if not (game.call("get_party_sighting_memory_v3_for_testing", caretaker, player) as Dictionary).is_empty():
		_fail("Observer memory magically learned the hidden hero when Irina was detected.")
		return
	var irina_memory: Dictionary = game.call("get_party_sighting_memory_v3_for_testing", caretaker, irina) as Dictionary
	var shared_irina: Dictionary = game.call("get_squad_sighting_memory_v3_for_testing", caretaker, irina) as Dictionary
	if irina_memory.is_empty() or shared_irina.is_empty():
		_fail("Irina sighting was not retained and shared target-specifically.")
		return
	if not (game.call("get_squad_sighting_memory_v3_for_testing", caretaker, player) as Dictionary).is_empty():
		_fail("Squad sighting sharing exposed an unrelated hero target.")
		return

	game.call("set_party_stealth_total_v3_for_testing", irina, 30)
	game.call("set_party_stealth_total_v3_for_testing", third, 5)
	var high_detection: Dictionary = game.call("resolve_party_passive_detection_v3_for_testing", caretaker, irina, 30, false) as Dictionary
	var low_detection: Dictionary = game.call("resolve_party_passive_detection_v3_for_testing", caretaker, third, 30, false) as Dictionary
	if bool(high_detection.get("detected", true)):
		_fail("High-stealth Irina was unexpectedly detected in the controlled passive test: %s" % JSON.stringify(high_detection))
		return
	if not bool(low_detection.get("detected", false)):
		_fail("Low-stealth third companion was not detected independently: %s" % JSON.stringify(low_detection))
		return

	var noise: Dictionary = game.call("report_party_noise_v3_for_testing", third, "normal_step") as Dictionary
	if str(noise.get("source_actor_id", "")) != THIRD_ID:
		_fail("Noise event lost its source_actor_id: %s" % JSON.stringify(noise))
		return
	var persisted: Dictionary = game.call("get_persisted_party_stealth_state_v3_for_testing") as Dictionary
	var target_states: Variant = persisted.get("targets", {})
	if not target_states is Dictionary or not (target_states as Dictionary).has(HERO_ID) or not (target_states as Dictionary).has(IRINA_ID) or not (target_states as Dictionary).has(THIRD_ID):
		_fail("Persistent Party Stealth v3 state does not contain all party actor IDs.")
		return

	# Combat starts because Irina is known. The hero remains hidden and is not
	# injected into every observer's last-known target memory by combat sync.
	game.call("set_party_stealth_total_v3_for_testing", player, 24)
	game.call("set_party_stealth_total_v3_for_testing", irina, 0)
	var alert_record: Dictionary = game.call("get_exploration_alert_record_for_testing", caretaker) as Dictionary
	alert_record["state"] = StealthAlertSystem.STATE_ALERTED
	alert_record["suspicion"] = StealthAlertSystem.SUSPICION_ALERTED
	game.call("_begin_combat_from_party_alert_v3", caretaker, alert_record, irina)
	var turn_system: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	if turn_system == null or not turn_system.active:
		_fail("Irina detection did not transition the encounter into combat.")
		return
	if not bool(game.call("is_player_combat_hidden_v3_for_testing")):
		_fail("Combat transition caused by Irina revealed the hidden hero.")
		return
	hero_state = game.call("get_party_stealth_snapshot_v3_for_testing", player) as Dictionary
	if not bool(hero_state.get("hidden", false)):
		_fail("Exploration stealth state for hero was cleared by another party member's alert.")
		return

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Party Stealth v3 actor registry, independent stealth, target memory, squad sharing, noise source and addressed combat transition passed.")
	quit(0)


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель скрытности"
	hero.character_class_id = "rogue"
	hero.character_class_name = "Плут"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.maximum_health = 24
	hero.current_health = 24
	hero.base_abilities["dexterity"] = 16
	hero.abilities["dexterity"] = 16
	hero.starter_loadout_granted = true
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
