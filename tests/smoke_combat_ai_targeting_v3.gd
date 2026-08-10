extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const TEST_ALLY_ID: String = "companion_test_target_02"


class DummyPartyTarget extends Node2D:
	var current_health: int = 10
	var maximum_health: int = 10
	var armor_class: int = 17
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
		return 5 if ability_id == "dexterity" else 2

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

	for method_name: String in [
		"get_party_combat_target_ids_v3_for_testing",
		"get_party_target_snapshot_v3_for_testing",
		"evaluate_spell_plan_for_target_v3_for_testing",
		"select_enemy_party_target_for_testing"
	]:
		if not game.has_method(method_name):
			_fail("Missing Combat AI Targeting v3 method: %s" % method_name)
			return

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var irina: ControllableAlly = game.call("get_controllable_ally_for_testing") as ControllableAlly
	var mage: Node = _find_actor("training_mage")
	if player == null or irina == null or mage == null or not mage is Node2D:
		_fail("Runtime fixtures for player, Irina or training mage are missing.")
		return

	var second_ally := DummyPartyTarget.new()
	second_ally.add_to_group("controllable_allies")
	second_ally.add_to_group("friendly_combatants")
	game.add_child(second_ally)
	second_ally.global_position = (mage as Node2D).global_position + Vector2(64.0, 0.0)

	var target_ids: Array = game.call("get_party_combat_target_ids_v3_for_testing") as Array
	if "player" not in target_ids or "companion_irna_guard_01" not in target_ids or TEST_ALLY_ID not in target_ids:
		_fail("Party discovery is still hardcoded to hero + Irina: %s" % target_ids)
		return

	var snapshot: Dictionary = game.call("get_party_target_snapshot_v3_for_testing", second_ally) as Dictionary
	if not bool(snapshot.get("supported", false)) or int(snapshot.get("armor_class", 0)) != 17 or int(snapshot.get("dexterity_save", 0)) != 5:
		_fail("Generic ally combat stats were not exposed through the v3 adapter: %s" % snapshot)
		return

	player.global_position = Vector2(160.0, 620.0)
	irina.global_position = Vector2(220.0, 620.0)
	second_ally.current_health = 2
	var selected: Node = game.call("select_enemy_party_target_for_testing", mage) as Node
	if selected != second_ally:
		_fail("Utility targeting did not select the immediate vulnerable second ally.")
		return

	var spell_plan: Dictionary = game.call("evaluate_spell_plan_for_target_v3_for_testing", mage, second_ally) as Dictionary
	if spell_plan.is_empty():
		_fail("Caster produced no spell plan for a non-Irina party target.")
		return

	second_ally.current_health = 10
	var single_spell: Dictionary = {
		"id": "targeting_v3_test_bolt",
		"name": "Тестовый импульс",
		"effect": "auto_hit_spell",
		"damage_dice": [0, 6],
		"damage_bonus": 2,
		"damage_type": "force",
		"on_hit_condition": "poisoned",
		"on_hit_condition_rounds": 2
	}
	game.call("_resolve_enemy_single_target_spell_v3", mage, second_ally, single_spell, 0)
	if second_ally.current_health != 8 or not second_ally.combat_state.has_condition("poisoned"):
		_fail("Single-target spell did not use generic ally HP/CombatantState contract.")
		return

	irina.global_position = second_ally.global_position + Vector2(32.0, 0.0)
	irina.set_current_health(irina.get_maximum_health())
	var area_spell: Dictionary = {
		"id": "targeting_v3_test_area",
		"name": "Тестовое поле",
		"effect": "auto_hit_spell",
		"damage_dice": [0, 6],
		"damage_bonus": 0,
		"damage_type": "force",
		"area": {"shape": "sphere", "origin": "point", "radius_ft": 5},
		"on_hit_condition": "frightened",
		"on_hit_condition_rounds": 1
	}
	game.call("_resolve_enemy_area_spell_against_party_v3", mage, second_ally, area_spell, 0)
	if not second_ally.combat_state.has_condition("frightened"):
		_fail("Area spell did not affect the generic second ally.")
		return
	if not irina.get_combatant_state().has_condition("frightened"):
		_fail("Area spell did not evaluate multiple party members in the same area.")
		return

	second_ally.enter_dying()
	if bool((game.call("get_party_target_snapshot_v3_for_testing", second_ally) as Dictionary).get("available", true)):
		_fail("Downed second ally remained a normal tactical target.")
		return

	game.queue_free()
	await process_frame
	print("Combat AI Targeting v3 actor-agnostic runtime smoke test passed.")
	quit(0)


func _find_actor(actor_id: String) -> Node:
	for target: Node in get_nodes_in_group("combat_targets"):
		if is_instance_valid(target) and target.has_method("get_actor_id") and str(target.call("get_actor_id")) == actor_id:
			return target
	return null


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель AI v3"
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
