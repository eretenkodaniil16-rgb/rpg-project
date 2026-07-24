from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_function(text: str, name: str, replacement: str) -> str:
    pattern = re.compile(rf"(?ms)^func {re.escape(name)}\(.*?(?=^func |\Z)")
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise RuntimeError(f"Expected one function {name}, found {len(matches)}")
    match = matches[0]
    return text[:match.start()] + replacement.rstrip() + "\n\n\n" + text[match.end():]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


spell_path = ROOT / "scripts/systems/spellcasting_system.gd"
text = spell_path.read_text(encoding="utf-8")
text = replace_once(
    text,
    "var _classes: Dictionary = {}\n",
    "var _classes: Dictionary = {}\nvar _progression: SpellcastingProgressionSystem = SpellcastingProgressionSystem.new()\n",
    "progression field",
)

text = replace_function(text, "ensure_character", '''func ensure_character(character: PlayerCharacter, refill_slots: bool = false) -> bool:
\tif character == null:
\t\treturn false
\tvar profile: Dictionary = get_spellcasting_profile(character.character_class_id)
\tvar changed: bool = false
\tif not profile.is_empty():
\t\tvar ability_id: String = str(profile.get("ability", ""))
\t\tif str(character.class_resources.get(SPELLCASTING_ABILITY_STATE_KEY, "")) != ability_id:
\t\t\tcharacter.class_resources[SPELLCASTING_ABILITY_STATE_KEY] = ability_id
\t\t\tchanged = true
\t\tvar fallback_limit: int = maxi(int(profile.get("prepared_limit", 0)), 0)
\t\tvar prepared_limit: int = _progression.get_prepared_limit(character.character_class_id, character.level, fallback_limit)
\t\tif int(character.class_resources.get(PREPARED_LIMIT_STATE_KEY, -1)) != prepared_limit:
\t\t\tcharacter.class_resources[PREPARED_LIMIT_STATE_KEY] = prepared_limit
\t\t\tchanged = true
\t\tfor spell_id: String in _string_array(profile.get("starting_spells", [])):
\t\t\tchanged = _append_unique(character.known_features, spell_id) or changed
\t\tvar had_prepared_state: bool = character.class_resources.has(PREPARED_SPELLS_STATE_KEY)
\t\tvar profile_prepared: Array[String] = get_prepared_spell_ids(character)
\t\tif not had_prepared_state:
\t\t\tfor spell_id: String in _string_array(profile.get("starting_prepared", [])):
\t\t\t\tif spell_id not in profile_prepared:
\t\t\t\t\tprofile_prepared.append(spell_id)
\t\t\t\t\tchanged = true
\t\t_store_prepared_spell_ids(character, profile_prepared)
\t\tchanged = changed or not had_prepared_state
\t\tvar maximums: Dictionary = _slot_maximums(character, profile)
\t\tchanged = _sync_slot_resources(character, profile, maximums, refill_slots) or changed
\tfor feature_id: String in character.known_features.duplicate():
\t\tvar spell: Dictionary = get_spell_definition(feature_id)
\t\tif spell.is_empty() or not bool(spell.get("always_prepared", false)):
\t\t\tcontinue
\t\tvar always_prepared_ids: Array[String] = get_prepared_spell_ids(character)
\t\tif feature_id not in always_prepared_ids:
\t\t\talways_prepared_ids.append(feature_id)
\t\t\t_store_prepared_spell_ids(character, always_prepared_ids)
\t\t\tchanged = true
\treturn changed''')

text = replace_function(text, "recover_after_rest", '''func recover_after_rest(character: PlayerCharacter, long_rest: bool) -> bool:
\tif character == null:
\t\treturn false
\tensure_character(character, false)
\tvar profile: Dictionary = get_spellcasting_profile(character.character_class_id)
\tif profile.is_empty():
\t\tif long_rest:
\t\t\tend_concentration(character)
\t\treturn false
\tvar recovery: String = str(profile.get("slot_recovery", "long_rest"))
\tvar should_refill: bool = long_rest or recovery == "short_rest"
\tvar changed: bool = false
\tif should_refill:
\t\tfor level_value: Variant in _slot_maximums(character, profile).keys():
\t\t\tvar level: int = maxi(int(str(level_value)), 1)
\t\t\tvar resource_key: String = slot_resource_key(character, level)
\t\t\tvar maximum: int = maxi(character.get_resource_maximum(resource_key), 0)
\t\t\tif character.get_resource(resource_key) != maximum:
\t\t\t\tcharacter.class_resources[resource_key] = maximum
\t\t\t\tchanged = true
\tif long_rest and not get_concentration_spell_id(character).is_empty():
\t\tend_concentration(character)
\t\tchanged = true
\treturn changed''')

