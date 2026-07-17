extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	if DistanceSystem.distance_feet(Vector2.ZERO, Vector2(64, 0)) != 5:
		_fail("64 pixels must equal 5 feet.")
		return
	if DistanceSystem.distance_feet(Vector2.ZERO, Vector2(65, 0)) != 10:
		_fail("Distance must round up to the next 5-foot band.")
		return

	var character := PlayerCharacter.new()
	character.level = 1
	character.abilities["dexterity"] = 16
	character.abilities["strength"] = 14
	var shortbow: Dictionary = {
		"name": "Короткий лук", "damage_dice": [1, 6], "damage_type": "колющий",
		"ability": "dexterity", "properties": ["ranged", "ammunition"],
		"range_normal_ft": 80, "range_long_ft": 320
	}
	var combat := CombatSystem.new()
	var normal: AttackResult = combat.perform_basic_attack(
		character, 10, shortbow, 10, [4], {"target_name":"Манекен", "distance_feet":80}
	)
	if not normal.hit or normal.disadvantage or normal.damage != 7 or normal.range_state != "normal":
		_fail("Normal-range bow attack is incorrect.")
		return

	var long_range: AttackResult = combat.perform_basic_attack(
		character, 10, shortbow, 18, [4], {
			"target_name":"Манекен", "distance_feet":85, "second_roll_override":5
		}
	)
	if not long_range.disadvantage or long_range.natural_roll != 5 or long_range.range_state != "long":
		_fail("Long-range attack must use the lower d20 roll.")
		return

	var beyond: AttackResult = combat.perform_basic_attack(
		character, 10, shortbow, 20, [6], {"distance_feet":325}
	)
	if not beyond.out_of_range or beyond.hit:
		_fail("Attack beyond maximum range must be impossible.")
		return

	var greatsword: Dictionary = {
		"name":"Двуручный меч", "damage_dice":[2,6], "damage_type":"рубящий",
		"ability":"strength", "properties":["heavy", "two_handed"], "reach_ft":5
	}
	var melee_far: AttackResult = combat.perform_basic_attack(
		character, 10, greatsword, 20, [6,6], {"distance_feet":10}
	)
	if not melee_far.out_of_range:
		_fail("Melee weapon must not attack beyond 5 feet.")
		return
	var unarmed_far: AttackResult = combat.perform_basic_attack(
		character, 10, {}, 20, [], {"distance_feet":10}
	)
	if not unarmed_far.out_of_range:
		_fail("Unarmed strike must not attack beyond 5 feet.")
		return

	print("Distance and ranged combat tests passed.")
	quit(0)
