extends SceneTree

class FakeCombatant:
	extends Node
	var combat_name: String
	var initiative_modifier: int
	var active: bool = true

	func _init(name_value: String, modifier_value: int) -> void:
		combat_name = name_value
		initiative_modifier = modifier_value

	func get_combat_name() -> String:
		return combat_name

	func get_initiative_modifier() -> int:
		return initiative_modifier

	func is_combat_active() -> bool:
		return active


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var player := FakeCombatant.new("Герой", 2)
	var enemy := FakeCombatant.new("Противник", 0)
	root.add_child(player)
	root.add_child(enemy)
	var system := TurnBasedCombatSystem.new()
	var overrides: Dictionary = {
		player.get_instance_id(): 2,
		enemy.get_instance_id(): 4
	}
	system.start_combat(player, [enemy], 2, overrides)
	if not system.active or system.round_number != 1:
		_fail("Combat did not start in round one.")
		return
	if system.current_actor() != player:
		_fail("Dexterity tie-breaker did not place the player first.")
		return
	if not system.action_available or not system.bonus_action_available or system.movement_remaining_feet != 30:
		_fail("Player turn resources were not initialized.")
		return
	if not system.spend_movement(5) or system.movement_remaining_feet != 25:
		_fail("Grid movement did not spend five feet.")
		return
	if not system.use_dash() or system.action_available or system.movement_remaining_feet != 55:
		_fail("Dash did not consume the action and add movement.")
		return
	if not system.consume_bonus_action() or system.bonus_action_available:
		_fail("Bonus action was not consumed.")
		return
	system.force_current_actor_for_testing(player)
	if not system.use_dodge() or not system.dodging:
		_fail("Dodge did not activate.")
		return
	system.advance_turn()
	if system.current_actor() != enemy or not system.dodging:
		_fail("Dodge should persist through the enemy turn.")
		return
	if not system.has_reaction(enemy) or not system.consume_reaction(enemy) or system.has_reaction(enemy):
		_fail("Enemy reaction resource did not behave correctly.")
		return
	system.advance_turn()
	if system.current_actor() != player or system.round_number != 2:
		_fail("Initiative order did not advance to the next round.")
		return
	if system.dodging:
		_fail("Dodge should end at the start of the player's next turn.")
		return
	system.stop_combat()
	if system.active or not system.entries.is_empty():
		_fail("Combat state did not stop cleanly.")
		return
	player.queue_free()
	enemy.queue_free()
	print("Turn based combat system tests passed.")
	quit(0)
