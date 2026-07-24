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


# PlayerCharacter: explicit spellbook state with serialization.
model_path = ROOT / "scripts/models/player_character.gd"
model = model_path.read_text(encoding="utf-8")
model = replace_once(
    model,
    'var known_features: Array[String] = []\nvar signature_ability_id: String = ""\n',
    'var known_features: Array[String] = []\nvar spellbook_spell_ids: Array[String] = []\nvar spellbook_initialized: bool = false\nvar signature_ability_id: String = ""\n',
    "spellbook fields",
)
model = replace_once(
    model,
    '\t\t"known_features": known_features.duplicate(),\n\t\t"signature_ability_id": signature_ability_id,\n',
    '\t\t"known_features": known_features.duplicate(),\n\t\t"spellbook_spell_ids": spellbook_spell_ids.duplicate(),\n\t\t"spellbook_initialized": spellbook_initialized,\n\t\t"signature_ability_id": signature_ability_id,\n',
    "spellbook serialization",
)
model = replace_once(
    model,
    '\tcharacter.known_features = _string_array(data.get("known_features", []))\n\tcharacter.signature_ability_id = str(data.get("signature_ability_id", ""))\n',
    '\tcharacter.known_features = _unique_string_array(data.get("known_features", []))\n\tcharacter.spellbook_spell_ids = _unique_string_array(data.get("spellbook_spell_ids", []))\n\tcharacter.spellbook_initialized = bool(data.get("spellbook_initialized", false))\n\tcharacter.signature_ability_id = str(data.get("signature_ability_id", ""))\n',
    "spellbook deserialization",
)
model_path.write_text(model, encoding="utf-8")


# Save version 5 safely defers old Wizard spellbook seeding to SpellcastingSystem.
state_path = ROOT / "scripts/core/game_state.gd"
state = state_path.read_text(encoding="utf-8")
state = replace_once(state, 'const SAVE_VERSION: int = 4\n', 'const SAVE_VERSION: int = 5\n', "save version")
state = replace_once(
    state,
    '''\tif version == 3:
\t\tsave_data = _migrate_version_3_to_4(save_data)
\t\tversion = 4
\tif version != SAVE_VERSION:
''',
    '''\tif version == 3:
\t\tsave_data = _migrate_version_3_to_4(save_data)
\t\tversion = 4
\tif version == 4:
\t\tsave_data = _migrate_version_4_to_5(save_data)
\t\tversion = 5
\tif version != SAVE_VERSION:
''',
    "migration chain",
)
state += '''

func _migrate_version_4_to_5(old_data: Dictionary) -> Dictionary:
\tvar migrated_data: Dictionary = old_data.duplicate(true)
\tmigrated_data["version"] = 5
\tvar character_value: Variant = migrated_data.get("player_character", {})
\tvar character_data: Dictionary = character_value as Dictionary if character_value is Dictionary else PlayerCharacter.create_legacy_default().to_dict()
\tif not character_data.has("spellbook_spell_ids"):
\t\tcharacter_data["spellbook_spell_ids"] = []
\tif not character_data.has("spellbook_initialized"):
\t\tcharacter_data["spellbook_initialized"] = false
\tmigrated_data["player_character"] = character_data
\treturn migrated_data
'''
state_path.write_text(state, encoding="utf-8")


# Structured spell-list metadata and one original executable Wizard spell for a meaningful scroll.
abilities_path = ROOT / "data/abilities/abilities.json"
abilities = json.loads(abilities_path.read_text(encoding="utf-8"))
for spell_id in [
    "detect_magic", "comprehend_languages", "fire_bolt", "poison_spray",
    "magic_missile", "burning_hands", "counterspell"
]:
    if spell_id in abilities:
        spell_lists = list(abilities[spell_id].get("spell_lists", []))
        if "wizard" not in spell_lists:
            spell_lists.append("wizard")
        abilities[spell_id]["spell_lists"] = spell_lists
