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
	state.call("new_game")
	var service := ClassDataSystem.new()
	var fighter := PlayerCharacter.new()
	fighter.character_name = "Тестер"
	fighter.character_class_id = "fighter"
	fighter.character_class_name = "Воин"
	fighter.level = 1
	fighter.maximum_health = 15
	fighter.current_health = 5
	fighter.abilities["constitution"] = 14
	state.set("player_character", fighter)
	if not service.ensure_starting_loadout(fighter):
		_fail("Fighter loadout was not initialized.")
		return
	if fighter.hit_die_size != 10 or fighter.hit_dice_current != 1:
		_fail("Fighter must start with one d10 Hit Die.")
		return

	var short_result: Dictionary = service.short_rest(fighter, 6)
	if not bool(short_result.get("success", false)) or fighter.current_health != 13 or fighter.hit_dice_current != 0:
		_fail("Short rest healing or Hit Die spending is incorrect.")
		return

	fighter.set_resource("second_wind", 0, 2)
	fighter.current_health = fighter.maximum_health
	var full_health_rest: Dictionary = service.short_rest(fighter, 10)
	if not bool(full_health_rest.get("success", false)) or bool(full_health_rest.get("spent_hit_die", true)):
		_fail("Full-health short rest must not spend a Hit Die.")
		return
	if fighter.get_resource("second_wind") != 1:
		_fail("Short rest must recharge one Second Wind use.")
		return

	fighter.current_health = 2
	fighter.set_resource("second_wind", 0, 2)
	var long_result: Dictionary = service.long_rest(fighter)
	if not bool(long_result.get("success", false)):
		_fail("Long rest failed.")
		return
	if fighter.current_health != fighter.maximum_health or fighter.hit_dice_current != fighter.hit_dice_maximum:
		_fail("Long rest did not restore health and Hit Dice.")
		return
	if fighter.get_resource("second_wind") != fighter.get_resource_maximum("second_wind"):
		_fail("Long rest did not restore class resources.")
		return

	print("Rest tests passed.")
	quit(0)
