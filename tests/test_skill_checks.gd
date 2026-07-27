extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var character := PlayerCharacter.new()
	character.abilities["charisma"] = 16
	character.abilities["wisdom"] = 8
	var system := SkillCheckSystem.new()

	var success := system.perform_check(character, "charisma", 12, 0, 10)
	assert(success.natural_roll == 10)
	assert(success.ability_modifier == 3)
	assert(success.total == 13)
	assert(success.success)

	var failure := system.perform_check(character, "wisdom", 12, 0, 10)
	assert(failure.ability_modifier == -1)
	assert(failure.total == 9)
	assert(not failure.success)

	var natural_twenty_failure := system.perform_check(character, "charisma", 30, 0, 20)
	assert(not natural_twenty_failure.success)
	character.active_effects[SpellcastingSystem.GUIDANCE_ACTIVE_KEY] = true
	character.class_resources[SpellcastingSystem.CONCENTRATION_STATE_KEY] = "guidance"
	var guided := system.perform_skill_check(character, "persuasion", 20, 0, 10, 0, 0, false, 4)
	assert(guided.total == 17)
	assert(guided.bonus == 4)
	assert(not character.active_effects.has(SpellcastingSystem.GUIDANCE_ACTIVE_KEY))
	assert(not character.class_resources.has(SpellcastingSystem.CONCENTRATION_STATE_KEY))
	assert(SkillCheckSystem.difficulty_name(15) == "Сложно")
	print("Skill check tests passed.")
	quit(0)
