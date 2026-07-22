extends SceneTree

const BACKGROUNDS_PATH: String = "res://data/origins/backgrounds.json"
const ITEMS_PATH: String = "res://data/items/items.json"

class FakeCombatant:
	extends Node
	var combat_name: String
	var initiative_modifier: int
	var initiative_proficiency: int
	var active: bool = true
	var incapacitated: bool = false
	var turn_started_count: int = 0

	func _init(name_value: String, modifier_value: int, proficiency_value: int = 0) -> void:
		combat_name = name_value
		initiative_modifier = modifier_value
		initiative_proficiency = proficiency_value

	func get_combat_name() -> String:
		return combat_name

	func get_initiative_modifier() -> int:
		return initiative_modifier

	func get_initiative_proficiency_bonus() -> int:
		return initiative_proficiency

	func is_combat_active() -> bool:
		return active

	func is_incapacitated() -> bool:
		return incapacitated

	func on_combat_turn_started() -> void:
		turn_started_count += 1


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	_test_d20_initiative_and_alert()
	_test_alert_swap()
	_test_savage_attacker()
	_test_magic_initiate()
	_test_origin_equipment_catalog()
	print("Origin feats and SRD d20 initiative tests passed.")
	quit(0)


func _test_d20_initiative_and_alert() -> void:
	var player := FakeCombatant.new("Герой", 2, 2)
	var enemy := FakeCombatant.new("Враг", 4, 0)
	root.add_child(player)
	root.add_child(enemy)
	var system := TurnBasedCombatSystem.new()
	var overrides: Dictionary = {
		player.get_instance_id(): 20,
		enemy.get_instance_id(): 19
	}
	system.start_combat(player, [enemy], 2, overrides)
	if system.get_initiative_roll(player) != 20:
		_fail("Initiative did not retain a natural d20 roll of 20.")
		return
	if system.get_initiative(player) != 24:
		_fail("Alert proficiency and Dexterity were not added to initiative.")
		return
	if system.get_initiative(enemy) != 23:
		_fail("Enemy initiative did not use d20 plus Dexterity.")
		return
	if system.current_actor() != player or player.turn_started_count != 1:
		_fail("Highest initiative did not begin the first turn or invoke its turn hook.")
		return
	system.stop_combat()
	player.queue_free()
	enemy.queue_free()


func _test_alert_swap() -> void:
	var alert_actor := FakeCombatant.new("Бдительный", 2, 2)
	var ally := FakeCombatant.new("Союзник", 0, 0)
	root.add_child(alert_actor)
	root.add_child(ally)
	var system := TurnBasedCombatSystem.new()
	var overrides: Dictionary = {
		alert_actor.get_instance_id(): 18,
		ally.get_instance_id(): 5
	}
	system.start_combat(alert_actor, [ally], 2, overrides)
	var alert_before: int = system.get_initiative(alert_actor)
	var ally_before: int = system.get_initiative(ally)
	if system.swap_initiative(alert_actor, ally, false, true):
		_fail("Alert swapped initiative without both creatures being willing.")
		return
	if not system.swap_initiative(alert_actor, ally, true, true):
		_fail("Alert could not swap initiative with a willing ally.")
		return
	if system.get_initiative(alert_actor) != ally_before or system.get_initiative(ally) != alert_before:
		_fail("Alert initiative values were not exchanged.")
		return
	ally.incapacitated = true
	if system.swap_initiative(alert_actor, ally, true, true):
		_fail("Alert swapped initiative with an incapacitated ally.")
		return
	system.stop_combat()
	alert_actor.queue_free()
	ally.queue_free()


