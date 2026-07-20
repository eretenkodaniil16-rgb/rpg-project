class_name ProgressionSystem
extends RefCounted

const EXPERIENCE_STEP: int = 100


static func total_experience_for_level(level: int) -> int:
	var safe_level: int = maxi(level, 1)
	return EXPERIENCE_STEP * (safe_level - 1) * safe_level / 2


static func experience_required_for_next_level(character: PlayerCharacter) -> int:
	if character == null:
		return EXPERIENCE_STEP
	return total_experience_for_level(character.level + 1) - total_experience_for_level(character.level)


static func experience_progress_in_level(character: PlayerCharacter) -> int:
	if character == null:
		return 0
	return maxi(character.experience - total_experience_for_level(character.level), 0)


static func experience_remaining(character: PlayerCharacter) -> int:
	return maxi(experience_required_for_next_level(character) - experience_progress_in_level(character), 0)


static func grant_experience(character: PlayerCharacter, amount: int) -> Dictionary:
	if character == null or amount <= 0:
		return {
			"experience_gained": 0,
			"levels_gained": 0,
			"health_gained": 0,
			"level": character.level if character != null else 1
		}

	var starting_level: int = character.level
	var total_health_gained: int = 0
	character.experience += amount

	while character.experience >= total_experience_for_level(character.level + 1):
		character.level += 1
		var health_gain: int = _health_gain_for_level(character)
		character.maximum_health += health_gain
		character.current_health = mini(character.current_health + health_gain, character.maximum_health)
		total_health_gained += health_gain

	character.hit_dice_maximum = maxi(character.level, 1)
	character.hit_dice_current = clampi(
		character.hit_dice_current + character.level - starting_level,
		0,
		character.hit_dice_maximum
	)

	return {
		"experience_gained": amount,
		"levels_gained": character.level - starting_level,
		"health_gained": total_health_gained,
		"level": character.level,
		"experience": character.experience,
		"progress": experience_progress_in_level(character),
		"required": experience_required_for_next_level(character)
	}


static func _health_gain_for_level(character: PlayerCharacter) -> int:
	var average_hit_die: int = floori(float(maxi(character.hit_die_size, 2)) * 0.5) + 1
	var constitution_bonus: int = character.get_ability_modifier("constitution")
	var racial_bonus: int = 0
	var race: Dictionary = RaceDataSystem.new().get_race(character.race_id)
	if not race.is_empty():
		racial_bonus = maxi(int(race.get("hp_bonus_per_level", 0)), 0)
	return maxi(average_hit_die + constitution_bonus + racial_bonus, 1)
