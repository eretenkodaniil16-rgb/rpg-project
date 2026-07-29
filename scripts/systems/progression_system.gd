class_name ProgressionSystem
extends RefCounted

const MAX_LEVEL: int = 20

# SRD 5.2.1 cumulative XP thresholds for character levels 1–20.
const EXPERIENCE_THRESHOLDS: Array[int] = [
	0,
	300,
	900,
	2700,
	6500,
	14000,
	23000,
	34000,
	48000,
	64000,
	85000,
	100000,
	120000,
	140000,
	165000,
	195000,
	225000,
	265000,
	305000,
	355000
]


static func total_experience_for_level(level: int) -> int:
	var safe_level: int = clampi(level, 1, MAX_LEVEL)
	return EXPERIENCE_THRESHOLDS[safe_level - 1]


static func level_for_experience(experience: int) -> int:
	var safe_experience: int = maxi(experience, 0)
	for level: int in range(MAX_LEVEL, 0, -1):
		if safe_experience >= total_experience_for_level(level):
			return level
	return 1


static func can_level_up(character: PlayerCharacter) -> bool:
	return (
		character != null
		and character.level < MAX_LEVEL
		and character.experience >= total_experience_for_level(character.level + 1)
	)


static func pending_level_count(character: PlayerCharacter) -> int:
	if character == null:
		return 0
	return maxi(level_for_experience(character.experience) - character.level, 0)


static func experience_required_for_next_level(character: PlayerCharacter) -> int:
	if character == null:
		return total_experience_for_level(2)
	if character.level >= MAX_LEVEL:
		return 0
	return (
		total_experience_for_level(character.level + 1)
		- total_experience_for_level(character.level)
	)


static func experience_progress_in_level(character: PlayerCharacter) -> int:
	if character == null:
		return 0
	if character.level >= MAX_LEVEL:
		return 0
	var required: int = experience_required_for_next_level(character)
	return clampi(
		character.experience - total_experience_for_level(character.level),
		0,
		required
	)


static func experience_remaining(character: PlayerCharacter) -> int:
	if character == null or character.level >= MAX_LEVEL:
		return 0
	return maxi(
		total_experience_for_level(character.level + 1) - character.experience,
		0
	)


static func grant_experience(character: PlayerCharacter, amount: int) -> Dictionary:
	if character == null or amount <= 0:
		return {
			"experience_gained": 0,
			"levels_gained": 0,
			"level_up_available": can_level_up(character),
			"pending_level_count": pending_level_count(character),
			"level": character.level if character != null else 1
		}

	character.experience += amount
	return {
		"experience_gained": amount,
		"levels_gained": 0,
		"level_up_available": can_level_up(character),
		"pending_level_count": pending_level_count(character),
		"level": character.level,
		"experience": character.experience,
		"progress": experience_progress_in_level(character),
		"required": experience_required_for_next_level(character),
		"remaining": experience_remaining(character)
	}