func _test_savage_attacker() -> void:
	var character := PlayerCharacter.new()
	character.character_name = "Солдат"
	character.origin_feat_id = OriginFeatSystem.SAVAGE_ATTACKER_FEAT_ID
	character.abilities["strength"] = 10
	var feats := OriginFeatSystem.new()
	feats.initialize_character(character, true)
	var combat := CombatSystem.new()
	var weapon: Dictionary = {
		"id": "test_sword",
		"name": "Тестовый меч",
		"damage_dice": [1, 8],
		"damage_type": "slashing",
		"ability": "strength",
		"properties": [],
		"reach_ft": 5
	}
	var first: AttackResult = combat.perform_basic_attack(
		character,
		10,
		weapon,
		15,
		[2],
		{"distance_feet": 5, "turn_based": true, "savage_damage_rolls_override": [7]}
	)
	if not first.hit or first.damage != 7 or "Свирепый атакующий" not in first.note:
		_fail("Savage Attacker did not choose the better weapon damage roll.")
		return
	var second: AttackResult = combat.perform_basic_attack(
		character,
		10,
		weapon,
		15,
		[3],
		{"distance_feet": 5, "turn_based": true, "savage_damage_rolls_override": [8]}
	)
	if second.damage != 3 or "Свирепый атакующий" in second.note:
		_fail("Savage Attacker was used more than once in the same turn.")
		return
	feats.begin_turn(character)
	var third: AttackResult = combat.perform_basic_attack(
		character,
		10,
		weapon,
		15,
		[1],
		{"distance_feet": 5, "turn_based": true, "savage_damage_rolls_override": [6]}
	)
	if third.damage != 6:
		_fail("Savage Attacker did not recharge at the start of the next turn.")
		return


func _test_magic_initiate() -> void:
	var character := PlayerCharacter.new()
	character.origin_feat_id = OriginFeatSystem.MAGIC_INITIATE_CLERIC_FEAT_ID
	character.maximum_health = 30
	character.current_health = 1
	character.abilities["wisdom"] = 14
	var feats := OriginFeatSystem.new()
	feats.initialize_character(character, true)
	for ability_id: String in ["sacred_flame", "toll_the_dead", "origin_cure_wounds"]:
		if ability_id not in character.known_features:
			_fail("Magic Initiate did not add required ability %s." % ability_id)
			return
	if character.get_resource("magic_initiate_cleric_1") != 1:
		_fail("Magic Initiate free first-level casting was not initialized.")
		return
	var class_data := ClassDataSystem.new()
	var ability: Dictionary = class_data.get_ability_definition("origin_cure_wounds")
	var ability_system := ClassAbilitySystem.new()
	var first_use: Dictionary = ability_system.use_self_ability(character, ability)
	if not bool(first_use.get("success", false)) or character.get_resource("magic_initiate_cleric_1") != 0:
		_fail("Magic Initiate free Cure Wounds use was not consumed.")
		return
	var stored_health: int = character.current_health
	character.current_health = maxi(stored_health - 1, 1)
	character.set_resource("spell_slots_1", 1, 1)
	var second_use: Dictionary = ability_system.use_self_ability(character, ability)
	if not bool(second_use.get("success", false)) or character.get_resource("spell_slots_1") != 0:
		_fail("Magic Initiate did not fall back to an available first-level spell slot.")
		return
	feats.initialize_character(character, false)
	if character.get_resource("magic_initiate_cleric_1") != 0:
		_fail("Loading a character incorrectly restored the spent Magic Initiate use.")
		return
	feats.initialize_character(character, true)
	if character.get_resource("magic_initiate_cleric_1") != 1:
		_fail("Long-rest initialization did not restore Magic Initiate.")
		return


func _test_origin_equipment_catalog() -> void:
	var backgrounds_root: Dictionary = _load_json(BACKGROUNDS_PATH)
	var items: Dictionary = _load_json(ITEMS_PATH)
	var backgrounds_value: Variant = backgrounds_root.get("backgrounds", [])
	if not backgrounds_value is Array:
		_fail("Background equipment catalog is missing.")
		return
	for background_value: Variant in backgrounds_value:
		if not background_value is Dictionary:
			_fail("Background entry is invalid.")
			return
		var background: Dictionary = background_value as Dictionary
		var package_value: Variant = background.get("equipment_package", [])
		if not package_value is Array or (package_value as Array).is_empty():
			_fail("Background %s has no equipment package." % str(background.get("id", "")))
			return
		for entry_value: Variant in package_value:
			if not entry_value is Dictionary:
				_fail("Background equipment entry is not structured data.")
				return
			var item_id: String = str((entry_value as Dictionary).get("item_id", ""))
			if item_id.is_empty() or not items.has(item_id):
				_fail("Origin equipment item %s is missing from items.json." % item_id)
				return
			if int((entry_value as Dictionary).get("quantity", 0)) <= 0:
				_fail("Origin equipment item %s has an invalid quantity." % item_id)
				return


func _load_json(path: String) -> Dictionary:
	var file: FileAccess = FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {}
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	return parsed as Dictionary if parsed is Dictionary else {}