text = replace_function(text, "can_cast_spell", '''func can_cast_spell(character: PlayerCharacter, spell: Dictionary, as_ritual: bool = false, in_combat: bool = false, slot_level: int = 0, casting_context: Dictionary = {}) -> bool:
\tif character == null or spell.is_empty() or not is_spell_definition(spell):
\t\treturn false
\tif not bool(check_spell_components(spell, casting_context).get("success", false)):
\t\treturn false
\tvar spell_id: String = str(spell.get("id", ""))
\tif spell_id.is_empty() or spell_id not in get_known_spell_ids(character):
\t\treturn false
\tvar level: int = maxi(int(spell.get("spell_level", 0)), 0)
\tvar prepared: bool = is_prepared(character, spell_id)
\tif as_ritual:
\t\tvar wizard_ritual_adept: bool = character.character_class_id == "wizard" and "ritual_adept" in character.known_features
\t\treturn level > 0 and bool(spell.get("ritual", false)) and not in_combat and (prepared or wizard_ritual_adept)
\tif not prepared:
\t\treturn false
\tif level == 0:
\t\treturn true
\tvar special_key: String = _available_special_resource_key(character, spell)
\tif not special_key.is_empty():
\t\treturn true
\tif _has_special_resource_contract(spell) and str(spell.get("fallback_resource_key", "")).is_empty():
\t\treturn false
\tif _turn_slot_rule_blocked(character, casting_context):
\t\treturn false
\treturn resolve_slot_level(character, spell, slot_level) > 0''')

text = replace_function(text, "consume_spell_cost", '''func consume_spell_cost(character: PlayerCharacter, spell: Dictionary, slot_level: int = 0) -> bool:
\treturn bool(consume_spell_cost_detailed(character, spell, slot_level).get("success", false))''')

text = replace_function(text, "active_resource_key", '''func active_resource_key(character: PlayerCharacter, spell: Dictionary) -> String:
\tif character == null or spell.is_empty():
\t\treturn ""
\tvar level: int = maxi(int(spell.get("spell_level", 0)), 0)
\tif level == 0:
\t\treturn "unlimited"
\tvar special_key: String = _available_special_resource_key(character, spell)
\tif not special_key.is_empty():
\t\treturn special_key
\tvar selected_level: int = resolve_slot_level(character, spell, 0)
\treturn slot_resource_key(character, selected_level if selected_level > 0 else level)''')

text = replace_function(text, "slot_resource_key", '''func slot_resource_key(character: PlayerCharacter, level: int) -> String:
\tvar profile: Dictionary = get_spellcasting_profile(character.character_class_id if character != null else "")
\tvar prefix: String = str(profile.get("slot_resource_prefix", "spell_slots"))
\tif character != null and _progression.uses_pact_magic(character.character_class_id):
\t\tvar pact_level: int = _progression.get_pact_slot_level(character.character_class_id, character.level)
\t\treturn "%s_%d" % [prefix, maxi(pact_level, 1)]
\treturn "%s_%d" % [prefix, maxi(level, 1)]''')

