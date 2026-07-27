class_name ClassDataSystem
extends RefCounted

const CLASSES_PATH: String = "res://data/classes/classes.json"
const ABILITIES_PATH: String = "res://data/abilities/abilities.json"
const RACIAL_ABILITIES_PATH: String = "res://data/abilities/racial_abilities.json"
const IGNORE_NONMAGICAL_DIFFICULT_TERRAIN: String = "ignore_nonmagical_difficult_terrain"
const ORIGIN_EQUIPMENT_GRANTED_FLAG: String = "origin_equipment_granted"
const ORIGIN_EQUIPMENT_CHOICE_FLAG: String = "origin_equipment_choice"

var _classes: Dictionary = {}
var _abilities: Dictionary = {}
var _dice: DiceRoller = DiceRoller.new()
var _race_data: RaceDataSystem = RaceDataSystem.new()
var _origin_data: OriginDataSystem = OriginDataSystem.new()
var _origin_feats: OriginFeatSystem = OriginFeatSystem.new()
var _class_proficiencies: ClassProficiencySystem = ClassProficiencySystem.new()
var _spellcasting: SpellcastingSystem = SpellcastingSystem.new()


func _init() -> void:
	_load_databases()


func ensure_starting_loadout(character: PlayerCharacter) -> bool:
	var state: Node = _get_game_state()
	if state == null:
		return false
	_race_data.ensure_character_race(character)
	var class_data: Dictionary = get_class_definition(character.character_class_id)
	if class_data.is_empty():
		return false
	_origin_data.ensure_legacy_origin(character)
	var proficiency_result: Dictionary = _class_proficiencies.ensure_character(character, class_data)
	var proficiencies_migrated: bool = bool(proficiency_result.get("changed", false))
	character.initialize_hit_dice(int(class_data.get("hit_die", 8)))
	if character.starter_loadout_granted:
		_origin_feats.initialize_character(character, false)
		var spell_migrated: bool = _spellcasting.ensure_character(character, false)
		var equipment_migrated: bool = _grant_origin_equipment(character, state)
		if proficiencies_migrated or spell_migrated or equipment_migrated:
			state.call("save_game")
		return proficiencies_migrated or spell_migrated or equipment_migrated
	var items_value: Variant = class_data.get("starting_items", {})
	if items_value is Dictionary:
		for item_id_value: Variant in (items_value as Dictionary).keys():
			var item_id: String = str(item_id_value)
			state.call("add_item", item_id, int((items_value as Dictionary)[item_id_value]), false)
	var equipment_value: Variant = class_data.get("equipment", {})
	var equipment: Dictionary = equipment_value as Dictionary if equipment_value is Dictionary else {}
	character.equipped_weapon_id = str(equipment.get("weapon", ""))
	character.equipped_armor_id = str(equipment.get("armor", ""))
	character.equipped_shield_id = str(equipment.get("shield", ""))
	character.known_features.clear()
	var features_value: Variant = class_data.get("features", [])
	if features_value is Array:
		for feature_value: Variant in features_value:
			character.known_features.append(str(feature_value))
	character.signature_ability_id = str(class_data.get("signature_ability", ""))
	_initialize_signature_resource(character)
	_origin_feats.initialize_character(character, true)
	_spellcasting.ensure_character(character, true)
	_grant_origin_equipment(character, state)
	if character.character_class_id == "rogue":
		character.active_effects["sneak_attack_ready"] = true
	character.starter_loadout_granted = true
	state.call("save_game")
	return true


