class_name SrdCombatRules
extends RefCounted

const DAMAGE_TYPES: Array[String] = [
	"acid", "bludgeoning", "cold", "fire", "force", "lightning", "necrotic",
	"piercing", "poison", "psychic", "radiant", "slashing", "thunder"
]
const CONDITION_NAMES: Dictionary = {
	"blinded": "Ослепление",
	"charmed": "Очарование",
	"deafened": "Глухота",
	"exhaustion": "Истощение",
	"frightened": "Испуг",
	"grappled": "Захват",
	"incapacitated": "Недееспособность",
	"invisible": "Невидимость",
	"paralyzed": "Паралич",
	"petrified": "Окаменение",
	"poisoned": "Отравление",
	"prone": "Лежит",
	"restrained": "Опутывание",
	"stunned": "Ошеломление",
	"unconscious": "Без сознания"
}

var _dice: DiceRoller = DiceRoller.new()


func roll_d20(
	modifier: int = 0,
	advantage: bool = false,
	disadvantage: bool = false,
	overrides: Array[int] = []
) -> Dictionary:
	if advantage and disadvantage:
		advantage = false
		disadvantage = false
	var first: int = clampi(overrides[0], 1, 20) if overrides.size() > 0 else _dice.roll_die(20)
	var second: int = 0
	var natural: int = first
	if advantage or disadvantage:
		second = clampi(overrides[1], 1, 20) if overrides.size() > 1 else _dice.roll_die(20)
		natural = maxi(first, second) if advantage else mini(first, second)
	return {
		"first": first,
		"second": second,
		"natural": natural,
		"modifier": modifier,
		"total": natural + modifier,
		"advantage": advantage,
		"disadvantage": disadvantage
	}


func resolve_d20_test(
	modifier: int,
	dc: int,
	advantage: bool = false,
	disadvantage: bool = false,
	overrides: Array[int] = []
) -> Dictionary:
	var roll: Dictionary = roll_d20(modifier, advantage, disadvantage, overrides)
	roll["dc"] = maxi(dc, 0)
	roll["success"] = int(roll.get("total", 0)) >= maxi(dc, 0)
	return roll


func resolve_saving_throw(
	ability_id: String,
	modifier: int,
	dc: int,
	state: CombatantState,
	advantage: bool = false,
	disadvantage: bool = false,
	overrides: Array[int] = [],
	context: Dictionary = {}
) -> Dictionary:
	var automatic_failure: bool = false
	if state != null:
		if ability_id in ["strength", "dexterity"] and (
			state.has_condition("paralyzed") or state.has_condition("stunned") or state.has_condition("unconscious")
		):
			automatic_failure = true
		if ability_id == "dexterity" and state.has_condition("restrained"):
			disadvantage = true
		if ability_id == "dexterity" and state.has_condition("petrified"):
			automatic_failure = true
		var condition_id: String = str(context.get("condition_id", ""))
		if not condition_id.is_empty() and condition_id in state.saving_throw_advantage_conditions:
			advantage = true
		if bool(context.get("magical", false)) and ability_id in state.magical_save_advantage_abilities:
			advantage = true
	if automatic_failure:
		return {
			"ability_id": ability_id,
			"natural": 0,
			"total": 0,
			"dc": dc,
			"success": false,
			"automatic_failure": true,
			"advantage": false,
			"disadvantage": false
		}
	var result: Dictionary = resolve_d20_test(modifier, dc, advantage, disadvantage, overrides)
	result["ability_id"] = ability_id
	result["automatic_failure"] = false
	return result


func attack_roll_adjustments(
	attacker: CombatantState,
	defender: CombatantState,
	distance_feet: int,
	attacker_can_see_defender: bool = true,
	defender_can_see_attacker: bool = true
) -> Dictionary:
	var advantage: bool = false
	var disadvantage: bool = false
	var blocked: bool = false
	var automatic_critical: bool = false
	if attacker != null:
		if attacker.has_condition("incapacitated") or attacker.has_condition("paralyzed") or attacker.has_condition("petrified") or attacker.has_condition("stunned") or attacker.has_condition("unconscious"):
			blocked = true
		if attacker.has_condition("blinded") or attacker.has_condition("poisoned") or attacker.has_condition("restrained") or attacker.has_condition("prone"):
			disadvantage = true
		if attacker.has_condition("frightened"):
			disadvantage = true
		if attacker.has_condition("invisible") and defender_can_see_attacker == false:
			advantage = true
		if attacker.helped_attack:
			advantage = true
	if defender != null:
		if defender.has_condition("blinded") or defender.has_condition("paralyzed") or defender.has_condition("restrained") or defender.has_condition("stunned") or defender.has_condition("unconscious"):
			advantage = true
		if defender.has_condition("invisible") and not attacker_can_see_defender:
			disadvantage = true
		if defender.has_condition("prone"):
			if distance_feet <= 5:
				advantage = true
			else:
				disadvantage = true
		if distance_feet <= 5 and (defender.has_condition("paralyzed") or defender.has_condition("unconscious")):
			automatic_critical = true
	return {
		"advantage": advantage,
		"disadvantage": disadvantage,
		"blocked": blocked,
		"automatic_critical": automatic_critical
	}


