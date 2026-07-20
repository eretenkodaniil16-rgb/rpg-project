extends SceneTree

func _init() -> void:
	call_deferred("_run")

func _fail(message: String) -> void:
	push_error(message)
	quit(1)

func _run() -> void:
	GameState.new_game()
	var hero := PlayerCharacter.new()
	hero.character_name = "Тестовый герой"
	hero.character_class_id = "paladin"
	hero.character_class_name = "Паладин"
	hero.maximum_health = 12
	hero.current_health = 12
	GameState.player_character = hero
	var class_data := ClassDataSystem.new()
	class_data.ensure_starting_loadout(hero)
	GameState.set_flag("prepared_ability_id", "lay_on_hands")

	var host := Control.new()
	host.size = Vector2(1280.0, 720.0)
	root.add_child(host)

	var prepared := PreparedActionPanel.new()
	host.add_child(prepared)
	prepared.bind_character(hero)
	await process_frame
	if prepared.get_prepared_ability_id() != "lay_on_hands":
		_fail("Universal prepared action did not load the selected ability.")
		return

	var hub := CharacterHubInventory.new()
	host.add_child(hub)
	await process_frame
	hub.open_tab(hero, 2)
	await process_frame
	var tabs := hub.find_child("CharacterTabs", true, false) as TabContainer
	if tabs == null or tabs.get_tab_count() != 3:
		_fail("Character hub does not contain three tabs.")
		return
	if tabs.get_tab_title(0) != "ПЕРСОНАЖ" or tabs.get_tab_title(1) != "ИНВЕНТАРЬ" or tabs.get_tab_title(2) != "ЗАКЛИНАНИЯ И СПОСОБНОСТИ":
		_fail("Character hub tab titles are incorrect.")
		return

	var test_weapon: Dictionary = {}
	for value: Variant in GameState.get_inventory_entries():
		if value is Dictionary and str((value as Dictionary).get("id", "")) == "javelin":
			test_weapon = value as Dictionary
			break
	if test_weapon.is_empty():
		_fail("Equipment test item is missing from the starter inventory.")
		return
	hub.call("_select_inventory_entry", test_weapon)
	hub.call("_equip_inventory_entry")
	if hero.equipped_weapon_id != "javelin":
		_fail("Character inventory tab did not equip the selected weapon.")
		return

	var dice := D20RollOverlay.new()
	host.add_child(dice)
	var feed := CombatEventFeed.new()
	host.add_child(feed)
	await process_frame
	var result := AttackResult.new()
	result.attacker_name = "Смотритель"
	result.target_name = "Тестовый герой"
	result.attack_name = "Атака по возможности"
	result.is_reaction = true
	result.natural_roll = 14
	result.first_roll = 14
	result.total = 17
	result.target_armor_class = 15
	result.hit = true
	result.damage = 5
	feed.show_result(result)
	await process_frame
	if feed.card_count() != 1:
		_fail("Compact combat feed did not create an attack card.")
		return
	if dice.queued_roll_count() < 1:
		_fail("Attack result did not start the d20 presentation.")
		return
	var serialized: Dictionary = result.to_dict()
	if str(serialized.get("attacker_name", "")) != "Смотритель" or not bool(serialized.get("is_reaction", false)):
		_fail("Attack result lost attacker or reaction metadata.")
		return

	hub.close_sheet()
	host.queue_free()
	await process_frame
	print("Prepared actions, character tabs, equipment, compact combat feed and d20 presentation test passed.")
	quit(0)
