class_name TurnBasedCombatSystemAi
extends TurnBasedCombatSystem


func has_combatant(actor: Node) -> bool:
	return _find_entry_index(actor) >= 0


func add_combatant(actor: Node, initiative_modifier: int = 0, initiative_override: int = -1) -> bool:
	if not active or actor == null or not is_instance_valid(actor) or has_combatant(actor):
		return false
	var overrides: Dictionary = {}
	if initiative_override > 0:
		overrides[actor.get_instance_id()] = clampi(initiative_override, 1, INITIATIVE_DIE_SIDES)
	var proficiency: int = int(actor.call("get_initiative_proficiency_bonus")) if actor.has_method("get_initiative_proficiency_bonus") else 0
	var entry: Dictionary = _make_entry(actor, false, initiative_modifier, maxi(proficiency, 0), overrides)
	entry["joined_round"] = round_number
	entry["joined_mid_combat"] = true
	entries.append(entry)
	return true
