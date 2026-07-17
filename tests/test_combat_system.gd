extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var character := PlayerCharacter.new()
	character.level = 1
	character.abilities["strength"] = 16
	var system := CombatSystem.new()

	var normal_hit := system.perform_unarmed_strike(character, 10, 10)
	assert(normal_hit.natural_roll == 10)
	assert(normal_hit.ability_modifier == 3)
	assert(normal_hit.proficiency_bonus == 2)
	assert(normal_hit.attack_bonus == 5)
	assert(normal_hit.total == 15)
	assert(normal_hit.hit)
	assert(normal_hit.damage == 4)

	var normal_miss := system.perform_unarmed_strike(character, 18, 10)
	assert(not normal_miss.hit)
	assert(normal_miss.damage == 0)

	var automatic_miss := system.perform_unarmed_strike(character, 1, 1)
	assert(automatic_miss.automatic_miss)
	assert(not automatic_miss.hit)

	var critical_hit := system.perform_unarmed_strike(character, 99, 20)
	assert(critical_hit.critical)
	assert(critical_hit.hit)
	assert(critical_hit.damage == 4)

	character.abilities["strength"] = 8
	var zero_damage_hit := system.perform_unarmed_strike(character, 5, 20)
	assert(zero_damage_hit.hit)
	assert(zero_damage_hit.damage == 0)

	assert(CombatSystem.proficiency_bonus_for_level(1) == 2)
	assert(CombatSystem.proficiency_bonus_for_level(5) == 3)
	assert(CombatSystem.proficiency_bonus_for_level(9) == 4)
	assert(CombatSystem.proficiency_bonus_for_level(13) == 5)
	assert(CombatSystem.proficiency_bonus_for_level(17) == 6)
	print("Combat system tests passed.")
	quit(0)
