from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


def replace_function(text: str, name: str, replacement: str) -> str:
    pattern = re.compile(rf"(?ms)^func {re.escape(name)}\(.*?(?=^func |\Z)")
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise RuntimeError(f"{name}: expected one function, found {len(matches)}")
    match = matches[0]
    return text[:match.start()] + replacement.rstrip() + "\n\n\n" + text[match.end():]


# Structured class armor training.
classes_path = ROOT / "data/classes/classes.json"
root = json.loads(classes_path.read_text(encoding="utf-8"))
training = {
    "barbarian": ["light", "medium", "shield"],
    "bard": ["light"],
    "cleric": ["light", "medium", "heavy", "shield"],
    "druid": ["light", "shield"],
    "fighter": ["light", "medium", "heavy", "shield"],
    "monk": [],
    "paladin": ["light", "medium", "heavy", "shield"],
    "ranger": ["light", "medium", "shield"],
    "rogue": ["light"],
    "sorcerer": [],
    "warlock": ["light"],
    "wizard": [],
}
for entry in root.get("classes", []):
    entry["armor_training"] = training.get(entry.get("id", ""), [])
classes_path.write_text(json.dumps(root, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Mark focus items semantically; avoid ID lists in gameplay code.
items_path = ROOT / "data/items/items.json"
items = json.loads(items_path.read_text(encoding="utf-8"))
for item_id in ("lute", "holy_symbol", "druidic_focus", "arcane_focus_crystal", "arcane_focus_orb"):
    if item_id in items:
        items[item_id]["spellcasting_focus"] = True
if "quarterstaff_focus" in items:
    items["quarterstaff_focus"]["spellcasting_focus"] = True
items.setdefault("component_pouch", {
    "id": "component_pouch",
    "name": "Сумка компонентов",
    "type": "gear",
    "description": "Хранит обычные материальные компоненты заклинаний без указанной стоимости.",
    "stackable": False,
    "max_stack": 1,
    "component_pouch": True,
})
items_path.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Stable production turn token.
turn_path = ROOT / "scripts/systems/turn_based_combat_system.gd"
turn = turn_path.read_text(encoding="utf-8")
marker = '''func is_player_turn(player: Node) -> bool:
'''
method = '''func current_turn_token() -> String:
\tvar actor: Node = current_actor()
\tif not active or not is_instance_valid(actor):
\t\treturn ""
\treturn "%d:%d:%d" % [round_number, current_index, actor.get_instance_id()]


'''
if marker not in turn:
    raise RuntimeError("turn token insertion marker missing")
turn = turn.replace(marker, method + marker, 1)
turn_path.write_text(turn, encoding="utf-8")

# Single equipment/inventory-derived casting context.
class_data_path = ROOT / "scripts/systems/class_data_system.gd"
class_data = class_data_path.read_text(encoding="utf-8")
marker = '''func short_rest(character: PlayerCharacter, roll_override: int = -1) -> Dictionary:
'''
method = '''func get_spellcasting_context(
\tcharacter: PlayerCharacter,
\tcombat_state: CombatantState = null,
\tturn_token: String = ""
) -> Dictionary:
\tif character == null:
\t\treturn {}
\tvar state: Node = _get_game_state()
\tvar class_definition: Dictionary = get_class_definition(character.character_class_id)
\tvar weapon: Dictionary = {}
\tvar armor: Dictionary = {}
\tvar shield: Dictionary = {}
\tvar inventory_entries: Array = []
\tif state != null:
\t\tweapon = state.call("get_item_definition", character.equipped_weapon_id) as Dictionary
\t\tarmor = state.call("get_item_definition", character.equipped_armor_id) as Dictionary
\t\tshield = state.call("get_item_definition", character.equipped_shield_id) as Dictionary
\t\tinventory_entries = state.call("get_inventory_entries") as Array

\tvar armor_category: String = str(armor.get("armor_category", "clothing"))
\tvar armor_training: Array[String] = _string_array(class_definition.get("armor_training", []))
\tvar armor_trained: bool = armor.is_empty() or armor_category == "clothing" or armor_category in armor_training
\tvar occupied_hands: int = 0
\tif not weapon.is_empty():
\t\t# Two-handed weapons need two hands to attack, but only one to hold while casting.
\t\toccupied_hands += 1
\tif not shield.is_empty():
\t\toccupied_hands += 1
\tvar free_hands: int = maxi(2 - occupied_hands, 0)
\tvar weapon_properties: Array[String] = _string_array(weapon.get("properties", []))
\tvar focus_in_hand: bool = bool(weapon.get("spellcasting_focus", false)) or "focus" in weapon_properties
\tvar has_component_pouch: bool = false
\tvar has_inventory_focus: bool = false
\tvar has_required_material: bool = true
\tfor value: Variant in inventory_entries:
\t\tif not value is Dictionary:
\t\t\tcontinue
\t\tvar item: Dictionary = value as Dictionary
\t\tif bool(item.get("component_pouch", false)):
\t\t\thas_component_pouch = true
\t\tif bool(item.get("spellcasting_focus", false)):
\t\t\thas_inventory_focus = true
\t# A holy symbol may be displayed on a shield; other loose foci require a hand.
\tvar shield_symbol_focus: bool = not shield.is_empty() and state != null and bool(state.call("has_item", "holy_symbol"))
\tif shield_symbol_focus:
\t\tfocus_in_hand = true
\telif not focus_in_hand and has_inventory_focus and free_hands > 0:
\t\tfocus_in_hand = true
\t\tfree_hands -= 1
\tvar can_speak: bool = not bool(character.active_effects.get("silenced", false)) and not bool(character.active_effects.get("gagged", false))
\tif combat_state != null and (combat_state.has_condition("unconscious") or combat_state.has_condition("incapacitated")):
\t\tcan_speak = false
\treturn {
\t\t"can_speak": can_speak,
\t\t"armor_trained": armor_trained,
\t\t"free_hands": free_hands,
\t\t"focus_in_hand": focus_in_hand,
\t\t"has_component_pouch": has_component_pouch,
\t\t"has_required_material": has_required_material,
\t\t"turn_token": turn_token,
\t\t"equipped_weapon_id": character.equipped_weapon_id,
\t\t"equipped_armor_id": character.equipped_armor_id,
\t\t"equipped_shield_id": character.equipped_shield_id
\t}


'''
if marker not in class_data:
    raise RuntimeError("class context insertion marker missing")
class_data = class_data.replace(marker, method + marker, 1)
# Add local typed string helper at the end.
class_data += '''\n\nstatic func _string_array(value: Variant) -> Array[String]:
\tvar result: Array[String] = []
\tif value is Array:
\t\tfor item: Variant in value:
\t\t\tresult.append(str(item))
\treturn result
'''
class_data_path.write_text(class_data, encoding="utf-8")

# Fix fallback resources: only the primary free use is special; fallback slots follow normal slot rules.
spell_path = ROOT / "scripts/systems/spellcasting_system.gd"
spell = spell_path.read_text(encoding="utf-8")
spell = replace_function(spell, "cast_ritual", '''func cast_ritual(character: PlayerCharacter, spell_id: String, current_world_minutes: int, in_combat: bool = false, casting_context: Dictionary = {}) -> Dictionary:
\tvar spell: Dictionary = get_spell_definition(spell_id)
\tif not can_cast_spell(character, spell, true, in_combat, 0, casting_context):
\t\treturn _failure("Ритуал недоступен: проверьте подготовку, компоненты и отсутствие боя.")
\tvar casting_minutes: int = ritual_casting_minutes(spell)
\tvar completion_minute: int = maxi(current_world_minutes, 0) + casting_minutes
\tvar effect_result: Dictionary = _apply_utility_effect(character, spell, completion_minute)
\tif not bool(effect_result.get("success", false)):
\t\treturn effect_result
\tif bool(spell.get("concentration", false)):
\t\tbegin_concentration(character, spell_id)
\treturn {
\t\t"success": true,
\t\t"message": "%s сотворено как ритуал без расхода ячейки. Затрачено %d мин." % [str(spell.get("name", "Заклинание")), casting_minutes],
\t\t"advance_minutes": casting_minutes,
\t\t"spell_id": spell_id,
\t\t"ritual": true
\t}''')
spell = replace_function(spell, "cast_utility_spell", '''func cast_utility_spell(character: PlayerCharacter, spell: Dictionary, current_world_minutes: int, in_combat: bool = false, casting_context: Dictionary = {}) -> Dictionary:
\tif not can_cast_spell(character, spell, false, in_combat, 0, casting_context):
\t\treturn _failure("Заклинание не подготовлено, не хватает компонентов или нет доступной ячейки.")
\tvar payment: Dictionary = consume_spell_cost_detailed(character, spell, 0, casting_context)
\tif not bool(payment.get("success", false)):
\t\treturn payment
\tvar result: Dictionary = _apply_utility_effect(character, spell, maxi(current_world_minutes, 0))
\tif bool(result.get("success", false)) and bool(spell.get("concentration", false)):
\t\tbegin_concentration(character, str(spell.get("id", "")))
\tresult["slot_level"] = int(payment.get("slot_level", int(spell.get("spell_level", 0))))
\treturn result''')
spell = replace_function(spell, "consume_spell_cost_detailed", '''func consume_spell_cost_detailed(character: PlayerCharacter, spell: Dictionary, slot_level: int = 0, casting_context: Dictionary = {}) -> Dictionary:
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
\tif _has_special_resource_contract(spell) and str(spell.get("fallback_resource_key", "")).is_empty():
\t\treturn _failure("Специальные применения закончились.")
\tif _turn_slot_rule_blocked(character, casting_context):
\t\treturn _failure("На этом ходу уже была потрачена ячейка на другое заклинание.")
\tvar selected_level: int = resolve_slot_level(character, spell, slot_level)
\tif selected_level <= 0:
\t\treturn _failure("Нет доступной ячейки подходящего уровня.")
\tvar resource_key: String = slot_resource_key(character, selected_level)
\tif not character.consume_resource(resource_key, 1):
\t\treturn _failure("Не удалось израсходовать выбранную ячейку.")
\t_mark_slot_expended(character, casting_context)
\treturn {"success": true, "message": "Израсходована ячейка %d уровня." % selected_level, "slot_level": selected_level, "resource_key": resource_key, "expended_slot": true}''')
spell = replace_function(spell, "_available_special_resource_key", '''func _available_special_resource_key(character: PlayerCharacter, spell: Dictionary) -> String:
\tif not _has_special_resource_contract(spell):
\t\treturn ""
\tvar resource_key: String = str(spell.get("resource_key", ""))
\treturn resource_key if character.get_resource(resource_key) > 0 else ""''')
spell_path.write_text(spell, encoding="utf-8")

# Pass context through all spell executors.
ability_path = ROOT / "scripts/systems/class_ability_system.gd"
ability = ability_path.read_text(encoding="utf-8")
ability = replace_once(ability, "func use_self_ability(character: PlayerCharacter, ability: Dictionary) -> Dictionary:\n", "func use_self_ability(character: PlayerCharacter, ability: Dictionary, casting_context: Dictionary = {}) -> Dictionary:\n", "self signature")
ability = replace_once(ability, "return _spellcasting.cast_utility_spell(character, ability, current_minutes, false)", "return _spellcasting.cast_utility_spell(character, ability, current_minutes, false, casting_context)", "utility context")
ability = ability.replace("return _heal_with_dice(character, ability, 2, 8, character.get_ability_modifier(\"wisdom\"))", "return _heal_with_dice(character, ability, 2, 8, character.get_ability_modifier(\"wisdom\"), casting_context)")
ability = ability.replace("return _heal_with_dice(character, ability, 1, 10, character.level)", "return _heal_with_dice(character, ability, 1, 10, character.level, casting_context)")
ability = ability.replace("return _heal_with_dice(character, ability, healing_pair[0], healing_pair[1], character.get_ability_modifier(ability_id))", "return _heal_with_dice(character, ability, healing_pair[0], healing_pair[1], character.get_ability_modifier(ability_id), casting_context)")
ability = replace_function(ability, "apply_target_ability", '''func apply_target_ability(character: PlayerCharacter, ability: Dictionary, casting_context: Dictionary = {}) -> Dictionary:
\tvar effect: String = str(ability.get("effect", ""))
\tif effect != "hunters_mark":
\t\treturn _failure("Способность не может быть применена к этой цели.")
\tif _spellcasting.is_spell_definition(ability):
\t\tvar payment: Dictionary = _spellcasting.consume_spell_cost_detailed(character, ability, int(casting_context.get("slot_level", 0)), casting_context)
\t\tif not bool(payment.get("success", false)):
\t\t\treturn _failure(str(payment.get("message", "Заклинание недоступно.")))
\telif not _consume_ability_resource(character, ability, 1):
\t\treturn _failure("Ресурс способности закончился.")
\tcharacter.active_effects["hunters_mark_hits"] = 3
\tif bool(ability.get("concentration", false)):
\t\t_spellcasting.begin_concentration(character, str(ability.get("id", "hunters_mark")))
\treturn _success("Цель отмечена. Три следующих попадания нанесут дополнительно 1d6 урона.")''')
ability = replace_once(ability, "func _heal_with_dice(character: PlayerCharacter, ability: Dictionary, count: int, sides: int, bonus: int) -> Dictionary:\n", "func _heal_with_dice(character: PlayerCharacter, ability: Dictionary, count: int, sides: int, bonus: int, casting_context: Dictionary = {}) -> Dictionary:\n", "heal signature")
ability = replace_once(ability, "var payment: Dictionary = _spellcasting.consume_spell_cost_detailed(character, ability)\n", "var payment: Dictionary = _spellcasting.consume_spell_cost_detailed(character, ability, 0, casting_context)\n", "heal payment context")
ability_path.write_text(ability, encoding="utf-8")

# Production game contexts.
game_path = ROOT / "scripts/game/game_srd_combat.gd"
game = game_path.read_text(encoding="utf-8")
game = replace_function(game, "_build_srd_attack_context", '''func _build_srd_attack_context(target: Node, distance: int) -> Dictionary:
\tvar cover: Dictionary = _get_cover_to_target(target)
\tvar context: Dictionary = {
\t\t"target_name": _target_name(target),
\t\t"distance_feet": distance,
\t\t"disadvantage": false,
\t\t"ranged_threat": _has_hostile_within_five_feet(),
\t\t"advantage": _player_combat_state.hidden,
\t\t"cover_bonus": int(cover.get("bonus", 0)),
\t\t"total_cover": bool(cover.get("total_cover", false)),
\t\t"attacker_can_see_defender": not bool(cover.get("total_cover", false)),
\t\t"defender_can_see_attacker": not _player_combat_state.hidden,
\t\t"attacker_state": _player_combat_state,
\t\t"defender_state": _state_for(target),
\t\t"target_save_modifier": int(target.call("get_saving_throw_modifier", "dexterity")) if target.has_method("get_saving_throw_modifier") else 0
\t}
\tcontext.merge(_build_spellcasting_context(), true)
\treturn context


func _build_spellcasting_context() -> Dictionary:
\tvar turn_token: String = _turn_system.current_turn_token() if _turn_system != null else ""
\treturn _class_data.get_spellcasting_context(GameState.player_character, _player_combat_state, turn_token)''')
game = replace_once(game, "var target_type: String = str(ability.get(\"target\", \"self\"))\n", "var target_type: String = str(ability.get(\"target\", \"self\"))\n\tvar casting_context: Dictionary = _build_spellcasting_context()\n", "production casting context")
game = replace_once(game, "response = _ability_system.use_self_ability(GameState.player_character, ability)", "response = _ability_system.use_self_ability(GameState.player_character, ability, casting_context)", "self production context")
game = replace_once(game, "response = _ability_system.apply_target_ability(GameState.player_character, ability)", "response = _ability_system.apply_target_ability(GameState.player_character, ability, casting_context)", "target production context")
game_path.write_text(game, encoding="utf-8")

# Ritual UI uses the same equipment-derived context.
hub_path = ROOT / "scripts/ui/character_hub.gd"
hub = hub_path.read_text(encoding="utf-8")
hub = replace_once(
    hub,
    "var response: Dictionary = _spellcasting.cast_ritual(_hero, _selected_power, current_minutes, _is_combat_active())",
    "var casting_context: Dictionary = _class_data.get_spellcasting_context(_hero)\n\tvar response: Dictionary = _spellcasting.cast_ritual(_hero, _selected_power, current_minutes, _is_combat_active(), casting_context)",
    "ritual production context",
)
hub_path.write_text(hub, encoding="utf-8")

# Regression tests for production token/context and fallback slots.
test_path = ROOT / "tests/test_spellcasting_progression_components.gd"
test = test_path.read_text(encoding="utf-8")
insert = '''\n\tvar game_state: Node = root.get_node_or_null("GameState")
\tif game_state == null:
\t\t_fail("GameState was unavailable for production casting-context tests.")
\t\treturn
\tgame_state.call("new_game")
\tgame_state.set("player_character", wizard)
\tgame_state.call("add_item", "quarterstaff_focus", 1, false)
\tgame_state.call("add_item", "robe", 1, false)
\twizard.equipped_weapon_id = "quarterstaff_focus"
\twizard.equipped_armor_id = "robe"
\twizard.equipped_shield_id = ""
\tvar class_data := ClassDataSystem.new()
\tvar production_context: Dictionary = class_data.get_spellcasting_context(wizard)
\tif not bool(production_context.get("focus_in_hand", false)) or int(production_context.get("free_hands", 0)) != 1 or not bool(production_context.get("armor_trained", false)):
\t\t_fail("Production casting context did not derive the equipped focus, hand count, and clothing state.")
\t\treturn
\tgame_state.call("add_item", "chain_mail", 1, false)
\twizard.equipped_armor_id = "chain_mail"
\tproduction_context = class_data.get_spellcasting_context(wizard)
\tif bool(production_context.get("armor_trained", true)):
\t\t_fail("Wizard casting context incorrectly treated heavy armor as trained.")
\t\treturn
\twizard.equipped_armor_id = "robe"
\twizard.active_effects["silenced"] = true
\tproduction_context = class_data.get_spellcasting_context(wizard)
\tif bool(production_context.get("can_speak", true)):
\t\t_fail("Silenced character retained verbal component access.")
\t\treturn
\twizard.active_effects.erase("silenced")

\tvar turn_system := TurnBasedCombatSystem.new()
\tvar player_node := Node.new()
\tplayer_node.name = "Caster"
\tvar opponent_node := Node.new()
\topponent_node.name = "Opponent"
\troot.add_child(player_node)
\troot.add_child(opponent_node)
\tturn_system.start_combat(player_node, [opponent_node], 0, {player_node.get_instance_id(): 20, opponent_node.get_instance_id(): 1})
\tvar first_turn_token: String = turn_system.current_turn_token()
\tif first_turn_token.is_empty() or turn_system.current_turn_token() != first_turn_token:
\t\t_fail("TurnBasedCombatSystem did not expose a stable token for the active turn.")
\t\treturn
\tturn_system.advance_turn()
\tif turn_system.current_turn_token() == first_turn_token:
\t\t_fail("Turn token did not change after advancing combat.")
\t\treturn
\tplayer_node.queue_free()
\topponent_node.queue_free()

\tvar origin_spell: Dictionary = spells.get_spell_definition("origin_magic_missile")
\tif "origin_magic_missile" not in wizard.known_features:
\t\twizard.known_features.append("origin_magic_missile")
\twizard.set_resource("magic_initiate_wizard_1", 0, 1)
\twizard.class_resources.erase("_slot_spell_turn_token")
\tvar fallback_before: int = wizard.get_resource("spell_slots_1")
\tvar fallback_payment: Dictionary = spells.consume_spell_cost_detailed(wizard, origin_spell, 1, {"turn_token": "fallback_turn"})
\tif not bool(fallback_payment.get("success", false)) or not bool(fallback_payment.get("expended_slot", false)):
\t\t_fail("Magic Initiate fallback was not treated as a real spell-slot expenditure.")
\t\treturn
\tif wizard.get_resource("spell_slots_1") != fallback_before - 1:
\t\t_fail("Magic Initiate fallback did not consume the mapped spell slot.")
\t\treturn
\tvar fallback_second: Dictionary = spells.consume_spell_cost_detailed(wizard, origin_spell, 1, {"turn_token": "fallback_turn"})
\tif bool(fallback_second.get("success", false)):
\t\t_fail("Magic Initiate fallback bypassed the one-slot-per-turn rule.")
\t\treturn
'''
needle = '\n\tvar warlock := PlayerCharacter.new()\n'
if needle not in test:
    raise RuntimeError("test insertion marker missing")
test = test.replace(needle, insert + needle, 1)
# Add Warlock fallback upcast assertion after pact setup.
needle = '''\tif spells.slot_resource_key(warlock, 1) != "pact_slots_3":
\t\t_fail("A lower-level Warlock spell did not resolve to the current Pact slot level.")
\t\treturn
'''
replacement = needle + '''\tif "origin_magic_missile" not in warlock.known_features:
\t\twarlock.known_features.append("origin_magic_missile")
\twarlock.set_resource("magic_initiate_wizard_1", 0, 1)
\tvar pact_fallback: Dictionary = spells.consume_spell_cost_detailed(warlock, origin_spell, 0, {"turn_token": "warlock_turn"})
\tif not bool(pact_fallback.get("success", false)) or int(pact_fallback.get("slot_level", 0)) != 3 or str(pact_fallback.get("resource_key", "")) != "pact_slots_3":
\t\t_fail("Magic Initiate fallback did not use and upcast through the current Pact slot.")
\t\treturn
'''
test = replace_once(test, needle, replacement, "warlock fallback test")
test_path.write_text(test, encoding="utf-8")

print("Production casting context and fallback fixes applied.")
