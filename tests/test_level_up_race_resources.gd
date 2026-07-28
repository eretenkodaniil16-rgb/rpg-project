extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	var races := RaceDataSystem.new()
	var levels := LevelUpSystem.new()

	state.call("new_game")
	var dwarf := _fighter("dwarf")
	races.apply_race(dwarf, "dwarf")
	var dwarf_before: int = dwarf.maximum_health
	var applied_before: int = dwarf.applied_racial_hit_point_bonus
	dwarf.experience = ProgressionSystem.total_experience_for_level(2)
	state.set("player_character", dwarf)
	levels.begin_transaction(dwarf, state)
	var expected_gain: int = levels.get_fixed_hp_gain(dwarf)
	levels.choose_fixed_hp(dwarf, state)
	if not bool(levels.commit_transaction(dwarf, state).get("success", false)):
		_fail("Dwarf level-up did not commit.")
		return
	if dwarf.maximum_health != dwarf_before + expected_gain:
		_fail("Dwarven Toughness was applied more than once during level-up.")
		return
	if dwarf.applied_racial_hit_point_bonus != applied_before + 1:
		_fail("Applied racial HP tracking did not advance by exactly one level.")
		return
	var dwarf_after: int = dwarf.maximum_health
	races.ensure_character_race(dwarf)
	if dwarf.maximum_health != dwarf_after:
		_fail("A later race synchronization duplicated the level-up HP bonus.")
		return

	state.call("new_game")
	var dragonborn := _fighter("dragonborn")
	dragonborn.level = 4
	dragonborn.experience = ProgressionSystem.total_experience_for_level(5)
	dragonborn.hit_dice_maximum = 4
	dragonborn.hit_dice_current = 4
	races.apply_race(dragonborn, "dragonborn")
	if dragonborn.get_resource_maximum("dragon_breath") != 2:
		_fail("Level 4 dragon breath maximum is not tied to proficiency bonus.")
		return
	dragonborn.set_resource("dragon_breath", 1, 2)
	state.set("player_character", dragonborn)
	levels.begin_transaction(dragonborn, state)
	levels.choose_fixed_hp(dragonborn, state)
	if not bool(levels.commit_transaction(dragonborn, state).get("success", false)):
		_fail("Dragonborn level-up did not commit.")
		return
	if dragonborn.get_resource_maximum("dragon_breath") != 3:
		_fail("Racial resource maximum did not follow the new proficiency bonus.")
		return
	if dragonborn.get_resource("dragon_breath") != 1:
		_fail("Level-up incorrectly refilled an already spent racial resource.")
		return

	print("Racial HP and proficiency-based resource level-up tests passed.")
	quit(0)


func _fighter(race_id: String) -> PlayerCharacter:
	var character := PlayerCharacter.new()
	character.character_name = "Расовый тест"
	character.character_class_id = "fighter"
	character.character_class_name = "Воин"
	character.race_id = race_id
	character.abilities["constitution"] = 14
	character.base_abilities["constitution"] = 14
	character.maximum_health = 12
	character.current_health = 12
	character.hit_die_size = 10
	character.hit_dice_maximum = 1
	character.hit_dice_current = 1
	return character
