class_name CombatSubclassSystem
extends CombatSystem


func perform_basic_attack(
	character: PlayerCharacter,
	target_armor_class: int,
	weapon: Dictionary = {},
	natural_roll_override: int = -1,
	damage_rolls_override: Array[int] = [],
	attack_context: Dictionary = {}
) -> AttackResult:
	var tactical_ready: bool = (
		character != null
		and bool(character.active_effects.get(FighterSubclassSystem.TACTICAL_READY_KEY, false))
	)
	var context: Dictionary = attack_context.duplicate(true)
	if tactical_ready:
		context["advantage"] = true
	var result: AttackResult = super.perform_basic_attack(
		character,
		target_armor_class,
		weapon,
		natural_roll_override,
		damage_rolls_override,
		context
	)
	if not tactical_ready or character == null or result.first_roll <= 0:
		return result
	character.active_effects.erase(FighterSubclassSystem.TACTICAL_READY_KEY)
	if result.hit:
		var bonus_damage: int = character.get_proficiency_bonus()
		result.bonus_damage += bonus_damage
		result.damage += bonus_damage
		result.damage_before_mitigation = result.damage
		result.note = _subclass_note(
			result.note,
			"Тактическая подготовка: преимущество и +%d урона." % bonus_damage
		)
	else:
		result.note = _subclass_note(
			result.note,
			"Тактическая подготовка дала преимущество и была израсходована."
		)
	return result


func _subclass_note(current: String, addition: String) -> String:
	return addition if current.is_empty() else "%s %s" % [current, addition]
