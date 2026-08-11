extends SceneTree


class DummyPartyTarget extends Node2D:
	var actor_id: String = "companion_test_02"
	var combat_name: String = "Тестовый союзник"
	var current_health: int = 9
	var maximum_health: int = 14
	var armor_class: int = 16
	var combat_state: CombatantState = CombatantState.new()

	func get_actor_id() -> String:
		return actor_id

	func get_combat_name() -> String:
		return combat_name

	func get_current_health() -> int:
		return current_health

	func get_maximum_health() -> int:
		return maximum_health

	func get_armor_class() -> int:
		return armor_class

	func get_saving_throw_modifier(ability_id: String) -> int:
		return 4 if ability_id == "dexterity" else 1

	func get_combatant_state() -> CombatantState:
		return combat_state

	func can_receive_enemy_attack() -> bool:
		return not combat_state.dead

	func set_current_health(value: int) -> void:
		current_health = clampi(value, 0, maximum_health)


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var adapter := CombatAiPartyTargetAdapter.new()
	var player := Node2D.new()
	var character := PlayerCharacter.new()
	character.maximum_health = 20
	character.current_health = 13
	var player_state := CombatantState.new()
	var ally := DummyPartyTarget.new()

	if not adapter.is_supported(player, player):
		_fail("Primary player is not supported by the target adapter.")
		return
	if not adapter.is_supported(ally, player):
		_fail("A second ally implementing the combat contract is not supported.")
		return
	if adapter.get_actor_id(ally, player) != "companion_test_02":
		_fail("Stable actor_id was not preserved for a generic ally.")
		return
	if adapter.get_armor_class(ally, player, 12) != 16:
		_fail("Generic ally armor class was not read from the target contract.")
		return
	if adapter.get_saving_throw_modifier(ally, "dexterity", player, character) != 4:
		_fail("Generic ally saving throw modifier was not read from the target contract.")
		return
	if not is_equal_approx(adapter.get_health_ratio(ally, player, character), 9.0 / 14.0):
		_fail("Generic ally health ratio is incorrect.")
		return
	if not adapter.is_available(ally, player, character, player_state):
		_fail("Living generic ally was not considered targetable.")
		return
	ally.current_health = 0
	ally.combat_state.enter_dying()
	if adapter.is_available(ally, player, character, player_state):
		_fail("Downed ally remained in normal target candidates.")
		return
	ally.current_health = 5
	ally.combat_state.recover_from_zero_hit_points()
	ally.combat_state.dead = true
	if adapter.is_available(ally, player, character, player_state):
		_fail("Dead ally remained in normal target candidates.")
		return
	if adapter.get_current_health(player, player, character) != 13:
		_fail("Primary player health fallback is incorrect.")
		return

	print("Combat AI party target adapter tests passed.")
	quit(0)


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
