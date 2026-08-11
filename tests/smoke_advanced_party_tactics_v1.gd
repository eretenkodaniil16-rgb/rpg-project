extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const MAGE_SCENE: String = "res://scenes/game/combat_ai_training_mage.tscn"
const TEST_ALLY_ID: String = "companion_advanced_tactics_test_02"


class DummyPartyTarget extends Node2D:
	var current_health: int = 12
	var maximum_health: int = 12
	var armor_class: int = 15
	var combat_state: CombatantState = CombatantState.new()

	func get_actor_id() -> String:
		return TEST_ALLY_ID

	func get_combat_name() -> String:
		return "Второй союзник"

	func get_current_health() -> int:
		return current_health

	func get_maximum_health() -> int:
		return maximum_health

	func get_armor_class() -> int:
		return armor_class

	func get_saving_throw_modifier(ability_id: String) -> int:
		return 4 if ability_id == "dexterity" else 2

	func get_combatant_state() -> CombatantState:
		return combat_state

	func can_receive_enemy_attack() -> bool:
		return current_health > 0 and not combat_state.dead

	func set_current_health(value: int) -> void:
		current_health = clampi(value, 0, maximum_health)
		if current_health > 0:
			combat_state.recover_from_zero_hit_points()

	func enter_dying() -> void:
		current_health = 0
		combat_state.enter_dying()

	func is_dodging() -> bool:
		return false


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

	for method_name: String in [
		"record_party_target_sighting_v1_for_testing",
		"get_party_target_memory_v1_for_testing",
		"get_party_tactical_context_v1_for_testing",
		"choose_party_tactical_intent_v1_for_testing"
	]:
		if not game.has_method(method_name):
			_fail("Missing Advanced Party Tactics v1 method: %s" % method_name)
			return

	var mage_packed: PackedScene = load(MAGE_SCENE) as PackedScene
	var mage: Node = mage_packed.instantiate() if mage_packed != null else null
	if mage == null or not mage is Node2D:
		_fail("Training mage scene could not be instantiated.")
		return
	game.add_child(mage)
	(mage as Node2D).global_position = Vector2(560.0, 360.0)
	if not mage.has_method("activate_combat_participant") or not bool(mage.call("activate_combat_participant")):
		_fail("Training mage could not become a combat participant.")
		return

	var second_ally := DummyPartyTarget.new()
	second_ally.add_to_group("controllable_allies")
	second_ally.add_to_group("friendly_combatants")
	game.add_child(second_ally)
	second_ally.global_position = Vector2(400.0, 360.0)

	game.call("record_party_target_sighting_v1_for_testing", mage, second_ally)
	var memory: Dictionary = game.call("get_party_target_memory_v1_for_testing", mage) as Dictionary
	if str(memory.get("target_actor_id", "")) != TEST_ALLY_ID:
		_fail("Party target memory did not store the stable generic ally id: %s" % memory)
		return
	if not memory.get("position", null) is Vector2:
		_fail("Party target memory did not preserve the last known position.")
		return

	second_ally.combat_state.add_condition("prone", 1, mage.get_instance_id())
	var context: Dictionary = game.call("get_party_tactical_context_v1_for_testing", mage, second_ally) as Dictionary
	if not bool(context.get("target_prone", false)):
		_fail("Advanced context did not read prone from the selected generic ally CombatantState.")
		return
	if not is_equal_approx(float(context.get("target_health_ratio", 0.0)), 1.0):
		_fail("Advanced context did not use the selected ally health ratio.")
		return

	var blocked_score: float = NpcCombatAiSystem.BLOCKED_SCORE
	var rally: Dictionary = game.call("choose_party_tactical_intent_v1_for_testing", mage, second_ally, {
		"new_casualty_seen": true,
		"casualty_count": 1,
		"rally_active": false,
		"ally_count": 2,
		"actor_health_ratio": 1.0,
		"target_visible": false,
		"has_target_memory": false,
		"memory_confidence": 0.0,
		"spell_plan_score": blocked_score,
		"better_cover_available": false,
		"can_shove": false,
		"no_useful_attack": false,
		"no_safe_retreat": false,
		"nearest_ally_distance_feet": 5
	}) as Dictionary
	if str(rally.get("intent", "")) != AdvancedNpcCombatAiSystem.INTENT_RALLY:
		_fail("Generic-party casualty context did not select Rally: %s" % rally)
		return

	var take_cover: Dictionary = game.call("choose_party_tactical_intent_v1_for_testing", mage, second_ally, {
		"new_casualty_seen": false,
		"casualty_count": 0,
		"rally_active": false,
		"ally_count": 2,
		"actor_health_ratio": 1.0,
		"target_visible": true,
		"has_target_memory": true,
		"distance_feet": 45,
		"spell_plan_score": blocked_score,
		"better_cover_available": true,
		"can_shove": false,
		"no_useful_attack": false,
		"no_safe_retreat": false,
		"nearest_ally_distance_feet": 10
	}) as Dictionary
	if str(take_cover.get("intent", "")) != AdvancedNpcCombatAiSystem.INTENT_TAKE_COVER:
		_fail("Target-aware cover context did not select Take Cover: %s" % take_cover)
		return

	var regroup: Dictionary = game.call("choose_party_tactical_intent_v1_for_testing", mage, second_ally, {
		"new_casualty_seen": false,
		"casualty_count": 3,
		"rally_active": false,
		"ally_count": 2,
		"actor_health_ratio": 0.5,
		"target_visible": false,
		"has_target_memory": true,
		"memory_confidence": 0.2,
		"spell_plan_score": blocked_score,
		"better_cover_available": false,
		"can_shove": false,
		"no_useful_attack": false,
		"no_safe_retreat": false,
		"nearest_ally_distance_feet": 40
	}) as Dictionary
	if str(regroup.get("intent", "")) != AdvancedNpcCombatAiSystem.INTENT_REGROUP:
		_fail("Generic-party pressure context did not select Regroup: %s" % regroup)
		return

	second_ally.enter_dying()
	var invalid_memory: Dictionary = game.call("get_party_target_memory_v1_for_testing", mage) as Dictionary
	if not invalid_memory.is_empty():
		_fail("Downed generic ally remained a valid remembered tactical target: %s" % invalid_memory)
		return

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Advanced Party Tactics v1 memory, target state, Rally, Take Cover and Regroup passed.")
	quit(0)


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель тактики отряда"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.level = 1
	hero.maximum_health = 20
	hero.current_health = 20
	hero.hit_die_size = 10
	hero.hit_dice_maximum = 1
	hero.hit_dice_current = 1
	hero.starter_loadout_granted = true
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