abilities["caustic_pulse"] = {
    "id": "caustic_pulse",
    "name": "Едкий импульс",
    "kind": "active",
    "is_spell": True,
    "spell_level": 1,
    "school": "Воплощение",
    "spell_lists": ["wizard"],
    "rules_origin": "game_adaptation",
    "target": "enemy",
    "resource_key": "spell_slots_1",
    "description": "Оригинальное заклинание проекта: дальняя магическая атака сгустком едкой энергии, наносящая 2к6 урона кислотой.",
    "effect": "spell_attack",
    "ability": "intelligence",
    "damage_dice": [2, 6],
    "damage_type": "acid",
    "range_ft": 90,
    "casting_time_text": "1 действие",
    "components": ["v", "s", "m"],
    "material": "капля кислого раствора",
    "button": "ЕДКИЙ ИМПУЛЬС",
    "upcast": {"damage_dice_per_level": [1, 6]}
}
if "ritual_adept" in abilities:
    abilities["ritual_adept"]["description"] = "Волшебник может сотворять ритуальное заклинание из своей физической книги без подготовки, увеличивая время сотворения на 10 минут."
abilities_path.write_text(json.dumps(abilities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# Scroll item data remains separate from spell execution data.
items_path = ROOT / "data/items/items.json"
items = json.loads(items_path.read_text(encoding="utf-8"))
scrolls = {
    "spell_scroll_caustic_pulse": ("Свиток: Едкий импульс", "caustic_pulse", 1),
    "spell_scroll_detect_magic": ("Свиток: Обнаружение магии", "detect_magic", 1),
    "spell_scroll_cure_wounds": ("Свиток: Лечение ран", "cure_wounds", 1),
    "spell_scroll_counterspell": ("Свиток: Контрзаклинание", "counterspell", 3),
}
for item_id, (name, spell_id, level) in scrolls.items():
    items[item_id] = {
        "id": item_id,
        "name": name,
        "type": "spell_scroll",
        "description": "Магический свиток с формулой заклинания. Волшебник может попытаться переписать её в книгу.",
        "stackable": True,
        "max_stack": 10,
        "spell_id": spell_id,
        "spell_level": level,
    }
items_path.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# Production casting context exposes physical spellbook access.
class_data_path = ROOT / "scripts/systems/class_data_system.gd"
class_data = class_data_path.read_text(encoding="utf-8")
class_data = replace_once(
    class_data,
    '\t\t"has_required_material": has_required_material,\n\t\t"turn_token": turn_token,\n',
    '\t\t"has_required_material": has_required_material,\n\t\t"has_spellbook": state != null and bool(state.call("has_item", "spellbook")),\n\t\t"turn_token": turn_token,\n',
    "spellbook casting context",
)
class_data_path.write_text(class_data, encoding="utf-8")


# Spellcasting integration: seed book, restrict Wizard preparation, require book for unprepared rituals.
spellcasting_path = ROOT / "scripts/systems/spellcasting_system.gd"
spellcasting = spellcasting_path.read_text(encoding="utf-8")
spellcasting = replace_once(
    spellcasting,
    'var _progression: SpellcastingProgressionSystem = SpellcastingProgressionSystem.new()\n',
    'var _progression: SpellcastingProgressionSystem = SpellcastingProgressionSystem.new()\nvar _spellbook: WizardSpellbookSystem = WizardSpellbookSystem.new()\n',
    "spellbook service field",
)
spellcasting = replace_once(
    spellcasting,
    '\tfor feature_id: String in character.known_features.duplicate():\n',
    '\tchanged = _spellbook.ensure_character(character) or changed\n\tfor feature_id: String in character.known_features.duplicate():\n',
    "spellbook ensure hook",
)
spellcasting = replace_once(
    spellcasting,
    '''\tif int(spell.get("spell_level", 0)) == 0 or bool(spell.get("always_prepared", false)):
\t\treturn _success("Это заклинание всегда подготовлено.")
\tvar prepared: Array[String] = get_prepared_spell_ids(character)
''',
    '''\tif int(spell.get("spell_level", 0)) == 0 or bool(spell.get("always_prepared", false)):
\t\treturn _success("Это заклинание всегда подготовлено.")
\tif character.character_class_id == "wizard" and not _spellbook.is_in_spellbook(character, spell_id):
\t\treturn _failure("Заклинание отсутствует в книге Волшебника.")
\tvar prepared: Array[String] = get_prepared_spell_ids(character)
''',
    "Wizard preparation restriction",
)
spellcasting = replace_once(
    spellcasting,
    '''\tif as_ritual:
\t\tvar wizard_ritual_adept: bool = character.character_class_id == "wizard" and "ritual_adept" in character.known_features
\t\treturn level > 0 and bool(spell.get("ritual", false)) and not in_combat and (prepared or wizard_ritual_adept)
''',
    '''\tif as_ritual:
\t\tvar wizard_ritual_adept: bool = (
\t\t\tcharacter.character_class_id == "wizard"
\t\t\tand "ritual_adept" in character.known_features
\t\t\tand _spellbook.is_in_spellbook(character, spell_id)
\t\t\tand bool(casting_context.get("has_spellbook", false))
\t\t)
\t\treturn level > 0 and bool(spell.get("ritual", false)) and not in_combat and (prepared or wizard_ritual_adept)
''',
    "Ritual Adept book requirement",
)
spellcasting_path.write_text(spellcasting, encoding="utf-8")


# Inventory UI: scroll details and transcription action.
inventory_path = ROOT / "scripts/ui/inventory_panel.gd"
inventory = inventory_path.read_text(encoding="utf-8")
inventory = replace_once(
    inventory,
    'var _class_data: ClassDataSystem = ClassDataSystem.new()\n',
    'var _class_data: ClassDataSystem = ClassDataSystem.new()\nvar _spellbook_system: WizardSpellbookSystem = WizardSpellbookSystem.new()\n',
    "inventory spellbook service",
)
inventory = replace_once(
    inventory,
    'var _equip_button: Button\nvar _selected_entry: Dictionary = {}\n',
    'var _equip_button: Button\nvar _copy_scroll_button: Button\nvar _selected_entry: Dictionary = {}\n',
    "inventory scroll button field",
)
inventory = replace_once(
    inventory,
    '''\t_equip_button.hide()
\tdetail_column.add_child(_equip_button)
''',
    '''\t_equip_button.hide()
\tdetail_column.add_child(_equip_button)
\t_copy_scroll_button = Button.new()
\t_copy_scroll_button.name = "CopyScrollButton"
\t_copy_scroll_button.text = "ПЕРЕПИСАТЬ В КНИГУ"
\t_copy_scroll_button.custom_minimum_size = Vector2(0.0, 58.0)
\t_copy_scroll_button.add_theme_font_size_override("font_size", 19)
\t_copy_scroll_button.pressed.connect(_copy_selected_scroll)
\t_copy_scroll_button.hide()
\tdetail_column.add_child(_copy_scroll_button)
''',
    "inventory scroll button build",
)
inventory = replace_once(
    inventory,
    '''\t\t_details_label.text = "Предметы появятся здесь после получения наград, находок или добычи."
\t\t_equip_button.hide()
\t\treturn
''',
    '''\t\t_details_label.text = "Предметы появятся здесь после получения наград, находок или добычи."
\t\t_equip_button.hide()
\t\t_copy_scroll_button.hide()
\t\treturn
''',
    "empty inventory buttons",
)
inventory = replace_function(inventory, "_show_details", '''func _show_details(entry: Dictionary) -> void:
\t_selected_entry = entry.duplicate(true)
\tvar type_id: String = str(entry.get("type", "misc"))
\tvar type_name: String = {
\t\t"quest":"Квестовый предмет", "material":"Материал", "consumable":"Расходуемый предмет",
\t\t"weapon":"Оружие", "armor":"Броня", "shield":"Щит", "ammunition":"Боеприпасы",
\t\t"currency":"Валюта", "focus":"Магический фокус", "tool":"Инструмент",
\t\t"book":"Книга", "spell_scroll":"Свиток заклинания", "gear":"Снаряжение", "misc":"Прочее"
\t}.get(type_id, "Прочее")
\tvar item_id: String = str(entry.get("id", ""))
\tvar equipped: bool = _class_data.is_equipped(GameState.player_character, item_id)
\tvar equipment_text: String = "\nСостояние: ЭКИПИРОВАНО" if equipped else ""
\tvar stats_text: String = _equipment_stats(entry)
\tvar scroll_text: String = _scroll_transcription_text(entry) if type_id == "spell_scroll" else ""
\t_details_label.text = "%s\n\nТип: %s\nКоличество: %d%s%s\n\n%s%s" % [
\t\tstr(entry.get("name", "Предмет")), type_name, int(entry.get("quantity", 0)),
\t\tequipment_text, stats_text, str(entry.get("description", "Описание отсутствует.")), scroll_text
\t]
\t_equip_button.visible = type_id in ["weapon", "armor", "shield"]
\t_equip_button.disabled = equipped
\t_equip_button.text = "ЭКИПИРОВАНО" if equipped else "ЭКИПИРОВАТЬ"
\t_copy_scroll_button.visible = type_id == "spell_scroll"
\tif type_id == "spell_scroll":
\t\tvar inspection: Dictionary = _spellbook_system.inspect_scroll(GameState.player_character, item_id, GameState)
\t\t_copy_scroll_button.disabled = not bool(inspection.get("success", false))
\t\t_copy_scroll_button.text = "ПЕРЕПИСАТЬ В КНИГУ"
\telse:
\t\t_copy_scroll_button.disabled = true''')

insert_marker = 'func _equipment_stats(entry: Dictionary) -> String:\n'
scroll_methods = '''func _scroll_transcription_text(entry: Dictionary) -> String:
\tvar inspection: Dictionary = _spellbook_system.inspect_scroll(
\t\tGameState.player_character,
\t\tstr(entry.get("id", "")),
\t\tGameState
\t)
\tif not bool(inspection.get("success", false)):
\t\treturn "\n\nПереписывание: %s" % str(inspection.get("message", "Недоступно."))
\tvar minutes: int = int(inspection.get("time_minutes", 0))
\tvar hours: int = floori(float(minutes) / 60.0)
\tvar remaining_minutes: int = minutes % 60
\tvar time_text: String = "%d ч" % hours
\tif remaining_minutes > 0:
\t\ttime_text += " %d мин" % remaining_minutes
\treturn "\n\nПереписывание в книгу:\nСтоимость: %d зм · Время: %s · Проверка Магии: Сл %d\nСвиток уничтожается при успехе и провале." % [
\t\tint(inspection.get("cost_gp", 0)),
\t\ttime_text,
\t\tint(inspection.get("check_dc", 0))
\t]


func _copy_selected_scroll() -> void:
\tvar item_id: String = str(_selected_entry.get("id", ""))
\tif item_id.is_empty() or str(_selected_entry.get("type", "")) != "spell_scroll":
\t\treturn
\tvar result: Dictionary = _spellbook_system.copy_scroll_to_spellbook(
\t\tGameState.player_character,
\t\titem_id,
\t\tGameState
\t)
\t_refresh()
\tvar check_text: String = ""
\tif bool(result.get("scroll_consumed", false)):
\t\tcheck_text = "\nБросок: %d, итог %d против Сл %d." % [
\t\t\tint(result.get("natural_roll", 0)),
\t\t\tint(result.get("check_total", 0)),
\t\t\tint(result.get("check_dc", 0))
\t\t]
\t_details_label.text = "%s%s" % [str(result.get("message", "Переписывание завершено.")), check_text]


'''
if insert_marker not in inventory:
    raise RuntimeError("inventory helper marker missing")
inventory = inventory.replace(insert_marker, scroll_methods + insert_marker, 1)
inventory_path.write_text(inventory, encoding="utf-8")


# Existing ritual regression now declares physical spellbook access explicitly.
test_path = ROOT / "tests/test_spellcasting_and_rituals.gd"
test = test_path.read_text(encoding="utf-8")
test = replace_once(
    test,
    'if not spells.can_cast_spell(wizard, detect_magic, true, false):',
    'if not spells.can_cast_spell(wizard, detect_magic, true, false, 0, {"has_spellbook": true}):',
    "ritual can cast context",
)
test = replace_once(
    test,
    'var ritual_result: Dictionary = spells.cast_ritual(wizard, "detect_magic", 480, false)',
    'var ritual_result: Dictionary = spells.cast_ritual(wizard, "detect_magic", 480, false, {"has_spellbook": true})',
    "ritual cast context",
)
test = replace_once(
    test,
    'if bool(spells.cast_ritual(wizard, "detect_magic", 500, true).get("success", false)):',
    'if bool(spells.cast_ritual(wizard, "detect_magic", 500, true, {"has_spellbook": true}).get("success", false)):',
    "combat ritual context",
)
test_path.write_text(test, encoding="utf-8")

print("Wizard spellbook, scroll data, save migration, casting rules and inventory UI integration applied.")