insert_marker = "func ritual_casting_minutes(spell: Dictionary) -> int:\n"
new_methods = '''func consume_spell_cost_detailed(character: PlayerCharacter, spell: Dictionary, slot_level: int = 0, casting_context: Dictionary = {}) -> Dictionary:
\tif character == null or spell.is_empty():
\t\treturn _failure("Заклинание не найдено.")
\tvar component_result: Dictionary = check_spell_components(spell, casting_context)
\tif not bool(component_result.get("success", false)):
\t\treturn component_result
\tvar level: int = maxi(int(spell.get("spell_level", 0)), 0)
\tif level == 0:
\t\treturn {"success": true, "message": "Заговор не расходует ячейку.", "slot_level": 0, "resource_key": "unlimited", "expended_slot": false}
\tvar special_key: String = _available_special_resource_key(character, spell)
\tif not special_key.is_empty():
\t\tif not character.consume_resource(special_key, 1):
\t\t\treturn _failure("Не удалось израсходовать бесплатное применение.")
\t\treturn {"success": true, "message": "Использовано специальное применение.", "slot_level": level, "resource_key": special_key, "expended_slot": false}
\tif _turn_slot_rule_blocked(character, casting_context):
\t\treturn _failure("На этом ходу уже была потрачена ячейка на другое заклинание.")
\tvar selected_level: int = resolve_slot_level(character, spell, slot_level)
\tif selected_level <= 0:
\t\treturn _failure("Нет доступной ячейки подходящего уровня.")
\tvar resource_key: String = slot_resource_key(character, selected_level)
\tif not character.consume_resource(resource_key, 1):
\t\treturn _failure("Не удалось израсходовать выбранную ячейку.")
\t_mark_slot_expended(character, casting_context)
\treturn {"success": true, "message": "Израсходована ячейка %d уровня." % selected_level, "slot_level": selected_level, "resource_key": resource_key, "expended_slot": true}


func get_available_slot_levels(character: PlayerCharacter, minimum_level: int = 1, require_remaining: bool = true) -> Array[int]:
\tvar result: Array[int] = []
\tif character == null:
\t\treturn result
\tvar profile: Dictionary = get_spellcasting_profile(character.character_class_id)
\tvar maximums: Dictionary = _slot_maximums(character, profile)
\tfor level_value: Variant in maximums.keys():
\t\tvar level: int = maxi(int(str(level_value)), 1)
\t\tif level < minimum_level:
\t\t\tcontinue
\t\tvar key: String = slot_resource_key(character, level)
\t\tif not require_remaining or character.get_resource(key) > 0:
\t\t\tif level not in result:
\t\t\t\tresult.append(level)
\tresult.sort()
\treturn result


func resolve_slot_level(character: PlayerCharacter, spell: Dictionary, requested_level: int = 0) -> int:
\tif character == null or spell.is_empty():
\t\treturn 0
\tvar minimum: int = maxi(int(spell.get("spell_level", 0)), 1)
\tvar chosen: int = requested_level
\tif chosen <= 0:
\t\tchosen = get_selected_slot_level(character, str(spell.get("id", "")))
\tvar available: Array[int] = get_available_slot_levels(character, minimum, true)
\tif chosen > 0:
\t\treturn chosen if chosen in available else 0
\treturn available[0] if not available.is_empty() else 0


func set_selected_slot_level(character: PlayerCharacter, spell_id: String, slot_level: int) -> Dictionary:
\tvar spell: Dictionary = get_spell_definition(spell_id)
\tif character == null or spell.is_empty() or int(spell.get("spell_level", 0)) <= 0:
\t\treturn _failure("Для этого заклинания уровень ячейки не выбирается.")
\tvar selectable: Array[int] = get_available_slot_levels(character, int(spell.get("spell_level", 1)), false)
\tif slot_level not in selectable:
\t\treturn _failure("Ячейка %d уровня недоступна этому персонажу." % slot_level)
\tvar choices_value: Variant = character.class_resources.get("_selected_spell_slot_levels", {})
\tvar choices: Dictionary = (choices_value as Dictionary).duplicate(true) if choices_value is Dictionary else {}
\tchoices[spell_id] = slot_level
\tcharacter.class_resources["_selected_spell_slot_levels"] = choices
\treturn _success("Выбрана ячейка %d уровня." % slot_level)


func get_selected_slot_level(character: PlayerCharacter, spell_id: String) -> int:
\tif character == null:
\t\treturn 0
\tvar choices_value: Variant = character.class_resources.get("_selected_spell_slot_levels", {})
\tif not choices_value is Dictionary:
\t\treturn 0
\treturn maxi(int((choices_value as Dictionary).get(spell_id, 0)), 0)


func check_spell_components(spell: Dictionary, casting_context: Dictionary = {}) -> Dictionary:
\tvar components: Array[String] = _string_array(spell.get("components", []))
\tif "v" in components and not bool(casting_context.get("can_speak", true)):
\t\treturn _failure("Для вербального компонента требуется нормальная речь.")
\tif not bool(casting_context.get("armor_trained", true)):
\t\treturn _failure("Нельзя сотворять заклинание в доспехе без соответствующего обучения.")
\tvar free_hands: int = maxi(int(casting_context.get("free_hands", 1)), 0)
\tvar focus_in_hand: bool = bool(casting_context.get("focus_in_hand", true))
\tvar has_pouch: bool = bool(casting_context.get("has_component_pouch", true))
\tvar has_material: bool = bool(casting_context.get("has_required_material", true))
\tvar has_m: bool = "m" in components
\tif has_m:
\t\tvar costly_or_consumed: bool = int(spell.get("material_cost_gp", 0)) > 0 or bool(spell.get("material_consumed", false))
\t\tif costly_or_consumed:
\t\t\tif not has_material or free_hands <= 0:
\t\t\t\treturn _failure("Нужен указанный материальный компонент и свободная рука.")
\t\telif not focus_in_hand and not (has_pouch and free_hands > 0):
\t\t\treturn _failure("Нужен магический фокус в руке или сумка компонентов со свободной рукой.")
\tif "s" in components and free_hands <= 0 and not (has_m and focus_in_hand):
\t\treturn _failure("Для соматического компонента требуется свободная рука.")
\treturn _success("Компоненты доступны.")


func scale_dice_for_slot(spell: Dictionary, base_dice: Array[int], slot_level: int, kind: String) -> Array[int]:
\tvar result: Array[int] = [maxi(base_dice[0] if base_dice.size() > 0 else 1, 1), maxi(base_dice[1] if base_dice.size() > 1 else 6, 2)]
\tvar base_level: int = maxi(int(spell.get("spell_level", 0)), 0)
\tvar extra_levels: int = maxi(slot_level - base_level, 0)
\tif extra_levels <= 0:
\t\treturn result
\tvar upcast_value: Variant = spell.get("upcast", {})
\tif not upcast_value is Dictionary:
\t\treturn result
\tvar field: String = "%s_dice_per_level" % kind
\tvar pair_value: Variant = (upcast_value as Dictionary).get(field, [])
\tif pair_value is Array and (pair_value as Array).size() >= 2:
\t\tresult[0] += maxi(int((pair_value as Array)[0]), 0) * extra_levels
\t\tresult[1] = maxi(int((pair_value as Array)[1]), 2)
\treturn result


func damage_bonus_for_slot(spell: Dictionary, slot_level: int) -> int:
\tvar base_bonus: int = int(spell.get("damage_bonus", 0))
\tvar extra_levels: int = maxi(slot_level - maxi(int(spell.get("spell_level", 0)), 0), 0)
\tvar upcast_value: Variant = spell.get("upcast", {})
\tvar per_level: int = int((upcast_value as Dictionary).get("damage_bonus_per_level", 0)) if upcast_value is Dictionary else 0
\treturn base_bonus + per_level * extra_levels


'''
if insert_marker not in text:
    raise RuntimeError("ritual marker missing")
