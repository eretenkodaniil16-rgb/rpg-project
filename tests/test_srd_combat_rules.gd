extends SceneTree

var _rules: SrdCombatRules = SrdCombatRules.new()


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var roll: Dictionary = _rules.roll_d20(3, true, false, [4, 17])
	if int(roll.get("natural", 0)) != 17 or int(roll.get("total", 0)) != 20:
		_fail("Advantage did not select the higher d20.")
		return
	roll = _rules.roll_d20(3, true, true, [4, 17])
	if int(roll.get("natural", 0)) != 4 or bool(roll.get("advantage", true)) or bool(roll.get("disadvantage", true)):
		_fail("Advantage and disadvantage did not cancel.")
		return

	var state := CombatantState.new()
	state.damage_resistances = ["fire"]
	state.temporary_hit_points = 3
	var damage: Dictionary = _rules.resolve_damage(10, "fire", state)
	if int(damage.get("applied", -1)) != 2 or int(damage.get("absorbed", -1)) != 3 or state.temporary_hit_points != 0:
		_fail("Resistance and temporary hit points were applied incorrectly: %s" % damage)
		return
	state.damage_immunities = ["poison"]
	if int(_rules.resolve_damage(12, "poison", state).get("applied", -1)) != 0:
		_fail("Damage immunity did not reduce damage to zero.")
		return
	state.damage_vulnerabilities = ["cold"]
	if int(_rules.resolve_damage(6, "cold", state).get("applied", -1)) != 12:
		_fail("Damage vulnerability did not double damage.")
		return

	state.set_concentration("test_spell", 1)
	var concentration: Dictionary = _rules.resolve_concentration_check(0, 22, state, [5])
	if int(concentration.get("dc", 0)) != 11 or bool(concentration.get("success", true)) or not state.concentrating_on.is_empty():
		_fail("Concentration failure or DC was incorrect: %s" % concentration)
		return

	state = CombatantState.new()
	state.enter_dying()
	var death: Dictionary = _rules.resolve_death_save(state, 1)
	if int(death.get("failures", 0)) != 2 or bool(death.get("dead", false)):
		_fail("Natural 1 death save must add two failures.")
		return
	death = _rules.resolve_death_save(state, 9)
	if not bool(death.get("dead", false)):
		_fail("Third death save failure did not kill the combatant.")
		return
	state = CombatantState.new()
	state.enter_dying()
	death = _rules.resolve_death_save(state, 20)
	if not bool(death.get("regained_hit_point", false)) or state.has_condition("unconscious"):
		_fail("Natural 20 death save did not restore consciousness.")
		return

	var attacker := CombatantState.new()
	var defender := CombatantState.new()
	defender.add_condition("paralyzed")
	var adjustments: Dictionary = _rules.attack_roll_adjustments(attacker, defender, 5)
	if not bool(adjustments.get("advantage", false)) or not bool(adjustments.get("automatic_critical", false)):
		_fail("Paralyzed target did not grant advantage and automatic critical at 5 feet.")
		return
	attacker.add_condition("stunned")
	if not bool(_rules.attack_roll_adjustments(attacker, defender, 5).get("blocked", false)):
		_fail("Stunned attacker was still allowed to attack.")
		return

	state = CombatantState.new()
	state.add_condition("prone")
	if _rules.movement_cost_feet(5, state, true, false) != 15:
		_fail("Prone movement through difficult terrain must cost 15 feet per cell.")
		return
	state.add_condition("grappled")
	if _rules.effective_speed_feet(30, state) != 0:
		_fail("Grappled condition did not reduce speed to zero.")
		return

	print("SRD combat rules tests passed.")
	quit(0)