func get_class_definition(class_id: String) -> Dictionary:
	var value: Variant = _classes.get(class_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func get_movement_traits(character: PlayerCharacter) -> Array[String]:
	var result: Array[String] = []
	if character == null:
		return result
	var class_data: Dictionary = get_class_definition(character.character_class_id)
	var traits_value: Variant = class_data.get("movement_traits", [])
	if traits_value is Array:
		for value: Variant in traits_value:
			result.append(str(value))
	return result


func has_movement_trait(character: PlayerCharacter, trait_id: String) -> bool:
	return trait_id in get_movement_traits(character)


func ignores_nonmagical_difficult_terrain(character: PlayerCharacter) -> bool:
	return has_movement_trait(character, IGNORE_NONMAGICAL_DIFFICULT_TERRAIN)


func exploration_speed_multiplier(character: PlayerCharacter, difficult_terrain: bool, magical_terrain: bool = false) -> float:
	if not difficult_terrain:
		return 1.0
	if not magical_terrain and ignores_nonmagical_difficult_terrain(character):
		return 1.0
	return 0.5


func movement_cost_for_terrain(character: PlayerCharacter, base_cost_feet: int, difficult_terrain: bool, magical_terrain: bool = false) -> int:
	var base_cost: int = maxi(base_cost_feet, 0)
	if not difficult_terrain:
		return base_cost
	if not magical_terrain and ignores_nonmagical_difficult_terrain(character):
		return base_cost
	return base_cost * 2


func get_ability_definition(ability_id: String) -> Dictionary:
	var value: Variant = _abilities.get(ability_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func get_signature_ability(character: PlayerCharacter) -> Dictionary:
	return get_ability_definition(character.signature_ability_id)


func get_racial_ability(character: PlayerCharacter) -> Dictionary:
	return get_ability_definition(character.racial_ability_id)


func get_feature_views(character: PlayerCharacter) -> Array:
	var result: Array = []
	for feature_id: String in character.known_features:
		var feature: Dictionary = get_ability_definition(feature_id)
		if not feature.is_empty():
			result.append(feature)
	if ignores_nonmagical_difficult_terrain(character):
		result.append({
			"id": "wilderness_guide",
			"name": "Проводник бездорожья",
			"kind": "passive",
			"description": "Немагическая труднопроходимая местность не увеличивает стоимость перемещения Следопыта и не замедляет его вне боя."
		})
	for racial_feature: Dictionary in _race_data.get_feature_views(character):
		result.append(racial_feature)
	return result


func equip_item(character: PlayerCharacter, item_id: String) -> bool:
	var state: Node = _get_game_state()
	if state == null or not bool(state.call("has_item", item_id)):
		return false
	var item: Dictionary = state.call("get_item_definition", item_id) as Dictionary
	match str(item.get("type", "")):
		"weapon": character.equipped_weapon_id = item_id
		"armor": character.equipped_armor_id = item_id
		"shield": character.equipped_shield_id = item_id
		_: return false
	state.call("save_game")
	return true


func is_equipped(character: PlayerCharacter, item_id: String) -> bool:
	return item_id in [character.equipped_weapon_id, character.equipped_armor_id, character.equipped_shield_id]


func get_equipped_weapon(character: PlayerCharacter) -> Dictionary:
	var state: Node = _get_game_state()
	if state == null or character.equipped_weapon_id.is_empty():
		return {}
	return state.call("get_item_definition", character.equipped_weapon_id) as Dictionary


func get_equipment_training_state(character: PlayerCharacter) -> Dictionary:
	if character == null:
		return {}
	var state: Node = _get_game_state()
	var armor: Dictionary = {}
	var shield: Dictionary = {}
	if state != null:
		armor = state.call("get_item_definition", character.equipped_armor_id) as Dictionary
		shield = state.call("get_item_definition", character.equipped_shield_id) as Dictionary
	var armor_category: String = str(armor.get("armor_category", "clothing"))
	var wears_armor: bool = not armor.is_empty() and armor_category in ["light", "medium", "heavy"]
	var armor_trained: bool = not wears_armor or character.has_armor_training(armor_category)
	var shield_equipped: bool = not shield.is_empty()
	var shield_trained: bool = not shield_equipped or character.has_armor_training("shield")
	return {
		"armor_category": armor_category,
		"armor_trained": armor_trained,
		"shield_equipped": shield_equipped,
		"shield_trained": shield_trained,
		"untrained_armor": wears_armor and not armor_trained,
		"untrained_shield": shield_equipped and not shield_trained
	}


func has_untrained_armor_d20_disadvantage(character: PlayerCharacter, ability_id: String) -> bool:
	if ability_id not in ["strength", "dexterity"]:
		return false
	return bool(get_equipment_training_state(character).get("untrained_armor", false))


func get_armor_class(character: PlayerCharacter) -> int:
	var state: Node = _get_game_state()
	if state == null:
		return 10 + character.get_ability_modifier("dexterity")
	var dexterity: int = character.get_ability_modifier("dexterity")
	var armor: Dictionary = state.call("get_item_definition", character.equipped_armor_id) as Dictionary
	var shield: Dictionary = state.call("get_item_definition", character.equipped_shield_id) as Dictionary
	var armor_class: int
	if armor.is_empty() or str(armor.get("armor_category", "")) == "clothing":
		if character.character_class_id == "barbarian":
			armor_class = 10 + dexterity + character.get_ability_modifier("constitution")
		elif character.character_class_id == "monk" and shield.is_empty():
			armor_class = 10 + dexterity + character.get_ability_modifier("wisdom")
		else:
			armor_class = 10 + dexterity
	else:
		var dexterity_cap: int = int(armor.get("dex_cap", 99))
		var dexterity_bonus: int = 0 if dexterity_cap == 0 else mini(dexterity, dexterity_cap)
		armor_class = int(armor.get("base_ac", 10)) + dexterity_bonus
		if character.character_class_id == "fighter":
			armor_class += 1
	if not shield.is_empty() and character.has_armor_training("shield"):
		armor_class += int(shield.get("ac_bonus", 2))
	return maxi(armor_class, 0)


func get_spellcasting_context(
	character: PlayerCharacter,
	combat_state: CombatantState = null,
	turn_token: String = ""
) -> Dictionary:
	if character == null:
		return {}
	var state: Node = _get_game_state()
	var weapon: Dictionary = {}
	var shield: Dictionary = {}
	var inventory_entries: Array = []
	if state != null:
		weapon = state.call("get_item_definition", character.equipped_weapon_id) as Dictionary
		shield = state.call("get_item_definition", character.equipped_shield_id) as Dictionary
		inventory_entries = state.call("get_inventory_entries") as Array

	var training_state: Dictionary = get_equipment_training_state(character)
	var armor_trained: bool = bool(training_state.get("armor_trained", true))
	var occupied_hands: int = 0
	if not weapon.is_empty():
		# Two-handed weapons need two hands to attack, but only one to hold while casting.
		occupied_hands += 1
	if not shield.is_empty():
		occupied_hands += 1
	var free_hands: int = maxi(2 - occupied_hands, 0)
	var weapon_properties: Array[String] = _string_array(weapon.get("properties", []))
	var focus_in_hand: bool = bool(weapon.get("spellcasting_focus", false)) or "focus" in weapon_properties
	var has_component_pouch: bool = false
	var has_inventory_focus: bool = false
	var has_required_material: bool = true
	for value: Variant in inventory_entries:
		if not value is Dictionary:
			continue
		var item: Dictionary = value as Dictionary
		if bool(item.get("component_pouch", false)):
			has_component_pouch = true
		if bool(item.get("spellcasting_focus", false)):
			has_inventory_focus = true
	# A holy symbol may be displayed on a shield; other loose foci require a hand.
	var shield_symbol_focus: bool = not shield.is_empty() and state != null and bool(state.call("has_item", "holy_symbol"))
	if shield_symbol_focus:
		focus_in_hand = true
	elif not focus_in_hand and has_inventory_focus and free_hands > 0:
		focus_in_hand = true
		free_hands -= 1
	var can_speak: bool = not bool(character.active_effects.get("silenced", false)) and not bool(character.active_effects.get("gagged", false))
	if combat_state != null and (combat_state.has_condition("unconscious") or combat_state.has_condition("incapacitated")):
		can_speak = false
	return {
		"can_speak": can_speak,
		"armor_trained": armor_trained,
		"untrained_armor_d20_disadvantage": bool(training_state.get("untrained_armor", false)),
		"shield_trained": bool(training_state.get("shield_trained", true)),
		"free_hands": free_hands,
		"focus_in_hand": focus_in_hand,
		"has_component_pouch": has_component_pouch,
		"has_required_material": has_required_material,
		"turn_token": turn_token,
		"equipped_weapon_id": character.equipped_weapon_id,
		"equipped_armor_id": character.equipped_armor_id,
		"equipped_shield_id": character.equipped_shield_id
	}


func short_rest(character: PlayerCharacter, roll_override: int = -1) -> Dictionary:
	if character.current_health <= 0:
		return {"success": false, "message": "Нельзя отдыхать без сознания.", "healing": 0}
	var before: int = character.current_health
	var roll: int = 0
	var spent_hit_die: bool = false
	if character.current_health < character.maximum_health and character.hit_dice_current > 0:
		roll = clampi(roll_override, 1, character.hit_die_size) if roll_override >= 1 else _dice.roll_die(character.hit_die_size)
		var healing: int = maxi(1, roll + character.get_ability_modifier("constitution"))
		character.current_health = mini(character.maximum_health, character.current_health + healing)
		character.hit_dice_current -= 1
		spent_hit_die = true
	_recharge_short_rest_features(character)
	_race_data.recharge_short_rest_resources(character)
	_spellcasting.recover_after_rest(character, false)
	_save_state()
	if spent_hit_die:
		return {
			"success": true,
			"message": "Короткий отдых: d%d выпало %d, восстановлено %d здоровья. Ресурсы короткого отдыха восстановлены." % [character.hit_die_size, roll, character.current_health - before],
			"healing": character.current_health - before,
			"roll": roll,
			"spent_hit_die": true,
			"duration_hours": 1
		}
	var message: String = "Короткий отдых завершён без траты Кости Хитов. Ресурсы короткого отдыха восстановлены."
	if character.current_health < character.maximum_health:
		message += " Свободных Костей Хитов не осталось."
	else:
		message += " Здоровье уже было полным."
	return {"success": true, "message": message, "healing": 0, "roll": 0, "spent_hit_die": false, "duration_hours": 1}


func long_rest(character: PlayerCharacter) -> Dictionary:
	if character.current_health <= 0:
		return {"success": false, "message": "Для долгого отдыха нужно хотя бы 1 здоровье.", "healing": 0}
	var before: int = character.current_health
	character.current_health = character.maximum_health
	character.hit_dice_maximum = maxi(character.level, 1)
	character.hit_dice_current = character.hit_dice_maximum
	character.restore_class_resources()
	_origin_feats.initialize_character(character, true)
	_spellcasting.recover_after_rest(character, true)
	if character.character_class_id == "rogue":
		character.active_effects["sneak_attack_ready"] = true
	_save_state()
	return {
		"success": true,
		"message": "Долгий отдых (%d ч.) восстановил здоровье, Кости Хитов, ячейки и прочие ресурсы." % character.long_rest_hours,
		"healing": character.current_health - before,
		"duration_hours": character.long_rest_hours
	}


func get_resource_text(character: PlayerCharacter, ability: Dictionary) -> String:
	if _spellcasting.is_spell_definition(ability):
		var spell_level: int = maxi(int(ability.get("spell_level", 0)), 0)
		if spell_level == 0:
			return "Без ячейки"
		var spell_key: String = _spellcasting.active_resource_key(character, ability)
		return "%d / %d" % [character.get_resource(spell_key), character.get_resource_maximum(spell_key)]
	var resource_key: String = str(ability.get("resource_key", "unlimited"))
	if resource_key == "unlimited" or resource_key.is_empty():
		return "Без ограничений"
	var primary_text: String = "%d / %d" % [character.get_resource(resource_key), character.get_resource_maximum(resource_key)]
	var fallback_key: String = str(ability.get("fallback_resource_key", ""))
	if fallback_key.is_empty():
		return primary_text
	return "Бесплатно %s · ячейки %d / %d" % [primary_text, character.get_resource(fallback_key), character.get_resource_maximum(fallback_key)]


func _grant_origin_equipment(character: PlayerCharacter, state: Node) -> bool:
	if bool(state.call("get_flag", ORIGIN_EQUIPMENT_GRANTED_FLAG, false)):
		return false
	if character.background_id == OriginDataSystem.LEGACY_BACKGROUND_ID:
		state.call("set_flag", ORIGIN_EQUIPMENT_GRANTED_FLAG, true)
		return true
	var background: Dictionary = _origin_data.get_background(character.background_id)
	if background.is_empty():
		return false
	var choice: String = str(state.call("get_flag", ORIGIN_EQUIPMENT_CHOICE_FLAG, "package"))
	if choice == "gold":
		state.call("add_item", "gold_coin", 50, false)
	else:
		var package_value: Variant = background.get("equipment_package", [])
		if package_value is Array:
			for entry_value: Variant in package_value:
				if not entry_value is Dictionary:
					continue
				var entry: Dictionary = entry_value as Dictionary
				state.call("add_item", str(entry.get("item_id", "")), maxi(int(entry.get("quantity", 1)), 1), false)
	state.call("set_flag", ORIGIN_EQUIPMENT_GRANTED_FLAG, true)
	return true


func _recharge_short_rest_features(character: PlayerCharacter) -> void:
	if character.character_class_id == "fighter" and character.get_resource_maximum("second_wind") > 0:
		character.set_resource("second_wind", mini(character.get_resource("second_wind") + 1, character.get_resource_maximum("second_wind")))
	if character.character_class_id == "wizard" and not bool(character.active_effects.get("arcane_recovery_used", false)):
		if character.get_resource("spell_slots_1") < character.get_resource_maximum("spell_slots_1"):
			character.set_resource("spell_slots_1", character.get_resource("spell_slots_1") + 1)
			character.active_effects["arcane_recovery_used"] = true


func _initialize_signature_resource(character: PlayerCharacter) -> void:
	var ability: Dictionary = get_signature_ability(character)
	var resource_key: String = str(ability.get("resource_key", "unlimited"))
	if resource_key == "unlimited" or resource_key.is_empty():
		return
	var maximum: int = int(ability.get("max_uses", 0))
	var formula: String = str(ability.get("max_uses_formula", ""))
	if formula == "charisma_modifier_min_1":
		maximum = maxi(character.get_ability_modifier("charisma"), 1)
	elif formula == "wisdom_modifier_min_1":
		maximum = maxi(character.get_ability_modifier("wisdom"), 1)
	character.set_resource(resource_key, maximum, maximum)


func _save_state() -> void:
	var state: Node = _get_game_state()
	if state != null:
		state.call("save_game")


func _get_game_state() -> Node:
	var main_loop: MainLoop = Engine.get_main_loop()
	if main_loop is SceneTree:
		return (main_loop as SceneTree).root.get_node_or_null("GameState")
	return null


func _load_databases() -> void:
	var class_root: Dictionary = _load_json(CLASSES_PATH)
	var classes_value: Variant = class_root.get("classes", [])
	if classes_value is Array:
		for class_value: Variant in classes_value:
			if class_value is Dictionary:
				var class_data: Dictionary = class_value as Dictionary
				_classes[str(class_data.get("id", ""))] = class_data
	_abilities = _load_json(ABILITIES_PATH)
	var racial_abilities: Dictionary = _load_json(RACIAL_ABILITIES_PATH)
	for key: Variant in racial_abilities.keys():
		_abilities[str(key)] = racial_abilities[key]


func _load_json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		push_error("Файл данных не найден: %s" % path)
		return {}
	var file: FileAccess = FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {}
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	return parsed as Dictionary if parsed is Dictionary else {}


static func _string_array(value: Variant) -> Array[String]:
	var result: Array[String] = []
	if value is Array:
		for item: Variant in value:
			result.append(str(item))
	return result