text = text.replace(insert_marker, new_methods + insert_marker, 1)

text = replace_function(text, "_find_available_slot_level", '''func _find_available_slot_level(character: PlayerCharacter, preferred_level: int, minimum_level: int) -> int:
\tvar available: Array[int] = get_available_slot_levels(character, minimum_level, true)
\tif preferred_level in available:
\t\treturn preferred_level
\tfor level: int in available:
\t\tif level >= preferred_level:
\t\t\treturn level
\treturn available[0] if not available.is_empty() else 0''')

helper_marker = "func _mapped_resource_key(character: PlayerCharacter, resource_key: String) -> String:\n"
helpers = '''func _slot_maximums(character: PlayerCharacter, profile: Dictionary) -> Dictionary:
\tvar progression_maximums: Dictionary = _progression.get_slot_maximums(character.character_class_id, character.level)
\tif not progression_maximums.is_empty():
\t\treturn progression_maximums
\tvar fallback_value: Variant = profile.get("slot_maximums", {})
\treturn (fallback_value as Dictionary).duplicate(true) if fallback_value is Dictionary else {}


func _sync_slot_resources(character: PlayerCharacter, profile: Dictionary, maximums: Dictionary, refill_slots: bool) -> bool:
\tif _progression.uses_pact_magic(character.character_class_id):
\t\treturn _sync_pact_slot_resources(character, profile, maximums, refill_slots)
\tvar prefix: String = str(profile.get("slot_resource_prefix", "spell_slots"))
\tvar changed: bool = false
\tfor level: int in range(1, 10):
\t\tvar key: String = "%s_%d" % [prefix, level]
\t\tvar maximum: int = maxi(int(maximums.get(str(level), maximums.get(level, 0))), 0)
\t\tvar had_maximum: bool = character.class_resource_maximums.has(key)
\t\tvar old_maximum: int = character.get_resource_maximum(key)
\t\tvar current: int = character.get_resource(key)
\t\tif maximum <= 0:
\t\t\tif had_maximum or character.class_resources.has(key):
\t\t\t\tcharacter.class_resource_maximums.erase(key)
\t\t\t\tcharacter.class_resources.erase(key)
\t\t\t\tchanged = true
\t\t\tcontinue
\t\tvar spent: int = maxi(old_maximum - current, 0)
\t\tvar next_current: int = maximum if refill_slots or not had_maximum else clampi(maximum - spent, 0, maximum)
\t\tif not had_maximum or old_maximum != maximum or current != next_current:
\t\t\tchanged = true
\t\tcharacter.class_resource_maximums[key] = maximum
\t\tcharacter.class_resources[key] = next_current
\treturn changed


func _sync_pact_slot_resources(character: PlayerCharacter, profile: Dictionary, maximums: Dictionary, refill_slots: bool) -> bool:
\tvar prefix: String = str(profile.get("slot_resource_prefix", "pact_slots"))
\tvar new_level: int = _progression.get_pact_slot_level(character.character_class_id, character.level)
\tvar new_maximum: int = maxi(int(maximums.get(str(new_level), maximums.get(new_level, 0))), 0)
\tvar old_maximum: int = 0
\tvar old_current: int = 0
\tvar changed: bool = false
\tfor level: int in range(1, 10):
\t\tvar key: String = "%s_%d" % [prefix, level]
\t\tif character.class_resource_maximums.has(key) or character.class_resources.has(key):
\t\t\told_maximum = maxi(old_maximum, character.get_resource_maximum(key))
\t\t\told_current = maxi(old_current, character.get_resource(key))
\t\t\tif level != new_level:
\t\t\t\tcharacter.class_resource_maximums.erase(key)
\t\t\t\tcharacter.class_resources.erase(key)
\t\t\t\tchanged = true
\tvar key: String = "%s_%d" % [prefix, maxi(new_level, 1)]
\tvar had_target: bool = character.class_resource_maximums.has(key)
\tvar spent: int = maxi(old_maximum - old_current, 0)
\tvar next_current: int = new_maximum if refill_slots or old_maximum <= 0 else clampi(new_maximum - spent, 0, new_maximum)
\tif not had_target or character.get_resource_maximum(key) != new_maximum or character.get_resource(key) != next_current:
\t\tchanged = true
\tcharacter.class_resource_maximums[key] = new_maximum
\tcharacter.class_resources[key] = next_current
\tcharacter.class_resources["_pact_slot_level"] = new_level
\treturn changed


func _has_special_resource_contract(spell: Dictionary) -> bool:
\tvar resource_key: String = str(spell.get("resource_key", ""))
\treturn not resource_key.is_empty() and resource_key != "unlimited" and not resource_key.begins_with("spell_slots_")


func _available_special_resource_key(character: PlayerCharacter, spell: Dictionary) -> String:
\tif not _has_special_resource_contract(spell):
\t\treturn ""
\tvar resource_key: String = str(spell.get("resource_key", ""))
\tif character.get_resource(resource_key) > 0:
\t\treturn resource_key
\tvar fallback_key: String = str(spell.get("fallback_resource_key", ""))
\tif fallback_key.is_empty():
\t\treturn ""
\tvar mapped: String = _mapped_resource_key(character, fallback_key)
\treturn mapped if character.get_resource(mapped) > 0 else ""


func _turn_slot_rule_blocked(character: PlayerCharacter, casting_context: Dictionary) -> bool:
\tvar turn_token: String = str(casting_context.get("turn_token", ""))
\treturn not turn_token.is_empty() and str(character.class_resources.get("_slot_spell_turn_token", "")) == turn_token


func _mark_slot_expended(character: PlayerCharacter, casting_context: Dictionary) -> void:
\tvar turn_token: String = str(casting_context.get("turn_token", ""))
\tif not turn_token.is_empty():
\t\tcharacter.class_resources["_slot_spell_turn_token"] = turn_token


'''
if helper_marker not in text:
    raise RuntimeError("helper marker missing")