func resolve_damage(amount: int, damage_type: String, state: CombatantState) -> Dictionary:
	var normalized_type: String = normalize_damage_type(damage_type)
	var original: int = maxi(amount, 0)
	var applied: int = original
	var reason: String = ""
	if state != null:
		if normalized_type in state.damage_immunities:
			applied = 0
			reason = "иммунитет"
		elif normalized_type in state.damage_resistances:
			applied = floori(float(original) / 2.0)
			reason = "сопротивление"
		elif normalized_type in state.damage_vulnerabilities:
			applied = original * 2
			reason = "уязвимость"
	var absorbed: int = 0
	if state != null and state.temporary_hit_points > 0 and applied > 0:
		absorbed = mini(state.temporary_hit_points, applied)
		state.temporary_hit_points -= absorbed
		applied -= absorbed
	return {
		"damage_type": normalized_type,
		"original": original,
		"absorbed": absorbed,
		"applied": applied,
		"reason": reason
	}


func concentration_dc(damage_taken: int) -> int:
	return clampi(maxi(10, floori(float(maxi(damage_taken, 0)) / 2.0)), 10, 30)


func resolve_concentration_check(
	constitution_modifier: int,
	damage_taken: int,
	state: CombatantState,
	overrides: Array[int] = []
) -> Dictionary:
	if state == null or state.concentrating_on.is_empty():
		return {"required": false, "success": true, "dc": 0}
	var dc: int = concentration_dc(damage_taken)
	var disadvantage: bool = state.has_condition("poisoned")
	var result: Dictionary = resolve_saving_throw("constitution", constitution_modifier, dc, state, false, disadvantage, overrides)
	result["required"] = true
	if not bool(result.get("success", false)):
		result["lost_effect"] = state.clear_concentration()
	else:
		result["lost_effect"] = ""
	return result


func resolve_death_save(state: CombatantState, roll_override: int = -1) -> Dictionary:
	if state == null:
		return {"resolved": false}
	if state.dead or state.stable:
		return {
			"resolved": false,
			"dead": state.dead,
			"stable": state.stable,
			"successes": state.death_save_successes,
			"failures": state.death_save_failures
		}
	var natural: int = clampi(roll_override, 1, 20) if roll_override >= 1 else _dice.roll_die(20)
	var regained_hit_point: bool = false
	if natural == 20:
		regained_hit_point = true
		state.recover_from_zero_hit_points()
	elif natural == 1:
		state.death_save_failures = mini(state.death_save_failures + 2, 3)
	elif natural >= 10:
		state.death_save_successes = mini(state.death_save_successes + 1, 3)
	else:
		state.death_save_failures = mini(state.death_save_failures + 1, 3)
	if state.death_save_successes >= 3:
		state.stable = true
		state.remove_condition("incapacitated")
	if state.death_save_failures >= 3:
		state.dead = true
	return {
		"resolved": true,
		"natural": natural,
		"successes": state.death_save_successes,
		"failures": state.death_save_failures,
		"stable": state.stable,
		"dead": state.dead,
		"regained_hit_point": regained_hit_point
	}


func damage_at_zero_hit_points(state: CombatantState, critical_hit: bool = false) -> Dictionary:
	if state == null or state.dead:
		return {"dead": state != null and state.dead, "failures_added": 0}
	var failures_added: int = 2 if critical_hit else 1
	state.death_save_failures = mini(state.death_save_failures + failures_added, 3)
	if state.death_save_failures >= 3:
		state.dead = true
	return {
		"dead": state.dead,
		"failures_added": failures_added,
		"failures": state.death_save_failures
	}


func movement_cost_feet(
	base_cost_feet: int,
	state: CombatantState,
	difficult_terrain: bool = false,
	crawling: bool = false
) -> int:
	var cost: int = maxi(base_cost_feet, 0)
	if difficult_terrain:
		cost += maxi(base_cost_feet, 0)
	if crawling:
		cost += maxi(base_cost_feet, 0)
	if state != null and state.has_condition("prone") and not crawling:
		cost += maxi(base_cost_feet, 0)
	return cost


func effective_speed_feet(base_speed_feet: int, state: CombatantState) -> int:
	if state == null:
		return maxi(base_speed_feet, 0)
	if state.dead or state.has_condition("grappled") or state.has_condition("restrained") or state.has_condition("paralyzed") or state.has_condition("petrified") or state.has_condition("stunned") or state.has_condition("unconscious"):
		return 0
	var speed: int = maxi(base_speed_feet, 0)
	var exhaustion: int = state.get_exhaustion_level()
	if exhaustion > 0:
		speed = maxi(speed - exhaustion * 5, 0)
	return speed


func can_take_action(state: CombatantState) -> bool:
	return state == null or not (
		state.dead or state.has_condition("incapacitated") or state.has_condition("paralyzed") or state.has_condition("petrified") or state.has_condition("stunned") or state.has_condition("unconscious")
	)


func can_take_reaction(state: CombatantState) -> bool:
	return can_take_action(state)


func format_conditions(state: CombatantState) -> String:
	if state == null or state.conditions.is_empty():
		return "нет"
	var names: Array[String] = []
	for condition_id: String in state.get_condition_ids():
		names.append(str(CONDITION_NAMES.get(condition_id, condition_id)))
	return ", ".join(names)


func normalize_damage_type(value: String) -> String:
	var normalized: String = value.strip_edges().to_lower()
	var aliases: Dictionary = {
		"кислотный": "acid", "дробящий": "bludgeoning", "холод": "cold", "огненный": "fire", "огонь": "fire",
		"силовой": "force", "электрический": "lightning", "некротический": "necrotic", "колющий": "piercing",
		"яд": "poison", "психический": "psychic", "излучение": "radiant", "рубящий": "slashing", "звук": "thunder"
	}
	return str(aliases.get(normalized, normalized if normalized in DAMAGE_TYPES else "bludgeoning"))
