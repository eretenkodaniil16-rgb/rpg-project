from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


abilities_path = ROOT / "data/abilities/abilities.json"
abilities = json.loads(abilities_path.read_text(encoding="utf-8"))
abilities["counterspell"] = {
    "id": "counterspell",
    "name": "Контрзаклинание",
    "kind": "reaction",
    "is_spell": True,
    "spell_level": 3,
    "school": "Ограждение",
    "target": "spell_cast_attempt",
    "effect": "counterspell",
    "range_ft": 60,
    "casting_time_text": "Реакция",
    "casting_time_kind": "reaction",
    "reaction_trigger": "visible_creature_casts_observable_spell",
    "components": ["s"],
    "description": "Реакция на видимое сотворение заклинания в пределах 60 футов. Заклинатель совершает спасбросок Телосложения против Сл ваших заклинаний. При провале его заклинание рассеивается, действие теряется, а исходная ячейка не расходуется.",
    "button": "КОНТРЗАКЛИНАНИЕ"
}
abilities_path.write_text(json.dumps(abilities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


classes_path = ROOT / "data/classes/classes.json"
classes_root = json.loads(classes_path.read_text(encoding="utf-8"))
for class_data in classes_root.get("classes", []):
    if class_data.get("id") not in ("wizard", "sorcerer", "warlock"):
        continue
    spellcasting = class_data.setdefault("spellcasting", {})
    level_spells = spellcasting.setdefault("level_spells", {})
    fifth_level = level_spells.setdefault("5", [])
    if "counterspell" not in fifth_level:
        fifth_level.append("counterspell")
classes_path.write_text(json.dumps(classes_root, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


spell_path = ROOT / "scripts/systems/spellcasting_system.gd"
text = spell_path.read_text(encoding="utf-8")
old = '''\t\tfor spell_id: String in _string_array(profile.get("starting_spells", [])):
\t\t\tchanged = _append_unique(character.known_features, spell_id) or changed
\t\tvar had_prepared_state: bool = character.class_resources.has(PREPARED_SPELLS_STATE_KEY)
'''
new = '''\t\tfor spell_id: String in _string_array(profile.get("starting_spells", [])):
\t\t\tchanged = _append_unique(character.known_features, spell_id) or changed
\t\tvar level_spells_value: Variant = profile.get("level_spells", {})
\t\tif level_spells_value is Dictionary:
\t\t\tfor required_level_value: Variant in (level_spells_value as Dictionary).keys():
\t\t\t\tvar required_level: int = maxi(int(str(required_level_value)), 1)
\t\t\t\tif character.level < required_level:
\t\t\t\t\tcontinue
\t\t\t\tfor spell_id: String in _string_array((level_spells_value as Dictionary).get(required_level_value, [])):
\t\t\t\t\tchanged = _append_unique(character.known_features, spell_id) or changed
\t\tvar had_prepared_state: bool = character.class_resources.has(PREPARED_SPELLS_STATE_KEY)
'''
count = text.count(old)
if count != 1:
    raise RuntimeError(f"Expected one level-spell insertion point, found {count}")
spell_path.write_text(text.replace(old, new, 1), encoding="utf-8")

print("Counterspell data and level unlocks applied.")