text = text.replace(helper_marker, helpers + helper_marker, 1)
spell_path.write_text(text, encoding="utf-8")

# Upcast metadata is data, not executor-specific conditionals.
abilities_path = ROOT / "data/abilities/abilities.json"
data = json.loads(abilities_path.read_text(encoding="utf-8"))
for spell_id in ("magic_missile", "origin_magic_missile"):
    if spell_id in data:
        data[spell_id]["upcast"] = {"damage_dice_per_level": [1, 4], "damage_bonus_per_level": 1}
for spell_id in ("cure_wounds", "origin_cure_wounds"):
    if spell_id in data:
        data[spell_id]["upcast"] = {"healing_dice_per_level": [1, 8]}
abilities_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

ability_path = ROOT / "scripts/systems/class_ability_system.gd"
ability = ability_path.read_text(encoding="utf-8")
ability = replace_once(
    ability,
    '''\tif not _consume_ability_resource(character, ability, 1):
\t\tresult.note = "Заклинание не подготовлено или не осталось ячеек подходящего уровня."
\t\treturn result
\tif bool(ability.get("concentration", false)):
\t\t_spellcasting.begin_concentration(character, str(ability.get("id", "")))
\tvar damage_dice: Array[int] = _damage_dice_for_level(ability, character.level)
''',
    '''\tvar cast_slot_level: int = maxi(int(ability.get("spell_level", 0)), 0)
\tif _spellcasting.is_spell_definition(ability):
\t\tvar payment: Dictionary = _spellcasting.consume_spell_cost_detailed(character, ability, int(attack_context.get("slot_level", 0)), attack_context)
\t\tif not bool(payment.get("success", false)):
\t\t\tresult.note = str(payment.get("message", "Заклинание недоступно."))
\t\t\treturn result
\t\tcast_slot_level = int(payment.get("slot_level", cast_slot_level))
\telif not _consume_ability_resource(character, ability, 1):
\t\tresult.note = "Ресурс способности закончился."
\t\treturn result
\tif bool(ability.get("concentration", false)):
\t\t_spellcasting.begin_concentration(character, str(ability.get("id", "")))
\tvar damage_dice: Array[int] = _damage_dice_for_level(ability, character.level)
\tdamage_dice = _spellcasting.scale_dice_for_slot(ability, damage_dice, cast_slot_level, "damage")
''',
    "offensive payment",
)
ability = ability.replace('int(ability.get("damage_bonus", 0))', '_spellcasting.damage_bonus_for_slot(ability, cast_slot_level)')
ability = replace_function(ability, "_heal_with_dice", '''func _heal_with_dice(character: PlayerCharacter, ability: Dictionary, count: int, sides: int, bonus: int) -> Dictionary:
\tif character.current_health >= character.maximum_health:
\t\treturn _failure("Здоровье уже полностью восстановлено.")
\tvar slot_level: int = maxi(int(ability.get("spell_level", 0)), 0)
\tif _spellcasting.is_spell_definition(ability):
\t\tvar payment: Dictionary = _spellcasting.consume_spell_cost_detailed(character, ability)
\t\tif not bool(payment.get("success", false)):
\t\t\treturn _failure(str(payment.get("message", "Заклинание недоступно.")))
\t\tslot_level = int(payment.get("slot_level", slot_level))
\telif not _consume_ability_resource(character, ability, 1):
\t\treturn _failure("Ресурс способности закончился.")
\tvar healing_dice: Array[int] = _spellcasting.scale_dice_for_slot(ability, [count, sides], slot_level, "healing")
\tvar amount: int = maxi(0, _roll_damage(healing_dice[0], healing_dice[1], []) + bonus)
\tvar before: int = character.current_health
\tcharacter.current_health = mini(character.maximum_health, character.current_health + amount)
\tvar restored: int = character.current_health - before
\treturn {"success": true, "message": "Восстановлено %d здоровья ячейкой %d уровня." % [restored, slot_level], "healing": restored, "slot_level": slot_level}''')
ability_path.write_text(ability, encoding="utf-8")

print("Spellcasting progression patch applied.")
