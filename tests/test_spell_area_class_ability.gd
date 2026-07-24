extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var spells := SpellcastingSystem.new()
	var burning_hands: Dictionary = spells.get_spell_definition("burning_hands")
	if burning_hands.is_empty():
		_fail("Burning Hands definition was unavailable.")
		return
	if burning_hands.has("ability"):
		_fail("A shared area spell must not hard-code one class spellcasting ability.")
		return

	var wizard := PlayerCharacter.new()
	wizard.character_class_id = "wizard"
	wizard.character_class_name = "Волшебник"
	wizard.level = 5
	wizard.abilities["intelligence"] = 18
	wizard.base_abilities["intelligence"] = 18
	wizard.abilities["charisma"] = 8
	wizard.base_abilities["charisma"] = 8
	spells.ensure_character(wizard, false)
	if spells.get_spellcasting_ability(wizard, burning_hands) != "intelligence":
		_fail("Wizard did not use Intelligence for Burning Hands.")
		return
	if spells.get_spell_save_dc(wizard, burning_hands) != 15:
		_fail("Wizard Burning Hands save DC did not use Intelligence and level-five proficiency.")
		return

	var sorcerer := PlayerCharacter.new()
	sorcerer.character_class_id = "sorcerer"
	sorcerer.character_class_name = "Чародей"
	sorcerer.level = 5
	sorcerer.abilities["charisma"] = 18
	sorcerer.base_abilities["charisma"] = 18
	sorcerer.abilities["intelligence"] = 8
	sorcerer.base_abilities["intelligence"] = 8
	spells.ensure_character(sorcerer, false)
	if spells.get_spellcasting_ability(sorcerer, burning_hands) != "charisma":
		_fail("Sorcerer did not use Charisma for Burning Hands.")
		return
	if spells.get_spell_save_dc(sorcerer, burning_hands) != 15:
		_fail("Sorcerer Burning Hands save DC did not use Charisma and level-five proficiency.")
		return

	print("Area spells preserve each caster class spellcasting ability.")
	quit(0)
