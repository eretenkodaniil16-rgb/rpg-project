class_name DiceRoller
extends RefCounted

var _rng: RandomNumberGenerator = RandomNumberGenerator.new()


func _init() -> void:
	_rng.randomize()


func roll_die(sides: int) -> int:
	assert(sides >= 2, "У кубика должно быть не менее двух граней.")
	return _rng.randi_range(1, sides)


func roll_dice(count: int, sides: int) -> Array[int]:
	var result: Array[int] = []
	for _index: int in range(maxi(count, 0)):
		result.append(roll_die(sides))
	return result


func roll_ability_score() -> Dictionary:
	var dice: Array[int] = roll_dice(4, 6)
	var discarded_index: int = 0
	for index: int in range(1, dice.size()):
		if dice[index] < dice[discarded_index]:
			discarded_index = index

	var total: int = 0
	for index: int in range(dice.size()):
		if index != discarded_index:
			total += dice[index]

	return {
		"dice": dice,
		"discarded_index": discarded_index,
		"total": total
	}


func roll_d20(modifier: int = 0) -> Dictionary:
	var natural_roll: int = roll_die(20)
	return {
		"natural": natural_roll,
		"modifier": modifier,
		"total": natural_roll + modifier
	}
